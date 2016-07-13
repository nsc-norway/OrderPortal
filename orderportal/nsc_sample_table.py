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
from order import OrderSaver
from orderportal import settings
from orderportal import utils
from orderportal.fields import Fields
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

    def get_samples_from_post(self):
        samples = []
        n_rows = min(
                nsc_transporter.MAX_SAMPLES,
                int(self.get_argument('n_rows', 0))
                )

        for i in range(n_rows):
            sample = dict(
                (field.id, self.get_argument(field.id + "_" + str(i), ''))
                for field in nsc_transporter.SAMPLE_FIELDS
            )
            samples.append(sample)
        return samples

    def get_samples_from_upload(self):
        """Runs CSV import if CSV file present, else runs
        Excel import if excel file present, else raises
        exception."""

        try:
            infile = self.request.files['csv-file'][0]['body']
        except (KeyError, IndexError):
            try:
                infile = self.request.files['excel-file'][0]['body']
            except (KeyError, IndexError):
                raise nsc_transporter.ImportException("No file was uploaded")
            else:
                return nsc_transporter.import_excel_file(infile)
        else:
            return nsc_transporter.import_csv_file(infile)

    @tornado.web.authenticated
    def get(self, iuid):
        try:
            order = self.get_order(iuid)
        except RedirectException:
            return

        samples = order.get('samples', [])
        validation_table, sample_list = nsc_transporter.validate_table(samples)
        self.prepare_page(order, validation_table, sample_list, [])

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

        messages = []

        # Sample data selection:
        # upload (replace all) / clear (all) / alter existing
        if self.get_argument('upload', False):
            try:
                data = self.get_samples_from_upload()
            except nsc_transporter.ImportException as e:
                messages.append(str(e))
                data = order.get('samples', [])
        elif self.get_argument('clear', False):
            data = []
        else:
            data = self.get_samples_from_post()
            if not data:
                data = order.get('samples', [])

        for i, _ in reversed(list(enumerate(data))):
            if self.get_argument('remove-sample-' + str(i), False):
                del data[i]

        validation_table, sample_list = nsc_transporter.validate_table(data)
        is_valid = all(
                    cell.valid
                    for row in validation_table
                    for cell in row
                    ) and validation_table != []

        if not is_valid:
            if self.get_argument('upload', False):
                messages.append("See remarks in red below. You may correct your file and upload it again.")
            else:
                messages.append("Please correct any incorrect / missing values in the table below.")

        if self.get_argument('add-sample', False):
            data.append({})
            validation_table.append(
                [nsc_transporter.Cell(field, True, "", None) for field in nsc_transporter.SAMPLE_FIELDS]
            )
            sample_list.append({})

        # Determine which button was used
        if self.get_argument('submit', False):
            # TODO: if it's valid, redirect back to order page
            # Determine how navigation will work in general
            self.see_other('order', order.get('identifier'))
            return
        elif self.get_argument('save', False) or self.get_argument('clear', False):
            with OrderSaver(doc=order, rqh=self):
                order['samples'] = [
                    dict((c.field.id, c.value) for c in row)
                    for row in validation_table
                    ]
                order['samples_valid'] = is_valid
        self.prepare_page(order, validation_table, sample_list, messages)


    def prepare_page(self, order, validation_table, sample_list, messages=[]):
        self.render('nsc_sample_table.html',
                    title=u"Samples for order '{0}'".format(order['title']),
                    order=order,
                    is_editable=self.is_admin() or self.is_editable(order),
                    messages=messages,
                    table=validation_table,
                    valid=validation_table and all(c.valid for r in validation_table for c in r),
                    columns=nsc_transporter.SAMPLE_FIELDS
                    )
