from itertools import chain

from django.contrib import admin
from django.contrib.auth.models import Group

from users.models import FoodgramUser, Subscription

admin.site.unregister(Group)


class SubscriptionInline(admin.TabularInline):
    model = Subscription
    fk_name = 'user'
    extra = 1

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'author':
            try:
                parent_obj = self.model._meta.get_field(
                    'user'
                ).remote_field.model.objects.get(
                    id=request.resolver_match.kwargs['object_id']
                )
            except KeyError:
                parent_obj = None
            if parent_obj:
                kwargs['queryset'] = kwargs.get(
                    'queryset', db_field.related_model.objects
                ).exclude(id=parent_obj.id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(FoodgramUser)
class UserAdmin(admin.ModelAdmin):
    """Админка для пользователей Foodgram."""
    inlines = (SubscriptionInline,)
    exclude = ('groups', 'user_permissions')
    list_display = (
        'id', 'username', 'email', 'first_name', 'last_name',
        'subscriptions', 'subscribers'
    )
    list_display_links = ('username',)
    list_filter = ('email', 'username')
    search_fields = ('username',)
    ordering = ('username', 'first_name', 'last_name')

    def subscriptions(self, obj):
        return list(chain.from_iterable(obj.subscriptions.values_list(
            'author__username')))

    def subscribers(self, obj):
        return list(chain.from_iterable(obj.subscribers.values_list(
            'user__username')))

    subscriptions.short_description = 'Подписки'
    subscribers.short_description = 'Подписчики'
