from django.urls import path

from .views import AuthToken, UserDetail, UserList, set_password, logout

urlpatterns = [
    path('users/', UserList.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetail.as_view(), name='user-detail'),
    path('users/set_password/', set_password, name='set_password'),
    path('auth/token/login/', AuthToken.as_view(), name='login'),
    path('auth/token/logout/', logout, name='logout'),
]
