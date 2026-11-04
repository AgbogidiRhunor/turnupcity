from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from orders.models import Order
from .models import RefundRequest, RefundAuditLog
from organizers.models import OrganizerProfile


@login_required
def request_refund(request, order_pk):
    order = get_object_or_404(Order, pk=order_pk, user=request.user)

    if order.status != Order.STATUS_PAID:
        messages.error(request, 'Only paid orders can be refunded.')
        return redirect('orders:detail', pk=order_pk)

    if not order.event.refund_eligible:
        messages.error(request, 'The refund deadline has passed for this event.')
        return redirect('orders:detail', pk=order_pk)

    if RefundRequest.objects.filter(order=order, status__in=[
        RefundRequest.STATUS_PENDING, RefundRequest.STATUS_APPROVED
    ]).exists():
        messages.info(request, 'A refund request already exists for this order.')
        return redirect('orders:detail', pk=order_pk)

    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        if not reason:
            messages.error(request, 'Please provide a reason for the refund.')
        else:
            rr = RefundRequest.objects.create(
                order=order,
                requested_by=request.user,
                reason=reason,
                refund_amount=order.total_amount,
            )
            RefundAuditLog.objects.create(
                refund_request=rr,
                action='Refund requested',
                performed_by=request.user,
                notes=reason,
            )
            messages.success(request, 'Refund request submitted. We\'ll review it shortly.')
            return redirect('orders:detail', pk=order_pk)

    return render(request, 'refunds/request.html', {'order': order})


@login_required
def organizer_refunds(request):
    organizer = get_object_or_404(OrganizerProfile, user=request.user)
    refunds = RefundRequest.objects.filter(
        order__event__organizer=organizer
    ).select_related('order', 'requested_by', 'order__event').order_by('-created_at')
    from organizers.models import StaffRequest
    pending_staff_count = StaffRequest.objects.filter(
        organizer=organizer, status=StaffRequest.STATUS_PENDING
    ).count()
    pending_refund_count = refunds.filter(status=RefundRequest.STATUS_PENDING).count()
    return render(request, 'refunds/organizer_list.html', {
        'refunds': refunds,
        'organizer': organizer,
        'pending_refund_count': pending_refund_count,
        'pending_staff_count': pending_staff_count,
    })


@login_required
def process_refund(request, pk):
    organizer = get_object_or_404(OrganizerProfile, user=request.user)
    refund = get_object_or_404(RefundRequest, pk=pk, order__event__organizer=organizer)

    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')

        if action == 'approve':
            refund.status = RefundRequest.STATUS_APPROVED
            refund.reviewed_by = request.user
            refund.reviewer_notes = notes
            refund.reviewed_at = timezone.now()
            refund.save()

            # Mark order as refunded
            refund.order.status = Order.STATUS_REFUNDED
            refund.order.save()

            # Mark tickets as refunded
            refund.order.tickets.update(status='refunded')

            RefundAuditLog.objects.create(
                refund_request=refund,
                action='Approved by organizer',
                performed_by=request.user,
                notes=notes,
            )
            messages.success(request, 'Refund approved.')

        elif action == 'reject':
            refund.status = RefundRequest.STATUS_REJECTED
            refund.reviewed_by = request.user
            refund.reviewer_notes = notes
            refund.reviewed_at = timezone.now()
            refund.save()
            RefundAuditLog.objects.create(
                refund_request=refund,
                action='Rejected by organizer',
                performed_by=request.user,
                notes=notes,
            )
            messages.info(request, 'Refund rejected.')

    return redirect('refunds:organizer_list')


@login_required
def my_refunds(request):
    refunds = RefundRequest.objects.filter(
        requested_by=request.user
    ).select_related('order', 'order__event').order_by('-created_at')
    return render(request, 'refunds/my_refunds.html', {'refunds': refunds})
