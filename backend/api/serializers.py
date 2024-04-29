from django.contrib.auth import get_user_model
from django.db.models import F
from django.db.transaction import atomic
from django.db.utils import IntegrityError
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import status
from rest_framework.serializers import (ModelSerializer, SerializerMethodField,
                                        ValidationError)
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import Subscription

User = get_user_model()


class FoodgramUserSerializer(UserSerializer):
    """Сериализатор для вывода пользователей Foodgram."""
    is_subscribed = SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_subscribed',
        )
        read_only_fields = ('id', 'is_subscribed')

    def get_is_subscribed(self, obj):
        """Проверка подписки на пользователя."""

        user = self.context.get('request').user

        if user.is_anonymous or (user == obj):
            return False
        return user.subscriptions.filter(author=obj).exists()


class FoodgramUserCreateSerializer(UserCreateSerializer):
    """Сериализатор для создания пользователей Foodgram."""

    class Meta(FoodgramUserSerializer.Meta):
        fields = (
            'id', 'username', 'password', 'email', 'first_name', 'last_name'
        )
        read_only_fields = ('id',)


class SubscriptionSerializer(FoodgramUserSerializer):
    """
    Сериализатор для вывода пользователей на которых подписан текущий
    пользователь.
    """
    recipes = SerializerMethodField()
    recipes_count = SerializerMethodField()

    class Meta(FoodgramUserSerializer.Meta):
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count',
        )
        read_only_fields = ('__all__',)

    def get_recipes(self, obj):
        """Выдача рецепта в кратком виде."""
        recipes = obj.recipes.all()
        request = self.context.get('request')

        if request.query_params.get('recipes_limit'):
            recipes_limit = int(request.query_params.get('recipes_limit'))
            recipes = recipes[:recipes_limit]

        serializer = ShortRecipeSerializer(recipes, read_only=True, many=True)
        return serializer.data

    def get_recipes_count(self, obj):
        """Выдача общего количества рецептов у конкретного автора."""
        return obj.recipes.count()


class SubscriptionCreateSerializer(ModelSerializer):
    """Сериализатор для создания подписки на пользователя."""

    class Meta:
        model = Subscription
        fields = ('user', 'author')
        validators = [
            UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=('user', 'author'),
                message='Вы уже подписаны на этого пользователя!'
            )
        ]

    def validate(self, data):
        """Проверка запрета подписываться на самого себя."""
        user = data.get('user')
        author = data.get('author')
        if user == author:
            raise ValidationError(
                detail='Нельзя подписаться на самого себя!',
                code=status.HTTP_400_BAD_REQUEST
            )
        return data


class TagSerializer(ModelSerializer):
    """Сериализатор для вывода тэгов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')
        read_only_fields = ('__all__',)


class IngredientSerializer(ModelSerializer):
    """Сериализатор для вывода ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = ('__all__',)


class ShortRecipeSerializer(ModelSerializer):
    """Сериализатор для вывода рецептов во вложенном поле recipes."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('__all__',)


class RecipeSerializer(ModelSerializer):
    """Сериализатор для рецептов."""
    tags = TagSerializer(many=True, read_only=True)
    author = FoodgramUserSerializer(read_only=True)
    ingredients = SerializerMethodField()
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    image = Base64ImageField()

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
        read_only_fields = (
            'is_favorite',
            'is_shopping_cart',
        )

    def get_ingredients(self, recipe):
        """Список ингредиентов для рецепта."""
        ingredients = recipe.ingredients.values(
            'id', 'name', 'measurement_unit', amount=F(
                'recipeingredient__amount'
            )
        )
        return ingredients

    def get_is_favorited(self, recipe):
        """Проверка, находится ли рецепт в избранном у пользователя"""
        user = self.context.get('view').request.user

        if user.is_anonymous:
            return False

        return user.favorites.filter(recipe=recipe).exists()

    def get_is_in_shopping_cart(self, recipe):
        """Проверка, находится ли рецепт в списке покупок у пользователя"""
        user = self.context.get('view').request.user

        if user.is_anonymous:
            return False

        return user.shopping_cart.filter(recipe=recipe).exists()

    def to_representation(self, instance):
        """
        Изменяет выдаваемые данные в соответствии со спецификацией API,
        при отсутствии данных в полях автора или картинки рецепта.
        """
        data = super().to_representation(instance)

        if data['author'] is None:
            data['author'] = {
                'id': 0,
                'username': 'AnonymousUser',
                'email': '',
                'first_name': '',
                'last_name': '',
            }

        if data['image'] is None:
            data['image'] = 'Картинка отсутствует.'

        return data

    def validate_image(self, value):
        """Проверка наличия картинки в запросе на добавление рецепта."""

        if not value:
            raise ValidationError('Отсутствует картинка.')
        return value

    def validate(self, data):
        tags_id = self.initial_data.get('tags')

        if not tags_id:
            raise ValidationError('Не указаны теги.')

        set_tags_id = set(tags_id)

        if len(set_tags_id) != len(tags_id):
            raise ValidationError('Указан одинаковые теги.')

        valid_tags = Tag.objects.filter(id__in=tags_id)

        if len(valid_tags) != len(tags_id):
            raise ValidationError('Указан несуществующий тег.')

        ingredients = self.initial_data.get('ingredients')

        if not ingredients:
            raise ValidationError('Не указаны ингредиенты.')

        valid_ingredients = {}

        for ingredient in ingredients:
            try:
                ingredient['amount'] = int(ingredient['amount'])
            except ValueError:
                raise ValidationError(
                    'Количество ингредиента указано в неверном формате.'
                )
            if ingredient['amount'] < 1:
                raise ValidationError(
                    'Количество ингредиентов не должно быть меньше 1.'
                )
            if not isinstance(ingredient['id'], int):
                raise ValidationError(
                    'Id ингредиента указан в неверном формате.'
                )
            if ingredient['id'] < 1:
                raise ValidationError(
                    'Id ингредиента не должно быть меньше 1.'
                )
            if valid_ingredients.get(ingredient['id']):
                raise ValidationError(
                    'Повторение ингредиентов запрещено.'
                )
            valid_ingredients[ingredient['id']] = ingredient['amount']

        db_ingredients = Ingredient.objects.filter(
            pk__in=valid_ingredients.keys()
        )
        if len(db_ingredients) != len(valid_ingredients):
            raise ValidationError('Не все указанные ингредиенты существуют.')

        for ingredient in db_ingredients:
            valid_ingredients[ingredient.pk] = (
                ingredient, valid_ingredients[ingredient.pk]
            )

        data.update(
            {
                'tags': valid_tags,
                'ingredients': valid_ingredients,
                'author': self.context.get('request').user,
            }
        )
        return data

    @atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        try:
            recipe = Recipe.objects.create(
                **validated_data,
            )
        except IntegrityError:
            raise ValidationError(
                'Этот рецепт вами уже добавлен.'
            )
        recipe.tags.set(tags)
        self.recipe_ingredient_create(recipe, ingredients)
        return recipe

    @atomic
    def update(self, recipe, validated_data):
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")

        for key, value in validated_data.items():
            if hasattr(recipe, key):
                setattr(recipe, key, value)

        if tags:
            recipe.tags.clear()
            recipe.tags.set(tags)

        if ingredients:
            recipe.ingredients.clear()
            self.recipe_ingredient_create(recipe, ingredients)

        recipe.save()
        return recipe

    @staticmethod
    def recipe_ingredient_create(recipe, ingredients):
        objs = []

        for ingredient, amount in ingredients.values():
            objs.append(
                RecipeIngredient(
                    recipe=recipe, ingredient=ingredient, amount=amount
                )
            )

        RecipeIngredient.objects.bulk_create(objs)
