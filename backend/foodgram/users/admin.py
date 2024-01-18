from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """"Админка пользователей."""
    list_display = ('username', 'email', 'first_name')
    search_fields = ('username',)
    list_filter = ('username',)
    empty_value_display = '-пусто-'
