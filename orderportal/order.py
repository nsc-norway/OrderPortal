"OrderPortal: Order pages."

from __future__ import unicode_literals, print_function, absolute_import

import logging

import tornado.web

import orderportal
from orderportal import constants
from orderportal import settings
from orderportal import utils
from orderportal import saver
from orderportal.fields import Fields
from orderportal.requesthandler import RequestHandler


class OrderSaver(saver.Saver):
    doctype = constants.ORDER

    def update_fields(self, fields):
        "Update all fields from the HTML form input."
        assert self.rqh is not None
        # Loop over fields defined in the form document and get values.
        # Do not change values for a field if that argument is missing.
        docfields = self.doc['fields']
        for field in fields:
            identifier = field['identifier']
            try:
                value = self.rqh.get_argument(identifier)
            except tornado.web.MissingArgumentError:
                pass
            else:
                if value != docfields.get(identifier):
                    changed = self.changed.setdefault('field_values', dict())
                    changed[identifier] = value
                    docfields[identifier] = value
        # Check validity of current values
        self.doc['invalid'] = dict()
        for field in fields:
            value = docfields.get(identifier)
            # XXX temporary, simplistic
            if field['required'] and value is None:
                self.doc['invalid'][identifier] = 'required'


class OrderMixin(object):
    "Mixin for various useful methods."

    def get_order_status(self, order):
        "Get the order status lookup."
        try:
            return settings['ORDER_STATUSES'][order['status']]
        except KeyError:
            for status in settings['ORDER_STATUSES']:
                if status.get('initial'):
                    return status
            raise ValueError('no initial order status defined')

    def get_targets(self, order):
        "Get the allowed transition targets."
        result = []
        for transition in settings['ORDER_TRANSITIONS']:
            if transition['source'] != order['status']: continue
            permission = transition['permission']
            if self.is_staff() and permission == constants.STAFF:
                result.extend(transition['targets'])
            elif self.is_owner(order) and permission == constants.USER:
                result.extend(transition['targets'])
        return [settings['ORDER_STATUSES'][t] for t in result]

    def is_editable(self, order):
        "Is the order editable by the current user?"
        if self.is_admin(): return True
        status = self.get_order_status(order)
        edit = status.get('edit', [])
        if self.is_staff() and constants.STAFF in edit: return True
        if self.is_owner(order) and constants.USER in edit: return True
        return False


class Orders(RequestHandler):
    "Page for orders list and creating a new order from a form."

    @tornado.web.authenticated
    def get(self):
        if self.is_staff():
            view = self.db.view('order/modified', include_docs=True)
            title = 'Recent orders'
        else:
            view = self.db.view('order/owner', include_docs=True,
                                key=self.current_user['email'])
            title = 'Your orders'
        orders = [self.get_presentable(r.doc) for r in view]
        forms = [self.get_presentable(r.doc) for r in
                 self.db.view('form/pending', include_docs=True)] # XXX enabled!
        self.render('orders.html', title=title, orders=orders, forms=forms)


class Order(OrderMixin, RequestHandler):
    "Order page."

    @tornado.web.authenticated
    def get(self, iuid):
        order = self.get_entity(iuid, doctype=constants.ORDER)
        self.check_read_order(order)
        form = self.get_entity(order['form'], doctype=constants.FORM)
        fields = Fields(form)
        title = order['fields'].get('title') or order['_id']
        self.render('order.html',
                    title="Order '{}'".format(title),
                    order=order,
                    status=self.get_order_status(order),
                    fields=fields,
                    is_editable=self.is_editable(order),
                    targets=self.get_targets(order),
                    logs=self.get_logs(order['_id']))


class OrderCreate(RequestHandler):
    "Create a new order."

    @tornado.web.authenticated
    def post(self):
        self.check_xsrf_cookie()
        form = self.get_entity(self.get_argument('form'),doctype=constants.FORM)
        fields = Fields(form)
        with OrderSaver(rqh=self) as saver:
            saver['form'] = form['_id']
            saver['fields'] = dict([(f['identifier'], None) for f in fields])
            saver['owner'] = self.current_user['email']
            for transition in settings['ORDER_TRANSITIONS']:
                if transition['source'] is None:
                    saver['status'] = transition['target'][0]
                    break
            saver['status'] = None
            doc = saver.doc
        self.see_other(self.reverse_url('order', doc['_id']))


class OrderEdit(RequestHandler):
    "Page for editing an order."

    @tornado.web.authenticated
    def get(self, iuid):
        order = self.get_entity(iuid, doctype=constants.ORDER)
        self.check_edit_order(order)
        form = self.get_entity(order['form'], doctype=constants.FORM)
        fields = Fields(form)
        self.render('order_edit.html',
                    title="Edit order '{}'".format(order['title']),
                    order=order,
                    fields=fields)

    @tornado.web.authenticated
    def post(self, iuid):
        self.check_xsrf_cookie()
        order = self.get_entity(iuid, doctype=constants.ORDER)
        self.check_edit_order(order)
        form = self.get_entity(order['form'], doctype=constants.FORM)
        fields = Fields(form)
        with OrderSaver(doc=order, rqh=self) as saver:
            saver.update_fields(fields)
        self.see_other(self.reverse_url('order', order['_id']))