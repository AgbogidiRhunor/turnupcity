import uuid
import qrcode
from io import BytesIO
from django.db import models
from django.core.files import File
from django.conf import settings
from events.models import Event


class TicketType(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='ticket_types')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(
        default=100,
        help_text="Total number of tickets available. Set to 0 for unlimited."
    )
    max_per_order = models.PositiveIntegerField(default=10)
    sales_start = models.DateTimeField(
        null=True, blank=True,
        help_text="Leave blank to start selling immediately."
    )
    sales_end = models.DateTimeField(
        null=True, blank=True,
        help_text="Leave blank to sell until the event starts."
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.event.title}"

    @property
    def available_quantity(self):
        """How many tickets are still available for purchase."""
        if self.quantity == 0:
            return 999999  # unlimited
        sold = Ticket.objects.filter(
            ticket_type=self,
            order__status="paid"  # only count confirmed paid orders
        ).count()
        return max(0, self.quantity - sold)

    @property
    def is_sold_out(self):
        if self.quantity == 0:
            return False  # unlimited stock never sells out
        return self.available_quantity == 0

    @property
    def is_on_sale(self):
        from django.utils import timezone
        if not self.is_active:
            return False
        if self.is_sold_out:
            return False
        now = timezone.now()
        if self.sales_start and now < self.sales_start:
            return False
        if self.sales_end and now > self.sales_end:
            return False
        return True


class Ticket(models.Model):
    STATUS_VALID = "valid"
    STATUS_USED = "used"
    STATUS_CANCELLED = "cancelled"
    STATUS_REFUNDED = "refunded"
    STATUS_CHOICES = [
        (STATUS_VALID, "Valid"),
        (STATUS_USED, "Used"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_REFUNDED, "Refunded"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, related_name="tickets")
    ticket_type = models.ForeignKey(TicketType, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_VALID)
    qr_code = models.ImageField(upload_to="qr_codes/", blank=True, null=True)
    attendee_name = models.CharField(max_length=200, blank=True)
    attendee_email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket {self.uuid} - {self.ticket_type.event.title}"

    def generate_qr_code(self):
        qr_data = f"TURNUPCITY:{self.uuid}"
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        filename = f"ticket_{self.uuid}.png"
        self.qr_code.save(filename, File(buffer), save=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and not self.qr_code:
            self.generate_qr_code()


class ScanLog(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="scan_logs")
    scanned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    scanned_at = models.DateTimeField(auto_now_add=True)
    gate = models.CharField(max_length=100, blank=True)
    success = models.BooleanField(default=True)
    message = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"Scan {self.ticket.uuid} at {self.scanned_at}"