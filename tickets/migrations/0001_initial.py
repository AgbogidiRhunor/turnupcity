import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('events', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TicketType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('quantity', models.PositiveIntegerField(default=0)),
                ('max_per_order', models.PositiveIntegerField(default=10)),
                ('sales_start', models.DateTimeField(blank=True, null=True)),
                ('sales_end', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('event', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='ticket_types',
                    to='events.event',
                )),
            ],
        ),
        migrations.CreateModel(
            name='Ticket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('status', models.CharField(
                    choices=[
                        ('valid', 'Valid'),
                        ('used', 'Used'),
                        ('cancelled', 'Cancelled'),
                        ('refunded', 'Refunded'),
                    ],
                    default='valid', max_length=20,
                )),
                ('qr_code', models.ImageField(blank=True, null=True, upload_to='qr_codes/')),
                ('attendee_name', models.CharField(blank=True, max_length=200)),
                ('attendee_email', models.EmailField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('ticket_type', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to='tickets.tickettype',
                )),
            ],
        ),
        migrations.CreateModel(
            name='ScanLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scanned_at', models.DateTimeField(auto_now_add=True)),
                ('gate', models.CharField(blank=True, max_length=100)),
                ('success', models.BooleanField(default=True)),
                ('message', models.CharField(blank=True, max_length=255)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('scanned_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to=settings.AUTH_USER_MODEL,
                )),
                ('ticket', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='scan_logs',
                    to='tickets.ticket',
                )),
            ],
        ),
    ]
