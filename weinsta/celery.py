#!/usr/bin/env python
# coding: utf-8
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery, shared_task

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weinsta.settings')

app = Celery('weinsta', broker='sqla+sqlite:///celery_broker.sqlite3')
app.conf.update(
    CELERY_RESULT_BACKEND='db+sqlite:///celery_result.sqlite3',
    # CELERY_RESULT_BACKEND = 'redis://localhost/0',
    #   CELERY_RESULT_BACKEND = 'amqp',
    #   CELERY_RESULT_BACKEND = 'mongodb://127.0.0.1:27017/',
    CELERY_TASK_SERIALIZER='json',
    CELERY_IGNORE_RESULT=False,
)


# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@shared_task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))