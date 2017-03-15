"OrderPortal: Order information files."

from __future__ import print_function, absolute_import

import logging
import re

import tornado.web

from orderportal.requesthandler import RequestHandler, ApiV1Mixin
from orderportal.order import *


class NscOrderPkgV1(ApiV1Mixin, OrderApiV1Mixin, Order):
    """Order package; JSON.

    Returns a complete representation of the order, suitable for
    importing into LIMS.

    See project_data_package.py in int repository for a prototype
    script.
    """

    @tornado.web.authenticated
    def get(self, iuid):
        order = kwargs['order']
        data = OD()
        data['type'] = 'order'
        data = self.get_json(order,
                             names=self.get_account_names([order['owner']]),
                             item=data)

        data['fields'] = order['fields']
        data['invalid'] = order['invalid']
        data['owner'] = self.get_entity(order['owner'])
        self.write(data)
