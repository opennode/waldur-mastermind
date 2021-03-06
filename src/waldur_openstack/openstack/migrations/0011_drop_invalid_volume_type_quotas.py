from django.db import migrations


def drop_invalid_volume_type_quotas(apps, schema_editor):
    Tenant = apps.get_model('openstack', 'Tenant')
    VolumeType = apps.get_model('openstack', 'VolumeType')
    Quota = apps.get_model('quotas', 'Quota')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    tenant_type = ContentType.objects.get_for_model(Tenant)
    valid_volume_type_quotas = {
        f'gigabytes_{volume_type.name}' for volume_type in VolumeType.objects.all()
    }
    Quota.objects.filter(
        content_type=tenant_type, name__startswith='gigabytes_'
    ).exclude(name__in=valid_volume_type_quotas).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('openstack', '0010_router_fixed_ips'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('quotas', '0001_squashed_0004'),
    ]

    operations = [migrations.RunPython(drop_invalid_volume_type_quotas)]
