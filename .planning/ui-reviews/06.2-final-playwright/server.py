import json
from pathlib import Path
from tests.test1.conftest import pytest_configure
pytest_configure()
from django.conf import settings
settings.DATABASES['default']['NAME']='/tmp/dcv-playwright-062/db.sqlite3'
settings.ALLOWED_HOSTS=['127.0.0.1','localhost']
settings.ROOT_URLCONF=__name__
from django.core.management import call_command
call_command('migrate',run_syncdb=True,verbosity=0)
from django.contrib.auth.models import User,Permission
from django.contrib.auth import login
from guardian.shortcuts import assign_perm
from tests.test1.app.models import Publisher,Contract
from tests.test1.app.views import PublisherCascadeDeleteView,GuardianPublisherCascadeDeleteView
PublisherCascadeDeleteView.cv_modal=True
GuardianPublisherCascadeDeleteView.cv_modal=True
from django.http import HttpResponse,JsonResponse
from django.shortcuts import redirect
from django.template import engines
from django.urls import path,include
from django.views.decorators.csrf import csrf_exempt
cases=[]
for kind in ['core','guardian']:
 for mode in ['hidden','visible','stale']:
  u=User.objects.create_user(username=kind+'-'+mode)
  obj=Publisher.objects.create(name=kind+' '+mode)
  for perm in ['view_publisher','delete_publisher']:
   if kind=='guardian': assign_perm(perm,u,obj)
   else: u.user_permissions.add(Permission.objects.get(codename=perm,content_type__app_label='app'))
  if mode!='stale':
   contract=Contract.objects.create(publisher=obj,title='VISIBLE-CONTRACT' if mode=='visible' else 'SECRET-CONTRACT')
   if mode=='visible':
    if kind=='guardian': assign_perm('view_contract',u,contract)
    else: u.user_permissions.add(Permission.objects.get(codename='view_contract',content_type__app_label='app'))
  cases.append(dict(kind=kind,mode=mode,user=u.username,pk=obj.pk,url=f'/{"guardian_" if kind=="guardian" else ""}publisher_cascade/{obj.pk}/delete/'))
Path('/tmp/dcv-playwright-062/cases.json').write_text(json.dumps(cases))
def signin(request,name):
 login(request,User.objects.get(username=name),backend='django.contrib.auth.backends.ModelBackend')
 return redirect('/harness/')
def harness(request):
 template=engines['django'].from_string('{% extends "app/base.html" %}{% block content %}<h1>Blocked deletion browser check</h1><a id="launch" data-cv-modal="true" href="{{ target }}">Open delete modal</a>{% endblock %}')
 return HttpResponse(template.render({'target':request.GET.get('target','/')},request))
@csrf_exempt
def protect(request,pk):
 if request.method!='POST': return HttpResponse(status=405)
 Contract.objects.get_or_create(publisher_id=pk,title='STALE-SECRET-CONTRACT')
 return JsonResponse({'protected':True})
def state(request,pk): return JsonResponse({'exists':Publisher.objects.filter(pk=pk).exists(),'contracts':Contract.objects.filter(publisher_id=pk).count()})
urlpatterns=[path('signin/<str:name>/',signin),path('harness/',harness),path('protect/<int:pk>/',protect),path('state/<int:pk>/',state),path('',include('tests.test1.project.urls'))]
from django.core.wsgi import get_wsgi_application
from django.contrib.staticfiles.handlers import StaticFilesHandler
from wsgiref.simple_server import make_server
print('READY',flush=True)
make_server('127.0.0.1',8139,StaticFilesHandler(get_wsgi_application())).serve_forever()
