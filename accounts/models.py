from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_GUEST = 'guest'
    ROLE_ORGANIZER = 'organizer'
    ROLE_STAFF = 'staff'
    ROLE_ADMIN = 'admin'

    ROLE_CHOICES = [
        (ROLE_GUEST, 'Guest / Attendee'),
        (ROLE_ORGANIZER, 'Organizer'),
        (ROLE_STAFF, 'Staff / Check-in Agent'),
        (ROLE_ADMIN, 'Platform Admin'),
    ]

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_GUEST)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    @property
    def is_organizer(self):
        return self.role == self.ROLE_ORGANIZER

    @property
    def is_staff_agent(self):
        return self.role == self.ROLE_STAFF

    @property
    def is_platform_admin(self):
        return self.role == self.ROLE_ADMIN or self.is_superuser

    @property
    def display_name(self):
        return self.get_full_name() or self.username or self.email.split('@')[0]
