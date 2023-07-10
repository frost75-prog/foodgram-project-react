from django.contrib.auth.password_validation import validate_password
from djoser import serializers
from rest_framework.fields import CharField, SerializerMethodField

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

    @property
    def user(self):
        return self.context['request'].user

    def get_is_subscribed(self, author):
        if (self.context.get('request') and not self.user.is_anonymous):
            return Follow.objects.filter(user=self.user,
                                         author=author).exists()
        return False


class CustomUserCreateSerializer(serializers.UserCreateSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name', 'password')
        read_only_fields = ('id', )

    def validate_username(self, obj):
        invalid_usernames = ['me', 'set_password',
                             'subscriptions', 'subscribe']
        if self.initial_data.get('username') in invalid_usernames:
            raise serializers.ValidationError(
                {'username': 'Вы не можете использовать этот username.'}
            )
        return obj


class CustomSetPasswordSerializer(serializers.SetPasswordSerializer):
    current_password = CharField()
    new_password = CharField()

    def validate(self, obj):
        try:
            validate_password(obj['new_password'])
        except serializers.ValidationError as error:
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
