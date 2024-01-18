from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe, Tag
from users.models import User


class RecipeFilter(filters.FilterSet):
    """Фильтр для рецептов."""
    author = filters.ModelChoiceFilter(
        field_name='author_id',
        queryset=User.objects.all()
    )
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )

    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited'
    )

    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    def filter_is_favorited(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(favorite_is__user=self.request.user)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(recipe_in_cart__user=self.request.user)

    class Meta:
        model = Recipe
        fields = (
            'author',
            'tags',
            'is_favorited',
            'is_in_shopping_cart',
        )


class IngredientFilter(filters.FilterSet):
    """Фильтр для ингредиентов."""
    name = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ('name',)
