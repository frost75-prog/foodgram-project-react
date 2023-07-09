from django.db import transaction
from django.shortcuts import get_object_or_404

from drf_base64.fields import Base64ImageField
from rest_framework.exceptions import ValidationError
from rest_framework.fields import (DecimalField, IntegerField,
                                   SerializerMethodField)
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer

from apps.recipes.models import (Favorite, Ingredient, Recipe,
                                 RecipeIngredient, ShoppingCart, Tag)
from apps.users.models import Follow, User
from .users_serializers import CustomUsersSerialiser


class IngredientSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientInRecipeWriteSerializer(ModelSerializer):
    id = IntegerField(write_only=True)
    amount = DecimalField(max_digits=7, decimal_places=2, required=True)
    name = SerializerMethodField()
    measurement_unit = SerializerMethodField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount', 'name', 'measurement_unit')

    def get_measurement_unit(self, ingredient):
        return ingredient.ingredient.measurement_unit

    def get_name(self, ingredient):
        return ingredient.ingredient.name


class RecipeIngredientSerializer(ModelSerializer):
    id = IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeReadSerializer(ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUsersSerialiser(read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, read_only=True, source='recipes')
    image = Base64ImageField()
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    @property
    def user(self):
        return self.context['request'].user

    def get_is_favorited(self, obj):
        return (
            self.user.is_authenticated and Favorite.objects.filter(
                user=self.user, recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        return (
            self.user.is_authenticated and ShoppingCart.objects.filter(
                user=self.user, recipe=obj).exists()
        )


class RecipeWriteSerializer(ModelSerializer):
    tags = PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())
    author = CustomUsersSerialiser(read_only=True)
    ingredients = RecipeIngredientSerializer(many=True)
    image = Base64ImageField(max_length=None, use_url=True)

    class Meta:
        model = Recipe
        fields = '__all__'
        read_only_fields = ('author',)

    def validate(self, obj):
        for field in ['name', 'text', 'cooking_time']:
            if not obj.get(field):
                raise ValidationError(f'{field} - Обязательное поле.')
        if not obj.get('tags'):
            raise ValidationError('Нужно указать минимум 1 тег.')
        if not obj.get('ingredients'):
            raise ValidationError('Нужно указать минимум 1 ингредиент.')
        inrgedient_id_list = [item['id'] for item in obj.get('ingredients')]
        if len(inrgedient_id_list) != len(set(inrgedient_id_list)):
            raise ValidationError('Ингредиенты должны быть уникальны.')
        return obj

    @transaction.atomic
    def tags_and_ingredients_set(self, recipe, tags, ingredients):
        recipe.tags.set(tags)
        RecipeIngredient.objects.bulk_create(
            [RecipeIngredient(
                recipe=recipe,
                ingredient=get_object_or_404(Ingredient, pk=ingredient['id']),
                amount=ingredient['amount']
            ) for ingredient in ingredients])

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(author=self.context['request'].user,
                                       **validated_data)
        self.tags_and_ingredients_set(recipe, tags, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time)
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        RecipeIngredient.objects.filter(
            recipe=instance,
            ingredient__in=instance.ingredients.all()).delete()
        self.tags_and_ingredients_set(instance, tags, ingredients)
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data


class RecipeShortSerializer(ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowSerializer(ModelSerializer):
    recipes = RecipeShortSerializer(many=True, read_only=True)
    recipes_count = SerializerMethodField(read_only=True)
    is_subscribed = SerializerMethodField(read_only=True)

    def get_recipes_count(self, author):
        return author.recipes.count()

    def get_is_subscribed(self, author):
        if (self.context.get('request') and not self.user.is_anonymous):
            return Follow.objects.filter(user=self.user,
                                         author=author).exists()
        return False

    def get_recipes(self, author):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = author.recipes.all()
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return RecipeShortSerializer(recipes, many=True, read_only=True).data

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes',
                  'recipes', 'recipes_count')
