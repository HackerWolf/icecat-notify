#!/usr/bin/env python
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2009 Marco Simonelli <sumydi@gmail.com>
"""
Opens a file in a galago aware environment to inform the user that a download
has completed
"""

import os
import sys
import pynotify
import pygtk
pygtk.require('2.0')
import gtk
import logging
from subprocess import Popen, call

try:
    import gettext
    path = os.path.join(*([os.path.dirname(__file__)] + [os.pardir]*2 + ['po']))
    path = os.path.abspath(path)
    gettext.install('icecatnotify', path)
except ImportError:
    _ = lambda x: unicode(x)


OPEN_COMMAND = "xdg-open"
SUMMARY = _("Download Complete")
BODY = _('%(title)s')


logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger(__name__)


class GalagoNotRunningException(Exception):

    """
    Could not find galago server or Galago server did not behave as expected
    """

    pass


if not pynotify.init("IceCatNotify"):
    raise GalagoNotRunningException


POSSIBLE_ICON_NAMES = ('icecat')

def get_icon():
    try:
        import xdg.IconTheme
    except ImportError:
        return POSSIBLE_ICON_NAMES[0]
    else:
        for name in POSSIBLE_ICON_NAMES:
            if xdg.IconTheme.getIconPath(name) is not None:
                return name
        return POSSIBLE_ICON_NAMES[0]


class IceCatNotification(object):

    """
    Notification for a download complete from IcaCat, essentially a wrapper
    around pynotify
    """

    def __init__(self, title, location):
        """Creates a Notification for IceCat"""
        self.title = title
        self.location = location
        self.notif = None

    def show(self):
        """Displays a notification for icecat.

        Adds actions open and opendir if available
        
        """
        caps = pynotify.get_server_caps()
        if caps is None:
            raise GalagoNotRunningException

        body = BODY % {'title': self.title,
                       'location': self.location}
        self.notif = pynotify.Notification(SUMMARY,
                                      body,
                                      get_icon(),
                                      )
        self.notif.connect('closed', self._cleanup)
        self.notif.set_hint_string("category", "transfer.complete")
        # Note: This won't work until we get the pynotify instance to be
        # static through calls
        self.notif.set_hint_string("x-canonical-append", "allowed")

        if 'actions' in caps:
            try:
                call([OPEN_COMMAND, '--version'])
            except OSError:
                LOG.warn(_("xdg-open was not found"))
                xdg_exists = False
            else:
                xdg_exists = True
                self.notif.add_action("open",
                                    _("Open"),
                                    self.open_file)
                self.notif.add_action("opendir",
                                    _("Open Directory"),
                                    self.open_directory)
        else:
            xdg_exists = False

        LOG.info(_("Displaying notification"))
        if not self.notif.show():
            raise GalagoNotRunningException(_("Could not display notification"))
        if xdg_exists:
            gtk.main()

    def _cleanup(self, notif=None, reason=None):
        """
        Clean up the notification
        """
        assert notif is None or notif == self.notif
        LOG.info(_("Closing"))
        gtk.main_quit()

    def open_file(self, notif=None, action_key=None):
        """Opens the file for the file given in self.location"""
        assert notif is None or notif == self.notif
        LOG.info(_("Opening file %s") % unicode(self.location))
        if self.location:
            Popen([OPEN_COMMAND, self.location])
        self._cleanup()

    def open_directory(self, notif=None, action_key=None):
        """Opens the directory for the file given in self.location"""
        assert notif is None or notif == self.notif
        dir = os.path.abspath(os.path.dirname(self.location))
        LOG.info(_("Opening dir %s") % repr(dir))
        if dir:
            Popen([OPEN_COMMAND, dir])
        self._cleanup()


def main(argv):
    """Opens a notification in icecat
    sys.argv[1] should be the title and sys.argv[2] should be the location

    """
    if len(argv) != 3:
        LOG.critical(_("Invalid number of arguments called"))
        return 1
    notify = IceCatNotification(argv[1], argv[2])
    notify.show()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
