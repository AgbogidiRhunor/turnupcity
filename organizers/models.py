from django.db import models
from accounts.models import User


class OrganizerProfile(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_VERIFIED = 'verified'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_VERIFIED, 'Verified'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='organizer_profile')
    organization_name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='organizer_logos/', blank=True, null=True)
    website = models.URLField(blank=True)
    twitter = models.CharField(max_length=100, blank=True)
    instagram = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.organization_name

    @property
    def is_verified(self):
        return self.status == self.STATUS_VERIFIED


class StaffRequest(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='staff_requests')
    organizer = models.ForeignKey(OrganizerProfile, on_delete=models.CASCADE, related_name='staff_requests')
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'organizer')

    def __str__(self):
        return f"{self.user.email} → {self.organizer.organization_name}"


class StaffMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='staff_memberships')
    organizer = models.ForeignKey(OrganizerProfile, on_delete=models.CASCADE, related_name='staff_members')
    can_scan = models.BooleanField(default=True)
    can_manage_orders = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'organizer')

    def __str__(self):
        return f"{self.user.email} @ {self.organizer.organization_name}"

class BankAccount(models.Model):
    """Organizer's saved bank account for withdrawals."""
    organizer = models.OneToOneField(
        OrganizerProfile, on_delete=models.CASCADE, related_name='bank_account'
    )
    bank_name = models.CharField(max_length=100)
    bank_code = models.CharField(max_length=10)
    account_number = models.CharField(max_length=20)
    account_name = models.CharField(max_length=200)
    paystack_recipient_code = models.CharField(max_length=100, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.account_name} — {self.bank_name} ({self.account_number})"


class WithdrawalRequest(models.Model):
    STATUS_PENDING   = 'pending'
    STATUS_APPROVED  = 'approved'
    STATUS_PROCESSING = 'processing'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED    = 'failed'
    STATUS_CHOICES = [
        (STATUS_PENDING,    'Pending'),
        (STATUS_APPROVED,   'Approved'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_COMPLETED,  'Completed'),
        (STATUS_FAILED,     'Failed'),
    ]

    organizer = models.ForeignKey(
        OrganizerProfile, on_delete=models.CASCADE, related_name='withdrawals'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    paystack_transfer_code = models.CharField(max_length=100, blank=True)
    paystack_reference = models.CharField(max_length=100, blank=True)
    failure_reason = models.TextField(blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-requested_at']

    def __str__(self):
        return f"{self.organizer.organization_name} — ₦{self.amount} ({self.get_status_display()})"
