# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-06-24 03:36
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trips', '0002_tripexpectedpassengers'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='leg',
            options={'ordering': ['-timestamp'], 'verbose_name': 'Leg', 'verbose_name_plural': 'Legs'},
        ),
    ]
