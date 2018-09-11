# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-09-11 14:40
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models
import re


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_remove_organization'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(help_text='Required. 128 characters or fewer. Letters, numbers and @/./+/-/_ characters', max_length=128, unique=True, validators=[django.core.validators.RegexValidator(re.compile('^[\\w.@+-]+$'), 'Enter a valid username.', 'invalid')], verbose_name='username'),
        ),
    ]
