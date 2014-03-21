# -*- coding: utf-8 -*-
"""Tests for pyramid_bimt mailing views."""

from pyramid import testing
from pyramid_basemodel import Session
from pyramid_bimt.models import Group
from pyramid_bimt.models import Mailing
from pyramid_bimt.models import MailingTriggers
from pyramid_bimt.models import User
from pyramid_bimt.scripts.send_mailings import send_mailings
from pyramid_bimt.testing import initTestingDB
from pyramid_mailer import get_mailer
from sqlalchemy.exc import IntegrityError

import datetime
import mock
import transaction
import unittest


def _make_mailing(name='foo', days=0, subject=u'', body=u'', **kwargs):
    mailing = Mailing(
        name=name, days=days, subject=subject, body=body, **kwargs)
    Session.add(mailing)
    return mailing


class TestMailingModel(unittest.TestCase):

    def setUp(self):
        initTestingDB()
        self.config = testing.setUp()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_name_is_unique(self):
        _make_mailing(name='foo')
        _make_mailing(name='foo')
        with self.assertRaises(IntegrityError) as cm:
            Session.flush()
        self.assertIn('column name is not unique', cm.exception.message)


class TestMailingById(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        initTestingDB()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_invalid_id(self):
        self.assertEqual(Mailing.by_id(1), None)
        self.assertEqual(Mailing.by_id('foo'), None)
        self.assertEqual(Mailing.by_id(None), None)

    def test_valid_id(self):
        _make_mailing(name='foo')
        mailing = Mailing.by_id(1)
        self.assertEqual(mailing.name, 'foo')


class TestMailingByName(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        initTestingDB()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_invalid_name(self):
        self.assertEqual(Mailing.by_name(1), None)
        self.assertEqual(Mailing.by_name('foo'), None)
        self.assertEqual(Mailing.by_name(None), None)

    def test_valid_name(self):
        _make_mailing(name='foo')
        mailing = Mailing.by_name('foo')
        self.assertEqual(mailing.name, 'foo')


class TestSendMailingsScript(unittest.TestCase):

    def setUp(self):
        settings = {
            'bimt.app_title': 'BIMT',
        }
        self.config = testing.setUp(settings=settings)
        self.request = testing.DummyRequest()
        self.config = testing.setUp(request=self.request, settings=settings)
        self.config.include('pyramid_mailer.testing')
        self.mailer = get_mailer(self.request)
        initTestingDB(users=True, groups=True)

        self.group = Group(name='foo')
        Session.add(self.group)
        self.user = User(email='foo@bar.com')
        Session.add(self.user)
        self.user.groups = [self.group, ]
        Session.flush()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_no_mailings(self):
        send_mailings()
        self.assertEqual(len(self.mailer.outbox), 0)

    def test_never(self):
        _make_mailing(trigger=MailingTriggers.never.name)
        transaction.commit()

        send_mailings()
        self.assertEqual(len(self.mailer.outbox), 0)

    @mock.patch('pyramid_bimt.scripts.send_mailings.date')
    def test_after_create_no_match(self, date):
        _make_mailing(
            subject=u'foo',
            groups=[self.group],
            trigger=MailingTriggers.after_created.name,
            days=3,
        )
        self.user.created = datetime.datetime(2014, 1, 1, 0, 0, 0)
        date.today.return_value = datetime.date(2014, 1, 3)
        transaction.commit()

        send_mailings()
        self.assertEqual(len(self.mailer.outbox), 0)

    @mock.patch('pyramid_bimt.scripts.send_mailings.date')
    def test_after_create_match(self, date):
        _make_mailing(
            subject=u'foo',
            groups=[self.group],
            trigger=MailingTriggers.after_created.name,
            days=3,
        )
        self.user.created = datetime.datetime(2014, 1, 1, 0, 0, 0)
        date.today.return_value = datetime.date(2014, 1, 4)
        transaction.commit()

        send_mailings()
        self.assertEqual(len(self.mailer.outbox), 1)
        self.assertEqual(self.mailer.outbox[0].subject, 'foo')

    @mock.patch('pyramid_bimt.scripts.send_mailings.date')
    def test_after_last_payment_no_match(self, date):
        _make_mailing(
            subject=u'foo',
            groups=[self.group],
            trigger=MailingTriggers.after_last_payment.name,
            days=3,
        )
        self.user.last_payment = datetime.datetime(2014, 1, 1, 0, 0, 0)
        date.today.return_value = datetime.date(2014, 1, 3)
        transaction.commit()

        send_mailings()
        self.assertEqual(len(self.mailer.outbox), 0)

    @mock.patch('pyramid_bimt.scripts.send_mailings.date')
    def test_after_last_payment_match(self, date):
        _make_mailing(
            subject=u'foo',
            groups=[self.group],
            trigger=MailingTriggers.after_last_payment.name,
            days=3,
        )
        self.user.last_payment = datetime.datetime(2014, 1, 1, 0, 0, 0)
        date.today.return_value = datetime.date(2014, 1, 4)
        transaction.commit()

        send_mailings()
        self.assertEqual(len(self.mailer.outbox), 1)
        self.assertEqual(self.mailer.outbox[0].subject, 'foo')

    @mock.patch('pyramid_bimt.scripts.send_mailings.date')
    def test_before_valid_to_no_match(self, date):
        _make_mailing(
            subject=u'foo',
            groups=[self.group],
            trigger=MailingTriggers.before_valid_to.name,
            days=3,
        )
        self.user.valid_to = datetime.datetime(2014, 1, 1, 0, 0, 0)
        date.today.return_value = datetime.date(2013, 12, 30)
        transaction.commit()

        send_mailings()
        self.assertEqual(len(self.mailer.outbox), 0)

    @mock.patch('pyramid_bimt.scripts.send_mailings.date')
    def test_before_valid_to_match(self, date):
        _make_mailing(
            subject=u'foo',
            groups=[self.group],
            trigger=MailingTriggers.before_valid_to.name,
            days=3,
        )
        self.user.valid_to = datetime.datetime(2014, 1, 1, 0, 0, 0)
        date.today.return_value = datetime.date(2013, 12, 29)
        transaction.commit()

        send_mailings()
        self.assertEqual(len(self.mailer.outbox), 1)
        self.assertEqual(self.mailer.outbox[0].subject, 'foo')