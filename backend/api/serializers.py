from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import make_password
from django.utils.translation import gettext_lazy as _
from drf_base64.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.authtoken.serializers import AuthTokenSerializer

from recipes.models import Ingredient, Recipe, RecipeIngredient, Subscribe, Tag

User = get_user_model()


class UserListSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
        )


class UserCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'password',
        )


class UserPasswordSerializer(serializers.Serializer):

    new_password = serializers.CharField(label=_('New password'))
    current_password = serializers.CharField(label=_('Current password'))

    def validate(self, data):
        user = self.context['request'].user
        current_password = data.get('current_password')

        if not authenticate(username=user.email, password=current_password):
            msg = _('Unable to log in with provided credentials.')
            raise serializers.ValidationError(msg, code='authorization')

        return data

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
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):

    name = serializers.CharField(source='ingredient.name', required=False)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', required=False
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class RecipeSerializer(serializers.ModelSerializer):

    image = Base64ImageField()
    tags = TagSerializer(many=True, required=True)
    author = UserListSerializer(many=False, read_only=True,
                                default=serializers.CurrentUserDefault())
    ingredients = RecipeIngredientSerializer(
        many=True, required=True, source='recipe'
    )

    class Meta:
        model = Recipe
        fields = '__all__'


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(required=False)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeCreatePutSerializer(serializers.ModelSerializer):

    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    image = Base64ImageField()
    tags = serializers.SlugRelatedField(
        queryset=Tag.objects.all(), slug_field='id', many=True
    )
    ingredients = RecipeIngredientCreateSerializer(
        many=True, required=True,
    )

    class Meta:
        model = Recipe
        fields = '__all__'

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                recipe=recipe, ingredient=ingredient['id'],
                amount=ingredient['amount']
            )
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.get('tags')
        ingredients = validated_data.get('ingredients')
        if tags:
            instance.tags.set(validated_data.pop('tags'))

        if ingredients:
            instance.ingredients.clear()
            for ingredient in validated_data.pop('ingredients'):
                RecipeIngredient.objects.create(
                    recipe=instance, ingredient=ingredient['id'],
                    amount=ingredient['amount']
                )

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
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscribe
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'recipes', 'recipes_count'
        )

    def get_recipes_count(self, obj):
        return obj.following.recipe.count()
