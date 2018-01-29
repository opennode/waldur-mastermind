# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-01-24 12:59
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('support', '0012_attachment'),
    ]

    operations = [
        migrations.AddField(
            model_name='attachment',
            name='author',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='support.SupportUser'),
        ),
        migrations.AddField(
            model_name='attachment',
            name='file_size',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Filesize, B'),
        ),
        migrations.AddField(
            model_name='attachment',
            name='mime_type',
            field=models.CharField(blank=True, max_length=100, verbose_name='MIME type'),
        ),
        migrations.AddField(
            model_name='attachment',
            name='thumbnail',
            field=models.FileField(blank=True, null=True, upload_to='support_attachments_thumbnails'),
        ),
    ]
