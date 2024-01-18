from django.contrib import admin

from .models import Ingredient, Recipe, Tag


@admin.register(Recipe)
class RecipesAdmin(admin.ModelAdmin):
    """"Админка рецептов."""
    list_display = ('author', 'name')
    search_fields = ('name',)
    list_filter = ('author', 'tags')
    empty_value_display = 'пусто'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """"Админка рецептов."""
    list_display = ('name', 'slug')
    search_fields = ('slug',)
    list_filter = ('slug',)
    empty_value_display = 'пусто'


@admin.register(Ingredient)
class IngridientAdmin(admin.ModelAdmin):
    """"Админка рецептов."""
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)
    empty_value_display = 'пусто'
