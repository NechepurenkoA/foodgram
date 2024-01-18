from django.db.models import F
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import ValidationError

from recipes.models import (
    Cart,
    Favorite,
    Ingredient,
    IngredientAmount,
    Recipe,
    Tag
)
from users.models import Follow, User
from .handlers import create_ingredients_connections


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователей."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if (
            'request' in self.context
            and self.context['request'].method == 'GET'
        ):
            self.fields['is_subscribed'] = serializers.SerializerMethodField(
                read_only=True, source='get_is_subcribe'
            )

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'password'
        )
        extra_kwargs = {
            'id': {'read_only': True},
            'password': {'write_only': True}
        }

    def get_is_subscribed(self, obj):
        request = self.context['request']
        return Follow.objects.filter(
            user=request.user.id,
            author=obj
        ).exists()

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тэгов."""

    class Meta:
        fields = '__all__'
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингридиентов их кол-ва."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientForRecipeSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientAmount
        fields = ['id', 'amount']


class UserFollowedSerializer(UserSerializer):
    """Сериализатор для просмотра подписок."""
    recipes = serializers.SerializerMethodField(
        method_name='get_recipes'
    )
    recipes_count = serializers.SerializerMethodField(
        method_name='get_recipes_count'
    )
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'recipes', 'recipes_count'
        )
        extra_kwargs = {
            'id': {'read_only': True}
        }

    def get_recipes(self, obj):
        request = self.context['request']
        recipes_limit = int(request.GET.get('recipes_limit', 5))
        recipes = Recipe.objects.filter(author=obj)[:recipes_limit]
        serializer = self.get_recipes_serializer(recipes, many=True)
        return serializer.data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()

    def get_recipes_serializer(self, *args, **kwargs):
        serializer_class = ShortenRecipeSerializer
        kwargs.setdefault('context', self.context)
        return serializer_class(*args, **kwargs)


class UserFollowedForRecipeSerializer(UserFollowedSerializer):
    """Сериализатор для просмотра подписок."""
    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed'
        )
        extra_kwargs = {
            'id': {'read_only': True}
        }


class ReadRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов."""
    ingredients = serializers.SerializerMethodField(
        method_name='get_ingredients'
    )
    is_favorited = serializers.SerializerMethodField(
        method_name='get_is_favorited'
    )
    is_in_shopping_cart = serializers.SerializerMethodField(
        method_name='get_is_in_shopping_cart'
    )
    tags = TagSerializer(
        many=True
    )
    author = UserFollowedForRecipeSerializer()
    image = Base64ImageField()

    class Meta:
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')
        model = Recipe
        extra_kwargs = {
            'id': {'read_only': True}
        }

    def get_ingredients(self, obj):
        return obj.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=F('ingredientamount__amount')
        )

    def get_is_favorited(self, obj):
        request = self.context['request']
        return Favorite.objects.filter(
            user=request.user.id,
            recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context['request']
        return Cart.objects.filter(
            user=request.user.id,
            recipe=obj
        ).exists()


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов."""
    ingredients = IngredientForRecipeSerializer(
        many=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    author = UserSerializer(read_only=True)
    image = Base64ImageField()

    class Meta:
        fields = ('id', 'tags', 'author', 'ingredients',
                  'name', 'image', 'text', 'cooking_time')
        model = Recipe
        extra_kwargs = {
            'id': {'read_only': True}
        }

    def validate(self, data):
        if 'ingredients' not in data:
            raise ValidationError(
                {'ingredients': 'Укажите ингредиенты.'}
            )
        ingredients = data.get('ingredients')
        ingredients_id_lst = []
        for ingredient in ingredients:
            if ingredient['amount'] < 1:
                raise ValidationError(
                    {
                        'ingredients': 'Укажите верное значение ингредиента.'
                    }
                )
            ingredients_id_lst.append(ingredient['id'])
        if len(ingredients) != len(set(ingredients_id_lst)):
            raise ValidationError(
                {
                    'ingredients': 'Ингредиенты должны быть уникальными.'
                }
            )
        data['ingredients'] = ingredients
        return data

    def create(self, validated_data):
        image = validated_data.pop('image')
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(image=image, **validated_data)
        recipe.tags.set(tags_data)
        create_ingredients_connections(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        IngredientAmount.objects.filter(recipe=instance).delete()
        create_ingredients_connections(instance, ingredients_data)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return ReadRecipeSerializer(
            instance,
            context={'request': self.context['request']}
        ).data


class ShortenRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор укороченных рецептов."""
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class PasswordSerializer(serializers.Serializer):
    """Сериализатор смены пароля."""
    new_password = serializers.CharField(required=True)
    current_password = serializers.CharField(required=True)

    def validate(self, data):
        request = self.context['request']
        user = request.user
        if not user.check_password(data['current_password']):
            raise ValidationError({'current_password': 'Пароль не совпадает!'})
        if user.check_password(data['new_password']):
            raise ValidationError({'new_password': 'Пароль тотже!'})
        return data


class FollowSerializer(serializers.Serializer):
    """Сериализатор подписок."""
    def validate(self, data):
        request = self.context['request']
        author = get_object_or_404(
            User,
            id=self.context['view'].kwargs['user_id']
        )
        user = request.user
        if request.method == 'POST':
            if author == user:
                raise ValidationError(
                    {'error': 'Нельзя подписаться на себя!'}
                )
            if Follow.objects.filter(author=author, user=user).exists():
                raise ValidationError(
                    {'error': 'Вы уже подписаны на этого пользователя!'}
                )
        if request.method == 'DELETE':
            if not Follow.objects.filter(
                author=author,
                user=user
            ).exists():
                raise ValidationError(
                    {'error': 'Вы не подписаны на этого пользователя!'}
                )
        return data


class ShoppingCartSerializer(serializers.Serializer):
    """Сериализатор для корзины"""
    def validate(self, data):
        request = self.context['request']
        recipe = get_object_or_404(
            Recipe,
            id=self.context['view'].kwargs['recipe_id']
        )
        user = request.user
        if request.method == 'POST':
            if Cart.objects.filter(user=user, recipe=recipe).exists():
                raise ValidationError(
                    {'error': 'Рецепт уже в корзине!'}
                )
        if request.method == 'DELETE':
            if not Cart.objects.filter(
                user=user,
                recipe=recipe
            ).exists():
                raise ValidationError(
                    {'error': 'Рецепта нет в корзине!'}
                )
        return data


class FavoriteSerializer(serializers.Serializer):
    """Сериализатор регистрации пользователей."""
    def validate(self, data):
        request = self.context['request']
        recipe = get_object_or_404(
            Recipe,
            id=self.context['view'].kwargs['recipe_id']
        )
        user = request.user
        if request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                raise ValidationError(
                    {'error': 'Рецепт уже в избранном!'}
                )
        if request.method == 'DELETE':
            if not Favorite.objects.filter(
                user=user,
                recipe=recipe
            ).exists():
                raise ValidationError(
                    {'error': 'Рецепта нет в избранном!'}
                )
        return data
