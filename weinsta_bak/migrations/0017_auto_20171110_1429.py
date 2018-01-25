# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-11-10 06:29
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('weinsta', '0016_auto_20171025_1540'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activity',
            name='battle',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activities', to='weinsta.Battle'),
        ),
        migrations.AlterField(
            model_name='activity',
            name='date',
            field=models.DateField(help_text='When the activity data was collected'),
        ),
        migrations.AlterField(
            model_name='activity',
            name='type',
            field=models.CharField(choices=[('repost', 'repost'), ('comment', 'comment'), ('like', 'like')], max_length=50),
        ),
        migrations.AlterField(
            model_name='media',
            name='type',
            field=models.CharField(choices=[('', 'unknown'), ('video', 'video'), ('photo', 'photo'), ('audio', 'audio')], default='photo', max_length=50),
        ),
        migrations.AlterField(
            model_name='mediainstance',
            name='type',
            field=models.CharField(choices=[('', 'unknown'), ('video', 'video'), ('photo', 'photo'), ('audio', 'audio')], default='photo', max_length=50),
        ),
    ]
