import datetime
import io

from django.conf import settings
from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Rss201rev2Feed

from .models import Writeup


class StyledRss201Feed(Rss201rev2Feed):
    """Rss201rev2Feed that adds an xml-stylesheet PI so browsers render
    the feed as a styled page (via static/feed.xsl) instead of raw XML."""

    def write(self, outfile, encoding):
        buffer = io.StringIO()
        super().write(buffer, encoding)
        content = buffer.getvalue()
        decl_end = content.index('?>') + 2
        stylesheet_pi = '\n<?xml-stylesheet type="text/xsl" href="/static/feed.xsl" media="all"?>'
        outfile.write(content[:decl_end] + stylesheet_pi + content[decl_end:])


class WriteupFeed(Feed):
    feed_type = StyledRss201Feed
    title = settings.SITE_TITLE
    link = '/writeups/'
    description = f'Recent content on {settings.SITE_TITLE}'

    def items(self):
        return Writeup.objects.prefetch_related('tags').order_by('-date')[:20]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.description

    def item_link(self, item):
        return item.get_absolute_url()

    def item_pubdate(self, item):
        return datetime.datetime.combine(item.date, datetime.time(), tzinfo=datetime.timezone.utc)
