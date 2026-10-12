from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("triggers", views.TriggerViewSet)
router.register("templates", views.TemplateViewSet)

urlpatterns = [
    path("admin/", include(router.urls)),
    path("admin/logs/", views.logs),
    path("admin/variables/", views.variables),
    path("admin/run-inactivity-check/", views.run_inactivity_check),
    path("events/fire/", views.fire_event),
    path("cron/inactivity-check/", views.cron_inactivity_check),
    path("status/", views.status),
    path("whatsapp/webhook/", views.whatsapp_webhook),
]
