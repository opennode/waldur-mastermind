# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-06-06 12:17
from __future__ import unicode_literals

import django.utils.timezone
import model_utils.fields
from django.db import migrations, models

import waldur_core.core.fields
import waldur_core.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('uuid', waldur_core.core.fields.UUIDField()),
                ('title', models.CharField(max_length=255)),
                ('icon', models.ImageField(blank=True, null=True, upload_to='marketplace_category_icons')),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'Category',
                'verbose_name_plural': 'Categories',
            },
        ),
        migrations.CreateModel(
            name='Offering',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('description', models.CharField(blank=True, max_length=500, verbose_name='description')),
                ('name', models.CharField(max_length=150, validators=[waldur_core.core.validators.validate_name], verbose_name='name')),
                ('uuid', waldur_core.core.fields.UUIDField()),
                ('thumbnail', models.ImageField(blank=True, null=True, upload_to='marketplace_service_offering_thumbnails')),
                ('full_description', models.TextField(blank=True)),
                ('rating', models.IntegerField(default=0)),
                ('features', waldur_core.core.fields.JSONField(default=[])),
                ('geolocations', waldur_core.core.fields.JSONField(blank=True, default=[], help_text='List of latitudes and longitudes. For example: [{"latitude": 123, "longitude": 345}, {"latitude": 456, "longitude": 678}]')),
                ('is_active', models.BooleanField(default=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='offerings', to='marketplace.Category')),
                ('provider', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='offerings', to='marketplace.ServiceProvider')),
            ],
            options={
                'verbose_name': 'Offering',
            },
        ),
    ]
