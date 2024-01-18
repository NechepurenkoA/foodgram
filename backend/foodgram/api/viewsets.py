from django.forms.models import model_to_dict
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.models import Recipe
from .serializers import ShortenRecipeSerializer


class CustomViewsetForFavoriteAndCart(
    viewsets.ModelViewSet
):
    permission_classes = (IsAuthenticated,)
    http_method_names = ['post', 'delete']

    def create(self, request, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=kwargs['recipe_id'])
        serializer = self.get_serializer(data=model_to_dict(recipe))
        serializer.is_valid(raise_exception=True)
        self.model.objects.create(
            user=request.user,
            recipe=recipe
        )
        serialized_recipe = self.get_recipe_serializer(
            instance=recipe
        )
        return Response(
            serialized_recipe.data,
            status=status.HTTP_201_CREATED
        )

    def delete(self, request, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=kwargs['recipe_id'])
        serializer = self.get_serializer(data=model_to_dict(recipe))
        serializer.is_valid(raise_exception=True)
        self.model.objects.filter(
            user=request.user,
            recipe=recipe
        ).delete()
        return Response(
            serializer.data,
            status=status.HTTP_204_NO_CONTENT
        )

    def get_recipe_serializer(self, *args, **kwargs):
        serializer_class = ShortenRecipeSerializer
        kwargs.setdefault(
            'context',
            self.get_serializer_context()
        )
        return serializer_class(*args, **kwargs)
