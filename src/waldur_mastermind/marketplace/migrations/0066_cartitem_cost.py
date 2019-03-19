# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-03-18 09:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0065_add_resource_cost_estimate'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartitem',
            name='cost',
            field=models.DecimalField(blank=True, decimal_places=10, max_digits=22, null=True),
        ),
    ]