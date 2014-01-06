# -*- coding: utf-8 -*-
"""Tests for the email_reminders script."""

from datetime import date
from pyramid import testing
from pyramid_basemodel import Session
from pyramid_bimt.models import User
from pyramid_bimt.scripts.reminder_emails import get_reminder_template
from pyramid_bimt.scripts.reminder_emails import reminder_emails
from pyramid_bimt.testing import initTestingDB

import mock
import transaction
import unittest


class TestEmailReminders(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _make_user(self, enabled=True, valid_to=None):
        user = mock.Mock(spec='enabled disable valid_to'.split())
        user.id = 1
        user.enabled = enabled
        user.valid_to = valid_to
        user.fullname = 'Mocked User'
        user.email = 'mocked@user.xyz'
        return user

    def test_get_reminder_template_disabled(self):
        self.assertIsNone(
            get_reminder_template(
                self._make_user(enabled=False),
                date.today(),
                {}
            )
        )

    def test_get_reminder_template_match(self):
        from pyramid_bimt.scripts.reminder_emails import get_reminder_template
        from dateutil.relativedelta import relativedelta

        valid_to = date.today()
        self.assertEqual(
            {
                'name': 'first', 'template': 'first_email_reminder.pt',
                'subject': u'First payment reminder for {} membership'
            },
            get_reminder_template(
                self._make_user(valid_to=valid_to),
                valid_to,
                {'first': relativedelta(days=0)}
            )
        )

    def test_get_reminder_template_no_match(self):
        from pyramid_bimt.scripts.reminder_emails import get_reminder_template
        from dateutil.relativedelta import relativedelta

        valid_to = date.today()
        self.assertIsNone(
            get_reminder_template(
                self._make_user(valid_to=valid_to),
                valid_to,
                {'zero': relativedelta(days=0)}
            )
        )

    def test_send_reminder_email(self):
        from pyramid_bimt.scripts.reminder_emails import send_reminder_email
        mailer = mock.Mock()
        user = self._make_user()
        template = {
            'name': 'first', 'template': 'first_email_reminder.pt',
            'subject': u'First payment reminder for {} membership'
        }
        send_reminder_email(
            mailer, user, template,
            'App Title', 'http://pricing.url/', 'default@sender.email'
        )

        message = mailer.send.call_args[0][0]

        self.assertEqual(
            message.subject,
            u'First payment reminder for App Title membership'
        )

        self.assertEqual(
            message.sender,
            'default@sender.email'
        )

        self.assertEqual(
            message.recipients,
            ['mocked@user.xyz', ]
        )

        self.assertIn(
            'Hi Mocked User,<br>\n',
            message.body
        )


class TestReminderEmailsIntegration(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        initTestingDB(auditlog_types=False, groups=True, users=True)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    @mock.patch('pyramid_bimt.scripts.reminder_emails.logger')
    def test_reminder_emails(self, mocked_logger):
        today = date(2013, 12, 30)
        user = User.by_email('admin@bar.com')
        user.valid_to = date(2013, 12, 20)
        transaction.commit()

        deltas_json = ('{"first": {"months": 1, "days": 3}, '
                       '"second": {"months": 0, "days": 17}, '
                       '"third": {"months": 0, "days": 10}}')
        settings = {
            'bimt.user_reminders': deltas_json,
            'bimt.app_title': 'Test App',
            'mail.default_sender': 'default@sender.email',
            'bimt.pricing_page_url': 'http://pricing.url/',
        }

        reminder_emails(today, settings, dry_run=True)

        self.assertEqual(
            u'Sent reminder email with template name third to user admin@bar.com, who is valid to 2013-12-20.',  # noqa
            mocked_logger.info.call_args[0][0]
        )
