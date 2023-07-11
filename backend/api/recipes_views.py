from datetime import datetime

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from reportlab.pdfgen.canvas import Canvas
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response

from apps.recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from foodgram.settings import FILE_NAME
from .filters import RecipeFilter
from .pagination import CustomPagination
from .permissions import IsAuthorOrReadOnly
from .recipes_serializers import (IngredientSerializer, RecipeReadSerializer,
                                  RecipeShortSerializer, RecipeWriteSerializer,
                                  TagSerializer)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter,)
    pagination_class = None
    search_fields = ('name',)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = CustomPagination
    permission_classes = (IsAuthorOrReadOnly, )
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'create', 'delete']

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def get_recipe(self, id):
        return get_object_or_404(Recipe, id=id)

    @action(detail=True, methods=['post'],
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk):
        return self.add_to(Favorite, request.user, pk)

    @favorite.mapping.delete
    def unfavorite(self, request, pk):
        return self.delete_from(Favorite, request.user, pk)

    @action(detail=True, methods=['post'],
            permission_classes=(IsAuthenticated,),
            pagination_class=None)
    def shopping_cart(self, request, pk):
        return self.add_to(ShoppingCart, request.user, pk)

    @shopping_cart.mapping.delete
    def delete_from_shopping_cart(self, request, pk):
        return self.delete_from(ShoppingCart, request.user, pk)

    @action(detail=False, methods=['get'],
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        ingredients = ShoppingCart.objects.ingredients(request)
        if not ingredients:
            return Response(
                {'errors': 'В Корзине отсутствуют рецепты'},
                status=status.HTTP_400_BAD_REQUEST
            )
        canvas = Canvas(FILE_NAME)
        canvas.setFont("Helvetica-Bold", 18)
        shopping_list_title = (
            f'Список покупок для: {request.user.get_full_name()}\n'
            f'Дата: {datetime.now().strftime("%A, %d-%m-%Y")}\n\n'
        )
        canvas.drawString(shopping_list_title)
        canvas.setFont("Helvetica", 14)
        shopping_list_body = '\n'.join([
            ' - {ingredient__name} ({ingredient__measurement_unit})'
            ' - {amount:g}'.format(**ingredient) for ingredient in ingredients
        ])
        canvas.drawString(shopping_list_body)
        file = HttpResponse(canvas.save(), content_type='application/pdf;')
        file['Content-Disposition'] = f'inline; filename={FILE_NAME}'
        file['Content-Transfer-Encoding'] = 'binary'
        return file

    def add_to(self, model, user, pk):
        if model.objects.filter(user=user, recipe__id=pk).exists():
            return Response({'errors': 'Рецепт уже добавлен!'},
                            status=status.HTTP_400_BAD_REQUEST)
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.create(user=user, recipe=recipe)
        serializer = RecipeShortSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_from(self, model, user, pk):
        obj = model.objects.filter(user=user, recipe__id=pk)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'errors': 'Рецепт уже удален!'},
                        status=status.HTTP_400_BAD_REQUEST)
