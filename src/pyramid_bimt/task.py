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
            result = self.TaskModel(
                user_id=kwargs['user_id'],
                task_id=self.request.id,
                task_name=self.name,
                state=TaskStates.started.name,
            )
            Session.add(result)
            Session.flush()
            logger.info(
                'START {} (task id: {}, result id: {})'.format(
                    self.name, self.request.id, result.id))

        return self.run(*args, **kwargs)

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """Log end of task execution."""
        result = self.TaskModel.by_task_id(task_id)
        if result:
            result.state = TaskStates[status.lower()].name
            result_id = result.id
        else:
            result_id = None
        logger.info('END {} (task id: {}, result id: {})'.format(
            self.name, task_id, result_id))

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Save traceback to Task.traceback."""
        with transaction.manager:
            task = self.TaskModel.by_task_id(task_id)
            if task:  # pragma: no branch
                task.traceback = unicode(einfo.traceback, 'utf-8')
            logger.exception(einfo.exception)
