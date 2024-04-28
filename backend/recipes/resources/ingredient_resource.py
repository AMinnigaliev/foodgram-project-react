from import_export import resources

from recipes.models import Ingredient


class IngredientResource(resources.ModelResource):
    """
    Ресурс для импорта и экспорта данных по ингредиентам.

    Этот класс используется для определения формата данных при импорте
    и экспорте информации о ингредиентах в административной панели Django.
    """

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        import_id_fields = ['id']
