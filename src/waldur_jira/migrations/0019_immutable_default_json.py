# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-07-03 17:43
from __future__ import unicode_literals

from django.db import migrations
import waldur_core.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('waldur_jira', '0018_project_runtime_state'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='action_details',
            field=waldur_core.core.fields.JSONField(default=dict),
        ),
    ]