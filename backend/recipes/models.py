from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from foodgram.constants import (INGREDIENT_NAME_LENGTH, INGREDIENT_UNIT_LENGTH,
                                RECIPE_NAME_LENGTH, TAG_COLOR_LENGTH,
                                TAG_NAME_LENGTH)

User = get_user_model()


class Tag(models.Model):
    """Теги для рецептов."""
    name = models.CharField(
        'Название тега', max_length=TAG_NAME_LENGTH, unique=True,
    )
    color = models.CharField(
        'Цвет тега',
        max_length=TAG_COLOR_LENGTH,
        validators=[
            RegexValidator(
                r'^#[A-Fa-f0-9]{6}$',
                message='Введите # затем 6 символов(цифры и латинские буквы)',
            ),
        ],
        unique=True,
    )
    slug = models.SlugField('Slug', unique=True)

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Название и единица измерения ингредиентов использующихся в рецептах."""
    name = models.CharField(
        'Название ингредиента', max_length=INGREDIENT_NAME_LENGTH
    )
    measurement_unit = models.CharField(
        'Единицы измерения', max_length=INGREDIENT_UNIT_LENGTH
    )

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name', 'measurement_unit')

    def __str__(self):
        return f'{self.name} - {self.measurement_unit}'


class Recipe(models.Model):
    """Рецепты."""
    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Автор',
    )
    name = models.CharField(
        'Название', max_length=RECIPE_NAME_LENGTH
    )
    image = models.ImageField(
        'Картинка', upload_to='images/'
    )
    text = models.TextField(
        'Описание'
    )
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredient', verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag, verbose_name='Тег'
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (мин.)', validators=[MinValueValidator(1)]
    )
    pub_date = models.DateTimeField(
        'Дата публикации', auto_now_add=True, editable=False
    )

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date', 'name', 'author')
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'author'),
                name='unique_name_author',
            ),
        )

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """
    Модель связывает Recipe и Ingredient, а также содержит количество
    данного ингредиента в данном рецепте.
    """
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество', validators=[MinValueValidator(1)]
    )

    class Meta:
        verbose_name = 'ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        ordering = ('recipe', 'ingredient', 'ingredient__measurement_unit')
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_recipe_ingredient',
            ),
        )

    def __str__(self):
        return (f'{self.ingredient}, {self.amount} '
                f'{self.ingredient.measurement_unit}')


class Favorites(models.Model):
    """Избранные рецепты пользователя."""
    user = models.ForeignKey(
        User,
        related_name='favorites',
        on_delete=models.CASCADE,
        verbose_name='Избранное',
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='in_favorites',
        on_delete=models.CASCADE,
        verbose_name='В избранном',
    )

    class Meta:
        verbose_name = 'избранный'
        verbose_name_plural = 'Избранные'
        ordering = ('user', 'recipe')
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_user_recipe_in_favorites',
            ),
        )

    def __str__(self) -> str:
        return f'{self.recipe} в избранном у {self.user}'


class ShoppingCart(models.Model):
    """Рецепты добавленные в список покупок пользователя."""
    user = models.ForeignKey(
        User,
        related_name='shopping_cart',
        on_delete=models.CASCADE,
        verbose_name='Список покупок',
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='in_shopping_cart',
        on_delete=models.CASCADE,
        verbose_name='В списку покупок',
    )

    class Meta:
        verbose_name = 'список покупок'
        verbose_name_plural = 'Списки покупок'
        ordering = ('user', 'recipe')
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_user_recipe_in_shop_list',
            ),
        )
