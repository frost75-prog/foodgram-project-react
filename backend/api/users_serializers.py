from djoser.serializers import UserSerializer
from rest_framework import serializers

from apps.users.models import User


class CustomUsersSerialiser(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        user = self.context.get('user')
        return user.follower.filter(author=obj).exists()
