# Generated by Django 2.2.13 on 2020-11-25 19:36

import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
from django.conf import settings
from django.db import migrations, models

import waldur_core.core.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('marketplace', '0034_change_offering_geo_data'),
    ]

    operations = [
        migrations.CreateModel(
            name='OfferingPermission',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('uuid', waldur_core.core.fields.UUIDField()),
                (
                    'created',
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now, editable=False
                    ),
                ),
                ('expiration_time', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.NullBooleanField(db_index=True, default=True)),
                (
                    'created_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='+',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'offering',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='permissions',
                        to='marketplace.Offering',
                    ),
                ),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={'unique_together': {('offering', 'user', 'is_active')},},
        ),
    ]
