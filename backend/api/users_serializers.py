from djoser import serializers
from rest_framework.fields import SerializerMethodField

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
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password'
        )
        write_only_fields = ('password',)
