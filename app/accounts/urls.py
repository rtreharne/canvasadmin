from django.urls import path, include
from django.contrib.auth.views import LogoutView, LoginView

from . import views

app_name = 'accounts'
urlpatterns = [
    path('login/', LoginView.as_view(redirect_authenticated_user=True)),
    path('', include("django.contrib.auth.urls")),
    path('register/', views.register_user, name='register'),
]