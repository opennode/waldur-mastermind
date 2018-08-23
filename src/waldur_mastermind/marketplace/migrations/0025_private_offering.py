# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-08-23 11:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('structure', '0002_immutable_default_json'),
        ('marketplace', '0024_rename_screenshot'),
    ]

    operations = [
        migrations.AddField(
            model_name='offering',
            name='allowed_customers',
            field=models.ManyToManyField(related_name='_offering_allowed_customers_+', to='structure.Customer'),
        ),
        migrations.AddField(
            model_name='offering',
            name='shared',
            field=models.BooleanField(default=False, help_text='Anybody can use it'),
        ),
    ]