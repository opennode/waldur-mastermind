# Generated by Django 2.2.13 on 2020-10-07 11:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('waldur_aws', '0003_extend_description_limits'),
    ]

    operations = [
        migrations.AddField(
            model_name='instance',
            name='error_traceback',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='volume',
            name='error_traceback',
            field=models.TextField(blank=True),
        ),
    ]