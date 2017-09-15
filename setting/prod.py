#!/usr/bin/env python
# coding: utf-8

from weinsta.settings import *


PROXIES = {

}

MEDIA_ROOT = '/opt/data/'


if CACHES['default']['BACKEND'] == 'django.core.cache.backends.filebased.FileBasedCache':
    CACHES['default']['LOCATION'] = os.path.abspath(os.path.join(MEDIA_ROOT, 'cache'))