from django.conf import settings


def demo(request):
    return {"demo_mode": getattr(settings, "DEMO_MODE", False)}
