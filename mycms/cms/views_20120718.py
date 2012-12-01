# coding:utf-8
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

def dispatcher(request, section_code):
  '''
  Выводит страницу, соответствующую данному разделу
  '''
  # журналируем запрос
  #return HttpResponse(request.method)
  log = m.RequestLog(request)
  log.save()
  #try:
  #  log = m.RequestLog(request)
  #  log.save()
  #except:
  #  None
  try:
    section = m.StandardSection.objects.get(code=section_code)
  except e.ObjectDoesNotExist:
    section = None
  #return HttpResponse('sec: '+section.code)
  if section:
    # проверка группы пользователя
    #if request.user.groups!=
    try:
      page = m.BlogEntry.objects.filter(section=section, close_date__isnull=True).latest()
      return page.get_html(request)
    except e.ObjectDoesNotExist:
      pass
    try:
      page = m.StandardPage.objects.filter(section=section, close_date__isnull=True).latest()
      return page.get_html(request)
    except e.ObjectDoesNotExist:
      pass
    try:
      page = m.BlogPage.objects.filter(section=section, close_date__isnull=True).latest()
      return page.get_html(request)
    except e.ObjectDoesNotExist:
      pass
    return HttpResponse('Страница не найдена 1.')
  else:
    return HttpResponse('Страница не найдена 2.')
  # переделать под различные типы шаблонов
  return HttpResponse('Пролёт')
  pass
  

# fuckin' тесты
def getnow(request):
  timezone.activate(pytz.timezone('Europe/Moscow'))
  #now = datetime.datetime.utcnow() #.replace(tzinfo=utc)
  now = datetime.datetime.now(tz=timezone.get_default_timezone())
  #now =django.utils.timezone.now() 
  return HttpResponse(now)
  
def list_tz(request):
  s = u''
  for tz in pytz.common_timezones:
    s += (tz + u'\n')
  return HttpResponse(s)  
  
def hi(request):
    # обработка логина
    if request.method=='POST':
        uname = request.POST['username']
        passw = request.POST['password']
        user = auth.authenticate(username=uname, password=passw)
        if user is not None and user.is_active:
            auth.login(request, user)
  
    # TODO доб для одного раздела признак "корневой"
    return dispatcher(request, 'MAIN')
  
def my_logout(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('/')
    
from django import forms

class CommentForm(forms.Form):
    name = forms.CharField(max_length=30, label='Имя:')
    comment = forms.CharField(widget=forms.Textarea, label='Комментарий:')
    
def view2(request):
    parent_template = Template('<h1>{{ title }}</h1>{{ parent_content }}')
    child_template = Template('Сегодня поговорим на тему "{{ child_content }}".')
    child_context = Context({'child_content':'вреда курения'})
    parent_context = Context({'parent_content':child_template.render(child_context), 'title':'Лекция о вреде курения'})
    return HttpResponse(parent_template.render(parent_context))

    
def view3(request):
    if request.method=='POST':
        return redirect('/')
    context = {}
    context.update(csrf(request))
    context_instance = RequestContext(request, context)	   
    parent_template = Template('<h1>{{ title }}</h1>{{ parent_content }}')
    child_template = Template('Сегодня поговорим на тему "{% autoescape off %}{{ child_content }}{% endautoescape %}".' + \
                              '<FORM action="." method="POST">{% csrf_token %}<TABLE>{{comment_form.as_table}}</table>' + \
                              '<input type="submit" value="Отправить"></form>')
    comment_form=CommentForm()
    context_instance.update({'child_content':'<B>вреда курения</b>', 'comment_form':comment_form})
    parent_context = Context({'parent_content':child_template.render(context_instance), 'title':'Лекция о вреде курения'})
    return HttpResponse(parent_template.render(parent_context))

@login_required
def upload_static_file(request):
    if request.method=='POST':
        # обработка файла - создаём подкаталог в SETTINGS.MY_FILE_ROOT c именем=section.code!
        form = f.StaticFileUpload(request.POST, request.FILES)
        if form.is_valid():
            # проверяем, создан ли подкаталог и создаём если нет
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
            # сохраняем файл в созданном подкаталоге
            file = request.FILES['file']
            destination = open(dirname + '\\' + file.name, 'wb+')
            for chunk in file.chunks():
                destination.write(chunk)
            destination.close()
        return redirect('/upload_ok/')
    else:
        form = f.StaticFileUpload()
    base_template = t.Template(m.Template.objects.get(code='BASE_00').body)
    child_template = t.Template('{% if form.is_multipart %}' + \
              '<form enctype="multipart/form-data" method="post" action="">{% csrf_token %}' + \
              '{% else %}' + \
              '<form method="post" action="">{% csrf_token %}' + \
              '{% endif %}' + \
              '<table>' + \
              '{{ form.as_table }}' + \
              '</table><input type="submit" value="Загрузить" />'
              '</form>')
    context = {}
    context.update(csrf(request))
    context_instance = RequestContext(request, context)
    context_instance.update({'form':form})    
    content = child_template.render(context_instance)
    menu_items = m.StandardSection.objects.filter(is_menu_item='Y', is_active='Y').order_by('order')
    base_items = {'menu_items':menu_items, 'content':content, 'STATIC_URL':settings.STATIC_URL, 'curr_date':datetime.datetime.now(tz=pytz.timezone('Europe/Moscow'))}
    context_instance.update(base_items)
    return HttpResponse(base_template.render(context_instance))    

def ok_message(request):
    return HttpResponse('Данные переданы успешно.')
    
def my_logout(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('/')

    