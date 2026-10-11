from django.contrib import admin

from .models import NotificationLog, Template, Trigger

admin.site.register(Trigger)
admin.site.register(Template)
admin.site.register(NotificationLog)
