# coding:utf-8
"""
Changes:
25.07.2012
- additional filtering of sections by field is_active added

14.11.2012
- internationalization of content added
21.11.2012
- settings.MYCMS_LOGGING switcher added
"""

import os
import mycms.settings as settings

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.contrib import auth


import django.utils.timezone
from django.utils import timezone
import datetime
from django.utils.timezone import utc
import pytz
from django.db.models import Q
from django.core.context_processors import csrf
from django.template import RequestContext, Context, Template
import django.template as t
from django.middleware.csrf import get_token

from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group

import django.core.exceptions as e

import cms.models as m
import cms.forms as f

# 14.11.2012
from django.utils.translation import ugettext as _, ugettext_lazy

def dispatcher(request, section_code, lang_code=None):
  '''
  seeks content by given section_code and returns it as HttpResponse 
  '''
  #return HttpResponse(request.LANGUAGES)
  #return HttpResponse(request.LANGUAGE_CODE)
  # logging a request
  # 21.11.2012
  try:
    if settings.MYCMS_LOGGING: 
      log = m.RequestLog(); log.populate(request) 
      log.creation_time = datetime.datetime.now(tz=pytz.timezone('Europe/Moscow'))
      log.save()
  except NameError:
    # if the setting does not exist then logging is off
    None 
  try:
    section = m.StandardSection.objects.get(code=section_code, is_active='Y')
  except e.ObjectDoesNotExist:
    section = None
  if section:
    # TODO: check users group
    #if request.user.groups!=
    try:
      page = m.BlogEntry.objects.filter(section=section, close_date__isnull=True).latest()
      return page.get_html(request, lang_code=lang_code)
    except e.ObjectDoesNotExist:
      pass
    try:
      page = m.StandardPage.objects.filter(section=section, close_date__isnull=True).latest()
      return page.get_html(request, lang_code=lang_code)
    except e.ObjectDoesNotExist:
      pass
    try:
      page = m.BlogPage.objects.filter(section=section, close_date__isnull=True).latest()
      return page.get_html(request, lang_code=lang_code)
    except e.ObjectDoesNotExist:
      pass
    return HttpResponse(_(u'Page for given section not found.'))
  else:
    return HttpResponse(_(u'Section haven\'t been given or not exists. Page not found.'))
  return HttpResponse(_(u'Unknown error when returning a page.'))
  pass
  
def getnow(request):
  '''
  test view
  '''
  timezone.activate(pytz.timezone('Europe/Moscow'))
  #now = datetime.datetime.utcnow() #.replace(tzinfo=utc)
  now = datetime.datetime.now(tz=timezone.get_default_timezone())
  #now =django.utils.timezone.now() 
  return HttpResponse(now)
  
def list_tz(request):
  '''
  test view
  '''
  s = u''
  for tz in pytz.common_timezones:
    s += (tz + u'\n')
  return HttpResponse(s)  
  
def hi(request):
    '''
    handling login from login form
    '''
    if request.method=='POST':
        uname = request.POST['username']
        passw = request.POST['password']
        user = auth.authenticate(username=uname, password=passw)
        if user is not None and user.is_active:
            auth.login(request, user)
  
    # Section with 'MAIN' code must exist.
    # TODO move section code to settings
    try:
      if settings.MYCMS_MAIN_URL:
        return dispatcher(request, settings.MYCMS_MAIN_URL)
    except NameError:
      None
    return dispatcher(request, 'MAIN') #if setting doesn't exist - use "MAIN" value
  
def my_logout(request):
    '''
    on logout redirecting to the root page
    '''
    from django.contrib.auth import logout
    logout(request)
    return redirect('/')
    
def site_message_form(request):
    '''
    send message form
    '''
    v_lang_code = 'ru'
    if request.LANGUAGE_CODE == 'en':
      v_lang_code = 'en'
    elif request.LANGUAGE_CODE == 'ru':
      v_lang_code = 'ru'
    form = m.SiteMessageForm(request.POST or None)
    if request.method=='POST':
        if form.is_valid():
            form.save()
            from django.core.mail import send_mail
            send_mail('[e-pyfan.com]' + form.cleaned_data['subj'], form.cleaned_data['body'], settings.ADMINS[0][1], [settings.ADMINS[0][1]], fail_silently=False)
            return redirect('/result/message_sent/')
    base_template = t.Template(m.Template.objects.get(code='BASE_00').body)
    child_template = t.Template('<P><B>' + _(u'Compose and send a message:') + '</b></p>{% if form.is_multipart %}' + \
              '<form enctype="multipart/form-data" method="post" action="">{% csrf_token %}' + \
              '{% else %}' + \
              '<form method="post" action="">{% csrf_token %}' + \
              '{% endif %}' + \
              '<table>' + \
              '{{ form.as_table }}' + \
              '</table><input type="submit" value="' + _('Send') + '" />'
              '</form>')
    context = {}
    context.update(csrf(request))
    context_instance = RequestContext(request, context)
    context_instance.update({'form':form})    
    content = child_template.render(context_instance)
    menu_items = m.StandardSection.objects.filter(is_menu_item='Y', is_active='Y').order_by('order')
    base_items = {'menu_items':menu_items, 'content':content, 'STATIC_URL':settings.STATIC_URL, 
                  'curr_date':datetime.datetime.now(tz=pytz.timezone('Europe/Moscow')), 'lang_code':v_lang_code}
    context_instance.update(base_items)
    return HttpResponse(base_template.render(context_instance))    
        
def show_result(request, name):
    #TODO take away constant template code
    v_lang_code = 'ru'
    if request.LANGUAGE_CODE == 'en':
      v_lang_code = 'en'
    elif request.LANGUAGE_CODE == 'ru':
      v_lang_code = 'ru'
    base_template = ''
    try:
      if settings.MYCMS_BASE_TEMPLATE:
        base_template = t.Template(m.Template.objects.get(code=settings.MYCMS_BASE_TEMPLATE).body)
    except NameError:
      base_template = t.Template(m.Template.objects.get(code='BASE_00').body)
    #
    context = {}
    context.update(csrf(request))
    context_instance = RequestContext(request, context)
    content = None
    if name=='message_sent':
        content = _(u'Message sent successfully.')
    menu_items = m.StandardSection.objects.filter(is_menu_item='Y', is_active='Y').order_by('order')
    base_items = {'menu_items':menu_items, 'content':content, 'STATIC_URL':settings.STATIC_URL, 
                  'curr_date':datetime.datetime.now(tz=pytz.timezone('Europe/Moscow')), 'lang_code':v_lang_code}
    context_instance.update(base_items)
    return HttpResponse(base_template.render(context_instance))    
    
    
from django import forms

class CommentForm(forms.Form):
    name = forms.CharField(max_length=30, label=ugettext_lazy(u'Your name'))
    comment = forms.CharField(widget=forms.Textarea, label=ugettext_lazy(u'Comment'))
    
@login_required
def upload_static_file(request):
    v_lang_code = 'en'
    if request.LANGUAGE_CODE == 'en':
      v_lang_code = 'en'
    elif request.LANGUAGE_CODE == 'ru':
      v_lang_code = 'ru'
    if request.method=='POST':
        # uploading a file - make a subdirectory SETTINGS.MY_FILE_ROOT with name=section.code
        form = f.StaticFileUpload(request.POST, request.FILES)
        if form.is_valid():
            # check if subdirectory has been created, if not - create it
            dirname = settings.MY_FILE_ROOT + '\\' + form.cleaned_data['section'].code
            try:
                os.makedirs(dirname)
            except OSError:
                if os.path.exists(dirname):
                    # We are nearly safe
                    pass
                else:
                    # There was an error on creation, so make sure we know about it
                    raise
                if os.path.isdir(dirname):
                    pass
                else: 
                    raise
            # saving a file in a subdirectory
            file = request.FILES['file']
            destination = open(dirname + '\\' + file.name, 'wb+')
            for chunk in file.chunks():
                destination.write(chunk)
            destination.close()
        return redirect('/upload_ok/')
    else:
        form = f.StaticFileUpload()
    # TODO take away a hardcoded template code
    base_template = ''
    try:
      if settings.MYCMS_BASE_TEMPLATE:
        base_template = t.Template(m.Template.objects.get(code=settings.MYCMS_BASE_TEMPLATE).body)
    except NameError:
      base_template = t.Template(m.Template.objects.get(code='BASE_00').body)
    #
    child_template = t.Template('{% if form.is_multipart %}' + \
              '<form enctype="multipart/form-data" method="post" action="">{% csrf_token %}' + \
              '{% else %}' + \
              '<form method="post" action="">{% csrf_token %}' + \
              '{% endif %}' + \
              '<table>' + \
              '{{ form.as_table }}' + \
              '</table><input type="submit" value="' + _('Upload') + '" />'
              '</form>')
    context = {}
    context.update(csrf(request))
    context_instance = RequestContext(request, context)
    context_instance.update({'form':form})    
    content = child_template.render(context_instance)
    menu_items = m.StandardSection.objects.filter(is_menu_item='Y', is_active='Y').order_by('order')
    base_items = {'menu_items':menu_items, 'content':content, 'STATIC_URL':settings.STATIC_URL, 
                  'curr_date':datetime.datetime.now(tz=pytz.timezone('Europe/Moscow')),
                   'lang_code':v_lang_code}
    context_instance.update(base_items)
    return HttpResponse(base_template.render(context_instance))    

def ok_message(request):
    return HttpResponse(_('Data uploaded successfully.'))

