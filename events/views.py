from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils.text import slugify
from django.views.generic import ListView, DetailView
from .models import Event, Category, Coupon
from .forms import EventForm, CouponForm
from organizers.models import OrganizerProfile
from tickets.models import TicketType


class HomeView(ListView):
    template_name = 'events/home.html'
    context_object_name = 'events'
    paginate_by = 12

    def get_queryset(self):
        qs = Event.objects.filter(
            status=Event.STATUS_PUBLISHED, is_private=False
        ).select_related('organizer', 'category').order_by('-start_date')
        q = self.request.GET.get('q')
        city = self.request.GET.get('city')
        category = self.request.GET.get('category')
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q) | Q(city__icontains=q))
        if city:
            qs = qs.filter(city__icontains=city)
        if category:
            qs = qs.filter(category__slug=category)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = Category.objects.all()
        ctx['search_query'] = self.request.GET.get('q', '')
        ctx['selected_city'] = self.request.GET.get('city', '')
        return ctx


class EventDetailView(DetailView):
    model = Event
    template_name = 'events/detail.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        from django.db.models import Q
        base_qs = Event.objects.select_related("organizer", "category")
        if self.request.user.is_authenticated:
            return base_qs.filter(
                Q(status=Event.STATUS_PUBLISHED) | Q(organizer__user=self.request.user)
            )
        return base_qs.filter(status=Event.STATUS_PUBLISHED)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Pass ALL ticket types to organizer, only active ones to public
        user = self.request.user
        is_owner = (
            user.is_authenticated and
            hasattr(user, 'organizer_profile') and
            user.organizer_profile == self.object.organizer
        )
        if is_owner:
            ctx['ticket_types'] = TicketType.objects.filter(event=self.object)
        else:
            ctx['ticket_types'] = TicketType.objects.filter(event=self.object, is_active=True)
        ctx['is_owner'] = is_owner
        return ctx


@login_required
def create_event(request):
    try:
        organizer = request.user.organizer_profile
    except OrganizerProfile.DoesNotExist:
        messages.error(request, 'You need an organizer profile to create events.')
        return redirect('organizers:setup')

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = organizer
            base_slug = slugify(event.title)
            slug = base_slug
            counter = 1
            while Event.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            event.slug = slug
            event.save()
            messages.success(request, 'Event created! Add ticket types to publish.')
            return redirect('events:manage', slug=event.slug)
    else:
        form = EventForm()

    return render(request, 'events/create.html', {'form': form})


@login_required
def manage_event(request, slug):
    organizer = get_object_or_404(OrganizerProfile, user=request.user)
    event = get_object_or_404(Event, slug=slug, organizer=organizer)
    ticket_types = TicketType.objects.filter(event=event)
    coupons = Coupon.objects.filter(event=event)
    return render(request, 'events/manage.html', {
        'event': event,
        'ticket_types': ticket_types,
        'coupons': coupons,
    })


@login_required
def edit_event(request, slug):
    organizer = get_object_or_404(OrganizerProfile, user=request.user)
    event = get_object_or_404(Event, slug=slug, organizer=organizer)

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event updated.')
            return redirect('events:manage', slug=event.slug)
    else:
        form = EventForm(instance=event)

    return render(request, 'events/edit.html', {'form': form, 'event': event})


@login_required
def publish_event(request, slug):
    organizer = get_object_or_404(OrganizerProfile, user=request.user)
    event = get_object_or_404(Event, slug=slug, organizer=organizer)
    if request.method == 'POST':
        if not TicketType.objects.filter(event=event).exists():
            messages.error(request, 'Add at least one ticket type before publishing.')
        else:
            event.status = Event.STATUS_PUBLISHED
            event.save()
            messages.success(request, 'Event published!')
    return redirect('events:manage', slug=slug)


@login_required
def cancel_event(request, slug):
    organizer = get_object_or_404(OrganizerProfile, user=request.user)
    event = get_object_or_404(Event, slug=slug, organizer=organizer)
    if request.method == 'POST':
        event.status = Event.STATUS_CANCELLED
        event.save()
        messages.warning(request, 'Event has been cancelled.')
    return redirect('events:manage', slug=slug)


@login_required
def add_coupon(request, slug):
    organizer = get_object_or_404(OrganizerProfile, user=request.user)
    event = get_object_or_404(Event, slug=slug, organizer=organizer)
    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            coupon = form.save(commit=False)
            coupon.event = event
            coupon.save()
            messages.success(request, 'Coupon created.')
            return redirect('events:manage', slug=slug)
    else:
        form = CouponForm()
    return render(request, 'events/add_coupon.html', {'form': form, 'event': event})