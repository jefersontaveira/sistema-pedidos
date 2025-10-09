# contas/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Quando o usuário acessar /contas/login/, o Django usará sua view de login padrão
    path('login/', auth_views.LoginView.as_view(template_name='contas/login.html'), name='login'),

    # Quando o usuário acessar /contas/logout/, o Django fará o logout
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]