# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-26 01:44
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('trips', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Passenger',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=20)),
                ('middle_name', models.CharField(max_length=20, null=True)),
                ('last_name', models.CharField(max_length=20)),
                ('phone', models.CharField(max_length=10)),
                ('gender', models.CharField(choices=[('M', 'male'), ('F', 'female')], max_length=1)),
                ('birthdate', models.DateField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('trip', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='passengers', to='trips.Trip')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='passengers', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Passengers',
                'verbose_name': 'Passenger',
                'ordering': ['-timestamp'],
            },
        ),
    ]