from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers, status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.models import Ingredient, Recipe, Tag
from api.filters import TagFilter

from .serializers import (IngredientSerializer, RecipeCreatePutSerializer,
                          RecipeSerializer, SubscribeRecipeSerializer,
                          SubscribeSerializer, TagSerializer, TokenSerializer,
                          UserCreateSerializer, UserListSerializer,
                          UserPasswordSerializer)

User = get_user_model()


class UserList(generics.ListCreateAPIView):

    queryset = User.objects.all()

    def perform_create(self, serializer):
        password = make_password(self.request.data['password'])
        serializer.save(password=password)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserListSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_password(request):
    serializer = UserPasswordSerializer(
        data=request.data, context={'request': request}
    )
    if serializer.is_valid():
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetail(generics.RetrieveUpdateDestroyAPIView):

    queryset = User.objects.all()
    serializer_class = UserListSerializer


class AuthToken(ObtainAuthToken):

    serializer_class = TokenSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response(
            {'auth_token': token.key}, status=status.HTTP_201_CREATED
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    token = get_object_or_404(Token, user=request.user)
    token.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


class TagList(generics.ListAPIView):

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class TagDetail(generics.RetrieveAPIView):

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class IngredientList(generics.ListAPIView):

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    search_fields = ('^name',)
    pagination_class = None


class IngredientDetail(generics.RetrieveAPIView):

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)


class RecipeList(generics.ListCreateAPIView):

    queryset = Recipe.objects.all()
    filterset_class = TagFilter

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RecipeCreatePutSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class RecipeDetail(generics.RetrieveUpdateDestroyAPIView):

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return RecipeCreatePutSerializer
        return RecipeSerializer


class SubscribeList(generics.ListAPIView):

    serializer_class = SubscribeSerializer

    def get_queryset(self):
        return self.request.user.follower.all()


class SubscribeDetail(generics.RetrieveDestroyAPIView):

    serializer_class = SubscribeSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.id == instance.id:
            raise serializers.ValidationError(
                {'errors': 'Нельзя подписаться на самого себя!'}
            )
        if request.user.follower.filter(following=instance).exists():
            raise serializers.ValidationError(
                {'errors': 'Такая подписка существует!'}
            )
        subs = request.user.follower.create(following=instance)
        serializer = self.get_serializer(subs)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        if self.request.user.follower.filter(following=instance).exists():
            return (
                self.request.user.follower.filter(following=instance).delete()
            )
        raise serializers.ValidationError({'errors': 'Подписка не найдена!'})

    def get_object(self):
        user_id = self.kwargs['user_id']
        user = get_object_or_404(User, id=user_id)
        return user


class RecipeFavoriteDetail(generics.RetrieveDestroyAPIView):

    serializer_class = SubscribeRecipeSerializer

    def get_object(self):
        recipe_id = self.kwargs['recipe_id']
        recipe = get_object_or_404(Recipe, id=recipe_id)
        return recipe

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.favorite_recipe.filter(user=request.user).exists():
            raise serializers.ValidationError(
                {'errors': 'Рецепт уже в избранном!'}
            )
        request.user.user_favorite.recipe.add(instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        if instance.favorite_recipe.filter(user=self.request.user).exists():
            return (
                self.request.user.user_favorite.recipe.remove(instance)
            )
        raise serializers.ValidationError(
            {'errors': 'В избранном данного рецепта нет!'}
        )
