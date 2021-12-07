from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db.models.aggregates import Count, Sum
from django.db.models.expressions import OuterRef, Value
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from reportlab.pdfgen import canvas
from rest_framework import generics, serializers, status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from api.filters import RecipeFilter
from api.permissions import IsAuthorOrAdminOrReadOnly
from recipes.models import (FavoriteRecipe, Ingredient, Recipe, ShoppingCart,
                            Tag)

from .serializers import (IngredientSerializer, RecipeSerializer,
                          SubscribeRecipeSerializer, SubscribeSerializer,
                          TagSerializer, TokenSerializer, UserCreateSerializer,
                          UserListSerializer, UserPasswordSerializer)

User = get_user_model()


class UserList(generics.ListCreateAPIView):

    permission_classes = (AllowAny,)

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return User.objects.annotate(is_subscribed=Value(False))
        return User.objects.annotate(
            is_subscribed=Count(self.request.user.follower.filter(
                following=OuterRef('id')
            ).only('id'))
        )

    def perform_create(self, serializer):
        password = make_password(self.request.data['password'])
        serializer.save(password=password)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserListSerializer


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


class UserDetail(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = UserListSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return User.objects.annotate(is_subscribed=Value(False))
        return User.objects.annotate(
            is_subscribed=Count(self.request.user.follower.filter(
                following=OuterRef('id')
            ).only('id'))
        )


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
    permission_classes = (AllowAny,)
    search_fields = ('^name',)
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
            )

        return Recipe.objects.annotate(
            is_favorited=Count(FavoriteRecipe.objects.filter(
                user=self.request.user, recipe=OuterRef('id')).only('id')
            ),
            is_in_shopping_cart=Count(ShoppingCart.objects.filter(
                user=self.request.user, recipe=OuterRef('id')).only('id')
            )
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class RecipeDetail(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrAdminOrReadOnly,)

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Recipe.objects.annotate(
                is_favorited=Value(False),
                is_in_shopping_cart=Value(False),
            )
        return Recipe.objects.annotate(
            is_favorited=Count(FavoriteRecipe.objects.filter(
                user=self.request.user, recipe=OuterRef('id')).only('id')
            ),
            is_in_shopping_cart=Count(ShoppingCart.objects.filter(
                user=self.request.user, recipe=OuterRef('id')).only('id')
            )
        )


class SubscribeList(generics.ListAPIView):

    serializer_class = SubscribeSerializer

    def get_queryset(self):
        return self.request.user.follower.annotate(is_subscribed=Value(True))


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


class FavoriteRecipeDetail(generics.RetrieveDestroyAPIView):

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


class SoppingCartDetail(generics.RetrieveDestroyAPIView):

    serializer_class = SubscribeRecipeSerializer

    def get_object(self):
        recipe_id = self.kwargs['recipe_id']
        recipe = get_object_or_404(Recipe, id=recipe_id)
        return recipe

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.favorite_recipe.filter(user=request.user).exists():
            raise serializers.ValidationError(
                {'errors': 'Рецепт уже в корзине!'}
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
            {'errors': 'В корзине данного рецепта нет!'}
        )


@api_view(['GET'])
def download_shopping_cart(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="shoppingcart.pdf"'
    p = canvas.Canvas(response)
    x = 50
    y = 800
    indent = 15
    shopping_cart = (
        request.user.shopping_cart.recipe.
        values('ingredients__name', 'ingredients__measurement_unit').
        annotate(amount=Sum('recipe__amount')).order_by('amount')
    )
    if not shopping_cart:
        p.drawString(x, y, 'Ваш список покупок пуст')
        p.save()
        return response
    p.drawString(x, y, 'Ваш список покупок:')
    for index, recipe in enumerate(shopping_cart, start=1):
        p.drawString(
            x, y - indent, f'{index}. {recipe["ingredients__name"]} -'
            f'{recipe["amount"]}{recipe["ingredients__measurement_unit"]}.'
        )
        indent += 15
    p.save()
    return response
