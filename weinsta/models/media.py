#!/usr/bin/env python
# coding: utf-8

from django.contrib.auth import get_user_model
from django.db import models
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
from django.utils import timezone
from django.utils.translation import pgettext_lazy, ugettext_noop, override, ugettext as _
import simplejson as json
import logging
import hashlib


log = logging.getLogger(__name__)
# FS = FileSystemStorage(location=os.path.abspath(os.path.join(settings.MEDIA_ROOT, 'authors')))
FS = FileSystemStorage()
UserMode = get_user_model()


class SocialProviders(object):
    UNKNOWN = ''
    INSTAGRAM = 'instagram'
    TWITTER = 'twitter'
    WEIBO = 'weibo'
    _texts = {
        UNKNOWN: '',        #_(''),
        INSTAGRAM: _('instagram'),
        TWITTER: _('twitter'),
        WEIBO: _('weibo'),
    }
    _icons = {
        UNKNOWN: 'fa fa-question-circle ',
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
    UNKNOWN = None
    PHOTO = 'photo'
    VIDEO = 'video'
    AUDIO = 'audio'
    _texts = {
        UNKNOWN: _('unknown'),
        PHOTO: _('photo'),
        VIDEO: _('video'),
        AUDIO: _('audio'),
    }
    _icons = {
        UNKNOWN: 'fa fa-unknonn',
        PHOTO: 'fa fa-picture ',
        VIDEO: 'fa fa-video',
        AUDIO: 'fa fa-audio',
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
        elif type_str in ['audio', ]:
            return MediaType.AUDIO
        else:
            log.warn('"%s" is unknown media type.' % type_str)
            return MediaType.UNKNOWN


class MediaQuality(object):
    THUMB = 0
    LOW = 10
    # MID = 20
    HIGH = 20
    ORIGIN = 100

    _texts = {
        # ORIGIN: _n('media quality', 'origin'),
        # THUMB: _n('media quality', 'thumb'),
        # LOW: _n('media quality', 'low'),
        # MID: _n('media quality', 'medium'),
        # HIGH: _n('media quality', 'high'),
        ORIGIN: _('origin'),
        THUMB: _('thumb'),
        LOW: _('low'),
        # MID: _n('medium'),
        HIGH: _('high'),
    }
    _icons = {
        ORIGIN: 'fa fa-origin',
        THUMB: 'fa fa-origin',
        LOW: 'fa fa-low',
        # MID: 'fa fa-mid',
        HIGH: 'fa fa-high',
    }
    Choices = _texts.items()
    Icons = _icons.items()

    @classmethod
    def get_text(cls, code):
        return cls._texts.get(code)

    @classmethod
    def get_slug(cls, code):
        slug = cls._texts.get(code)
        with override('en'):
            return slug

    @classmethod
    def get_icon(cls, code):
        return cls._icons.get(code)

    # @classmethod
    # def from_str(cls, resolution_str):
    #     resolution_str = resolution_str.lower()
    #     if resolution_str in ['thumbnail', 'thumb', 'avatar', 'icon']:
    #         return MediaQuality.LOW
    #     elif resolution_str in ['low', 'low_resolution', 'low_bandwidth']:
    #         return MediaQuality.LOW
    #     elif resolution_str in ['standard', 'standard_resolution']:
    #         return MediaQuality.MID
    #     elif resolution_str in ['high', 'hi', 'high_resolution', 'hi_resolution', 'hi_bandwith', 'high_bandwidth']:
    #         return MediaQuality.HIGH
    #     else:
    #         return None


class MediaInstance(models.Model):
    id = models.BigAutoField(primary_key=True)
    # media = models.ForeignKey(Media)
    type = models.CharField(max_length=50, choices=MediaType.Choices, default=MediaType.PHOTO)
    # provider = models.CharField(max_length=50, choices=SocialProviders.Choices, default=SocialProviders.INSTAGRAM)
    quality = models.CharField(max_length=50, choices=MediaQuality.Choices, default=MediaQuality.ORIGIN)

    # thumb = models.ImageField(storage=FS, null=True, blank=True, help_text='Thumbnail picture')
    instance = models.FileField(storage=FS, null=True, blank=True, help_text='Media instance storage')
    origin_url = models.TextField(null=True, blank=True)
    url_hash = models.CharField(max_length=50, unique=True, db_index=True)

    height = models.IntegerField(null=True, blank=True)
    width = models.IntegerField(null=True, blank=True)
    # size = models.IntegerField(null=True, blank=True)
    # extra_data = models.TextField(help_text='extra data in JSON format', null=True, blank=True)

    def __str__(self):
        return '%s <%s> %s (%s %s %dx%d) from %s (%s)' % (
            self.__class__.__name__, self.id,
            os.path.join(self.instance.path, self.instance.name) if self.instance else '<path:none>', self.type,
            MediaQuality.get_text(self.quality), self.width or 0, self.height or 0, self.origin_url,
            self.url_hash)

    @staticmethod
    def calc_url_hash(url):
        if url:
            md5 = hashlib.md5()
            md5.update(url.encode())
            return md5.hexdigest()
        else:
            return None

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.url_hash = MediaInstance.calc_url_hash(self.origin_url if self.origin_url else str(self.id))
        super(MediaInstance, self).save(force_insert=force_insert, force_update=force_update,
                                        using=using, update_fields=update_fields)

    def get_url(self, prefer_origin_url=True):
        if prefer_origin_url:
            url = self.origin_url or self.instance.url
        else:
            url = self.instance.url if self.instance else self.origin_url
        return url or ''


class SocialUser(models.Model):
    id = models.BigAutoField(primary_key=True)
    provider = models.CharField(max_length=50, choices=SocialProviders.Choices, help_text="Social platform provider name")
    username = models.CharField(max_length=50, db_index=True, help_text='username on origin platform')
    rid = models.CharField(max_length=100, db_index=True, help_text='id on origin platform')
    fullname = models.CharField(max_length=200, blank=True, null=True)
    # picture_url = models.TextField(null=True, blank=True)
    # picture = models.ImageField(storage=FS, null=True, blank=True)
    picture = models.ForeignKey(MediaInstance, null=True, blank=True, on_delete=models.SET_NULL)
    bio = models.TextField(null=True, blank=True)
    website = models.TextField(null=True, blank=True)
    is_artist = models.BooleanField(default=False)
    is_publisher = models.BooleanField(default=False)

    class Meta:
        unique_together = (
            ('provider', 'rid', 'username')
        )

    def __str__(self):
        return self.fullname if self.fullname else self.username or ''

    def get_pic_url(self, prefer_origin_url=False):
        if self.picture:
            return self.picture.get_url(prefer_origin_url=prefer_origin_url)
        else:
            return ''

    def get_picture_folder(self):
        return 'authors/%s/' % self.provider

    def get_name(self):
        return self.fullname or self.username

    def get_icon(self):
        return 'fa fa-' + self.provider


class Media(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(UserMode, on_delete=models.PROTECT)

    provider = models.CharField(max_length=50, choices=SocialProviders.Choices, help_text="Social platform provider name")
    rid = models.CharField(max_length=100, db_index=True, help_text='id on origin platform')
    rcode = models.CharField(max_length=100, db_index=True, help_text="code/id on origin platform")
    rlink = models.TextField()

    # owner = models.CharField(max_length=100, help_text='owner username on instagram')
    owner = models.ForeignKey(SocialUser, related_name='posted_media', null=True, on_delete=models.SET_NULL)
    author = models.ForeignKey(SocialUser, related_name='authorized_media', null=True, on_delete=models.SET_NULL)
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

    # thumbnail for media (must)
    thumb = models.ForeignKey(MediaInstance, on_delete=models.SET_NULL, null=True, blank=True, related_name='thumb_media')

    # pictures for vide/audio (high/low quality screen-shot or cover)
    pic_high = models.ForeignKey(MediaInstance, on_delete=models.SET_NULL, null=True, blank=True, related_name='pic_high_res_media')
    pic_low = models.ForeignKey(MediaInstance, on_delete=models.SET_NULL, null=True, blank=True, related_name='pic_low_res_media')

    # instances for media (quality: origin, high, low)
    origin = models.ForeignKey(MediaInstance, on_delete=models.SET_NULL, null=True, blank=True, related_name='origin_media')
    high = models.ForeignKey(MediaInstance, on_delete=models.SET_NULL, null=True, blank=True, related_name='high_quality_media')
    low = models.ForeignKey(MediaInstance, on_delete=models.SET_NULL, null=True, blank=True, related_name='low_quality_media')

    class Meta:
        unique_together = (
            ('provider', 'rid', 'rcode'),
        )
        # abstract = True

    def __str__(self):
        return '<%s> %s %s by %s@%s' % (self.__class__.__name__, self.type, self.rcode, self.owner, self.provider)

    def get_media_instance(self, quality):
        mi = None
        if quality == MediaQuality.ORIGIN:
            mi = self.origin
        elif quality == MediaQuality.HIGH:
            mi = self.high
        elif quality == MediaQuality.LOW:
            mi = self.low
        if not mi:
            mi = self.origin or self.high or self.low
        return mi

    def get_pic_instance(self, quality):
        mi = None
        if quality == MediaQuality.THUMB:
            mi = self.thumb
        elif quality == MediaQuality.LOW:
            mi = self.pic_low
        elif quality == MediaQuality.HIGH:
            mi = self.pic_high
        if not mi:
            mi = self.pic_high or self.pic_low or self.thumb

        return mi

    def get_pic_url(self, quality=MediaQuality.THUMB, prefer_origin_url=True):
        mi = self.get_pic_instance(quality)
        url = ''
        if mi:
            return mi.get_url(prefer_origin_url=prefer_origin_url)
        return url

    def get_url(self, quality=MediaQuality.ORIGIN, prefer_origin_url=True):
        mi = self.get_media_instance(quality)
        url = ''
        if mi:
            return mi.get_url(prefer_origin_url=prefer_origin_url)
        return url

    def get_thumb_url(self, prefer_origin_url=False):
        return self.get_pic_url(quality=MediaQuality.THUMB, prefer_origin_url=prefer_origin_url)

    def get_pic_low_url(self):
        return self.get_pic_url(quality=MediaQuality.LOW)

    def get_pic_high_url(self):
        return self.get_pic_url(quality=MediaQuality.HIGH)

    def get_low_url(self):
        return self.get_url(quality=MediaQuality.LOW)

    def get_high_url(self):
        return self.get_url(quality=MediaQuality.HIGH)

    def get_origin_url(self):
        return self.get_url(quality=MediaQuality.ORIGIN)

    def get_instance_folder(self):
        return '%s/' % self.provider


class SysConfig(models.Model):
    name = models.CharField(max_length=50, primary_key=True)
    value = models.CharField(max_length=200)


class MyMedia(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(UserMode, on_delete=models.CASCADE)
    media = models.ForeignKey(Media, on_delete=models.CASCADE, related_name='media')


class LikedMedia(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(UserMode, on_delete=models.CASCADE)
    media = models.ForeignKey(Media, on_delete=models.CASCADE)


# class UserMediaOrigin(models.Model):
#     pass
#
#
# class UserMediaHighRes(models.Model):
#     pass
#
#
# class UserMediaMidRes(models.Model):
#     pass


# class Photo(models.Model):
#
#     def __init__(self, *args, **kwargs):
#         super(Photo, self).__init__(*args, **kwargs)
#         self.type = MediaType.PHOTO
#
#
# class Video(models.Model):
#     video_low_res = models.FileField(storage=FS, help_text='Low quality file.')
#     video_standard_res = models.FileField(storage=FS, help_text='Standard quality file.')
#
#     video_low_width = models.IntegerField(null=True, blank=True, help_text='Low quality width.')
#     video_low_height = models.IntegerField(null=True, blank=True, help_text='Low quality height.')
#     video_standard_width = models.IntegerField(null=True, blank=True, help_text='Standard quality width.')
#     video_standard_height = models.IntegerField(null=True, blank=True, help_text='Standard quality height.')
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