# Generated by Django 2.2.13 on 2020-09-02 11:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('waldur_jira', '0021_extend_icon_url_size'),
    ]

    operations = [
        migrations.AlterField(
            model_name='issuetype',
            name='description',
            field=models.CharField(
                blank=True, max_length=2000, verbose_name='description'
            ),
        ),
        migrations.AlterField(
            model_name='priority',
            name='description',
            field=models.CharField(
                blank=True, max_length=2000, verbose_name='description'
            ),
        ),
        migrations.AlterField(
            model_name='project',
            name='description',
            field=models.CharField(
                blank=True, max_length=2000, verbose_name='description'
            ),
        ),
        migrations.AlterField(
            model_name='projecttemplate',
            name='description',
            field=models.CharField(
                blank=True, max_length=2000, verbose_name='description'
            ),
        ),
    ]
