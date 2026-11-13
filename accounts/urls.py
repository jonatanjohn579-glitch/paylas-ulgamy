from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import profile_view, student_list, register_view, logout_view


urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('profile/', profile_view, name='profile'),
    path('students/', student_list, name='student_list'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),

]
