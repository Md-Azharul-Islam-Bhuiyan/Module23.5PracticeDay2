from django.urls import path
from . import views
# from django.contrib.auth.views import LogoutView 

urlpatterns = [
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('profile/', views.UserBankAccountUpdateView.as_view(), name='profile'),
    path('change_pass/', views.pass_change, name='change_pass')
]
