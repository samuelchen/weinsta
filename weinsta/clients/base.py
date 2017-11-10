#!/usr/bin/env python
# coding: utf-8

import abc
from concurrent.futures import ThreadPoolExecutor
import os
import logging
from django.db import IntegrityError
import requests
from django.core.cache import cache
from ..models import Media, MediaInstance, MediaQuality, SocialUser, MediaType

log = logging.getLogger(__name__)


class SocialClientException(Exception):
    pass


class SocialClient(object, metaclass=abc.ABCMeta):

    __set = set()

    __api_root = ''
    __provider = ''
    __download_root = ''
    __proxies = None
    __executors = None
    _token = None

    @classmethod
    def get_downloading_set(cls):
        return cls.__set

    @property
    def api_root(self):
        return self.__api_root

    @property
    def provider(self):
        return self.__provider

    @property
    def download_root(self):
        return self.__download_root

    @property
    def proxies(self):
        return self.__proxies

    @property
    def token(self):
        return self._token

    @abc.abstractmethod
    def __init__(self, token, provider, api_root, download_root=None, proxies=None, *args, **kwargs):
        self.__provider = provider
        self.__api_root = api_root
        self.__download_root = download_root
        self.__proxies = proxies
        self.__executors = ThreadPoolExecutor(max_workers=2)
        self._token = token

    @abc.abstractmethod
    def prepare_invoking(self, requests_session):
        """
        Prepare the invoking session such as auth(token), header and etc.
        http://docs.python-requests.org/en/master/user/advanced/#session-objects
        :param requests_session: requests session objects
        :return:
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_token_hash(self):
        """
        Return a hash code of token to represent the client user
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_status(self, rid):
        """
        """
        raise NotImplementedError

    @abc.abstractmethod
    def post_status(self, text, medias=[]):
        """
        Post a status
        :param text: text to be posted. truck if over platform limitation
        :param medias: Medias objects to be post in status. number by platform limitation
        :return
        """
        # TODO: return value need to be unified.
        raise NotImplementedError

    @abc.abstractmethod
    def get_activity_data(self, rid):
        """
        Get status data for activities such as reply, like or repost.
        :param rid: remote status id in str
        :return dict of activity data.
        """
        raise NotImplementedError

    # ----- class method

    @abc.abstractclassmethod
    def get_token(self, user, request=None):
        raise NotImplementedError



    # @abc.abstractmethod
    # def save_media(self, media_dict, download_media=False, callback=None):
    #     """
    #     Save media object to DB by converting from dict
    #     :return:
    #     """
    #     raise NotImplementedError
    #
    # @abc.abstractmethod
    # def save_author(self, author_dict, download_pic=False, callback=None):
    #     """
    #     Save author (social user) to DB by converting from dict
    #     :return:
    #     """
    #     raise NotImplementedError

    # ---- common methods ----

    def invoke_async(self, endpoint, method='get', callback=None, **kwargs):
        """
        Invoke a RESTful API asynchronously
        """
        method = method.lower()
        assert method in ['get', 'post', 'delete', 'update', 'option']

        url = '%s/%s' % (self.api_root, endpoint)

        cache_key = None
        if method in ['get', ]:
            # gen cache key
            if 'params' in kwargs:
                d = kwargs['params']
                params = '?' + '&'.join([k + '='+str(d[k]) for k in sorted(d.keys())])
            else:
                params = '?access_token=' + self.get_token_hash()
            cache_key = url + params

        if cache_key:
            cached_obj = cache.get(cache_key)
            if cached_obj:
                log.debug('cache hit %s' % url)
                return cached_obj
            else:
                log.debug('cache missed %s' % url)

        session = requests.Session()
        self.prepare_invoking(session)

        def on_invoked_result(fu):
            r = fu.result(0.1)
            log.debug('%s invoking %s.' % (r.status_code, url))
            # log.debug(r.headers)
            # log.debug(r.content)
            obj = r.json()
            if 200 > r.status_code or r.status_code >= 400:
                log.error('%d %s. "%s". %s' % (r.status_code, r.reason, endpoint, obj))
            else:
                if cache_key:
                    cache.set(self.get_token_hash() + '_' + url, obj)

            if callback:
                callback(obj)

        func = getattr(session, method.lower())
        future = self.__executors.submit(func, url=url, proxies=self.proxies, **kwargs)
        future.add_done_callback(on_invoked_result)

    def invoke(self, endpoint, method='get', **kwargs):
        """
        Invoke a RESTful API synchronously
        """
        method = method.lower()
        assert method in ['get', 'post', 'delete', 'update', 'option']

        if endpoint.startswith('http'):
            url = endpoint
        else:
            url = '%s/%s' % (self.api_root, endpoint)

        cache_key = None
        if method in ['get', ]:
            # gen cache key
            if 'params' in kwargs:
                d = kwargs['params']
                params = '?' + '&'.join([k + '='+str(d[k]) for k in sorted(d.keys())])
            else:
                params = '?access_token=' + self.get_token_hash()
            cache_key = url + params

        if cache_key:
            # store to cache
            cached_obj = cache.get(cache_key)
            if cached_obj:
                log.debug('cache hit %s' % url)
                return cached_obj
            else:
                log.debug('cache missed %s' % url)

        session = requests.Session()
        self.prepare_invoking(session)

        func = getattr(session, method.lower())
        r = func(url, proxies=self.proxies, **kwargs)
        log.debug('%s invoking %s. kwargs: %s' % (r.status_code, r.url, kwargs))
        # log.debug(r.headers)
        # log.debug(r.content)
        obj = r.json()
        if 200 > r.status_code or r.status_code >= 400:
            log.error('%d %s. "%s". %s' % (r.status_code, r.reason, endpoint, obj))
        else:
            if cache_key:
                cache.set(self.get_token_hash() + '_' + url, obj)

        return obj

    def download_async(self, url, filename=None, folder='./', file_field=None, delete_if_exists=True, callback=None):
        raise NotImplementedError

    def download(self, url, filename=None, folder='./', file_field=None, delete_if_exists=True):
        """
        Download a media file asynchronously
        If file_field specified, argument 'folder' will be IGNORED. Will use 'file_field.field.upload_to'.
        :return:
        """
        rc = None
        downloading_set = SocialClient.get_downloading_set()
        if url in downloading_set:
            log.info('[IGNORED] %s is in downloading.' % url)
            return rc
        else:
            downloading_set.add(url)

        if not filename:
            filename = url.split('/')[-1]

        try:
            if file_field is not None:
                folder = file_field.field.upload_to(file_field, filename) \
                    if callable(file_field.field.upload_to) else file_field.field.upload_to
            fullpath = os.path.join(self.download_root, folder, filename)
            fullpath = os.path.abspath(fullpath)
            os.makedirs(os.path.dirname(fullpath), exist_ok=True)
            rc = fullpath

            # TODO: handle BIG file
            log.debug('Downloading %s to %s' % (url, fullpath))
            r = requests.get(url, stream=True, proxies=self.proxies)
            if r.status_code != requests.codes.ok:
                log.error('%d %s. Downloading %s' % (r.status_code, r.reason, url))
                rc = None

            if delete_if_exists:
                if os.path.exists(fullpath):
                    try:
                        os.remove(fullpath)
                    except Exception as err:
                        log.exception(err)
                        # then will auto rename

            if file_field is not None:
                file_field.save(filename, r.raw)
            else:
                try:
                    with open(fullpath, 'wb') as f:
                        f.write(r.raw)
                except Exception as err:
                    log.exception(err)
                    try:
                        if os.path.exists(fullpath):
                            os.remove(fullpath)
                    except:
                        pass
                    rc = None
        except Exception as err:
            log.exception(err)
            rc = None
        finally:
            downloading_set.remove(url)

        return rc

    def save_media_instance(self, media, url, media_type, quality, width=None, height=None,
                            update_if_exists=False, cache_to_local=False):

        assert isinstance(media, Media)

        m = media
        url_hash = MediaInstance.calc_url_hash(url)
        mi, created = MediaInstance.objects.get_or_create(url_hash=url_hash)

        if created or update_if_exists:
            log.debug('%s MediaInstance for %s (hash=%s)' % ('creating' if created else 'updating', url, url_hash))
            mi.type = media_type
            mi.quality = quality
            mi.origin_url = url
            mi.width = width
            mi.height = height
            try:
                mi.save()
            except IntegrityError as err:
                log.error('%s media url "%s". Already existed (hash=%s)' % (
                    '[create]' if created else '[updated]', url, url_hash))
                log.exception(err)
                return None

        if cache_to_local:
            if not (mi.instance and os.path.exists(mi.instance.path)):
                file_ext = url[url.rindex('.'):]
                filename = os.path.join(m.get_instance_folder(), MediaQuality.get_slug(quality),
                    m.rcode + file_ext)
                self.download(url=url, filename=filename, file_field=mi.instance)
                log.info('[Downloaded] %s' % mi)

        return mi

    def save_author(self, rid, username, fullname=None, pic_url=None, bio=None, website=None, update_if_exists=False,
                    cache_pic_to_local=False):
        provider = self.provider
        dirty = False

        u, created = SocialUser.objects.get_or_create(provider=provider, rid=rid)
        if created or update_if_exists:
            log.info('%s social user: %s' % ('Creating new' if created else 'Updating', username))
            u.username = username
            u.fullname = fullname
            u.bio = bio
            u.website = website
            dirty = True

        if u.picture is None:
            log.debug('user picture is None. creating from %s...' % pic_url)
            pic_url_hash = MediaInstance.calc_url_hash(pic_url)
            u.picture, created = MediaInstance.objects.get_or_create(url_hash=pic_url_hash)
            dirty = True

        mi = u.picture
        if mi and created or update_if_exists:
            mi.type = MediaType.PHOTO
            mi.quality = MediaQuality.ORIGIN
            mi.origin_url = pic_url
            mi.save()
            log.debug('[SAVED] %s' % mi)

        if cache_pic_to_local and mi.origin_url:
            if not (mi and mi.instance and os.path.exists(mi.instance.path)):
                file_ext = pic_url[pic_url.rindex('.'):]
                filename = username + file_ext
                filename = os.path.join(u.get_picture_folder(), filename)
                self.download(url=pic_url, filename=filename, file_field=mi.instance)
                log.info('[Downloaded] %s' % mi)

        if dirty:
            u.save()
            log.debug('[SAVED] %s' % u)
        return u


class CampaignMixin(object, metaclass=abc.ABCMeta):
    pass
    # @abc.abstractmethod
    # def start_campaign(self, camp):
    #     raise NotImplementedError
