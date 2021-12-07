# Generated by Django 3.2.9 on 2021-12-06 19:48

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('recipes', '0009_auto_20211204_2143'),
    ]

    operations = [
        migrations.CreateModel(
            name='FavoriteRecipe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'verbose_name': 'Любимый рецепт',
                'verbose_name_plural': 'Любимые рецепты',
            },
        ),
        migrations.AlterField(
            model_name='subscribe',
            name='following',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='following', to=settings.AUTH_USER_MODEL, verbose_name='Following'),
        ),
        migrations.AddConstraint(
            model_name='subscribe',
            constraint=models.UniqueConstraint(fields=('follower', 'following'), name='unique subs'),
        ),
        migrations.AddField(
            model_name='favoriterecipe',
            name='recipe',
            field=models.ManyToManyField(related_name='favorite_recipe', to='recipes.Recipe', verbose_name='Favorite recipe'),
        ),
        migrations.AddField(
            model_name='favoriterecipe',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='user_favorite', to=settings.AUTH_USER_MODEL, verbose_name='User'),
        ),
    ]