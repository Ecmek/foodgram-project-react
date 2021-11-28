from django.urls import path

from .views import (
    AuthToken, IngredientDetail, IngredientList, UserDetail, UserList,
    set_password, logout, TagDetail, TagList
)

urlpatterns = [
    path('users/', UserList.as_view(), name='user_list'),
    path('users/<int:pk>/', UserDetail.as_view(), name='user_detail'),
    path('users/set_password/', set_password, name='set_password'),
    path('auth/token/login/', AuthToken.as_view(), name='login'),
    path('auth/token/logout/', logout, name='logout'),

    path('tags/', TagList.as_view(), name='tag_list'),
    path('tags/<int:pk>/', TagDetail.as_view(), name='tag_detail'),

    path('ingredients/', IngredientList.as_view(), name='ingredient_list'),
    path('ingredients/<int:pk>/', IngredientDetail.as_view(),
         name='ingredient_detail'),

]
