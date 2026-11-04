import csv
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Sum, Count
from organizers.models import OrganizerProfile
from events.models import Event
from orders.models import Order
from tickets.models import Ticket, ScanLog


@login_required
def organizer_analytics(request):
    organizer = get_object_or_404(OrganizerProfile, user=request.user)
    events = Event.objects.filter(organizer=organizer).order_by('-start_date')

    event_stats = []
    for event in events:
        tickets_sold = Ticket.objects.filter(
            ticket_type__event=event,
            order__status=Order.STATUS_PAID
        ).count()
        revenue = Order.objects.filter(
            event=event, status=Order.STATUS_PAID
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        checked_in = Ticket.objects.filter(
            ticket_type__event=event,
            status=Ticket.STATUS_USED
        ).count()
        event_stats.append({
            'event': event,
            'tickets_sold': tickets_sold,
            'revenue': revenue,
            'checked_in': checked_in,
            'attendance_pct': (checked_in / tickets_sold * 100) if tickets_sold > 0 else 0,
        })

    total_revenue = sum(s['revenue'] for s in event_stats)
    total_tickets = sum(s['tickets_sold'] for s in event_stats)
    total_checkins = sum(s['checked_in'] for s in event_stats)

    from refunds.models import RefundRequest
    from organizers.models import StaffRequest
    pending_refund_count = RefundRequest.objects.filter(
        order__event__organizer=organizer, status=RefundRequest.STATUS_PENDING
    ).count()
    pending_staff_count = StaffRequest.objects.filter(
        organizer=organizer, status=StaffRequest.STATUS_PENDING
    ).count()

    return render(request, 'analytics/dashboard.html', {
        'organizer': organizer,
        'event_stats': event_stats,
        'total_revenue': total_revenue,
        'total_tickets': total_tickets,
        'total_checkins': total_checkins,
        'pending_refund_count': pending_refund_count,
        'pending_staff_count': pending_staff_count,
    })


@login_required
def event_analytics(request, event_slug):
    organizer = get_object_or_404(OrganizerProfile, user=request.user)
    event = get_object_or_404(Event, slug=event_slug, organizer=organizer)

    tickets_by_type = Ticket.objects.filter(
        ticket_type__event=event, order__status=Order.STATUS_PAID
    ).values('ticket_type__name').annotate(count=Count('id'))

    revenue_by_type = Order.objects.filter(
        event=event, status=Order.STATUS_PAID
    ).values('items__ticket_type__name').annotate(total=Sum('items__total_price'))

    recent_orders = Order.objects.filter(event=event).order_by('-created_at')[:20]
    scan_logs = ScanLog.objects.filter(
        ticket__ticket_type__event=event
    ).order_by('-scanned_at')[:50]

    return render(request, 'analytics/event_detail.html', {
        'organizer': organizer,
        'event': event,
        'tickets_by_type': list(tickets_by_type),
        'revenue_by_type': list(revenue_by_type),
        'recent_orders': recent_orders,
        'scan_logs': scan_logs,
    })


@login_required
def export_csv(request, event_slug):
    organizer = get_object_or_404(OrganizerProfile, user=request.user)
    event = get_object_or_404(Event, slug=event_slug, organizer=organizer)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{event.slug}-attendees.csv"'

    writer = csv.writer(response)
    writer.writerow(['Order #', 'Attendee Name', 'Email', 'Ticket Type', 'Status', 'Purchased At'])

    tickets = Ticket.objects.filter(
        ticket_type__event=event
    ).select_related('order', 'ticket_type', 'order__user')

    for ticket in tickets:
        writer.writerow([
            ticket.order.order_number,
            ticket.attendee_name or ticket.order.user.display_name,
            ticket.attendee_email or ticket.order.user.email,
            ticket.ticket_type.name,
            ticket.get_status_display(),
            ticket.created_at.strftime('%Y-%m-%d %H:%M'),
        ])

    return response


@login_required
def broadcast_email(request, event_slug):
    organizer = get_object_or_404(OrganizerProfile, user=request.user)
    event = get_object_or_404(Event, slug=event_slug, organizer=organizer)

    if request.method == 'POST':
        subject = request.POST.get('subject', '')
        message_body = request.POST.get('message', '')

        if subject and message_body:
            from django.core.mail import send_mail
            attendees = Order.objects.filter(
                event=event, status=Order.STATUS_PAID
            ).values_list('user__email', flat=True).distinct()

            send_mail(
                subject=f"[{event.title}] {subject}",
                message=message_body,
                from_email=None,
                recipient_list=list(attendees),
                fail_silently=True,
            )
            from django.contrib import messages as msg
            msg.success(request, f'Email broadcast sent to {len(list(attendees))} attendees.')
            return redirect('analytics:event_detail', event_slug=event_slug)

    return render(request, 'analytics/broadcast.html', {'event': event, 'organizer': organizer})
