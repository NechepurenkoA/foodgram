from django.urls import include, path
from rest_framework import routers

from .views import (
    FavoriteViewSet,
    FollowViewSet,
    IngredientViewSet,
    RecipeViewSet,
    ShoppingCartViewSet,
    TagViewSet,
    UserViewSet
)

router = routers.DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(
    r'users/(?P<user_id>\d+)/subscribe',
    FollowViewSet,
    basename='subscribe'
)
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(
    r'recipes/(?P<recipe_id>\d+)/shopping_cart',
    ShoppingCartViewSet,
    basename='shopping_cart'
)
router.register(
    r'recipes/(?P<recipe_id>\d+)/favorite',
    FavoriteViewSet,
    basename='favorite'
)
router.register(r'tags', TagViewSet, basename='tags')


urlpatterns = [
    path('', include(router.urls)),
    path(r'auth/', include('djoser.urls.authtoken')),
]
