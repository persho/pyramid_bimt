# -*- coding: utf-8 -*-
"""Task model definition."""

from celery import Task
from pyramid_basemodel import Session
from raven import Client
from flufl.enum import Enum

import logging
import os
import transaction

logger = logging.getLogger(__name__)

if os.environ.get('SENTRY_DSN'):  # pragma: no cover
    from raven.contrib.celery import register_signal
    client = Client()
    register_signal(client)


class TaskStates(Enum):
    pending = 'Pending'
    received = 'Received'
    started = 'Started'
    success = 'Finished'
    failure = 'Failed'
    revoked = 'Revoked'
    retry = 'Retrying'


class CeleryTask(Task):
    """A base class that apps use to create their own celery tasks."""
    abstract = True

    #: Specify in your app which model should store task results.
    #: The model needs to have user_id, task_id & task_name.
    TaskModel = None

    def __call__(self, *args, **kwargs):
        """Create a TaskModel object and log start of task execution."""
        with transaction.manager:
            if kwargs.get('app_task_id'):
                task = self.TaskModel.by_id(kwargs['app_task_id'])
                task.task_id = self.request.id
                task.state = TaskStates.retry.name
            else:
                task = self.TaskModel(
                    user_id=kwargs['user_id'],
                    task_id=self.request.id,
                    task_name=self.name,
                    args=args,
                    kwargs=kwargs,
                    state=TaskStates.started.name,
                )
                Session.add(task)
                Session.flush()
            logger.info(
                'START {} (celery task id: {}, app task id: {})'.format(
                    self.name, self.request.id, task.id))

        return self.run(*args, **kwargs)

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """Log end of task execution."""
        task = self.TaskModel.by_task_id(task_id)
        if task:
            task.state = TaskStates[status.lower()].name
            app_task_id = task.id
        else:
            app_task_id = None
        logger.info('END {} (celery task id: {}, app task id: {})'.format(
            self.name, task_id, app_task_id))

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Save traceback to Task.traceback."""
        with transaction.manager:
            task = self.TaskModel.by_task_id(task_id)
            if task:  # pragma: no branch
                task.traceback = unicode(einfo.traceback, 'utf-8')
                task.msg = u'An unexpected error occurred when running this '\
                    u'task. Please contact support and provide task ID number.'
            logger.exception(einfo.exception)
