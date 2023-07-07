from dataclasses import asdict

from django.core.validators import (MinValueValidator, RegexValidator,
                                    validate_image_file_extension,
                                    validate_unicode_slug)
from django.db import models
from django.utils.translation import gettext_lazy as _

from foodgram.settings import MAX_LENGTH_INGREDIENTFIELDS, REGEX_COLOR_TAG
from apps.users.models import User


class IngredientsQuerySet(models.QuerySet):
    def ingredients(self, request):
        shopping_cart = ShoppingCart.objects.filter(user=request.user)
        recipes_id = [item.recipe.id for item in shopping_cart]
        return RecipeIngredient.objects.filter(recipe__in=recipes_id).values(
            'ingredient__name', 'ingredient__measurement_unit').annotate(
            amount=models.Sum('amount'))


class Ingredient(models.Model):
    name = models.CharField(
        verbose_name=_('Название'),
        max_length=MAX_LENGTH_INGREDIENTFIELDS
    )
    measurement_unit = models.CharField(
        verbose_name=_('Единица измерения'),
        max_length=MAX_LENGTH_INGREDIENTFIELDS
    )

    class Meta:
        ordering = ('-id',)
        verbose_name = _('Ингридиент')
        verbose_name_plural = _('Ингридиенты')
        constraints = [
            models.UniqueConstraint(fields=['name', 'measurement_unit'],
                                    name='unique ingredient')
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Tag(models.Model):
    name = models.CharField(
        verbose_name=_('Название'),
        max_length=MAX_LENGTH_INGREDIENTFIELDS
    )
    color = models.CharField(
        verbose_name=_('Цвет в HEX'),
        max_length=7,
        null=True,
        validators=[
            RegexValidator(
                REGEX_COLOR_TAG,
                message=_('Поле должно содержать HEX-код выбранного цвета.')
            )
        ]

    )
    slug = models.SlugField(
        verbose_name=_('Уникальный слаг'),
        max_length=MAX_LENGTH_INGREDIENTFIELDS,
        unique=True,
        null=True,
        validators=[validate_unicode_slug]
    )

    class Meta:
        verbose_name = _('Тег')
        verbose_name_plural = _('Теги')
        default_related_name = 'tags'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    name = models.CharField(
        verbose_name=_('Название рецепта'),
        max_length=MAX_LENGTH_INGREDIENTFIELDS
    )
    text = models.TextField(
        verbose_name=_('Описание рецепта')
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name=_('Время приготовления, мин'),
        validators=[
            MinValueValidator(
                1, message=_('Минимальное время приготовления - 1 минута'))
        ]
    )
    image = models.ImageField(
        verbose_name=_('Картинка рецепта'),
        upload_to='recipes/',
        blank=True,
        validators=[validate_image_file_extension]
    )
    pub_date = models.DateTimeField(
        verbose_name=_('Дата публикации'),
        auto_now_add=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('Автор рецепта')
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        through_fields=('recipe', 'ingredient'),
        verbose_name=_('Ингредиенты для рецепта')
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name=_('Теги рецепта')
    )
    slug = models.SlugField(
        verbose_name=_('Уникальный слаг'),
        max_length=MAX_LENGTH_INGREDIENTFIELDS,
        unique=True,
        null=True,
        validators=[validate_unicode_slug]
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = _('Рецепт')
        verbose_name_plural = _('Рецепты')
        default_related_name = 'recipes'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):

    MESSAGE = ('{recipe.name}: {ingredient.name}'
               ' - {amount} {ingredient.measurement_unit}')

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name=_('Рецепт')
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredients',
        verbose_name=_('Ингредиент')
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name=_('Количество'),
        validators=[
            MinValueValidator(
                1, message=_('Минимальное количество ингридиентов - 1'))
        ]
    )

    class Meta:
        verbose_name = _('Ингредиенты в рецепте')
        verbose_name_plural = _('Ингредиенты в рецептах')
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_combination'
            )
        ]

    def __str__(self):
        return self.MESSAGE.format(**asdict(self))


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('Автор списка избранного')
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name=_('Избранный рецепт')
    )

    class Meta:
        verbose_name = _('Избранное')
        verbose_name_plural = _('Избранное')
        default_related_name = 'favorites'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite_recipes'
            )
        ]

    def __str__(self):
        return f'Рецепт {self.recipe} в избранном у {self.user}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('Добавил в корзину')
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name=_('Список покупок')
    )

    manager = IngredientsQuerySet.as_manager()

    class Meta:
        verbose_name = _('Список покупок')
        verbose_name_plural = _('Списки покупок')
        default_related_name = 'shopping'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart'
            )
        ]

    def __str__(self):
        return f'Рецепт {self.recipe} в списке покупок у {self.user}'
