from django.contrib.auth import get_user_model
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.paginators import PageLimitNumberPagination
from api.permissions import IsAuthorOrAdminOrReadOnly
from api.serializers import (IngredientSerializer, RecipeSerializer,
                             ShortRecipeSerializer,
                             SubscriptionCreateSerializer,
                             SubscriptionSerializer, TagSerializer)
from recipes.models import (Favorites, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Subscription

User = get_user_model()


class TagViewSet(ReadOnlyModelViewSet):
    """Представление для тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    """Представление для ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None

    def get_queryset(self):
        """Поиск по частичному вхождению в начале названия ингредиента."""
        queryset = super().get_queryset()
        search_term = self.request.query_params.get('name')

        if search_term:
            queryset = queryset.filter(
                Q(name__istartswith=search_term)
            )

        return queryset


class RecipeViewSet(ModelViewSet):
    """Представление для рецептов."""
    queryset = (
        Recipe.objects.all().prefetch_related('tags').select_related('author')
    )
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    pagination_class = PageLimitNumberPagination

    def get_queryset(self):
        """Фильтрация по избранному, автору, списку покупок и тегам."""
        queryset = super().get_queryset()

        author = self.request.query_params.get('author')
        if author:
            queryset = queryset.filter(author=author)

        tags = self.request.query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()

        if self.request.user.is_anonymous:
            return queryset

        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart'
        )
        if is_in_shopping_cart == '1':
            queryset = queryset.filter(
                in_shopping_cart__user=self.request.user
            )
        elif is_in_shopping_cart == '0':
            queryset = queryset.exclude(
                in_shopping_cart__user=self.request.user
            )

        is_favorite = self.request.query_params.get('is_favorited')
        if is_favorite == '1':
            queryset = queryset.filter(in_favorites__user=self.request.user)
        elif is_favorite == '0':
            queryset = queryset.exclude(in_favorites__user=self.request.user)

        return queryset

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, **kwargs):
        """Добавление, удаление рецепта для раздела избранного"""

        if request.method == 'POST':
            return self._create_object(
                'избранное', Favorites, kwargs.get('pk'), request.user
            )
        return self._delete_object(
            'избранном', Favorites, kwargs.get('pk'), request.user
        )

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, **kwargs):
        """Добавление, удаление рецепта для раздела списка покупок"""

        if request.method == 'POST':
            return self._create_object(
                'список покупок', ShoppingCart, kwargs.get('pk'), request.user
            )
        return self._delete_object(
            'списке покупок', ShoppingCart, kwargs.get('pk'), request.user
        )

    @action(detail=False, methods=['get'],
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        """Скачивание файл со списком покупок."""

        if not request.user.shopping_cart.exists():
            return Response(
                {'errors': 'Список покупок пуст.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        list_of_ingredients = (
            RecipeIngredient.objects
            .filter(recipe__in_shopping_cart__user=request.user)
            .values('ingredient')
            .annotate(total_amount=Sum('amount'))
            .values_list(
                'ingredient__name',
                'total_amount',
                'ingredient__measurement_unit',
            )
        )

        shopping_list = []
        for count, ingredient in enumerate(list_of_ingredients, 1):
            name, amount, unit = ingredient
            shopping_list.append(
                f'{count}. {name} - {amount}{unit}.'
            )

        response = HttpResponse(
            'Список покупок:\n'
            + '\n'.join(shopping_list)
            + '\n\nПриятного аппетита!',
            content_type='text.txt; charset=utf-8',
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping-list.txt"'
        )
        return response

    @staticmethod
    def _create_object(list_name, model, recipe_id, user):
        """
        Проверка наличия рецепта и добавление данного рецепта в
        соответствующую модель.
        """

        try:
            recipe = Recipe.objects.get(pk=recipe_id)
        except Recipe.DoesNotExist:
            raise ValidationError(
                'Данного рецепта не существует.'
            )
        subscride = model.objects.filter(recipe=recipe, user=user)
        if subscride.exists():
            raise ValidationError(
                f'Рецепт уже добавлен в {list_name}.',
            )

        model(recipe=recipe, user=user).save()

        serializer = ShortRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @staticmethod
    def _delete_object(list_name, model, recipe_id, user):
        """
        Проверка наличия рецепта и удаление данного рецепта из
        соответствующую модель.
        """
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        delete_obj = model.objects.filter(
            user=user, recipe__id=recipe.id).delete()

        if delete_obj[0]:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': f'Этого рецепта нет в {list_name}.'},
            status=status.HTTP_400_BAD_REQUEST,
        )


class FoodgramUserViewSet(UserViewSet):
    """Представление для пользователей Foodgram."""

    pagination_class = PageLimitNumberPagination

    def get_permissions(self):
        if self.action == 'me':
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(
        detail=True,
        permission_classes=(IsAuthenticated,),
        methods=('POST', 'DELETE'),
    )
    def subscribe(self, request, **kwargs):
        """Добавление, удаление подписки пользователя."""
        user = self.request.user
        author = get_object_or_404(User, pk=kwargs.get('id'))
        if request.method == 'POST':
            serializer = SubscriptionCreateSerializer(
                data={
                    'user': user.id,
                    'author': author.id,
                },
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            user_serializer = SubscriptionSerializer(
                author,
                context={'request': request},
            )
            return Response(
                user_serializer.data,
                status=status.HTTP_201_CREATED,
            )

        unsubscribe = Subscription.objects.filter(
            user=user, author=author).delete()
        if unsubscribe[0]:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Данного пользователя нет в подписках.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=False,
        permission_classes=[IsAuthenticated],
        methods=['GET']
    )
    def subscriptions(self, request):
        """Выдача подписок пользователя."""
        queryset = User.objects.filter(subscribers__user=request.user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)
