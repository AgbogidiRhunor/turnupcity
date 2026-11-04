from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404
from .models import TicketType, Ticket
from .forms import TicketTypeForm
from events.models import Event
from organizers.models import OrganizerProfile


@login_required
def add_ticket_type(request, event_slug):
    organizer = get_object_or_404(OrganizerProfile, user=request.user)
    event = get_object_or_404(Event, slug=event_slug, organizer=organizer)

    if request.method == 'POST':
        form = TicketTypeForm(request.POST)
        if form.is_valid():
            tt = form.save(commit=False)
            tt.event = event
            tt.save()
            messages.success(request, f'Ticket type "{tt.name}" created.')
            return redirect('events:manage', slug=event_slug)
    else:
        form = TicketTypeForm()

    return render(request, 'tickets/add_ticket_type.html', {'form': form, 'event': event})


@login_required
def edit_ticket_type(request, pk):
    tt = get_object_or_404(TicketType, pk=pk)
    if tt.event.organizer.user != request.user:
        raise Http404

    if request.method == 'POST':
        form = TicketTypeForm(request.POST, instance=tt)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ticket type updated.')
            return redirect('events:manage', slug=tt.event.slug)
    else:
        form = TicketTypeForm(instance=tt)

    return render(request, 'tickets/edit_ticket_type.html', {'form': form, 'ticket_type': tt})


@login_required
def ticket_detail(request, uuid):
    ticket = get_object_or_404(Ticket, uuid=uuid)
    if ticket.order.user != request.user and not request.user.is_platform_admin:
        raise Http404
    return render(request, 'tickets/ticket_detail.html', {'ticket': ticket})
