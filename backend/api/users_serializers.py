from django.contrib.auth.password_validation import validate_password
from django.core import exceptions

from djoser import serializers
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import CharField

from apps.users.models import Follow, User


class CustomUsersSerialiser(serializers.UserSerializer):
    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )

    def get_is_subscribed(self, author):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Follow.objects.filter(user=request.user, author=author).exists()


class CustomSetPasswordSerializer(serializers.SetPasswordSerializer):
    """[POST] Изменение пароля пользователя."""
    current_password = CharField()
    new_password = CharField()

    def validate(self, obj):
        try:
            validate_password(obj['new_password'])
        except exceptions.ValidationError as error:
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


class CustomUserCreateSerializer(serializers.UserCreateSerializer):
    """[POST] Создание нового пользователя."""
    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )
