from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Ingredient, Recipe, RecipeIngredient, RecipeTag, Subscribe, Tag
)


class RecipeTagAdmin(admin.StackedInline):
    model = RecipeTag
    autocomplete_fields = ('tag',)


class RecipeIngredientAdmin(admin.StackedInline):
    model = RecipeIngredient
    autocomplete_fields = ('ingredient',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):

    list_display = ('id', 'get_author', 'name', 'text', 'cooking_time',
                    'get_image', 'get_tags', 'get_ingredients', 'pub_date',)
    search_fields = ('name', 'cooking_time', 'author__email',
                     'ingredients__name')
    list_filter = ('pub_date', 'tags',)
    inlines = (RecipeTagAdmin, RecipeIngredientAdmin,)
    empty_value_display = '-пусто-'
    save_on_top = True

    @admin.display(description='author email')
    def get_author(self, obj):
        return obj.author.email

    @admin.display(description='image')
    def get_image(self, obj):
        return format_html(
            f'<img src="{obj.image.url}" width=50px; height=50px;>'
        )

    @admin.display(description='tags')
    def get_tags(self, obj):
        return ', '.join([i.name for i in obj.tags.all()])

    @admin.display(description='ingredient')
    def get_ingredients(self, obj):
        return '\n '.join(
            [f'{i.ingredient.name} - {i.amount}{i.ingredient.measurement_unit}'
             for i in RecipeIngredient.objects.filter(recipe=obj)]
        )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):

    list_display = ('id', 'name', 'color', 'slug', 'colored_name',)
    search_fields = ('name', 'slug')
    empty_value_display = '-пусто-'

    def colored_name(self, obj):
        return format_html(
            f'<span style="color: {obj.color}; width=20px;'
            f'height=20px;">{obj.name}</span>'
        )


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):

    list_display = ('id', 'name', 'measurement_unit',)
    search_fields = ('name', 'measurement_unit')
    empty_value_display = '-пусто-'


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):

    list_display = ('id', 'follower', 'following', 'created',)
    search_fields = ('follower__email', 'following__email',)
    empty_value_display = '-пусто-'
