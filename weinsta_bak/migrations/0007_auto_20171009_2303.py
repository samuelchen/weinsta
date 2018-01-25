# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-10-09 15:03
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('weinsta', '0006_auto_20170915_2124'),
    ]

    operations = [
        migrations.CreateModel(
            name='Campaign',
            fields=[
                ('created_at', models.DateTimeField(auto_created=True, help_text='When the campaign created.')),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('begin', models.DateTimeField(help_text='When will the campaign begin.')),
                ('end', models.DateTimeField(help_text='When will the campaign end.')),
                ('status', models.IntegerField(choices=[(0, 'new'), (100, 'done'), (10, 'ready'), (20, 'in progress')], db_index=True, max_length=50)),
                ('providers', models.TextField(help_text='Comma separated provider codes')),
                ('text', models.TextField()),
                ('timestamp', models.DateTimeField(auto_now=True, help_text='When the campaign modified.')),
            ],
        ),
        migrations.AlterField(
            model_name='media',
            name='author',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='authorized_media', to='weinsta.SocialUser'),
        ),
        migrations.AlterField(
            model_name='media',
            name='owner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='posted_media', to='weinsta.SocialUser'),
        ),
        migrations.AlterField(
            model_name='media',
            name='provider',
            field=models.CharField(choices=[('', ''), ('twitter', 'twitter'), ('instagram', 'instagram'), ('weibo', 'weibo')], help_text='Social platform provider name', max_length=50),
        ),
        migrations.AlterField(
            model_name='media',
            name='type',
            field=models.TextField(choices=[('audio', 'audio'), (None, 'unknown'), ('video', 'video'), ('photo', 'photo')], default='photo'),
        ),
        migrations.AlterField(
            model_name='mediainstance',
            name='type',
            field=models.CharField(choices=[('audio', 'audio'), (None, 'unknown'), ('video', 'video'), ('photo', 'photo')], default='photo', max_length=50),
        ),
        migrations.AlterField(
            model_name='socialuser',
            name='provider',
            field=models.CharField(choices=[('', ''), ('twitter', 'twitter'), ('instagram', 'instagram'), ('weibo', 'weibo')], help_text='Social platform provider name', max_length=50),
        ),
        migrations.AddField(
            model_name='campaign',
            name='medias',
            field=models.ManyToManyField(to='weinsta.Media'),
        ),
        migrations.AddField(
            model_name='campaign',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]