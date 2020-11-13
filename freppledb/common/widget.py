#
# Copyright (C) 2016 by frePPLe bv
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from django.conf import settings
from django.db import DEFAULT_DB_ALIAS
from django.utils import formats
from django.utils.html import escape
from django.utils.translation import gettext_lazy as _
from django.utils.text import capfirst
from django.utils.encoding import force_text

from freppledb import VERSION
from freppledb.common.dashboard import Dashboard, Widget
from freppledb.common.models import Notification


class WelcomeWidget(Widget):
    name = "welcome"
    title = _("Welcome")
    tooltip = _("Some links to get started")
    asynchronous = False

    def render(self, request=None):
        from freppledb.common.middleware import _thread_locals

        versionnumber = VERSION.split(".", 2)
        try:
            db = _thread_locals.request.database
            if not db or db == DEFAULT_DB_ALIAS:
                prefix = ""
            else:
                prefix = "/%s" % _thread_locals.request.database
        except Exception:
            prefix = ""
        return (
            _(
                """Welcome to the world's leading open source production planning tool!<br><br>
How to get started?
<ol>
<li>Check out the <span class="underline"><a href="%(docurl)s" target="_blank" rel="noopener">documentation</a></span></li>
<li>Visit and join the <span class="underline"><a href="http://groups.google.com/group/frepple-users" target="_blank" rel="noopener">user community</a></span></li>
<li><span class="underline"><a href="https://frepple.com/company/#contact" target="_blank" rel="noopener">Contact us</a></span></li>
</ol>
"""
            )
            % {
                "docurl": "%s/docs/%s.%s/"
                % (settings.DOCUMENTATION_URL, versionnumber[0], versionnumber[1]),
                "prefix": prefix,
            }
        )


Dashboard.register(WelcomeWidget)


class NewsWidget(Widget):
    name = "news"
    title = _("News")
    tooltip = _("Show the latest news items from the frePPLe website")
    asynchronous = False

    def render(self, request=None):
        return '<iframe style="width:100%; border:none;" src="https://frepple.com/news-summary/"></iframe>'


Dashboard.register(NewsWidget)


class InboxWidget(Widget):
    name = "inbox"
    title = _("inbox")
    tooltip = _("Unread messages from your inbox")
    url = "/inbox/"
    asynchronous = False
    limit = 10

    def render(self, request=None):
        from freppledb.common.middleware import _thread_locals

        try:
            db = _thread_locals.request.database or DEFAULT_DB_ALIAS
        except Exception:
            db = DEFAULT_DB_ALIAS
        notifs = (
            Notification.objects.using(db)
            .filter(user=_thread_locals.request.user)
            .order_by("-id")
            .select_related("comment", "user")[: self.limit]
        )
        result = []
        result.append(
            '<div class="table-responsive"><table class="table table-condensed table-hover"><tbody>'
        )
        for notif in notifs:
            result.append(
                '<tr><td><a class="underline" href="%s%s">%s</a>&nbsp;<span class="small">%s</span><div class="small" style="float: right;">%s&nbsp;&nbsp;%s</div><br><p style="padding-left: 10px; display: inline-block;">%s</p>'
                % (
                    _thread_locals.request.prefix,
                    notif.comment.getURL(),
                    notif.comment.object_pk,
                    escape(
                        capfirst(force_text(_(notif.comment.content_type.name)))
                        if notif.comment.content_type
                        else ""
                    ),
                    escape(notif.comment.user.username),
                    formats.date_format(notif.comment.lastmodified, "DATETIME_FORMAT"),
                    escape(notif.comment.comment),
                )
                + "</td></tr>"
            )
        result.append("</tbody></table></div>")
        return "\n".join(result) if result else force_text(_("No unread messages!"))

    javascript = """
    var hasForecast = %s;
    var hasIP = %s;
    var version = '%s.%s';
    """ % (
        "true" if "freppledb.forecast" in settings.INSTALLED_APPS else "false",
        "true" if "freppledb.inventoryplanning" in settings.INSTALLED_APPS else "false",
        VERSION.split(".", 2)[0],
        VERSION.split(".", 2)[1],
    )


Dashboard.register(InboxWidget)
