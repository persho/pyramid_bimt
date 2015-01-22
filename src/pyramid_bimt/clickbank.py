# -*- coding: utf-8 -*-
"""Clickbank API."""

from datetime import datetime
import requests


class ClickbankException(Exception):
    pass


class ClickbankAPI(object):
    api_endpoint = 'https://api.clickbank.com/rest/1.3/'

    def __init__(self, dev_key, api_key):
        self.dev_key = dev_key
        self.api_key = api_key

    def _request(self, path, method='GET', params=None):
        headers = {
            'Accept': 'application/json',
            'Authorization': '{}:{}'.format(self.dev_key, self.api_key)
        }
        return requests.request(
            method,
            self.api_endpoint + path,
            headers=headers,
            params=params,
        )

    def get_user_latest_receipt(self, email, product):
        response = self._request(
            'orders/list',
            params={'item': product, 'email': email}
        )
        orders = response.json()['orderData']

        latest_order = max(
            orders,
            key=lambda x: datetime.strptime(x['date'], '%Y-%m-%dT%H:%M:%S-08:00')  # noqa
        )
        return latest_order['receipt']

    def change_user_subscription(self, email, existing_product, new_product):
        """Change user's subscription and return the number of changed
        user's receipt.
        """
        receipt = self.get_user_latest_receipt(email, existing_product)
        response = self._request(
            'orders/{}/changeProduct'.format(receipt),
            method='POST',
            params={'oldSku': existing_product, 'newSku': new_product}
        )
        if response.content:
            raise ClickbankException(
                'Clickbank error: {}'.format(response.content))
        return receipt
