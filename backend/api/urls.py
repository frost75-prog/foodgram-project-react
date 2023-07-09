from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .recipes_views import IngredientViewSet, RecipeViewSet, TagViewSet
from .users_views import CustomUserViewSet

app_name = 'api'

router = DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'users', CustomUserViewSet, basename='users')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path(r'auth/', include('djoser.urls.jwt')),
]
