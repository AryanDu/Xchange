# backend/users/admin.py
from django.contrib import admin

# define admin class first (safe)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "get_full_name", "email", "is_active", "is_staff")
    search_fields = ("email", "full_name", "username")
    list_filter = ("is_active", "is_staff")
    readonly_fields = ("id",)

    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        ("Personal", {"fields": ("full_name", "age", "bio", "avatar_url", "skills", "languages")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login",)}),
    )

    def get_full_name(self, obj):
        return getattr(obj, "full_name", "") or obj.get_username()
    get_full_name.short_description = "Full name"


# Attempt to get the user model and register it with admin in a safe way.
# This avoids raising ImproperlyConfigured when imported outside Django managed context.
try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
except Exception:
    User = None

if User:
    try:
        admin.site.register(User, UserAdmin)
    except admin.sites.AlreadyRegistered:
        # if already registered, replace with our admin
        admin.site.unregister(User)
        admin.site.register(User, UserAdmin)
