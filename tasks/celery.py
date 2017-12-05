#!/usr/bin/env python
# coding: utf-8
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery, shared_task


# from django_celery_beat.models import PeriodicTask
# PeriodicTask.objects.update(last_run_at=None)

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weinsta.settings')


class MyCelery(Celery):

    def gen_task_name(self, name, module):
        if module.endswith('.tasks'):
            module = module[:-6]
        return super(MyCelery, self).gen_task_name(name, module)

app = MyCelery('weinsta', broker='sqla+sqlite:///celery_broker.sqlite3')
app.conf.update(
    CELERY_RESULT_BACKEND='db+sqlite:///celery_result.sqlite3',
    # CELERY_RESULT_BACKEND = 'redis://localhost/0',
    # CELERY_RESULT_BACKEND = 'amqp',
    # CELERY_RESULT_BACKEND = 'mongodb://127.0.0.1:27017/',
    CELERY_TASK_SERIALIZER='json',
    CELERY_IGNORE_RESULT=False,
    CELERY_ALWAYS_EAGER=True,
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
