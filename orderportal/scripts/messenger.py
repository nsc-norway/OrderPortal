#!/usr/bin/python2
"""OrderPortal: Send unsent messages to users.

The messages have been prepared previously. This script just sends
them to the designated recipients and records the timestamp.

This script is to be run as a cron job.
"""

from __future__ import print_function, absolute_import

import email.mime.text
import smtplib

from orderportal import settings
from orderportal import utils
from orderportal.message import MessageSaver


class Messenger(object):
    "Send unsent messages to given recipients."

    def __init__(self, db, dry_run=False):
        self.db = db
        self.dry_run = dry_run
        self.banner_printed = False

    @property
    def server(self):
        try:
            return self._server
        except AttributeError:
            host = settings['EMAIL']['HOST']
            try:
                port = settings['EMAIL']['PORT']
            except KeyError:
                self._server = smtplib.SMTP(host)
            else:
                self._server = smtplib.SMTP(host, port=port)
            if settings['EMAIL'].get('TLS'):
                self._server.starttls()
            try:
                user = settings['EMAIL']['USER']
                password = settings['EMAIL']['PASSWORD']
            except KeyError:
                pass
            else:
                self._server.login(user, password)
            return self._server

    def __del__(self):
        try:
            self._server.quit()
        except AttributeError:
            pass

    def process(self):
        "Go through unsent messages, and send them."
        view = self.db.view('message/unsent', include_docs=True)
        for row in view:
            message = row.doc
            if self.dry_run:
                self.print_log(message)
            else:
                self.send_email(message)
                with MessageSaver(doc=message, db=self.db) as saver:
                    saver['sent'] = utils.timestamp()

    def send_email(self, message):
        "Actually send the message as email."
        mail = email.mime.text.MIMEText(message['text'], 'plain', 'utf-8')
        mail['Subject'] = message['subject']
        mail['From'] = message['sender']
        for recipient in message['recipients']:
            mail['To'] = recipient
        self.server.sendmail(message['sender'],
                             message['recipients'],
                             mail.as_string())
        self.print_log(message)

    def print_log(self, message):
        if not self.banner_printed:
            print('Messenger', utils.timestamp())
            if self.dry_run:
                print('*** Dry run only! ***')
            self.banner_printed = True
        print(u"sent email '{0}' to {1}".format(
                message['subject'],
                ', '.join(message['recipients'])).encode('utf-8'))


def get_args():
    parser = utils.get_command_line_parser(description=
        'Send unsent messages.')
    parser.add_option('-d', '--dry-run',
                      action='store_true', dest='dry_run', default=False,
                      help='do not send messages; for debug')
    return parser.parse_args()


if __name__ == '__main__':
    (options, args) = get_args()
    utils.load_settings(filepath=options.settings)
    messenger = Messenger(utils.get_db(), dry_run=options.dry_run)
    messenger.process()
