import json
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from tickets.models import Ticket, ScanLog
from events.models import Event
from organizers.models import OrganizerProfile, StaffMembership


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


@login_required
def scanner_dashboard(request, event_slug=None):
    user = request.user
    if event_slug:
        event = get_object_or_404(Event, slug=event_slug)
        # Check permission
        is_organizer = hasattr(user, 'organizer_profile') and user.organizer_profile == event.organizer
        is_staff = StaffMembership.objects.filter(
            user=user, organizer=event.organizer, is_active=True
        ).exists()
        if not (is_organizer or is_staff or user.is_platform_admin):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        recent_scans = ScanLog.objects.filter(
            ticket__ticket_type__event=event
        ).select_related('ticket', 'scanned_by').order_by('-scanned_at')[:50]
        return render(request, 'checkin/scanner.html', {
            'event': event,
            'recent_scans': recent_scans,
        })
    else:
        # Show all events the user can check in for
        if hasattr(user, 'organizer_profile'):
            events = Event.objects.filter(organizer=user.organizer_profile, status=Event.STATUS_PUBLISHED)
        else:
            memberships = StaffMembership.objects.filter(user=user, is_active=True)
            organizer_ids = memberships.values_list('organizer_id', flat=True)
            events = Event.objects.filter(organizer_id__in=organizer_ids, status=Event.STATUS_PUBLISHED)
        return render(request, 'checkin/select_event.html', {'events': events})


@login_required
def scan_ticket(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method.'}, status=405)

    data = json.loads(request.body)
    qr_data = data.get('qr_data', '').strip()
    event_slug = data.get('event_slug', '')
    gate = data.get('gate', '')

    # Parse QR
    if not qr_data.startswith('TURNUPCITY:'):
        return JsonResponse({'success': False, 'message': 'Invalid QR code format.'})

    ticket_uuid = qr_data.replace('TURNUPCITY:', '')

    try:
        ticket = Ticket.objects.get(uuid=ticket_uuid)
    except Ticket.DoesNotExist:
        ScanLog.objects.create(
            ticket_id=None,
            scanned_by=request.user,
            gate=gate,
            success=False,
            message='Ticket not found.',
            ip_address=get_client_ip(request)
        ) if False else None  # Can't create without ticket FK
        return JsonResponse({'success': False, 'message': 'Ticket not found.'})

    event = ticket.ticket_type.event

    # Verify event match
    if event_slug and event.slug != event_slug:
        ScanLog.objects.create(
            ticket=ticket, scanned_by=request.user, gate=gate,
            success=False, message='Ticket belongs to a different event.',
            ip_address=get_client_ip(request)
        )
        return JsonResponse({'success': False, 'message': 'This ticket is for a different event.'})

    # Check permissions
    user = request.user
    is_organizer = hasattr(user, 'organizer_profile') and user.organizer_profile == event.organizer
    is_staff = StaffMembership.objects.filter(user=user, organizer=event.organizer, is_active=True).exists()
    if not (is_organizer or is_staff or user.is_platform_admin):
        return JsonResponse({'success': False, 'message': 'You do not have permission to scan for this event.'})

    # Check ticket status
    if ticket.status == Ticket.STATUS_USED:
        last_scan = ScanLog.objects.filter(ticket=ticket, success=True).order_by('-scanned_at').first()
        msg = f'Already checked in'
        if last_scan:
            msg += f' at {last_scan.scanned_at.strftime("%H:%M %b %d")}'
        ScanLog.objects.create(
            ticket=ticket, scanned_by=request.user, gate=gate,
            success=False, message=msg, ip_address=get_client_ip(request)
        )
        return JsonResponse({
            'success': False,
            'already_used': True,
            'message': msg,
            'attendee_name': ticket.attendee_name,
            'ticket_type': ticket.ticket_type.name,
        })

    if ticket.status != Ticket.STATUS_VALID:
        msg = f'Ticket is {ticket.get_status_display()}.'
        ScanLog.objects.create(
            ticket=ticket, scanned_by=request.user, gate=gate,
            success=False, message=msg, ip_address=get_client_ip(request)
        )
        return JsonResponse({'success': False, 'message': msg})

    # Check order paid
    if ticket.order.status != 'paid':
        msg = 'Order not paid.'
        ScanLog.objects.create(
            ticket=ticket, scanned_by=request.user, gate=gate,
            success=False, message=msg, ip_address=get_client_ip(request)
        )
        return JsonResponse({'success': False, 'message': msg})

    # Mark as used
    ticket.status = Ticket.STATUS_USED
    ticket.save()

    ScanLog.objects.create(
        ticket=ticket, scanned_by=request.user, gate=gate,
        success=True, message='Checked in successfully.',
        ip_address=get_client_ip(request)
    )

    return JsonResponse({
        'success': True,
        'message': 'Check-in successful!',
        'attendee_name': ticket.attendee_name,
        'ticket_type': ticket.ticket_type.name,
        'event_name': event.title,
    })


@login_required
def manual_lookup(request):
    query = request.GET.get('q', '')
    tickets = []
    if query:
        from tickets.models import Ticket
        tickets = Ticket.objects.filter(
            uuid__icontains=query.replace('-', '')
        ) | Ticket.objects.filter(attendee_email__icontains=query) | Ticket.objects.filter(attendee_name__icontains=query)
        tickets = tickets[:20]
    return render(request, 'checkin/manual_lookup.html', {'tickets': tickets, 'query': query})
