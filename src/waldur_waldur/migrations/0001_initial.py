# Generated by Django 2.2.13 on 2021-01-18 11:52

import django.db.models.deletion
from django.db import migrations, models

import waldur_core.core.fields
import waldur_core.core.models
import waldur_core.logging.loggers
import waldur_core.structure.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('structure', '0020_drop_servicecertification_model'),
    ]

    operations = [
        migrations.CreateModel(
            name='RemoteWaldurService',
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
                    'available_for_all',
                    models.BooleanField(
                        default=False,
                        help_text='Service will be automatically added to all customers projects if it is available for all',
                    ),
                ),
                (
                    'customer',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='structure.Customer',
                        verbose_name='organization',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Remote Waldur provider',
                'verbose_name_plural': 'Remote Waldur providers',
            },
            bases=(
                waldur_core.core.models.DescendantMixin,
                waldur_core.structure.models.StructureLoggableMixin,
                models.Model,
            ),
        ),
        migrations.CreateModel(
            name='RemoteWaldurServiceProjectLink',
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
                (
                    'project',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='structure.Project',
                    ),
                ),
                (
                    'service',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='waldur_waldur.RemoteWaldurService',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Remote Waldur provider project link',
                'verbose_name_plural': 'Remote Waldur provider project links',
                'abstract': False,
                'unique_together': {('service', 'project')},
            },
            bases=(
                waldur_core.core.models.DescendantMixin,
                waldur_core.logging.loggers.LoggableMixin,
                models.Model,
            ),
        ),
        migrations.AddField(
            model_name='remotewaldurservice',
            name='projects',
            field=models.ManyToManyField(
                related_name='remote_waldur_services',
                through='waldur_waldur.RemoteWaldurServiceProjectLink',
                to='structure.Project',
            ),
        ),
        migrations.AddField(
            model_name='remotewaldurservice',
            name='settings',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='structure.ServiceSettings',
            ),
        ),
        migrations.AlterUniqueTogether(
            name='remotewaldurservice', unique_together={('customer', 'settings')},
        ),
    ]
