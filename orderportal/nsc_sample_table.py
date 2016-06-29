"NSC sample table"



from __future__ import print_function, absolute_import

import logging
import re
import urlparse
from collections import OrderedDict as OD
from cStringIO import StringIO

import tornado.web

from orderportal import constants
from orderportal import saver
from orderportal import settings
from orderportal import utils
from orderportal.fields import Fields
from orderportal.message import MessageSaver
from orderportal.requesthandler import RequestHandler, ApiV1Mixin

from orderportal.order import OrderMixin



class OrderSamples(OrderMixin, RequestHandler):
    "Sample list page."

    @tornado.web.authenticated
    def get(self, iuid):
        try:
            match = re.match(settings['ORDER_IDENTIFIER_REGEXP'], iuid)
            if not match: raise KeyError
        except KeyError:
            order = self.get_entity(iuid, doctype=constants.ORDER)
            if order.get('identifier'):
                self.see_other('order', order.get('identifier'))
                return
        else:
            order = self.get_entity_view('order/identifier', match.group())
        try:
            self.check_readable(order)
        except ValueError, msg:
            self.see_other('home', error=str(msg))
            return

        samples = order.get("samples")
        if samples:
            xx
        else:
            table = None

        self.render('nsc_sample_table.html',
                    title=u"Samples for order '{0}'".format(order['title']),
                    order=order,
                    account_names=self.get_account_names([order['owner']]),
                    status=self.get_order_status(order),
                    is_editable=self.is_admin() or self.is_editable(order),
                    messages=["test"],
                    table=table,
                    valid=False)

    @tornado.web.authenticated
    def post(self, iuid):
        if self.get_argument('_http_method', None) == 'delete':
            self.delete(iuid)
            return
        raise tornado.web.HTTPError(
            405, reason='internal problem; POST only allowed for DELETE')

    @tornado.web.authenticated
    def delete(self, iuid):
        order = self.get_entity(iuid, doctype=constants.ORDER)
        try:
            self.check_editable(order)
        except ValueError, msg:
            self.see_other('home', error=str(msg))
            return
        self.delete_logs(order['_id'])
        self.db.delete(order)
        self.see_other('orders')
