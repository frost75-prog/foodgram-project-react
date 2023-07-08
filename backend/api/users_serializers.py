from djoser.serializers import UserSerializer
from rest_framework.fields import SerializerMethodField

from apps.users.models import Follow, User


class CustomUsersSerialiser(UserSerializer):
    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, author):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, author=author).exists()
