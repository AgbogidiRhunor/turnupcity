from django.db import models
from django.utils import timezone
from organizers.models import OrganizerProfile


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'categories'


class Event(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_PUBLISHED = 'published'
    STATUS_CANCELLED = 'cancelled'
    STATUS_COMPLETED = 'completed'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_PUBLISHED, 'Published'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_COMPLETED, 'Completed'),
    ]

    organizer = models.ForeignKey(OrganizerProfile, on_delete=models.CASCADE, related_name='events')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    banner = models.ImageField(upload_to='event_banners/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    is_private = models.BooleanField(default=False)

    venue_name = models.CharField(max_length=255)
    venue_address = models.TextField()
    venue_map_link = models.URLField(blank=True)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='US')

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    refund_deadline = models.DateTimeField(null=True, blank=True)

    capacity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    @property
    def is_upcoming(self):
        return self.start_date > timezone.now()

    @property
    def is_past(self):
        return self.end_date < timezone.now()

    @property
    def tickets_sold(self):
        from tickets.models import Ticket
        return Ticket.objects.filter(
            ticket_type__event=self,
            order__status__in=['paid']
        ).count()

    @property
    def attendance_percentage(self):
        if self.capacity == 0:
            return 0
        return min(100, int((self.tickets_sold / self.capacity) * 100))

    @property
    def refund_eligible(self):
        if self.refund_deadline:
            return timezone.now() < self.refund_deadline
        return False


class Coupon(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='coupons')
    code = models.CharField(max_length=50)
    discount_type = models.CharField(max_length=10, choices=[('percent', 'Percent'), ('fixed', 'Fixed')], default='percent')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    max_uses = models.PositiveIntegerField(default=0)
    used_count = models.PositiveIntegerField(default=0)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event', 'code')

    def __str__(self):
        return f"{self.code} ({self.event.title})"

    def is_valid(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if now < self.valid_from or now > self.valid_until:
            return False
        if self.max_uses > 0 and self.used_count >= self.max_uses:
            return False
        return True
