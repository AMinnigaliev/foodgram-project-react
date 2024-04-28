from django.forms.widgets import Widget
from django.utils.safestring import mark_safe


class ColorWidget(Widget):
    """
    Виджет для отображения цвета в административной панели Django.

    Отображает квадратный блок цвета, в который встраивается выбранный цвет.
    Если цвет не выбран, отображается пустой блок.
    """
    def render(self, name, value, attrs=None, renderer=None):
        style = f'background-color: {value};' if value else ''
        html = (f'<div style="width: 20px; height: 20px;'
                f' border: 1px solid #ccc; {style}"></div>')
        return mark_safe(html)
