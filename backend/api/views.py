from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from foodgram.settings import FILE_NAME
from .filters import IngredientFilter, RecipeFilter
from .pagination import CustomPagination
from .permissions import IsAuthorOrReadOnly
from .recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from .recipes.serializers import (IngredientSerializer, RecipeCreateSerializer,
                                  RecipeReadSerializer, RecipeSerializer,
                                  TagSerializer, UserReadSerializer)
from .serializers import SubscribeAuthorSerializer, SubscriptionsSerializer
from .users.models import Follow, User
from .users.serializers import SetPasswordSerializer, UserCreateSerializer


class IngredientsAndTagsMixin:
    permission_classes = (AllowAny,)
    pagination_class = None


class UserViewSet(mixins.CreateModelMixin,
                  mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  viewsets.GenericViewSet):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return UserReadSerializer
        return UserCreateSerializer

    def get_user(self, id):
        return get_object_or_404(User, id=id)

    @action(detail=False, methods=['get'],
            pagination_class=None,
            permission_classes=(IsAuthenticated,))
    def me(self, request):
        serializer = UserReadSerializer(request.user)
        return Response(serializer.data,
                        status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'],
            permission_classes=(IsAuthenticated,))
    def set_password(self, request):
        serializer = SetPasswordSerializer(request.user, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response({'detail': 'Пароль успешно изменен!'},
                        status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=(IsAuthenticated,),
            pagination_class=CustomPagination)
    def subscriptions(self, request):
        queryset = self.request.user.follower.prefetch_related(
            'follower', 'following')
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionsSerializer(page, many=True,
                                             context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post'],
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, **kwargs):
        serializer = SubscribeAuthorSerializer(
            self.get_user(kwargs['pk']),
            data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        Follow.objects.create(
            user=request.user, author=self.get_user(kwargs['pk']))
        return Response(serializer.data,
                        status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, **kwargs):
        get_object_or_404(
            Follow, user=request.user,
            author=self.get_user(kwargs['pk'])).delete()
        return Response({'detail': 'Успешная отписка'},
                        status=status.HTTP_204_NO_CONTENT)


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
        _, create = ShoppingCart.objects.get_or_create(
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
        file_list = []
        [file_list.append(
            '{} - {} {}.'.format(*ingredient)) for ingredient in ingredients]
        file = HttpResponse('Cписок покупок:\n' + '\n'.join(file_list),
                            content_type='text/plain')
        file['Content-Disposition'] = (f'attachment; filename={FILE_NAME}')
        return file
