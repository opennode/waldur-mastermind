# Generated by Django 2.2.13 on 2020-11-09 19:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('openstack_tenant', '0009_securitygrouprule_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='securitygrouprule',
            name='direction',
            field=models.CharField(
                choices=[('ingress', 'ingress'), ('egress', 'egress')],
                default='ingress',
                max_length=8,
            ),
        ),
    ]
