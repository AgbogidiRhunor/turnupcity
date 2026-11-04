from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Thread, Message
from organizers.models import OrganizerProfile


@login_required
def inbox(request):
    user = request.user
    if hasattr(user, 'organizer_profile'):
        threads = Thread.objects.filter(organizer=user.organizer_profile)
    else:
        threads = Thread.objects.filter(participant=user)
    return render(request, 'messaging/inbox.html', {'threads': threads})


@login_required
def thread_detail(request, pk):
    user = request.user
    thread = get_object_or_404(Thread, pk=pk)

    # Check permission
    is_organizer = hasattr(user, 'organizer_profile') and thread.organizer == user.organizer_profile
    is_participant = thread.participant == user
    if not (is_organizer or is_participant or user.is_platform_admin):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    # Mark messages as read
    thread.messages.exclude(sender=user).update(is_read=True)

    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        if body:
            Message.objects.create(thread=thread, sender=user, body=body)
            thread.save()  # updates updated_at
        return redirect('messaging:thread', pk=pk)

    return render(request, 'messaging/thread.html', {'thread': thread})


@login_required
def start_thread(request, organizer_slug):
    organizer = get_object_or_404(OrganizerProfile, slug=organizer_slug)
    if organizer.user == request.user:
        messages.error(request, "You can't message yourself.")
        return redirect('organizers:dashboard')

    thread, created = Thread.objects.get_or_create(
        organizer=organizer,
        participant=request.user,
        defaults={'subject': f'Message to {organizer.organization_name}'}
    )

    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        if body:
            Message.objects.create(thread=thread, sender=request.user, body=body)
            thread.save()
            messages.success(request, 'Message sent!')
            return redirect('messaging:thread', pk=thread.pk)

    return render(request, 'messaging/start_thread.html', {'organizer': organizer, 'thread': thread})
