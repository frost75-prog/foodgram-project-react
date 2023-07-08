from django.contrib.auth.password_validation import validate_password
from django.core import exceptions as django_exceptions
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from apps.users.models import Follow, User


class UserReadSerializer(UserSerializer):
    """[GET] Cписок пользователей."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, author):
        user = self.context.get('request').user
        return (
            user.is_authenticated and Follow.objects.filter(
                user=user, author=author).exists()
        )


class CustomUserCreateSerializer(UserCreateSerializer):
    """[POST] Создание нового пользователя."""
    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name',
                  'password')
        write_only_fields = ('password',)

    def validate_username(self, obj):
        invalid_usernames = ['me', 'set_password',
                             'subscriptions', 'subscribe']
        if self.initial_data.get('username') in invalid_usernames:
            raise serializers.ValidationError(
                {'username': 'Вы не можете использовать этот username.'}
            )
        return obj


class SetPasswordSerializer(serializers.Serializer):
    """[POST] Изменение пароля пользователя."""
    current_password = serializers.CharField()
    new_password = serializers.CharField()

    def validate(self, obj):
        try:
            validate_password(obj['new_password'])
        except django_exceptions.ValidationError as error:
            raise serializers.ValidationError(
                {'new_password': list(error.messages)}
            )
        return super().validate(obj)

    def update(self, instance, validated_data):
        current_password = validated_data['current_password']
        new_password = validated_data['new_password']
        if not instance.check_password(current_password):
            raise serializers.ValidationError(
                {'current_password': 'Неправильный пароль.'}
            )
        if current_password == new_password:
            raise serializers.ValidationError(
                {'new_password': 'Новый пароль должен отличаться от текущего.'}
            )
        instance.set_password(new_password)
        instance.save()
        return validated_data
