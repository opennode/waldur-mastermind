# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-04-15 10:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_user_backend_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='organization',
            field=models.CharField(blank=True, max_length=255, verbose_name='organization'),
        ),
    ]