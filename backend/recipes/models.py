from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html


class Tag(models.Model):

    name = models.CharField(_('tag name'), max_length=200, unique=True)
    color = models.CharField(_('tag hexcolor'), max_length=7, unique=True)
    slug = models.SlugField(_('tag slug'), max_length=200, unique=True)

    class Meta:
        verbose_name = 'Таг'
        verbose_name_plural = 'Таги'

    def colored_name(self):
        return format_html(
            '<span style="color: {}; width=20px; height=20px;">{}</span>',
            self.color, self.name
        )

    def __str__(self):
        return f'{self.name}, {self.slug}'


class Ingredient(models.Model):

    name = models.CharField(_('ingredient name'), max_length=200)
    measurement_unit = models.CharField(_('ingredient measurement unit'), max_length=200)

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'
