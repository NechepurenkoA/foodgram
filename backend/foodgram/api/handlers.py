from collections import OrderedDict

from django.db.models import Sum

from recipes.models import Ingredient, IngredientAmount, Recipe


def ingredients_extract(request) -> list:
    """Функция для 'распаковки' ингредиентов и их кол-ва."""
    ingredients = Ingredient.objects.filter(
        ingredientamount__recipe__recipe_in_cart__user=request.user
    ).annotate(amount=Sum('ingredientamount__amount'))
    lines = []
    for ingredient in ingredients:
        lines.append(
            f'{ingredient.name}: {ingredient.amount}'
            f'{ingredient.measurement_unit} \n'
        )
    return lines


def create_ingredients_connections(
        recipe: Recipe,
        ingredients_data: OrderedDict
) -> None:
    """
    Функция для создания связи между
    рецептом и кол-ом ингредиента
    """
    ingredients_list = []
    for ingredient in ingredients_data:
        ingredients_list.append(
            IngredientAmount(
                recipe=recipe,
                ingredient_id=ingredient['id'],
                amount=ingredient['amount']
            )
        )
    IngredientAmount.objects.bulk_create(ingredients_list)
