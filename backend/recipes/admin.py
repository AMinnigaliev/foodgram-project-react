from django.contrib import admin
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin

from recipes.models import (Favorites, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from recipes.resources.ingredient_resource import IngredientResource
from recipes.widgets import ColorWidget


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админка для тегов."""
    list_display = ('color_display', 'name', 'slug')
    list_display_links = ('color_display',)
    list_editable = ('name', 'slug')
    search_fields = ('name', 'slug')
    ordering = ('name',)

    def color_display(self, obj):
        return ColorWidget().render(name='color', value=obj.color)

    color_display.short_description = 'Цвет тега'


@admin.register(Ingredient)
class IngredientAdmin(ImportExportModelAdmin):
    """Админка для ингредиентов."""
    list_display = ('name', 'measurement_unit')
    list_display_links = ('name',)
    list_editable = ('measurement_unit',)
    search_fields = ('name',)
    ordering = ('name', 'measurement_unit')
    resource_class = IngredientResource


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка для рецептов."""
    inlines = (RecipeIngredientInline,)
    list_display = ('id', 'name', 'author', 'count_favorites', 'image_display')
    list_filter = ('name', 'author', 'tags')
    list_display_links = ('name',)
    filter_horizontal = ('tags',)
    search_fields = ('name', 'author', 'tags')
    ordering = ('name', 'tags')

    def image_display(self, obj):
        """Отображение иконки картинки рецепта."""
        image_tag = ('<img src="{url}" style="max-width: 50px; max-height: '
                     '50px;">')
        return format_html(image_tag, url=obj.image.url)

    image_display.short_description = "Изображение"

    def count_favorites(self, obj):
        """Вычисление количества подписок на данного пользователя"""
        return obj.in_favorites.count()

    count_favorites.short_description = "В избранном"


@admin.register(Favorites, ShoppingCart)
class FavoritesShoppingListAdmin(admin.ModelAdmin):
    """Админки для избранного и списка покупок."""
    list_display = ('user', 'recipe')
    list_display_links = ('user',)
    list_editable = ('recipe',)
    search_fields = ('user__username', 'recipe__name')
    ordering = ('user', 'recipe')
