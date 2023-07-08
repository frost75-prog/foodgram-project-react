from django.contrib import admin

from . import models


class RecipeIngredientsInLine(admin.TabularInline):
    model = models.Recipe.ingredients.through
    extra = 1


@admin.register(models.Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit')
    list_filter = ('name', )
    search_fields = ('name', )


@admin.register(models.Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'color', 'slug')
    list_editable = ('name', 'color', 'slug')
    empty_value_display = '-пусто-'


@admin.register(models.Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'author',
        'name',
        'text',
        'cooking_time',
        'get_tags',
        'get_favorite_count'
    )
    inlines = (RecipeIngredientsInLine,)
    list_filter = ('author__email', 'tags', 'name')
    search_fields = ('author__email', 'name',)
    empty_value_display = '-пусто-'

    @admin.display(description='Тэги')
    def get_tags(self, obj):
        list_ = [tag.name for tag in obj.tags.all()]
        return ', '.join(list_)

    @admin.display(description='В избранном')
    def get_favorite_count(self, obj):
        return obj.favorites.count()


@admin.register(models.RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'recipe', 'ingredient', 'amount')
    list_editable = ('recipe', 'ingredient', 'amount')


@admin.register(models.Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    list_editable = ('user', 'recipe')


@admin.register(models.ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    list_editable = ('user', 'recipe')
