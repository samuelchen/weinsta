#!/usr/bin/env python
# coding: utf-8

import abc
from concurrent.futures import ThreadPoolExecutor
import os
import logging
from django.db import IntegrityError
import requests
from django.core.cache import cache
from ..models import Media, MediaInstance, MediaResolution

log = logging.getLogger(__name__)


class SocialClient(object, metaclass=abc.ABCMeta):

    __api_root = ''
    __provider = ''
    __download_root = ''
    __proxies = None
    __executors = None
    _token = None

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
        pass

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

    def invoke_async(self, endpoint, method='get', callback=None, **kwargs):
        """
        Invoke a RESTful API asynchronously
        """

        assert method in ['get', 'post', 'delete', 'update', 'option']

        url = '%s/%s' % (self.api_root, endpoint)

        cached_obj = cache.get((self.token, url))
        if cached_obj:
            log.debug('cache hit %s' % url)
            if callback:
                callback(cached_obj)
            return
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
                cache.set((self.token, url), obj)
            if callback:
                callback(obj)

        func = getattr(session, method.lower())
        future = self.__executors.submit(func, url=url, proxies=self.proxies, **kwargs)
        future.add_done_callback(on_invoked_result)

    def invoke(self, endpoint, method='get', **kwargs):
        """
        Invoke a RESTful API asynchronously
        """

        assert method in ['get', 'post', 'delete', 'update', 'option']

        if endpoint.startswith('http'):
            url = endpoint
        else:
            url = '%s/%s' % (self.api_root, endpoint)

        cached_obj = cache.get((self.token, url))
        if cached_obj:
            log.debug('cache hit %s' % url)
            return cached_obj
        else:
            log.debug('cache missed %s' % url)

        session = requests.Session()
        self.prepare_invoking(session)

        func = getattr(session, method.lower())
        r = func(url, proxies=self.proxies, **kwargs)
        log.debug('%s invoking %s.' % (r.status_code, url))
        # log.debug(r.headers)
        # log.debug(r.content)
        obj = r.json()
        if 200 > r.status_code or r.status_code >= 400:
            log.error('%d %s. "%s". %s' % (r.status_code, r.reason, endpoint, obj))
        else:
            cache.set((self.token, url), obj)

        return obj

    def download_async(self, url, filename=None, folder='./', file_field=None, delete_if_exists=True, callback=None):
        raise NotImplementedError

    def download(self, url, filename=None, folder='./', file_field=None, delete_if_exists=True):
        """
        Download a media file asynchronously
        If file_field specified, argument 'folder' will be IGNORED. Will use 'file_field.field.upload_to'.
        :return:
        """
        if not filename:
            filename = url.split('/')[-1]

        if file_field is not None:
            folder = file_field.field.upload_to(file_field, filename) \
                if callable(file_field.field.upload_to) else file_field.field.upload_to
        fullpath = os.path.join(self.download_root, folder, filename)
        fullpath = os.path.abspath(fullpath)
        os.makedirs(os.path.dirname(fullpath), exist_ok=True)

        # TODO: handle BIG file
        log.debug('Downloading %s to %s' % (url, fullpath))
        r = requests.get(url, stream=True, proxies=self.proxies)
        if r.status_code != requests.codes.ok:
            log.error('%d %s. Downloading %s' % (r.status_code, r.reason, url))
            return None

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
                return None

        return fullpath

    def save_media_instance(self, media, url, media_type, resolution, width, height,
                            update_if_exists=False, cache_to_local=False):

        assert isinstance(media, Media)

        m = media
        url_hash = MediaInstance.calc_url_hash(url)
        mi, created = MediaInstance.objects.get_or_create(url_hash=url_hash)

        if created or update_if_exists:
            log.debug('%s MediaInstance for %s (hash=%s)' % ('creating' if created else 'updating', url, url_hash))
            mi.type = media_type
            mi.resolution = resolution
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
                filename = os.path.join(m.get_instance_folder(), MediaResolution.get_slug(resolution),
                    m.rcode + file_ext)
                self.download(url=url, filename=filename, file_field=mi.instance)
                log.info('[Downloaded] %s' % mi)

        return mi