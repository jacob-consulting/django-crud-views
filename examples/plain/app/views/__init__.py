from django.contrib.auth.views import LoginView
from django.views import generic


LoginView

class IndexView(generic.TemplateView):

    template_name = "app/index.html"


