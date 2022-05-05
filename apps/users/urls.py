"""meiduo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from apps.users.views import (AddressView, CenterView, EmailVerifyView,
                              EmailView, LoginView, LogoutView, RegisterView,
                              TestAPIView, TestDetailGenericMaxAPIView,
                              TestDetailGenericMixinsAPIView,
                              TestGenericAPIView, TestGenericDetailsAPIView,
                              TestGenericMaxAPIView, TestGenericMixinsAPIView,
                              UsernameCountView)

urlpatterns = [
    path('usernames/<username:username>/count/', UsernameCountView.as_view()),
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('info/', CenterView.as_view()),
    path('emails/', EmailView.as_view()),
    path('emails/verification/', EmailVerifyView.as_view()),
    path('addresses/', AddressView.as_view()),
    path('api/v1/test', TestAPIView.as_view()),
    path('api/v2/test', TestGenericAPIView.as_view()),
    path('api/v2/test/details/<pk>/', TestGenericDetailsAPIView.as_view()),
    path('api/v2.5/test', TestGenericMixinsAPIView.as_view()),
    path('api/v2.5/test/details/<pk>/', TestDetailGenericMixinsAPIView.as_view()),
    path('api/v3/test', TestGenericMaxAPIView.as_view()),
    path('api/v3/test/details/<pk>/', TestDetailGenericMaxAPIView.as_view()),

]
