from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from foodgram.settings import FILE_NAME
from .filters import IngredientFilter, RecipeFilter
from .pagination import CustomPagination
from .permissions import IsAuthorOrReadOnly
from .recipes_serializers import (IngredientSerializer, RecipeCreateSerializer,
                                  RecipeReadSerializer, RecipeSerializer,
                                  TagSerializer)


class IngredientsAndTagsMixin:
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(
        IngredientsAndTagsMixin,
        viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = IngredientFilter


class TagViewSet(
        IngredientsAndTagsMixin,
        viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = CustomPagination
    permission_classes = (IsAuthorOrReadOnly, )
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'create', 'delete']

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeCreateSerializer

    def get_recipe(self, id):
        return get_object_or_404(Recipe, id=id)

    @action(detail=True, methods=['post'],
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, **kwargs):
        serializer = RecipeSerializer(
            self.get_recipe(kwargs['pk']),
            data=request.data,
            context={"request": request})
        serializer.is_valid(raise_exception=True)
        _, create = Favorite.objects.get_or_create(
            user=request.user, recipe=self.get_recipe(kwargs['pk']))
        if create:
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response({'errors': 'Рецепт уже в избранном.'},
                        status=status.HTTP_400_BAD_REQUEST)

    @favorite.mapping.delete
    def delete_favorite(self, request, **kwargs):
        get_object_or_404(
            Favorite, user=request.user, recipe=self.get_recipe(
                kwargs['pk'])).delete()
        return Response({'detail': 'Рецепт успешно удален из избранного.'},
                        status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'],
            permission_classes=(IsAuthenticated,),
            pagination_class=None)
    def shopping_cart(self, request, **kwargs):
        serializer = RecipeSerializer(
            self.get_recipe(kwargs['pk']),
            data=request.data,
            context={"request": request})
        serializer.is_valid(raise_exception=True)
        _, create = ShoppingCart.manager.get_or_create(
            user=request.user, recipe=self.get_recipe(kwargs['pk']))
        if create:
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response({'errors': 'Рецепт уже в списке покупок.'},
                        status=status.HTTP_400_BAD_REQUEST)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, **kwargs):
        get_object_or_404(
            ShoppingCart, user=request.user,
            recipe=self.get_recipe(kwargs['pk'])).delete()
        return Response(
            {'detail': 'Рецепт успешно удален из списка покупок.'},
            status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request, **kwargs):
        ingredients = ShoppingCart.manager.ingredients(request)
        if not ingredients:
            return Response(
                {'errors': 'В Корзине отсутствуют рецепты'},
                status=status.HTTP_400_BAD_REQUEST
            )
        file_list = ['Список покупок:\n\n']
        [file_list.append(
            '{} - {} {}.\n'.format(*ingredient)) for ingredient in ingredients]
        file = HttpResponse(file_list, content_type='text/plain')
        file['Content-Disposition'] = f'attachment; filename={FILE_NAME}'
        return file
