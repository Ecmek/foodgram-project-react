from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db.models.aggregates import Count
from django.db.models.expressions import Exists, OuterRef, Value
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsAuthorOrAdminOrReadOnly
from recipes.models import (FavoriteRecipe, Ingredient, Recipe, ShoppingCart,
                            Tag)
from .serializers import (IngredientSerializer, RecipeSerializer,
                          SubscribeRecipeSerializer, SubscribeSerializer,
                          TagSerializer, TokenSerializer, UserCreateSerializer,
                          UserListSerializer, UserPasswordSerializer)

User = get_user_model()


class UserList(generics.ListCreateAPIView):

    queryset = User.objects.prefetch_related('follower', 'following')
    permission_classes = (AllowAny,)

    def perform_create(self, serializer):
        password = make_password(self.request.data['password'])
        serializer.save(password=password)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserListSerializer


class UserDetail(generics.RetrieveAPIView):

    queryset = User.objects.prefetch_related('follower', 'following')
    serializer_class = UserListSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return User.objects.annotate(is_subscribed=Value(False))
        return User.objects.annotate(
            is_subscribed=Exists(self.request.user.follower.filter(
                following=OuterRef('id')
            ))
        ).prefetch_related('follower', 'following')


@api_view(['GET'])
def about_me(request):
    serializer = UserListSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
def set_password(request):
    serializer = UserPasswordSerializer(
        data=request.data, context={'request': request}
    )
    if serializer.is_valid():
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
    filterset_class = IngredientFilter
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientDetail(generics.RetrieveAPIView):

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)


class RecipeList(generics.ListCreateAPIView):

    serializer_class = RecipeSerializer
    filterset_class = RecipeFilter
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Recipe.objects.annotate(
                is_in_shopping_cart=Value(False),
                is_favorited=Value(False),
            ).select_related(
                'author'
            ).prefetch_related(
                'tags', 'ingredients', 'recipe',
                'shopping_cart', 'favorite_recipe'
            )

        return Recipe.objects.annotate(
            is_favorited=Exists(FavoriteRecipe.objects.filter(
                user=self.request.user, recipe=OuterRef('id'))
            ),
            is_in_shopping_cart=Exists(ShoppingCart.objects.filter(
                user=self.request.user, recipe=OuterRef('id'))
            )
        ).select_related(
            'author'
        ).prefetch_related(
            'tags', 'ingredients', 'recipe',
            'shopping_cart', 'favorite_recipe'
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class RecipeDetail(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrAdminOrReadOnly,)

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Recipe.objects.annotate(
                is_in_shopping_cart=Value(False),
                is_favorited=Value(False),
            ).select_related(
                'author'
            ).prefetch_related(
                'tags', 'ingredients', 'recipe',
                'shopping_cart', 'favorite_recipe'
            )
        return Recipe.objects.annotate(
            is_favorited=Exists(FavoriteRecipe.objects.filter(
                user=self.request.user, recipe=OuterRef('id'))
            ),
            is_in_shopping_cart=Exists(ShoppingCart.objects.filter(
                user=self.request.user, recipe=OuterRef('id'))
            )
        ).select_related(
            'author'
        ).prefetch_related(
            'tags', 'ingredients', 'recipe',
            'shopping_cart', 'favorite_recipe'
        )


class SubscribeList(generics.ListAPIView):

    serializer_class = SubscribeSerializer

    def get_queryset(self):
        return self.request.user.follower.select_related(
            'following').prefetch_related(
                'following__recipe'
        ).annotate(
            recipes_count=Count('following__recipe'),
            is_subscribed=Value(True),
        )


class SubscribeDetail(generics.RetrieveDestroyAPIView):

    serializer_class = SubscribeSerializer

    def get_queryset(self):
        return self.request.user.follower.select_related(
            'following').prefetch_related(
                'following__recipe'
        ).annotate(
            recipes_count=Count('following__recipe'),
            is_subscribed=Value(True),
        )

    def get_object(self):
        user_id = self.kwargs['user_id']
        user = get_object_or_404(User, id=user_id)
        self.check_object_permissions(self.request, user)
        return user

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.id == instance.id:
            return Response(
                {'errors': 'Нельзя подписаться на самого себя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if request.user.follower.filter(following=instance).exists():
            return Response(
                {'errors': 'Такая подписка существует'},
                status=status.HTTP_400_BAD_REQUEST
            )
        subs = request.user.follower.create(following=instance)
        serializer = self.get_serializer(subs)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        self.request.user.follower.filter(following=instance).delete()


class FavoriteRecipeDetail(generics.RetrieveDestroyAPIView):

    serializer_class = SubscribeRecipeSerializer

    def get_object(self):
        recipe_id = self.kwargs['recipe_id']
        recipe = get_object_or_404(Recipe, id=recipe_id)
        self.check_object_permissions(self.request, recipe)
        return recipe

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        request.user.favorite_recipe.recipe.add(instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        self.request.user.favorite_recipe.recipe.remove(instance)


class ShoppingCartDetail(generics.RetrieveDestroyAPIView):

    serializer_class = SubscribeRecipeSerializer

    def get_object(self):
        recipe_id = self.kwargs['recipe_id']
        recipe = get_object_or_404(Recipe, id=recipe_id)
        self.check_object_permissions(self.request, recipe)
        return recipe

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        request.user.shopping_cart.recipe.add(instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        self.request.user.shopping_cart.recipe.remove(instance)
