from django.contrib import admin

from .models import Tag, Ingredient

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):

    list_display = ('id', 'name', 'color', 'slug', 'colored_name',)
    search_fields = ('name', 'slug')
    empty_value_display = '-пусто-'

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):

    list_display = ('id', 'name', 'measurement_unit',)
    search_fields = ('name', 'measurement_unit')
    empty_value_display = '-пусто-'
