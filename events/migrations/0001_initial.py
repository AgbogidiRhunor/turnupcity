from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('organizers', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('slug', models.SlugField(unique=True)),
                ('icon', models.CharField(blank=True, max_length=50)),
            ],
            options={
                'verbose_name_plural': 'categories',
            },
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('slug', models.SlugField(unique=True)),
                ('description', models.TextField()),
                ('banner', models.ImageField(blank=True, null=True, upload_to='event_banners/')),
                ('status', models.CharField(
                    choices=[
                        ('draft', 'Draft'),
                        ('published', 'Published'),
                        ('cancelled', 'Cancelled'),
                        ('completed', 'Completed'),
                    ],
                    default='draft', max_length=20,
                )),
                ('is_private', models.BooleanField(default=False)),
                ('venue_name', models.CharField(max_length=255)),
                ('venue_address', models.TextField()),
                ('venue_map_link', models.URLField(blank=True)),
                ('city', models.CharField(max_length=100)),
                ('country', models.CharField(default='US', max_length=100)),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField()),
                ('refund_deadline', models.DateTimeField(blank=True, null=True)),
                ('capacity', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='events.category',
                )),
                ('organizer', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='events',
                    to='organizers.organizerprofile',
                )),
            ],
        ),
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=50)),
                ('discount_type', models.CharField(
                    choices=[('percent', 'Percent'), ('fixed', 'Fixed')],
                    default='percent', max_length=10,
                )),
                ('discount_value', models.DecimalField(decimal_places=2, max_digits=10)),
                ('max_uses', models.PositiveIntegerField(default=0)),
                ('used_count', models.PositiveIntegerField(default=0)),
                ('valid_from', models.DateTimeField()),
                ('valid_until', models.DateTimeField()),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('event', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='coupons',
                    to='events.event',
                )),
            ],
            options={
                'unique_together': {('event', 'code')},
            },
        ),
    ]
