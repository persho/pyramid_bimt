# -*- coding: utf-8 -*-
"""Test clickbank api."""
from pyramid_bimt.clickbank import ClickbankAPI

import mock
import unittest

RESPONSES = {}
RESPONSES['list_orders'] = {'orderData': [
    {
        'date': '2014-12-18T01:53:59-08:00',
        'receipt': 'XDWXQSLE',
        'promo': {
            '@nil': 'true'
        },
        'pmtType': 'TEST',
        'txnType': 'TEST_SALE',
        'item': 'ipntest',
        'amount': '10.58',
        'site': 'NITEOWEB',
        'affi': {
            '@nil': 'true'
        },
        'country': 'US',
        'state': {
            '@nil': 'true'
        },
        'lastName': 'SMITH',
        'firstName': 'JOHN',
        'currency': 'EUR',
        'email': 'john.smith@gmail.com',
        'zip': '10000',
        'rebillAmount': '10.00',
        'processedPayments': '2',
        'futurePayments': '997',
        'nextPaymentDate': '2015-02-18T01:53:59-08:00',
        'status': 'CANCELED',
        'accountAmount': '8.25',
        'role': 'VENDOR',
        'customerDisplayName': 'John Smith',
        'title': 'EBN Test',
        'recurring': 'true',
        'physical': 'false',
        'customerRefundableState': {
            '@nil': 'true'
        }
    },
    {
        'date': '2014-12-20T14:03:10-08:00',
        'receipt': 'LPJ9VE42',
        'promo': {
            '@nil': 'true'
        },
        'pmtType': 'TEST',
        'txnType': 'TEST_SALE',
        'item': 'ipntest',
        'amount': '10.58',
        'site': 'NITEOWEB',
        'affi': {
            '@nil': 'true'
        },
        'country': 'US',
        'state': {
            '@nil': 'true'
        },
        'lastName': 'SMITH',
        'firstName': 'JOHN',
        'currency': 'EUR',
        'email': 'john.smith@gmail.com',
        'zip': '10000',
        'rebillAmount': '10.00',
        'processedPayments': '2',
        'futurePayments': '997',
        'nextPaymentDate': '2015-02-20T14:03:10-08:00',
        'status': 'CANCELED',
        'accountAmount': '8.25',
        'role': 'VENDOR',
        'customerDisplayName': 'John Smith',
        'title': 'IPN Test',
        'recurring': 'true',
        'physical': 'false',
        'customerRefundableState': {
            '@nil': 'true'
        }
    }, ]
}


class TestClickbankAPI(unittest.TestCase):

    def setUp(self):

        dev_key = 'secret'
        api_key = 'secret'

        self.client = ClickbankAPI(dev_key, api_key)

    @mock.patch('pyramid_bimt.clickbank.requests')
    def test_get_user_latest_receipt(self, requests):
        requests.request.return_value.json.return_value = RESPONSES['list_orders']  # noqa
        receipt = self.client.get_user_latest_receipt(
            'ipntest', 'john.smith@gmail.com')

        self.assertEqual(receipt, 'LPJ9VE42')

    @mock.patch('pyramid_bimt.clickbank.requests')
    def test_get_user_latest_receipt_only_one_order(self, requests):
        response = {}
        response['orderData'] = RESPONSES['list_orders']['orderData'][0]
        requests.request.return_value.json.return_value = response
        receipt = self.client.get_user_latest_receipt(
            'ipntest', 'john.smith@gmail.com')

        self.assertEqual(receipt, 'XDWXQSLE')

    @mock.patch('pyramid_bimt.clickbank.requests')
    def test_get_user_latest_receipt_empty(self, requests):
        requests.request.return_value.json.return_value = None

        with self.assertRaises(KeyError) as cm:
            self.client.get_user_latest_receipt('foo', 'bar')
        self.assertEqual(
            cm.exception.message, 'No receipt found for email foo.')

    @mock.patch('pyramid_bimt.clickbank.requests')
    @mock.patch.object(ClickbankAPI, 'get_user_latest_receipt')
    def test_change_user_subscription_success(
            self, get_user_latest_receipt, requests):
        get_user_latest_receipt.return_value = '1'

        requests.request.return_value.content = ''
        receipt = self.client.change_user_subscription(
            'john.smith@gmail.com', 'ipntest', 'ipntest2')

        self.assertEqual(receipt, '1')

    @mock.patch('pyramid_bimt.clickbank.requests')
    @mock.patch.object(ClickbankAPI, 'get_user_latest_receipt')
    def test_change_user_subscription_exception(
            self, get_user_latest_receipt, requests):
        from pyramid_bimt.clickbank import ClickbankException
        get_user_latest_receipt.return_value = '1'

        requests.request.return_value.content = 'error'
        with self.assertRaises(ClickbankException):
            self.client.change_user_subscription(
                'john.smith@gmail.com', 'ipntest', 'ipntest2')

    def test_get_date_different_timezone(self):
        date1 = self.client._get_date(
            {'date': '2014-12-18T01:53:59-08:00'})
        date2 = self.client._get_date(
            {'date': '2014-12-18T01:53:59-07:00'})
        date3 = self.client._get_date(
            {'date': '2014-12-18T01:53:59+07:00'})

        self.assertTrue(date2 > date1)
        self.assertTrue(date3 > date2)
