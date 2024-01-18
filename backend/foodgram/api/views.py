from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from recipes.models import Cart, Favorite, Ingredient, Recipe, Tag
from users.models import Follow, User
from .filters import IngredientFilter, RecipeFilter
from .handlers import ingredients_extract
from .pagination import CustomPagination
from .permissions import (
    IsAdminOrReadOnly,
    IsAuthenticatedOrSignUp,
    RecipePermissions
)
from .serializers import (
    FavoriteSerializer,
    FollowSerializer,
    IngredientSerializer,
    PasswordSerializer,
    RecipeSerializer,
    ShoppingCartSerializer,
    TagSerializer,
    UserFollowedSerializer,
    UserSerializer
)
from .viewsets import CustomViewsetForFavoriteAndCart


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (RecipePermissions,)
    serializer_class = RecipeSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = CustomPagination

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        methods=['get'],
        detail=False,
        url_path='download_shopping_cart',
        permission_classes=[permissions.IsAuthenticated],
        serializer_class=RecipeSerializer,
    )
    def download_shopping_cart(self, request):
        filename = 'Spisok_pokypok.txt'
        response = HttpResponse(
            content_type='text/plain; charset=UTF-8'
        )
        response['Content-Disposition'] = (
            'attachment; filename={0}'.format(filename)
        )
        response.writelines(ingredients_extract(request))
        return response


class ShoppingCartViewSet(CustomViewsetForFavoriteAndCart):
    model = Cart
    queryset = model.objects.all()
    serializer_class = ShoppingCartSerializer


class FavoriteViewSet(CustomViewsetForFavoriteAndCart):
    model = Favorite
    queryset = model.objects.all()
    serializer_class = FavoriteSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('username')
    permission_classes = (IsAuthenticatedOrSignUp,)
    serializer_class = UserSerializer
    pagination_class = CustomPagination
    ordering = 'id'
    http_method_names = ['get', 'post']

    @action(
        methods=['get'],
        detail=False,
        url_path='me',
        permission_classes=[permissions.IsAuthenticated],
        serializer_class=UserSerializer,
    )
    def users_own_profile(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['get'],
        detail=False,
        url_path='subscriptions',
        permission_classes=[permissions.IsAuthenticated],
        serializer_class=UserFollowedSerializer,
    )
    def user_subsctiptions(self, request):
        author_ids = Follow.objects.filter(
            user=request.user
        ).values_list('author', flat=True)
        users = User.objects.filter(pk__in=author_ids)
        page = self.paginate_queryset(users)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        methods=['post'],
        detail=False,
        url_path='set_password',
        permission_classes=[permissions.IsAuthenticated],
        serializer_class=PasswordSerializer
    )
    def reset_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.set_password(
            serializer.validated_data['new_password']
        )
        request.user.save()
        return Response(
            serializer.data,
            status=status.HTTP_204_NO_CONTENT
        )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    permission_classes = (IsAdminOrReadOnly,)
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    permission_classes = (IsAdminOrReadOnly,)
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class FollowViewSet(viewsets.ModelViewSet):
    queryset = Follow.objects.all()
    permission_classes = (permissions.IsAuthenticated,)
    http_method_names = ['post', 'delete']
    serializer_class = FollowSerializer

    def create(self, request, *args, **kwargs):
        author = get_object_or_404(User, id=kwargs['user_id'])
        serializer = self.get_serializer(data=model_to_dict(author))
        serializer.is_valid(raise_exception=True)
        Follow.objects.create(
            author=author,
            user=request.user
        )
        serialized_user = self.get_user_serializer(
            instance=author
        )
        return Response(
            serialized_user.data,
            status=status.HTTP_201_CREATED
        )

    def delete(self, request, *args, **kwargs):
        author = get_object_or_404(User, id=kwargs['user_id'])
        serializer = self.get_serializer(data=model_to_dict(author))
        serializer.is_valid(raise_exception=True)
        Follow.objects.filter(author=author, user=request.user).delete()
        return Response(
            serializer.data,
            status=status.HTTP_204_NO_CONTENT
        )

    def get_user_serializer(self, *args, **kwargs):
        serializer_class = UserFollowedSerializer
        kwargs.setdefault(
            'context',
            self.get_serializer_context()
        )
        return serializer_class(*args, **kwargs)
