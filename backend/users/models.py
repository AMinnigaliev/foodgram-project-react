from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from foodgram.constants import (FIRST_NAME_LENGTH, LAST_NAME_LENGTH,
                                PASSWORD_LENGTH)


class FoodgramUser(AbstractUser):
    """Пользователи Фудграм."""
    password = models.CharField(_('password'), max_length=PASSWORD_LENGTH)
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(
        _('first name'), max_length=FIRST_NAME_LENGTH
    )
    last_name = models.CharField(
        _('last name'), max_length=LAST_NAME_LENGTH
    )

    class Meta:
        verbose_name = 'пользователя'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username

    @property
    def is_admin(self):
        return self.is_superuser or self.is_staff


class Subscription(models.Model):
    """Подписки пользователей."""
    user = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчики',
    )
    author = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Подписки',
    )

    class Meta:
        verbose_name = 'пункт подписки'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='no_self_subscribe',
            ),
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_user_subscriber',
            ),
        ]

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
