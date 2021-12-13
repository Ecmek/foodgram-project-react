from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
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
    cooking_time = models.BigIntegerField(
        _('Recipe cokking time'),
    )
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

    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE,
                               related_name='recipe')
    ingredient = models.ForeignKey('Ingredient', on_delete=models.CASCADE,
                                   related_name='ingredient')
    amount = models.BigIntegerField(
        _('Amount of ingredient'),
    )

    class Meta:
        verbose_name = 'Количество ингредиента'
        verbose_name_plural = 'Количество ингредиентов'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique ingredient')
        ]


class RecipeTag(models.Model):

    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE)
    tag = models.ForeignKey('Tag', on_delete=models.CASCADE)


class Tag(models.Model):

    name = models.CharField(_('tag name'), max_length=200, unique=True)
    color = models.CharField(_('tag hexcolor'), max_length=7, unique=True)
    slug = models.SlugField(_('tag slug'), max_length=200, unique=True)

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return f'{self.name}, {self.slug}'


class Ingredient(models.Model):

    name = models.CharField(_('ingredient name'), max_length=200)
    measurement_unit = models.CharField(_('ingredient measurement unit'),
                                        max_length=200)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Subscribe(models.Model):

    follower = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='follower',
        verbose_name=_('Follower'),
    )
    following = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='following',
        verbose_name=_('Following'),
    )
    created = models.DateTimeField(
        _('Sub date'), auto_now_add=True,
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['follower', 'following'],
                name='unique subs')
        ]

    def __str__(self):
        return f'follower: {self.follower} - following: {self.following}'


class FavoriteRecipe(models.Model):

    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name='favorite_recipe',
        verbose_name=_('User'),
    )
    recipe = models.ManyToManyField(
        Recipe,
        related_name='favorite_recipe',
        verbose_name=_('Favorite recipe')
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'

    def __str__(self) -> str:
        return (
            f'{self.user}, '
            f'{[i.name for i in self.recipe.all()]}'
        )

    @receiver(post_save, sender=User)
    def create_empty_favorite_recipe(sender, instance, created, **kwargs):
        if created:
            FavoriteRecipe.objects.create(user=instance)


class ShoppingCart(models.Model):

    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name=_('User'),
    )
    recipe = models.ManyToManyField(
        Recipe,
        related_name='shopping_cart',
        verbose_name=_('Recipe in shopping cart')
    )

    class Meta:
        verbose_name = 'Корзина с рецептом'
        verbose_name_plural = 'Корзина с рецептами'

    def __str__(self) -> str:
        return (
            f'{self.user}, '
            f'{[i.name for i in self.recipe.all()]}'
        )

    @receiver(post_save, sender=User)
    def create_empty_shopping_cart(sender, instance, created, **kwargs):
        if created:
            ShoppingCart.objects.create(user=instance)
