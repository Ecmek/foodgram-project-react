import django_filters as filters

from recipes.models import Recipe, Ingredient


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Ingredient
        fields = ('name',)

class RecipeFilter(filters.FilterSet):
    is_favorited = filters.BooleanFilter(field_name="is_favorited")
    is_in_shopping_cart = filters.BooleanFilter(
        field_name="is_in_shopping_cart"
    )
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'is_in_shopping_cart', 'author', 'tags',)
