import django.contrib.auth.password_validation as validators
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import make_password
from django.utils.translation import gettext_lazy as _
from drf_base64.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.validators import UniqueTogetherValidator
from django.shortcuts import get_object_or_404

from recipes.models import Ingredient, Recipe, RecipeIngredient, Subscribe, Tag

User = get_user_model()


class UserListSerializer(serializers.ModelSerializer):

    is_subscribed = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_subscribed'
        )


class UserCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'password',
        )

    def validate_password(self, password):
        validators.validate_password(password)
        return password


class UserPasswordSerializer(serializers.Serializer):

    new_password = serializers.CharField(label=_('New password'))
    current_password = serializers.CharField(label=_('Current password'))

    def validate_current_password(self, current_password):
        user = self.context['request'].user

        if not authenticate(username=user.email, password=current_password):
            msg = _('Unable to log in with provided credentials.')
            raise serializers.ValidationError(msg, code='authorization')

        return current_password

    def validate_new_password(self, new_password):
        validators.validate_password(new_password)
        return new_password

    def create(self, validated_data):
        user = self.context['request'].user
        password = make_password(validated_data.get('new_password'))
        user.password = password
        user.save()
        return validated_data


class TokenSerializer(AuthTokenSerializer):
    email = serializers.CharField(
        label=_('Email'),
        write_only=True
    )
    password = serializers.CharField(
        label=_('Password'),
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True
    )
    token = serializers.CharField(
        label=_('Token'),
        read_only=True
    )

    def validate(self, attrs):
        username = attrs.get('email')
        password = attrs.get('password')

        if username and password:
            user = authenticate(request=self.context.get('request'),
                                username=username, password=password)
            if not user:
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = _('Must include "email" and "password".')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug',)


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def validate_amount(self, amount):
        if amount <= 0:
            raise serializers.ValidationError(
                'Убедитесь, что значение количества ингредиента больше 0'
            )
        return amount


class RecipeUserSerializer(serializers.ModelSerializer):

    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return user.follower.filter(following=obj).exists()


class RecipeSerializer(serializers.ModelSerializer):

    image = Base64ImageField()
    tags = TagSerializer(many=True, read_only=True,)
    author = RecipeUserSerializer(
        read_only=True, default=serializers.CurrentUserDefault()
    )
    ingredients = RecipeIngredientSerializer(
        many=True, required=True, source='recipe'
    )
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)

    class Meta:
        model = Recipe
        fields = '__all__'

    def validate(self, data):
        ingredients = self.initial_data.get('ingredients')
        ingredient_list = []
        for ingredient_item in ingredients:
            ingredient = get_object_or_404(
                Ingredient, id=ingredient_item['id']
            )
            if ingredient in ingredient_list:
                raise serializers.ValidationError(
                    'Ингридиент должны быть уникальным'
                )
            ingredient_list.append(ingredient)

        tags = self.initial_data.get('tags')
        for tag_id in tags:
            get_object_or_404(Tag, id=tag_id)

        return data

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                'Нужен хоть один ингридиент для рецепта'
            )
        return ingredients

    def create_ingredients(self, ingredients, recipe):
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient_id=ingredient.get("id"),
                amount=ingredient.get("amount"),
            )

    def create(self, validated_data):
        validated_data.pop('recipe')
        tags = self.initial_data.pop('tags')
        ingredients = self.initial_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        validated_data.pop('recipe')
        tags = self.initial_data.pop('tags')
        ingredients = self.initial_data.pop('ingredients')
        if tags:
            instance.tags.set(tags)

        if ingredients:
            instance.ingredients.clear()
            self.create_ingredients(ingredients, instance)

        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance


class SubscribeRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)


class SubscribeSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(source='following.id')
    email = serializers.EmailField(source='following.email')
    username = serializers.CharField(source='following.username')
    first_name = serializers.CharField(source='following.first_name')
    last_name = serializers.CharField(source='following.last_name')
    recipes = SubscribeRecipeSerializer(source='following.recipe', many=True)
    is_subscribed = serializers.BooleanField(read_only=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscribe
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count',
        )

    def get_recipes_count(self, obj):
        return obj.following.recipe.count()
