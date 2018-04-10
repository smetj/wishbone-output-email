#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  __init__.py
#
#  Copyright 2016 Jelle Smet <development@smetj.net>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

from gevent import monkey; monkey.patch_all()
from wishbone.module import OutputModule
from email.mime.text import MIMEText
import smtplib


class EmailOut(OutputModule):
    '''
    Sends out incoming events as email.

    Parameters::

        - from_address(str)("wishbone@localhost")*
           |  The form email address.

        - mta(string)("localhost:25)
           |  The address:port of the MTA to submit the
           |  mail to.

        - native_events(bool)(False)
           |  Submit Wishbone native events.

        - parallel_streams(int)(1)
           |  The number of outgoing parallel data streams.

        - payload(str)(None)
           |  The string to submit.
           |  If defined takes precedence over `selection`.

        - selection(str)("data")
           |  The part of the event to submit externally.
           |  Use an empty string to refer to the complete event.

        - subject(str)("Wishbone")*
           |  The subject of the email.

        - to(list)([])*
           |  A list of destinations.


    Queues::

        - inbox
           |  Incoming messages

    '''

    def __init__(self, actor_config, parallel_streams=1, payload=None, selection="data", native_events=False,
                 mta="localhost:25", subject="Wishbone", to=[], from_address="wishbone@localhost"):
        OutputModule.__init__(self, actor_config)
        self.pool.createQueue("inbox")
        self.registerConsumer(self.consume, "inbox")

    def consume(self, event):

        data = self.getDataToSubmit(event)
        data = self.encode(data)

        try:
            message = MIMEText(data)
            message["Subject"] = event.kwargs.subject
            message["From"] = event.kwargs.from_address
            message["To"] = ",".join(event.kwargs.to)

            mta = smtplib.SMTP(event.kwargs.mta)
            reply = mta.sendmail(event.kwargs.from_address,
                                 event.kwargs.to,
                                 message.as_string()
                                 )
            event.set(reply, "tmp.%s.response" % (self.name))
        except Exception as err:
            raise Exception("Failed to send out email.  Reason: %s" % (err))
