import json
import uuid as uuid_lib
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from .models import Order, OrderItem
from tickets.models import TicketType, Ticket
from events.models import Event, Coupon


def _build_ticket_data(ticket_types):
    """Pre-compute on_sale/availability for a list of ticket types."""
    now = timezone.now()
    ticket_data = []
    for tt in ticket_types:
        sold = Ticket.objects.filter(ticket_type=tt, order__status='paid').count()
        available = 999999 if tt.quantity == 0 else max(0, tt.quantity - sold)
        sold_out = False if tt.quantity == 0 else (available == 0)
        on_sale = (
            tt.is_active and not sold_out and
            (not tt.sales_start or now >= tt.sales_start) and
            (not tt.sales_end or now <= tt.sales_end)
        )
        ticket_data.append({
            'obj': tt,
            'available': available,
            'sold_out': sold_out,
            'on_sale': on_sale,
            'unlimited': tt.quantity == 0,
        })
    return ticket_data


@login_required
def checkout(request, event_slug):
    event = get_object_or_404(Event, slug=event_slug, status=Event.STATUS_PUBLISHED)
    ticket_types = TicketType.objects.filter(event=event, is_active=True)

    if request.method == 'POST':
        selections = {}
        for tt in ticket_types:
            qty = int(request.POST.get(f'qty_{tt.pk}', 0))
            if qty > 0:
                selections[tt] = qty

        if not selections:
            messages.error(request, 'Please select at least one ticket.')
            return redirect('events:detail', slug=event_slug)

        # Validate quantities
        for tt, qty in selections.items():
            if qty > tt.available_quantity:
                messages.error(request, f'Only {tt.available_quantity} tickets available for {tt.name}.')
                return redirect('events:detail', slug=event_slug)
            if qty > tt.max_per_order:
                messages.error(request, f'Maximum {tt.max_per_order} tickets per order for {tt.name}.')
                return redirect('events:detail', slug=event_slug)

        # Apply coupon
        coupon = None
        coupon_code = request.POST.get('coupon_code', '').strip()
        discount_amount = 0
        if coupon_code:
            try:
                coupon = Coupon.objects.get(event=event, code=coupon_code)
                if not coupon.is_valid():
                    messages.error(request, 'This coupon is invalid or expired.')
                    return redirect('events:detail', slug=event_slug)
            except Coupon.DoesNotExist:
                messages.error(request, 'Coupon code not found.')
                return redirect('events:detail', slug=event_slug)

        # Calculate totals
        subtotal = sum(tt.price * qty for tt, qty in selections.items())
        if coupon:
            if coupon.discount_type == 'percent':
                discount_amount = subtotal * (coupon.discount_value / 100)
            else:
                discount_amount = min(coupon.discount_value, subtotal)
        total = subtotal - discount_amount

        # Create order in PENDING state
        order = Order.objects.create(
            user=request.user,
            event=event,
            coupon=coupon,
            subtotal=subtotal,
            discount_amount=discount_amount,
            total_amount=total,
            status=Order.STATUS_PENDING,
        )

        # Create order items and tickets (status=valid, but order still pending)
        for tt, qty in selections.items():
            OrderItem.objects.create(
                order=order,
                ticket_type=tt,
                quantity=qty,
                unit_price=tt.price,
            )
            for _ in range(qty):
                Ticket(
                    order=order,
                    ticket_type=tt,
                    attendee_name=request.user.display_name,
                    attendee_email=request.user.email,
                ).save()

        if coupon:
            coupon.used_count += 1
            coupon.save()

        # Free order — skip payment entirely
        if total == 0:
            order.status = Order.STATUS_PAID
            order.paid_at = timezone.now()
            order.save()
            messages.success(request, 'Order confirmed! Your free tickets are ready.')
            return redirect('orders:confirmation', pk=order.pk)

        # Paid order — initialize Paystack
        from .paystack import initialize_payment
        callback_url = request.build_absolute_uri(f'/orders/paystack/callback/')
        metadata = {
            'order_id': order.pk,
            'order_number': order.order_number,
            'event': event.title,
            'cancel_action': request.build_absolute_uri(f'/orders/{order.pk}/cancel/'),
        }
        response = initialize_payment(
            email=request.user.email,
            amount_naira=total,
            reference=order.order_number,
            callback_url=callback_url,
            metadata=metadata,
        )

        if response.get('status') and response.get('data', {}).get('authorization_url'):
            return redirect(response['data']['authorization_url'])
        else:
            # Paystack failed — cancel order and show error
            order.status = Order.STATUS_CANCELLED
            order.save()
            messages.error(request, f"Payment initialization failed: {response.get('message', 'Unknown error')}. Please try again.")
            return redirect('events:detail', slug=event_slug)

    ticket_data = _build_ticket_data(ticket_types)
    return render(request, 'orders/checkout.html', {
        'event': event,
        'ticket_types': ticket_types,
        'ticket_data': ticket_data,
    })


@login_required
def paystack_callback(request):
    """
    Paystack redirects here after payment attempt.
    We verify the payment with Paystack API before confirming the order.
    """
    reference = request.GET.get('reference') or request.GET.get('trxref')
    if not reference:
        messages.error(request, 'No payment reference found.')
        return redirect('home')

    # Find the order by order_number (which we used as reference)
    order = get_object_or_404(Order, order_number=reference, user=request.user)

    if order.status == Order.STATUS_PAID:
        # Already confirmed (e.g. webhook already processed it)
        return redirect('orders:confirmation', pk=order.pk)

    from .paystack import verify_payment
    response = verify_payment(reference)

    if (
        response.get('status') and
        response.get('data', {}).get('status') == 'success'
    ):
        # Payment verified successfully
        order.status = Order.STATUS_PAID
        order.paid_at = timezone.now()
        order.paystack_reference = response['data'].get('reference', reference)
        order.save()
        messages.success(request, 'Payment confirmed! Your tickets are ready.')
        return redirect('orders:confirmation', pk=order.pk)
    else:
        order.status = Order.STATUS_CANCELLED
        order.save()
        gateway_msg = response.get('data', {}).get('gateway_response', 'Payment was not successful.')
        messages.error(request, f'Payment failed: {gateway_msg}. No charge was made.')
        return redirect('events:detail', slug=order.event.slug)


@csrf_exempt
def paystack_webhook(request):
    """
    Paystack webhook endpoint.
    Paystack POSTs payment events here for reliable server-side confirmation.
    Add this URL in your Paystack dashboard under Settings → Webhooks.
    """
    if request.method != 'POST':
        return HttpResponse(status=405)

    signature = request.headers.get('X-Paystack-Signature', '')
    from .paystack import verify_webhook_signature
    if not verify_webhook_signature(request.body, signature):
        return HttpResponse(status=401)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse(status=400)

    event_type = payload.get('event')
    data = payload.get('data', {})

    if event_type == 'transfer.success' or event_type == 'transfer.failed' or event_type == 'transfer.reversed':
        reference = data.get('reference', '')
        try:
            from organizers.models import WithdrawalRequest
            withdrawal = WithdrawalRequest.objects.get(paystack_reference=reference)
            if event_type == 'transfer.success':
                withdrawal.status = WithdrawalRequest.STATUS_COMPLETED
                from django.utils import timezone as tz
                withdrawal.processed_at = tz.now()
            elif event_type in ('transfer.failed', 'transfer.reversed'):
                withdrawal.status = WithdrawalRequest.STATUS_FAILED
                withdrawal.failure_reason = data.get('gateway_response', event_type)
            withdrawal.save()
        except Exception:
            pass

    if event_type == 'charge.success':
        reference = data.get('reference')
        try:
            order = Order.objects.get(order_number=reference, status=Order.STATUS_PENDING)
            order.status = Order.STATUS_PAID
            order.paid_at = timezone.now()
            order.paystack_reference = reference
            order.save()
        except Order.DoesNotExist:
            pass  # Order already paid or doesn't exist — safe to ignore

    return HttpResponse(status=200)


@login_required
def cancel_order(request, pk):
    """Cancel a pending order (e.g. user abandoned payment)."""
    order = get_object_or_404(Order, pk=pk, user=request.user, status=Order.STATUS_PENDING)
    order.status = Order.STATUS_CANCELLED
    order.save()
    messages.info(request, 'Order cancelled.')
    return redirect('events:detail', slug=order.event.slug)


@login_required
def order_confirmation(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    tickets = order.tickets.select_related('ticket_type', 'ticket_type__event')
    return render(request, 'orders/confirmation.html', {'order': order, 'tickets': tickets})


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    tickets = order.tickets.select_related('ticket_type')
    return render(request, 'orders/detail.html', {'order': order, 'tickets': tickets})


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/my_orders.html', {'orders': orders})


@login_required
def validate_coupon(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        code = data.get('code', '')
        event_id = data.get('event_id')
        try:
            event = Event.objects.get(pk=event_id)
            coupon = Coupon.objects.get(event=event, code=code)
            if coupon.is_valid():
                return JsonResponse({
                    'valid': True,
                    'discount_type': coupon.discount_type,
                    'discount_value': str(coupon.discount_value),
                })
            return JsonResponse({'valid': False, 'message': 'Coupon is expired or invalid.'})
        except (Event.DoesNotExist, Coupon.DoesNotExist):
            return JsonResponse({'valid': False, 'message': 'Coupon not found.'})
    return JsonResponse({'valid': False, 'message': 'Invalid request.'})


@login_required
def organizer_orders(request):
    from organizers.models import OrganizerProfile
    organizer = get_object_or_404(OrganizerProfile, user=request.user)
    orders = Order.objects.filter(
        event__organizer=organizer
    ).select_related('user', 'event').order_by('-created_at')
    from refunds.models import RefundRequest
    from organizers.models import StaffRequest
    return render(request, 'orders/organizer_orders.html', {
        'orders': orders,
        'organizer': organizer,
        'pending_refund_count': RefundRequest.objects.filter(
            order__event__organizer=organizer, status=RefundRequest.STATUS_PENDING
        ).count(),
        'pending_staff_count': StaffRequest.objects.filter(
            organizer=organizer, status=StaffRequest.STATUS_PENDING
        ).count(),
    })
