"""ISBG imap layer"""

import imaplib
import logging
import re

from isbg.base import ISBGImapError
from isbg.util import shorten

class ISBGImap:
    """
    This class wraps all standard imap operations used by isbg.

    Most operations are UID commands.

    It raises ISBGImapError when something unexpected happens.
    """
    def __init__(self, hostname, port=993, ssl=True):
        """Initialize server settings"""
        self.hostname = hostname
        self.port = port
        self.ssl = ssl
        self.imap = None
        self.logger = logging.getLogger(__name__)

    def __del__(self):
        self.logout()

    def _imapflags(self, flags):
        """
        Format a list of flags the way the STORE command wants it
        """
        # if we get a string, pass it through
        if isinstance(flags, str):
            return flags
        else:
            return '(' + ','.join(flaglist) + ')'

    def _assertok(self, res, *args):
        """
        Check that imap return code is OK and log the result
        If not ok, raise Exception
        """
        if 'fetch' in args[0]:
            res = shorten(res, 100)
        self.logger.debug("{} = {}".format(args,res))
        if res[0] != "OK":
            raise ISBGImapError(res, "{} returned {} - aborting".format(args, res))

    def connect(self, username, password):
        """Connect and login"""
        if self.ssl:
            self.imap = imaplib.IMAP4_SSL(self.hostname, self.port)
        else:
            self.imap = imaplib.IMAP4(self.hostname, self.port)

        res = self.imap.login(username, password)
        self._assertok(res, "login", username, password)

    def logout(self):
        """Log out and reset imap object"""
        if self.imap is not None:
            self.imap.logout()
            del self.imap
            self.imap = None

    def list(self):
        """
        Just imap list
        """
        res = self.imap.list()
        self._assertok(res, 'list')
        return res

    def getmessage(self, uid):
        """Fetches a message body by uid"""
        res = self.imap.uid("FETCH", uid, "(BODY.PEEK[])")
        self._assertok(res, 'uid fetch', uid, '(BODY.PEEK[])')
        try:
            body = res[1][0][1]
        except:
            self.exception('IMAP Message not in expected format!')
            self.logger.warning("Confused - rfc822 fetch gave {} - The message was probably deleted while we were running".format(res))
        return body

    def get_uidvalidity(self, mailbox):
        """
        Get the value of the UIDVALIDITY attribute of a mailbox.

        This attribute must change if messages are reordered, i.e. message id's changed.
        This is important for isbg since we use message id's to track messages we've already seen.

        https://tools.ietf.org/html/rfc3501#section-2.3.1.1
        """
        uidvalidity = 0
        mbstatus = self.imap.status(mailbox, '(UIDVALIDITY)')
        self._assertok(mbstatus, 'status (uidvalidity)', 'status', '(UIDVALIDITY)')
        body = mbstatus[1][0].decode()
        m = re.search('UIDVALIDITY ([0-9]+)', body)
        if m is not None:
            uidvalidity = int(m.groups()[0])
        return uidvalidity

    def select(self, mailbox, readonly=True):
        """
        Select a mailbox
        """
        if readonly:
            res = self.imap.select(mailbox, 1)
        else:
            res = self.imap.select(mailbox)
        self._assertok(res, 'select', mailbox, readonly)
        return res

    def append(self, mailbox, flags, time, message):
        """Append a message to a mailbox with flags"""
        if flags is not None:
            flags = self._imapflags(flags)
        res = self.imap.append(mailbox, flags, time, message)
        self._assertok(res, 'append', flags, time, message)

    def copy(self, uid, mailbox):
        """Copy message from selected mailbox to mailbox"""
        res = self.imap.uid("COPY", uid, mailbox)
        self._assertok(res, 'uid copy', uid, mailbox)
        return res

    def store(self, uid, command, flags):
        res = self.imap.uid("STORE", uid, command, self._imapflags(flags))
        self._assertok(res, 'uid copy', uid, command)
        return res

    def search(self, charset, criterion, *args):
        # res = typ, uids
        res = self.imap.uid("SEARCH", charset, criterion, *args)
        return res

    def expunge(self):
        res = self.imap.expunge()
        self._assertok(res, 'expunge')
        return res
