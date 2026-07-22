from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "office_or_hospital")
    search_fields = ("user__username", "office_or_hospital")
