#!/usr/bin/env python
# coding: utf-8

from django.contrib.auth import get_user_model
from django.db import models
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
from django.utils import timezone
from django.utils.translation import pgettext_lazy, ugettext as _
import simplejson as json
import logging

log = logging.getLogger(__name__)
# FS = FileSystemStorage(location=os.path.abspath(os.path.join(settings.MEDIA_ROOT, 'authors')))
FS = FileSystemStorage()
UserMode = get_user_model()


class SocialProviders(object):
    INSTAGRAM = 'instagram'
    TWITTER = 'twitter'
    WEIBO = 'weibo'
    _texts = {
        INSTAGRAM: _('instagram'),
        TWITTER: _('twitter'),
        WEIBO: _('weibo'),
    }
    _icons = {
        INSTAGRAM: 'fa fa-instagram',
        TWITTER: 'fa fa-twitter',
        WEIBO: 'fa fa-weibo',
    }
    Choices = _texts.items()
    Icons = _icons.items()

    @classmethod
    def get_text(cls, code):
        return cls._texts.get(code)

    @classmethod
    def get_icon(cls, code):
        return cls._icons.get(code)


class MediaType(object):
    PHOTO = 'photo'
    VIDEO = 'video'
    AUDIO = 'audio'
    _texts = {
        PHOTO: _('photo'),
        VIDEO: _('video'),
        AUDIO: _('audio')
    }
    _icons = {
        PHOTO: 'glyphicon glyphicon-picture ',
        VIDEO: 'glyphicon glyphicon-video',
        AUDIO: 'glyphicon glyphicon-audio',
    }
    Choices = _texts.items()
    Icons = _icons.items()

    @classmethod
    def get_text(cls, code):
        return cls._texts.get(code)

    @classmethod
    def get_icon(cls, code):
        return cls._icons.get(code)

    @classmethod
    def from_str(cls, type_str):
        type_str = type_str.lower()
        if type_str in ['picture', 'image', 'pic', 'img', 'photo']:
            return MediaType.PHOTO
        elif type_str in ['video', ]:
            return MediaType.VIDEO
        else:
            return None


class MediaResolution(object):
    THUMBNAIL = 'thumbnail'
    LOW = 'low'
    STANDARD = 'standard'
    HI = 'hi'
    _texts = {
        THUMBNAIL: pgettext_lazy('media resolution', 'thumbnail'),
        LOW: pgettext_lazy('media resolution', 'low'),
        STANDARD: pgettext_lazy('media resolution', 'standard'),
        HI: pgettext_lazy('media resolution', 'hi'),
    }
    _icons = {
        THUMBNAIL: 'glyphicon glyphicon-thumb ',
        LOW: 'glyphicon glyphicon-low ',
        STANDARD: 'glyphicon glyphicon-standard',
        HI: 'glyphicon glyphicon-hi',
    }
    Choices = _texts.items()
    Icons = _icons.items()

    @classmethod
    def get_text(cls, code):
        return cls._texts.get(code)

    @classmethod
    def get_icon(cls, code):
        return cls._icons.get(code)

    @classmethod
    def from_str(cls, resolution_str):
        resolution_str = resolution_str.lower()
        if resolution_str in ['thumbnail', 'thumb', 'avatar', 'icon']:
            return MediaResolution.THUMBNAIL
        elif resolution_str in ['low', 'low_resolution', 'low_bandwidth']:
            return MediaResolution.LOW
        elif resolution_str in ['standard', 'standard_resolution']:
            return MediaResolution.LOW
        elif resolution_str in ['high', 'hi', 'high_resolution', 'hi_resolution', 'hi_bandwith', 'high_bandwidth']:
            return MediaResolution.LOW
        else:
            return None


class SocialUser(models.Model):
    id = models.BigAutoField(primary_key=True)
    provider = models.CharField(max_length=50, choices=SocialProviders.Choices, help_text="Social platform provider name")
    username = models.CharField(max_length=50, db_index=True, help_text='username on origin platform')
    rid = models.CharField(max_length=100, db_index=True, help_text='id on origin platform')
    fullname = models.CharField(max_length=200, blank=True, null=True)
    picture_url = models.TextField(null=True, blank=True)
    picture = models.ImageField(storage=FS, upload_to='authors/')
    bio = models.TextField(null=True, blank=True)
    website = models.TextField(null=True, blank=True)
    is_artist = models.BooleanField(default=False)
    is_publisher = models.BooleanField(default=False)

    class Meta:
        unique_together = (
            ('provider', 'rid'),
            ('provider', 'username')
        )

    def __str__(self):
        return self.fullname if self.fullname else self.username


class SysConfig(models.Model):
    name = models.CharField(max_length=50, primary_key=True)
    value = models.CharField(max_length=200)


class Media(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(UserMode)

    provider = models.CharField(max_length=50, choices=SocialProviders.Choices, help_text="Social platform provider name")
    rid = models.CharField(max_length=100, db_index=True, help_text='id on origin platform')
    rcode = models.CharField(max_length=100, db_index=True, help_text="code/id on other platform")
    rlink = models.TextField()

    # owner = models.CharField(max_length=100, help_text='owner username on instagram')
    owner = models.ForeignKey(SocialUser, related_name='owner', null=True)
    author = models.ForeignKey(SocialUser, related_name='author', null=True)
    mentions = models.ManyToManyField(SocialUser, related_name='mentions')
    # mentions = models.TextField(null=True, blank=True, help_text="Mentioned persons in JSON format")
    # authors = models.ManyToManyField(Author)

    type = models.TextField(choices=MediaType.Choices, default=MediaType.PHOTO)
    text = models.TextField(null=True, blank=True)
    tags = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    timestamp = models.DateTimeField(auto_now=True)

    location = models.TextField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    rjson = models.TextField()

    thumb = models.ImageField(storage=FS, help_text='thumbnail. must be image', null=True, blank=True)
    thumb_url = models.TextField(null=True, blank=True)
    # low_res = models.ImageField(storage=FS, help_text='Low resolution file.')
    # standard_res = models.ImageField(storage=FS, help_text='Standard resolution file.')
    #
    thumb_width = models.IntegerField(null=True, blank=True, help_text='Thumbnail width.')
    thumb_height = models.IntegerField(null=True, blank=True, help_text='Thumbnail height.')
    # low_width = models.IntegerField(null=True, blank=True, help_text='Low resolution width.')
    # low_height = models.IntegerField(null=True, blank=True, help_text='Low resolution height.')
    # standard_width = models.IntegerField(null=True, blank=True, help_text='Standard resolution width.')
    # standard_height = models.IntegerField(null=True, blank=True, help_text='Standard resolution height.')

    class Meta:
        unique_together = (
            ('provider', 'rcode'),
            ('provider', 'rid')
        )
        # abstract = True


class MyMedia(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(UserMode)
    media = models.ForeignKey(Media, related_name='media')


class LikedMedia(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(UserMode)
    media = models.ForeignKey(Media)


# class MediaInstance(models.Model):
#     media = models.ForeignKey(Media)
#     type = models.TextField(choices=MediaType.Choices, default=MediaType.PHOTO)
#     link = models.TextField()
#     media_code = models.CharField(max_length=100, db_index=True)
#
#     height = models.IntegerField(null=True, blank=True)
#     width = models.IntegerField(null=True, blank=True)
#     size = models.IntegerField(null=True, blank=True)
#     resolution = models.CharField(max_length=50, choices=MediaResolution.Choices, default=MediaResolution.THUMBNAIL)
#
#     extra_data = models.TextField(help_text='extra data in JSON format', null=True, blank=True)
#
#     instance = models.FileField(storage=FS)
#

# class Photo(models.Model):
#
#     def __init__(self, *args, **kwargs):
#         super(Photo, self).__init__(*args, **kwargs)
#         self.type = MediaType.PHOTO
#
#
# class Video(models.Model):
#     video_low_res = models.FileField(storage=FS, help_text='Low resolution file.')
#     video_standard_res = models.FileField(storage=FS, help_text='Standard resolution file.')
#
#     video_low_width = models.IntegerField(null=True, blank=True, help_text='Low resolution width.')
#     video_low_height = models.IntegerField(null=True, blank=True, help_text='Low resolution height.')
#     video_standard_width = models.IntegerField(null=True, blank=True, help_text='Standard resolution width.')
#     video_standard_height = models.IntegerField(null=True, blank=True, help_text='Standard resolution height.')
#
#     def __init__(self, *args, **kwargs):
#         super(Video, self).__init__(*args, **kwargs)
#         self.type = MediaType.VIDEO
#
#
# class Audio(models.Model):
#
#     def __init__(self, *args, **kwargs):
#         super(Audio, self).__init__(*args, **kwargs)
#         self.type = MediaType.AUDIO