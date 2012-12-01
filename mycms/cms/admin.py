from django.contrib import admin
from cms.models import StandardSection, StandardPage, UserProfile, Template, BlogPage, \
                        BlogEntry,\
                        BlogEntryComment, RequestLog, BlogEntryTopic,\
			SiteMessage

class StandardSectionAdmin(admin.ModelAdmin):
  list_display = ('code', 'name', 'is_menu_item', 'is_active')
admin.site.register(StandardSection, StandardSectionAdmin)

class StandardPageAdmin(admin.ModelAdmin):
  list_display = ('section', 'title', 'pub_date')
  ordering = ('section', '-pub_date')
  def queryset(self, request):
    qs = StandardPage.objects.all()
    res = []
    for item in qs:
      if not item.has_descendants():
        res.append(item.id)
    return StandardPage.objects.filter(pk__in=res)

admin.site.register(StandardPage, StandardPageAdmin)

class BlogPageAdmin(admin.ModelAdmin):
  list_display = ('section', 'title', 'pub_date')
  ordering = ('section', '-pub_date')

admin.site.register(BlogPage, BlogPageAdmin)

class BlogEntryAdmin(admin.ModelAdmin):
  list_display = ('section', 'title', 'pub_date')
  ordering = ('section', '-pub_date')

admin.site.register(BlogEntry, BlogEntryAdmin)

admin.site.register(UserProfile)
admin.site.register(Template)
#admin.site.register(BasePage)
admin.site.register(BlogEntryComment)
admin.site.register(RequestLog)
admin.site.register(BlogEntryTopic)
admin.site.register(SiteMessage)


