from django.urls import path

from .views import (AuthToken, IngredientDetail, IngredientList, RecipeDetail,
                    RecipeFavoriteDetail, RecipeList, SoppingCartDetail,
                    SubscribeDetail, SubscribeList, TagDetail, TagList,
                    UserDetail, UserList, about_me, download_shopping_cart,
                    logout, set_password)

urlpatterns = [

    path('users/', UserList.as_view(), name='user_list'),
    path('users/<int:pk>/', UserDetail.as_view(), name='user_detail'),
    path('users/set_password/', set_password, name='set_password'),
    path('users/me/', about_me, name='about_me'),
    path('users/subscriptions/', SubscribeList.as_view(),
         name='subscribe_list'),
    path('users/<int:user_id>/subscribe/', SubscribeDetail.as_view(),
         name='subscribe'),

    path('auth/token/login/', AuthToken.as_view(), name='login'),
    path('auth/token/logout/', logout, name='logout'),

    path('tags/', TagList.as_view(), name='tag_list'),
    path('tags/<int:pk>/', TagDetail.as_view(), name='tag_detail'),

    path('ingredients/', IngredientList.as_view(), name='ingredient_list'),
    path('ingredients/<int:pk>/', IngredientDetail.as_view(),
         name='ingredient_detail'),

    path('recipes/', RecipeList.as_view(), name='recipe_list'),
    path('recipes/<int:pk>/', RecipeDetail.as_view(), name='recipe_detail'),
    path('recipes/<int:recipe_id>/favorite/', RecipeFavoriteDetail.as_view(),
         name='favorite_recipe'),
    path('recipes/<int:recipe_id>/shopping_cart/', SoppingCartDetail.as_view(),
         name='shopping_cart_detail'),
    path('recipes/download_shopping_cart/', download_shopping_cart,
         name='download_shopping_cart'),
]
