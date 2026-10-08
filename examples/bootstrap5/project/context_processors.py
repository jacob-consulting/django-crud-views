from django.conf import settings

import crud_views


def project_info(request):  # NOSONAR S1172: Django context-processor signature
    return {
        "demo_mode": getattr(settings, "DEMO_MODE", False),
        "crud_views_version": crud_views.__version__,
    }
