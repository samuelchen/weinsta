# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-10-25 07:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weinsta', '0014_auto_20171025_1539'),
    ]

    operations = [
        migrations.RenameField(
            model_name='battle',
            old_name='post_id',
            new_name='rid',
        ),
        migrations.AlterField(
            model_name='media',
            name='type',
            field=models.CharField(choices=[('', 'unknown'), ('audio', 'audio'), ('video', 'video'), ('photo', 'photo')], default='photo', max_length=50),
        ),
        migrations.AlterField(
            model_name='mediainstance',
            name='type',
            field=models.CharField(choices=[('', 'unknown'), ('audio', 'audio'), ('video', 'video'), ('photo', 'photo')], default='photo', max_length=50),
        ),
        migrations.AlterUniqueTogether(
            name='battle',
            unique_together=set([('provider', 'rid')]),
        ),
    ]
