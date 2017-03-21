"OrderPortal: Order information files."

from __future__ import print_function, absolute_import

import logging
from collections import OrderedDict as OD
import re
import base64

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
        order = self.get_entity(iuid, doctype=constants.ORDER)
        data = OD()
        data['type'] = 'order'
        data = self.get_json(order,
                             names=self.get_account_names([order['owner']]),
                             item=data)

        data['fields'] = order['fields']
        data['invalid'] = order['invalid']
        data['files'] = []
        for filename in order.get("_attachments", []):
            stub = order['_attachments'][filename]
            file_content = self.db.get_attachment(order, filename).read()
            data['files'].append(dict(filename=filename,
                              size=stub['length'],
                              content_type=stub['content_type'],
                              data=base64.b64encode(file_content)))

        ## data['owner'] = self.get_account(order['owner'])
        self.set_header('Content-Type', "text/json")
        filename = "{0}.order".format(order['title'])
        self.set_header('Content-Disposition', 'attachment; filename="{0}"'.format(filename))
        self.write(data)

