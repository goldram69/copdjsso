# apps/discourse/admin.py
from django.contrib import admin
from .models import DiscourseProfile, SsoEventLog

@admin.register(DiscourseProfile)
class DiscourseProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'external_id', 'username', 'last_sync')
    search_fields = ('user__username', 'external_id', 'username')
    list_filter = ('last_sync',)

@admin.register(SsoEventLog)
class SsoEventLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'event_type', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('user__username',)

