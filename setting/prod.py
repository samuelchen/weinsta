#!/usr/bin/env python
# coding: utf-8

from weinsta.settings import *


PROXIES = {

}

MEDIA_ROOT = '/opt/data/weinsta'


if CACHES['default']['BACKEND'] == 'django.core.cache.backends.filebased.FileBasedCache':
    CACHES['default']['LOCATION'] = os.path.abspath(os.path.join(MEDIA_ROOT, 'cache'))


if not os.path.exists(MEDIA_ROOT):
    os.makedirs(MEDIA_ROOT, mode=0o755, exist_ok=True)


TIME_ZONE = 'Asia/Shanghai'