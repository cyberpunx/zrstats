# Generated by Django 2.2.5 on 2019-11-19 00:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0008_auto_20191118_1410'),
    ]

    operations = [
        migrations.AddField(
            model_name='miembro',
            name='region',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Región'),
        ),
    ]
