from django.contrib.auth import get_user_model
from django.db import models
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Recipe(models.Model):

    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='recipe', verbose_name=_('Recipe author')
    )
    name = models.CharField(_('Recipe name'), max_length=255)
    image = models.ImageField(_('Recipe image'), upload_to='recipe/')
    text = models.TextField(_('Recipe text'))
    cooking_time = models.PositiveSmallIntegerField(_('Recipe cokking time'))
    ingredients = models.ManyToManyField('Ingredient',
                                         through='RecipeIngredient')
    tags = models.ManyToManyField('Tag', through='RecipeTag')
    pub_date = models.DateTimeField(_('Pub date'), auto_now_add=True,)

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self) -> str:
        return f'{self.author.email}, {self.name}'


class RecipeIngredient(models.Model):

    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE)
    ingredient = models.ForeignKey('Ingredient', on_delete=models.CASCADE)
    amount = models.PositiveSmallIntegerField(_('Amount of ingredient'))


class RecipeTag(models.Model):

    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE)
    tag = models.ForeignKey('Tag', on_delete=models.CASCADE)


class Tag(models.Model):

    name = models.CharField(_('tag name'), max_length=200, unique=True)
    color = models.CharField(_('tag hexcolor'), max_length=7, unique=True)
    slug = models.SlugField(_('tag slug'), max_length=200, unique=True)

    class Meta:
        verbose_name = 'Таг'
        verbose_name_plural = 'Таги'

    def colored_name(self):
        return format_html(
            f'<span style="color: {self.color}; width=20px;'
            f'height=20px;">{self.name}</span>'
        )

    def __str__(self):
        return f'{self.name}, {self.slug}'


class Ingredient(models.Model):

    name = models.CharField(_('ingredient name'), max_length=200)
    measurement_unit = models.CharField(_('ingredient measurement unit'),
                                        max_length=200)

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'
