# -*- coding: utf-8 -*-
"""Tests for models mixins."""

from pyramid import testing
from pyramid_basemodel import Base
from pyramid_basemodel import BaseMixin
from pyramid_basemodel import Session
from pyramid_bimt.models import GetByIdMixin
from pyramid_bimt.models import GetByNameMixin
from pyramid_bimt.models import WorkflowMixin
from pyramid_bimt.testing import initTestingDB
from sqlalchemy import Column
from sqlalchemy import String

import unittest


class _TestModelId(Base, BaseMixin, GetByIdMixin):
    """A class representing a test model with GetByIdMixin mixin."""

    __tablename__ = 'test_id_models'


class _TestModelName(Base, BaseMixin, GetByNameMixin):
    """A class representing a test model with GetByNameMixin."""

    __tablename__ = 'test_name_models'

    name = Column(
        String,
        unique=True,
        nullable=False,
    )


class _TestModelWorkflow(Base, BaseMixin, WorkflowMixin):
    """A class representing a test model with WorkflowMixin."""

    __tablename__ = 'test_workflow_models'

    status = Column(String)


class TestGetById(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        initTestingDB()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_invalid_id_with_default(self):
        self.assertEqual(_TestModelId.by_id(1, None), None)
        self.assertEqual(_TestModelId.by_id('foo', None), None)
        self.assertEqual(_TestModelId.by_id(None, None), None)

    def test_invalid_id_without_default(self):
        self.assertEqual(_TestModelId.by_id(1, None), None)
        with self.assertRaises(ValueError):
            _TestModelId.by_id('foo')
        with self.assertRaises(TypeError):
            _TestModelId.by_id(None)

    def test_valid_id(self):
        Session.add(_TestModelId(id=2))
        test_model = _TestModelId.by_id(2)
        self.assertEqual(test_model.id, 2)


class TestGetByName(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        initTestingDB()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_invalid_id(self):
        self.assertEqual(_TestModelName.by_name(1, None), None)
        self.assertEqual(_TestModelName.by_name('foo', None), None)
        self.assertEqual(_TestModelName.by_name('főő', None), None)
        self.assertEqual(_TestModelName.by_name(None, None), None)

    def test_invalid_id_without_default(self):
        self.assertEqual(_TestModelName.by_name(1), None)
        self.assertEqual(_TestModelName.by_name('foo'), None)
        self.assertEqual(_TestModelName.by_name(None), None)
        with self.assertRaises(UnicodeDecodeError):
            _TestModelName.by_name('főő')

    def test_valid_id(self):
        Session.add(_TestModelName(name='foo'))
        test_model = _TestModelName.by_name('foo')
        self.assertEqual(test_model.name, 'foo')


class TestWorkflow(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.model = _TestModelWorkflow()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_default_workflow(self):
        from repoze.workflow import Workflow
        from repoze.workflow.zcml import register_workflow

        workflow = Workflow(
            name='test workflow',
            state_attr='status',
            initial_state='first',
            permission_checker=None,
        )

        workflow.add_state(state_name='first', title='', callback=None)
        workflow.add_state(state_name='second', title='', callback=None)

        workflow.add_transition(
            transition_name='to_second',
            from_state='first',
            to_state='second',
            title='',
        )

        workflow.check()

        register_workflow(
            workflow=workflow,
            type='status',
            content_type=_TestModelWorkflow,
            elector=None,
        )

        self.model.to_state('second')
        self.assertEqual(self.model.status, 'second')

    def test_arbitrary_workflow(self):
        from repoze.workflow import Workflow
        from repoze.workflow.zcml import register_workflow

        workflow = Workflow(
            name='test workflow',
            state_attr='foo',
            initial_state='foo',
            permission_checker=None,
        )

        workflow.add_state(state_name='foo', title='', callback=None)
        workflow.add_state(state_name='bar', title='', callback=None)

        workflow.add_transition(
            transition_name='to_bar',
            from_state='foo',
            to_state='bar',
            title='',
        )

        workflow.check()

        register_workflow(
            workflow=workflow,
            type='foo',
            content_type=_TestModelWorkflow,
            elector=None,
        )

        self.model.to_state('bar', workflow='foo')
        self.assertEqual(self.model.foo, 'bar')
