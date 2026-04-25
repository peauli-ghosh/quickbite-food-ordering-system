from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


class CustomUserAdmin(UserAdmin):
    model = User

    list_display = ("username", "email", "role", "is_staff")
    list_filter = ("role", "is_staff")

    fieldsets = UserAdmin.fieldsets + (
        ("Additional Info", {"fields": ("role", "phone")}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Additional Info", {"fields": ("role", "phone")}),
    )


admin.site.register(User, CustomUserAdmin)