# -*- coding: utf-8 -*-
"""Tests for the FooTaskModel model & BaseTask base class."""

from pyramid import testing
from pyramid_basemodel import Base
from pyramid_basemodel import BaseMixin
from pyramid_basemodel import Session
from pyramid_bimt.models import User
from pyramid_bimt.task import CeleryTask
from pyramid_bimt.task import TaskStates
from pyramid_bimt.testing import initTestingDB
from sqlalchemy import Column
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Unicode
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship
from zope.testing.loggingsupport import InstalledHandler

import mock
import transaction
import unittest

handler = InstalledHandler('pyramid_bimt.task')


class FooTaskModel(Base, BaseMixin):
    """A dummy celery task backend."""

    __tablename__ = 'foo_tasks'

    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship(
        User,
        backref=backref('tasks'),
    )

    task_id = Column(
        String,
    )

    task_name = Column(
        String,
    )

    msg = Column(
        Unicode,
    )

    state = Column(
        Enum(*[s.name for s in TaskStates], name='task_states'),
        default=TaskStates.pending.name,
    )

    @classmethod
    def by_id(class_, id):
        return class_.query.filter_by(id=id).first()

    @classmethod
    def by_task_id(class_, id):
        return class_.query.filter_by(task_id=id).first()


class TestCeleryTask(unittest.TestCase):

    class FooTask(CeleryTask):
        TaskModel = FooTaskModel

        def run(self, *args, **kwargs):
            pass

    def setUp(self):
        handler.clear()
        testing.setUp()
        initTestingDB()

    def tearDown(self):
        handler.clear()
        Session.remove()
        testing.tearDown()

    def test__call__(self):
        task = self.FooTask()
        task.request_stack = mock.Mock()
        task.request_stack.top.id = 'foo'

        task(user_id=1)

        self.assertEqual(FooTaskModel.by_id(1).task_id, 'foo')

        self.assertEqual(len(handler.records), 1)
        self.assertEqual(
            handler.records[0].message,
            'START pyramid_bimt.tests.test_task.FooTask (task id: foo, result id: 1)',  # noqa
        )

    def test_after_return(self):
        Session.add(FooTaskModel(task_id='foo'))

        task = self.FooTask()
        task.after_return(
            status=None, retval=None, task_id='foo', args=None, kwargs=None, einfo=None)  # noqa

        self.assertEqual(len(handler.records), 1)
        self.assertEqual(
            handler.records[0].message,
            'END pyramid_bimt.tests.test_task.FooTask (task id: foo, result id: 1)',  # noqa
        )

    def test_on_success(self):

        with transaction.manager:
            Session.add(FooTaskModel(id=1, task_id='foo', msg=u'bär'))

        task = self.FooTask()
        self.assertEqual(
            FooTaskModel.by_id(1).state,
            TaskStates.pending.name,
        )

        task.on_success(retval=None, task_id='foo', args=None, kwargs=None)
        self.assertEqual(FooTaskModel.by_id(1).msg, u'bär')
        self.assertEqual(
            FooTaskModel.by_id(1).state,
            TaskStates.success.name,
        )

    def test_on_failure(self):
        einfo = mock.Mock(spec='exception'.split())
        einfo.exception = Exception('problem foö')

        with transaction.manager:
            Session.add(FooTaskModel(id=1, task_id='foo'))

        task = self.FooTask()
        self.assertEqual(
            FooTaskModel.by_id(1).state,
            TaskStates.pending.name,
        )

        task.on_failure(None, 'foo', None, None, einfo)
        self.assertEqual(
            FooTaskModel.by_id(1).state,
            TaskStates.failure.name,
        )
        self.assertEqual(FooTaskModel.by_id(1).msg, u'problem foö')
