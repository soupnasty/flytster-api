# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-25 20:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='flytsteruser',
            name='recieve_notifications',
            field=models.BooleanField(default=True),
        ),
    ]