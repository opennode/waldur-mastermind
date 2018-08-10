# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-05-21 10:48
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('openstack_tenant', '0031_unique_internal_ip'),
    ]

    operations = [
        migrations.AlterField(
            model_name='internalip',
            name='instance',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='internal_ips_set', to='openstack_tenant.Instance'),
        ),
    ]