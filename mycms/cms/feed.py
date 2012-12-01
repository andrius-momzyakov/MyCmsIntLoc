#coding:utf-8

from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed
from cms.models import BlogEntry, BlogEntryTopic, BlogPage, UserProfile
from django.contrib.sites.models import RequestSite
from django.contrib.auth.models import User


class RssLatestBlogEntriesFeed(Feed):
    title = "Новые посты"
    link = "/content/BLOG/"
    description = "Новые посты"
    def get_object(self, request, nickname, topic=None):
        if topic:
          return [BlogEntryTopic.objects.get(topic=topic), BlogPage.objects.get(user=User.objects.get(pk=UserProfile.objects.get(nickname=nickname).user.id))]
        return [None, BlogPage.objects.get(user=User.objects.get(pk=UserProfile.objects.get(nickname=nickname).user.id))]
    def items(self, obj):
      items = []
      if not obj[0]: # не указана рубрика
        return BlogEntry.objects.filter(close_date__isnull=True, blog=obj[1]).order_by('-pub_date')
      for x in BlogEntry.objects.filter(close_date__isnull=True, blog=obj[1]).order_by('-pub_date'):
        if x.topic.filter(topic=obj[0]):
            if x.section.is_active=='Y':
                items.append(x)
      return items
    def item_title(self, obj):
      return obj.title
    def item_description(self, obj):
      return obj.get_rss_content(200)
      
class AtomLatestBlogEntriesFeed(RssLatestBlogEntriesFeed):
    feed_type = Atom1Feed
    subtitle = RssLatestBlogEntriesFeed.description