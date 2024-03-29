from django.shortcuts import get_object_or_404

from djoser.views import UserViewSet
from rest_framework import exceptions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.users.models import Follow, User
from .pagination import CustomPagination
from .permissions import IsAuthenticatedOrAdmin
from .users_serializers import CustomUsersSerialiser
from .recipes_serializers import FollowSerializer


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    pagination_class = CustomPagination
    serializer_class = CustomUsersSerialiser

    def get_user(self, id):
        return get_object_or_404(User, id=id)

    @action(detail=False, permission_classes=(IsAuthenticatedOrAdmin,))
    def subscriptions(self, request):
        queryset = User.objects.filter(following__user=request.user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post'], serializer_class=FollowSerializer,
            permission_classes=(IsAuthenticatedOrAdmin,))
    def subscribe(self, request, **kwargs):
        author = self.get_user(kwargs['id'])
        if request.user == author:
            raise exceptions.ValidationError(
                'Подписываться на себя запрещено.')
        _, created = Follow.objects.get_or_create(
            user=request.user, author=author)
        if not created:
            raise exceptions.ValidationError(
                'Вы уже подписаны на этого пользователя.')
        serializer = self.get_serializer(author)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, **kwargs):
        author = self.get_user(kwargs['id'])
        get_object_or_404(Follow, user=request.user, author=author).delete()
        return Response({'detail': 'Успешная отписка'},
                        status=status.HTTP_204_NO_CONTENT)
