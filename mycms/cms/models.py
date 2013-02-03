# coding:utf-8
"""
Changes : 
25/07/2012 - Additional filter added to BlogPage by is_active flag of a Section
29/07/2012 - Title field added to plain HTML and Blog_page
"""

import django.utils.timezone
from django.utils import timezone
import datetime
from django.utils.timezone import utc
import pytz
from django.db import models
from django.contrib.auth.models import User, Group
import django.template as t
from django.core.context_processors import csrf
from django.template import RequestContext
from django.forms import ModelForm, Textarea, HiddenInput
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, redirect
from django.contrib.auth.models import User

from recaptcha.field import ReCaptchaField
from django.utils.translation import ugettext, ugettext_lazy as _

import mycms.settings as settings
import django.core.exceptions as ex


YN_CHOICES = (
('Y', _('Yes')), ('N', _('No')),
)

TZ = tuple([tuple([tz, tz]) for tz in pytz.common_timezones])

class StandardSection(models.Model):
  '''
  Section of a site
  '''
  
  user_grp =  models.ForeignKey(Group, verbose_name=_(u'User\'s group'), null=True, blank=True)
  parent_item = models.ForeignKey('self', verbose_name=_('Parent menu item'), null=True, blank=True)
  code = models.CharField(max_length=100, verbose_name=_('Section\'s unique code'))
  name = models.CharField(max_length=100, verbose_name=_('Menu items\'s name'), null=True, blank=True)
  name_ru = models.CharField(max_length=100, verbose_name=_('Menu items\'s name in russian'), null=True, blank=True)
  name_en = models.CharField(max_length=100, verbose_name=_('Menu items\'s name in english'), null=True, blank=True)
  description = models.CharField(max_length=240, null=True, blank=True, verbose_name=_('Description'))
  is_menu_item = models.CharField(max_length=1, choices=YN_CHOICES, verbose_name=_('\'Yes\' for menu item, \'No\' for reference'))
  order = models.IntegerField(verbose_name=_('Ordinal number'), null=True, blank=True)
  is_active = models.CharField(max_length=1, choices=YN_CHOICES, verbose_name=_('\'Yes\'-switched on, \'No\'-switched off'))
  
  def get_params(self):
    try:
        page = BasePage.objects.filter(section=self, close_date__isnull=True).latest()
        return page.get_params
    except:
        return ''
    
  def __unicode__(self):
     return self.code #+ '_' + self.name
	 
  def get_id(self):
    return int(self.id)

  def get_name_in_lang(lang_code=None):
    if lang_code == 'en':
      if self.name_en:
        return self.name_en
    elif lang_code == 'ru':
      if self.name_ru:
        return self.name_ru
    return self.name
  
  class Meta:
    unique_together = (('code',), ('name', ),)
  
class BasePage(models.Model):
  '''
  basic class for all content pages classes
  '''
  section = models.ForeignKey(StandardSection, verbose_name=_('Section'))
  title = models.CharField(max_length=500, verbose_name=_('Page\'s title'), null=True, \
                          blank=True) # for use in <TITLE> tag
  title_ru = models.CharField(max_length=500, verbose_name=_('Page\'s title in russian'), null=True, \
                          blank=True)
  title_en = models.CharField(max_length=500, verbose_name=_('Page\'s title in english'), null=True, \
                          blank=True)
  pub_date = models.DateTimeField(verbose_name=_('Pub. Date'), default=datetime.datetime.now(tz=pytz.timezone('Europe/Moscow')))
  close_date = models.DateTimeField(verbose_name=_('Close date'), null=True, blank=True)
  template = models.ForeignKey('Template', verbose_name=_('Template'), null=True, blank=True)
  get_params = models.CharField(max_length=500, verbose_name=_('GET-parameters'), null=True, blank=True)

  # to be redefined in subclasses
  def get_content(self, request, *args, **kwargs):
    return None
  
  def get_title_in_lang(self, lang_code=None):
    if lang_code=='ru':
      if self.title_ru:
        return self.title_ru
    elif lang_code=='en':
      if self.title_en:
        return self.title_en
    return self.title
 
  def get_html(self, request=None, *args, **kwargs): # inserts page's content part into base template, not to be redefined in subclasses
    content, show_form = self.get_content(request, *args, **kwargs) 
    #content = _(content)
    if request.method=='POST':
        if not show_form:
            return HttpResponseRedirect('/content/' + self.section.code + '/' + self.get_params)
    return HttpResponse(self.template.get_rendered_html(request, content, *args, **kwargs))

  def get_lang_code(self, request, *args, **kwargs):
    if kwargs.get('lang_code', None):
      return kwargs['lang_code']
    else:
      return request.LANGUAGE_CODE

  def __unicode__(self):
    return self.section.code + '_' + self.title # to be redefined in subclassess
    
  class Meta:
    get_latest_by = 'pub_date'
    
  def section_code(self):
    return self.section.code

class StandardPage(BasePage):
  '''
  class for standard HTML page: each page is revision, last revision is always taken in view!
  '''
  html = models.TextField(verbose_name=_('content HTML'))
  html_en = models.TextField(verbose_name=_('content HTML (english)'), blank=True, null=True )
  html_ru = models.TextField(verbose_name=_('content HTML (russian)'), blank=True, null=True)
  
  def get_content(self, request, *args, **kwargs):
    v_lang_code = self.get_lang_code(request, *args, **kwargs)
    v_html_lang = self.get_html_in_lang(v_lang_code)
    v_title_lang = self.get_title_in_lang(v_lang_code)

    # TODO move default lang to settings
    if v_lang_code not in ('en', 'ru'):
      v_lang_code = 'ru'

    #return t.Template(self.template.body).render(t.Context({'content':self.html, 'title':self.title})), False
    return t.Template(self.template.body).render(t.Context({'content':v_html_lang, 
                                                   'title':v_title_lang, 
                                                   'lang_code':v_lang_code,
                                                   'translations':self.get_available_langs(request, *args, **kwargs)})), False

  def get_html_in_lang(self, lang_code=None):
    if lang_code == 'en':
      if self.html_en:
        return self.html_en
    elif lang_code == 'ru':
      if self.html_ru:
        return self.html_ru
    #return self.html
    langs = ugettext(u'<P>WARNING: There is no translation in your preferred language. Read the original text or select one of available translations:</p>')
    if self.html_ru:
      langs += '<A href="/content/' + self.section.code + '/ru/">' + u'Русский' + '</a><br>'
    if self.html_en:
      langs += '<A href="/content/' + self.section.code + '/en/">' + u'English' + '</a></p><br>'
    return langs + self.html
  
  # 2012.11.30 - added to let Admin show leaf objects only
  def has_descendants(self):
    # checking BlogEnty descendants - for
    # additional filtering@admin site 
    try:
      obj = BlogEntry.objects.get(pk=self.id)
      return True
    except:
      return False
      
  def get_available_langs(self, request, *args, **kwargs):
    '''
    15/01/2013
    reurns a list of anchors to all available translations
    '''
    all_translations = ['en', 'ru']
    hrefs = ''
    v_lang_code = self.get_lang_code(request, *args, **kwargs)
    if v_lang_code not in ('en', 'ru'):
      v_lang_code = 'ru'

    # take off current content language from list
    all_translations.remove(v_lang_code)
    for lang in all_translations:
      if lang=='ru' and not self.html_ru:
        all_translations.remove(lang)
      elif lang=='en' and not self.html_en:
        all_translations.remove(lang)
    
    for lang in all_translations:
      if hrefs=='':
        if v_lang_code=='ru':
          hrefs += u'Переводы: '
        elif v_lang_code=='en':
          hrefs += u'Translations: '
      hrefs += '<A href="/content/' + self.section.code + '/' + lang + '/">' + '&nbsp;' + lang + '</a>' 
       
    return hrefs

class BlogPage(BasePage):
  '''
  Web log page for blog owner:
  1. List of blog entries (BlogEntry class):
    - Title
    - Date of publication
    - Number of comments
    
  2. Comment form
  
  3. TODO: special owner's mark in Admin part to let comment to be shown
  '''
  user = models.ForeignKey(User, verbose_name=_('User'), null=True, blank=True, unique=True)
  nickname = models.CharField(max_length=80, verbose_name=_('Author\'s nickname'))
  
  def get_content(self, request, *args, **kwargs):
    # Blog's content is a list of blog entries' title
    v_lang_code = self.get_lang_code(request, *args, **kwargs)
    v_title_lang = self.get_title_in_lang(v_lang_code)

    # TODO move default lang to settings
    if v_lang_code not in ('en', 'ru'):
      v_lang_code = 'ru'

    blog_entry_list = BlogEntry.objects.extra(where=['standardpage_ptr_id IN (select be.standardpage_ptr_id '
                                              + 'from cms_blogentry be, cms_standardpage p, cms_basepage bp, cms_standardsection s '
                                              + 'where be.standardpage_ptr_id = p.basepage_ptr_id '
                                              + 'and bp.id = p.basepage_ptr_id '
                                              + 'and s.id = bp.section_id '
                                              + 'and s.is_active = %s)'
                                              ], params=['Y']).filter(blog=self).order_by('-pub_date')

    # splitting list into pages
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    paginator = Paginator(blog_entry_list, 10)
    if request.GET.get('page'):
      page_number = request.GET.get('page') # default page must be set in Admin in parameters field!!!
    else:
      page_number = 1
    try:
        blog_entries = paginator.page(page_number)
    except PageNotAnInteger:
        blog_entries = paginator.page(1)
    except EmptyPage:
        blog_entries = paginator.page(paginator.num_pages)

    return t.Template(self.template.body).render(t.Context({'blog_entries':blog_entries, 
                                                            'title':v_title_lang, 
                                                             'lang_code':v_lang_code})), False
  
class BlogEntry(StandardPage):
    '''
    Blog entry
    --is_open - Y - to show, N - not to show
    --is_active - Y - active (in main list), N - archived (out of date list) - TODO
    --
    '''
    blog = models.ForeignKey(BlogPage, verbose_name=_('Blog to publish in'), null=True, blank=True)
    comment_allowed = models.CharField(max_length=1, verbose_name=_('Let comments (Y/N)'), choices=YN_CHOICES)
    topic = models.ManyToManyField('BlogEntryTopic', verbose_name=_('Topic'), null=True, blank=True)

    def get_content(self, request, *args, **kwargs):
        show_form = False
        form_errors = False 
        context = {}
        context.update(csrf(request))
        context_instance = RequestContext(request, context)
        v_lang_code = self.get_lang_code(request, *args, **kwargs)
        v_html_lang = self.get_html_in_lang(v_lang_code)
        v_title_lang = self.get_title_in_lang(v_lang_code)

        # TODO move default lang to settings
        if v_lang_code not in ('en', 'ru'):
          v_lang_code = 'ru'

        if request.method=='POST':
            comment_form = BlogCommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.creation_time = datetime.datetime.now(tz=pytz.timezone('Europe/Moscow'))
                comment.blog_entry = self
                comment.save()
                from django.core.mail import send_mail
                send_mail('[e-pyfan.com] ' + u'Комментарий на ' + comment.blog_entry.section.code, 
                                    u'Отправил: ' + comment.name + ' ' + str(comment.creation_time) + '\n' +  
                                    u'Текст комментария: ' + comment.text + ' ' + u'Связь: ' + comment.email,
                                   settings.ADMINS[0][1], [settings.ADMINS[0][1]], fail_silently=False)
                show_form = False
            else:
              try:
                comments = BlogEntryComment.objects.filter(blog_entry=self).order_by('creation_time')
              except:
                comments = tuple([])
              #context = {}
              #context.update(csrf(request))
              #context_instance = RequestContext(request, context)	   
              context_instance.update({'content':v_html_lang, 'title':v_title_lang, 
                                                    'comments':comments, 
                                                    'comment_form':comment_form,
                                                    'blog_entry':self,
                                                    'lang_code':v_lang_code,
                                                    'translations':self.get_available_langs(request, *args, **kwargs)})
              return t.Template(self.template.body).render(t.Context(context_instance)), True # to reload page when POST sent
        else:
            if request.GET.get('show_form')=='yes':
                show_form = True
            else:
                show_form = False
        
        if show_form:
            if not form_errors:
              comment_form = BlogCommentForm()
        else:
            comment_link = '/content/' + self.section.code + '/?show_form=yes'
        try:
            comments = BlogEntryComment.objects.filter(blog_entry=self).order_by('creation_time')
        except:
            comments = tuple([])
        #context = {}
        #context.update(csrf(request))
        #context_instance = RequestContext(request, context)	   
        if show_form:
            context_instance.update({'content':v_html_lang, 'title':v_title_lang, 
                                                    'comments':comments, 
                                                    'comment_form':comment_form,
                                                    'blog_entry':self,
                                                    'lang_code':v_lang_code,
                                                    'translations':self.get_available_langs(request, *args, **kwargs)})
        else:
            context_instance.update({'content':v_html_lang, 'title':v_title_lang, 
                                                    'comments':comments, 'comment_link':comment_link, #'comment_form':comment_form,
                                                    'blog_entry':self,
                                                    'lang_code':v_lang_code,
                                                    'translations':self.get_available_langs(request, *args, **kwargs)})
        return t.Template(self.template.body).render(t.Context(context_instance)), show_form
    
    def __unicode__(self):
        if self.blog:
            return self.blog.section.code #+ '_' + self.title
        return self.title
        
    def get_count(self):
        return BlogEntryComment.objects.filter(blog_entry=self).count()
        
    def get_absolute_url(self):
        return '/content/' + self.section.code + '/'
        
    def get_rss_content(self, max_length=100):
        # In RSS item's header first <P>...</p> is always included
        import re
        first_paragraph = re.split(u'<[Pp]>', re.split('</[Pp]>', self.html)[0])[1]
        return t.Template(Template.objects.get(code='PLAIN').body).render(t.Context({'content':first_paragraph}))[:max_length] 
        
class BlogEntryTopic(models.Model):
    '''
    Topics for Blog (python, oracle etc.)
    '''
    topic = models.CharField(max_length=30)
    
    def __unicode__(self):
        return self.topic
        
class BlogEntryComment(models.Model):
  '''
  Comments for a Blog entry
  '''
  blog_entry = models.ForeignKey(BlogEntry, verbose_name=_(u'Blog Entry'))
  creation_time = models.DateTimeField(verbose_name=_(u'Creation Date'), default=datetime.datetime.now(tz=pytz.timezone('Europe/Moscow')))
  name = models.CharField(max_length=100, verbose_name=_(u'Your name*'))
  email = models.CharField(max_length=100, verbose_name=_(u'Your e-mail (won\'t be published anyway)'), null=True, blank=True)
  #comment = models.ForeignKey('self', verbose_name='Ответ на', null=True, blank=True)
  text = models.CharField(max_length=4000, verbose_name=_(u'Comment*'))
  
  def __unicode__(self):
    return self.name + '_' + self.blog_entry.section.code

class UserProfile(models.Model):
  '''
  User profile - additional info about users
  '''
  user = models.OneToOneField(User, verbose_name=_(u'Username'))
  last_visited_url=models.CharField(max_length=240, null=True, blank=True, verbose_name=_(u'Last visited URL')) # not used now
  default_tz = models.CharField(max_length=100, choices=TZ, verbose_name=_(u'Time zone'), default='Europe/Moscow') # not used now
  nickname = models.CharField(max_length=30, unique=True, verbose_name=_(u'Blogger\'s nickname'),null=True, blank=True)
  
  def __unicode__(self):
    return self.user.username + '_profile'
  
class Template(models.Model):
  '''
  html template - used instead of templates stored in file system
  '''
  code = models.CharField(max_length=20, verbose_name=_(u'Template\'s code'), unique=True)
  description = models.TextField(verbose_name=_(u'Description'), null=True, blank=True)
  body = models.TextField(verbose_name=_(u'Template body'), null=True, blank=True)
  base = models.ForeignKey('self', null=True, blank=True, verbose_name=_('Base template'))
  
  def get_rendered_html(self, request, content, get_params=None, *args, **kwargs):
	#Base template's context
    menu_items = StandardSection.objects.filter(is_menu_item='Y', is_active='Y').order_by('order')
    #14.11.2012 defining lang_code
    language_code = kwargs.get('lang_code', None)
    if not language_code:
      language_code = request.LANGUAGE_CODE 
    if language_code in ('en', 'ru'):
      base_items = {'menu_items':menu_items, 'content':content, 'STATIC_URL':settings.STATIC_URL, 
                    'curr_date':datetime.datetime.now(tz=pytz.timezone('Europe/Moscow')), 'lang_code':language_code}
    else:
      base_items = {'menu_items':menu_items, 'content':content, 'STATIC_URL':settings.STATIC_URL, 
                    'curr_date':datetime.datetime.now(tz=pytz.timezone('Europe/Moscow'))}
    context_instance = None
    if request:
        context = {}
        context.update(csrf(request))
        context_instance = RequestContext(request, context)	   
        context_instance.update(base_items)
    else:
        base_context = t.Context(base_items)
    if self.base:
        if context_instance:
            return t.Template(self.base.body).render(context_instance)
        else:
            return t.Template(self.template.base.body).render(base_context)
    return content

  def __unicode__(self):
    return self.code + '_' + self.description 
    
class RequestLog(models.Model):
    '''
    class for storing reqests
    '''
    path = models.CharField(max_length=2000, null=True, blank=True)
    method = models.CharField(max_length=50, null=True, blank=True)
    referer = models.CharField(max_length=2000, null=True, blank=True)
    user = models.CharField(max_length=100, null=True, blank=True)
    ip = models.CharField(max_length=100, null=True, blank=True)
    creation_time = models.DateTimeField(default=datetime.datetime.now(tz=pytz.timezone('Europe/Moscow')))
    
    def populate(self, request):
        try:
          self.path = request.get_full_path()
        except:
          pass
        try:
          self.method = request.method
        except:
          pass
        try:
          self.referer = request.META['HTTP_REFERER']
        except:
          pass
        try:
            self.user = request.META['REMOTE_USER']
        except:
            try:
                self.user = request.META['USERNAME']
            except:
                pass
        self.ip = request.META['REMOTE_ADDR']
     
    def __unicode__(self):
        return self.path
        
class SiteMessage(models.Model):
    '''
    common messages sent from special form
    '''
    sender_name = models.CharField(max_length=100, verbose_name=_(u'Your name*'))
    sender_email = models.EmailField(max_length=100, verbose_name=_(u'Your e-mail'), null=True, blank=True)
    subj = models.CharField(max_length=100, verbose_name=_(u'Subject*'))
    body = models.TextField(verbose_name=_(u'Message body*'))
    
    def __unicode__(self):
        return self.sender_email + '_' + self.subj
  
class SiteMessageForm(ModelForm):
    '''
    A form for composing&sending a common message
    '''
    if settings.USE_RECAPTCHA:
        captcha = ReCaptchaField(error_messages = {  
          'required': _(u'Value is required'),            
          'invalid' : _(u'String is incorrect')  
          },label=_('Type a string from the picture*'))
    class Meta:
        model = SiteMessage
        
class BlogCommentForm(ModelForm):
    """
    A form for commenting a blog entry
    """
    if settings.USE_RECAPTCHA:
        captcha = ReCaptchaField(error_messages = {  
          'required': _(u'Value is required'),            
          'invalid' : _(u'String is incorrect')  
          },label=_('Type a string from the picture*'))
    class Meta:
        model = BlogEntryComment
        fields = ('name', 'email', 'text')
        widgets = {
                   'text': Textarea(),
                  }



