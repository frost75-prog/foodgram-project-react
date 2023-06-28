from rest_framework import serializers

from apps.recipes.serializers import RecipeSerializer
from apps.users.models import Follow, User


class SubscribeSerializer(serializers.ModelSerializer):
    """ Общий класс. """
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    @property
    def user(self):
        return self.context['request'].user

    def get_is_subscribed(self, obj):
        return (
            self.user.is_authenticated and Follow.objects.filter(
                user=self.user, author=obj).exists()
        )

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    class Meta:
        model = User
        fields = ('email', 'id',
                  'username', 'first_name',
                  'last_name', 'is_subscribed',
                  'recipes', 'recipes_count')


class SubscribeAuthorSerializer(SubscribeSerializer):
    """[POST, DELETE] Подписка на автора и отписка."""
    email = serializers.ReadOnlyField()
    username = serializers.ReadOnlyField()

    def validate(self, obj):
        if (self.user == obj):
            raise serializers.ValidationError({'errors': 'Ошибка подписки.'})
        return obj


class SubscriptionsSerializer(SubscribeSerializer):
    """[GET] Список авторов на которых подписан пользователь."""
    recipes = serializers.SerializerMethodField()

    def get_recipes(self, obj):
        request = self.context['request']
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = RecipeSerializer(recipes, many=True, read_only=True)
        return serializer.data
