from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_staff',
                    'is_active')
    readonly_fields = ('date_joined', 'last_login')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email', )


# Unregister the default UserAdmin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
