"NSC sample table"



from __future__ import print_function, absolute_import

import logging
import re
import urlparse
import json
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

from orderportal import nsc_transporter

class RedirectException(Exception):
    """Signals to the caller that a redirect has been
    triggered, so it should abort and return ASAP."""
    pass

class OrderSamples(OrderMixin, RequestHandler):
    "Sample list page."

    def get_order(self, iuid):
        try:
            match = re.match(settings['ORDER_IDENTIFIER_REGEXP'], iuid)
            if not match: raise KeyError
        except KeyError:
            order = self.get_entity(iuid, doctype=constants.ORDER)
            if order.get('identifier'):
                self.see_other('order', order.get('identifier'))
                raise RedirectException()
        else:
            order = self.get_entity_view('order/identifier', match.group())
        try:
            self.check_readable(order)
        except ValueError, msg:
            self.see_other('home', error=str(msg))
            raise RedirectException()
        return order

    def get_samples_from_post(self, request_args):
        samples = {}
        for i in range(nsc_transporter.MAX_SAMPLES):
            sample = dict(
                (field, self.get_argument(str(i) + '_' + field.id, ''))
                for field in nsc_transporter.SAMPLE_FIELDS
            )
            if any(sample.values()):
                samples.append(sample)
            else:
                break
        return samples


    @tornado.web.authenticated
    def get(self, iuid):
        try:
            order = self.get_order(iuid)
        except RedirectException:
            return

        samples = order.get("samples")
        if samples:
            xxx
        else:
            table = None

        self.prepare_page(order, order.get('samples', []))


    @tornado.web.authenticated
    def post(self, iuid):
        try:
            order = self.get_order(iuid)
        except RedirectException:
            return
        try:
            self.check_editable(order)
        except ValueError, msg:
            self.see_other('home', error=str(msg))

        try:
            infile = self.request.files['file'][0]
            data = nsc_transporter.import_file(infile)
        except (KeyError, IndexError):
            data = self.get_samples_from_post()

        print( args, kwargs )
        # Determine which button was used
        if kwargs.has_key('submit'):
            print ("hello from submitQ")
        elif kwargs.has_key('save'):
            print ("hello from save()")
        elif kwargs.has_key('add-sample'):
            sample_data = dict(
                    (f.id, kwargs.get(f.id, ''))
                    for f in nsc_transporter.SAMPLE_FIELDS
                )
            data.append(sample_data)
            self.prepare_page(order, data)
        else:
            self.prepare_page(order, [])


    def prepare_page(self, order, samples, messages=[]):
        validation_table, sample_list = nsc_transporter.validate_table(samples)

        self.render('nsc_sample_table.html',
                    title=u"Samples for order '{0}'".format(order['title']),
                    order=order,
                    is_editable=self.is_admin() or self.is_editable(order),
                    messages=messages,
                    table=validation_table,
                    valid=validation_table and all(c.valid for c in r for r in validation_table),
                    columns=nsc_transporter.SAMPLE_FIELDS
                    )
