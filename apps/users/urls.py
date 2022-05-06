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
from django import views
from django.urls import path
# viewset 路由
from rest_framework.routers import DefaultRouter, SimpleRouter

from apps.users.views import (AddressView, CenterView, EmailVerifyView,
                              EmailView, LoginView, LogoutView, RegisterView,
                              TestAPIView, TestDetailGenericMaxAPIView,
                              TestDetailGenericMixinsAPIView,
                              TestGenericAPIView, TestGenericDetailsAPIView,
                              TestGenericMaxAPIView, TestGenericMixinsAPIView,
                              TestModelViewSet, UsernameCountView)

urlpatterns = [
    path('usernames/<username:username>/count/', UsernameCountView.as_view()),
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('info/', CenterView.as_view()),
    path('emails/', EmailView.as_view()),
    path('emails/verification/', EmailVerifyView.as_view()),
    path('addresses/', AddressView.as_view()),
    #二级和三级视图
    path('api/v1/test', TestAPIView.as_view()),
    path('api/v2/test', TestGenericAPIView.as_view()),
    path('api/v2/test/details/<pk>/', TestGenericDetailsAPIView.as_view()),
    path('api/v2.5/test', TestGenericMixinsAPIView.as_view()),
    path('api/v2.5/test/details/<pk>/',
         TestDetailGenericMixinsAPIView.as_view()),
    path('api/v3/test', TestGenericMaxAPIView.as_view()),
    path('api/v3/test/details/<pk>/', TestDetailGenericMaxAPIView.as_view()),
]
# 终极版本viewset的路由
# 1. 创建router实例
router = DefaultRouter()

# 2. 设置列表视图和详细视图的公共部分
# prefix    路由,列表视图和详细视图的公共部分
#           route会生成2个路由:1.列表视图的路由 prefix 2.详情视图的路由 prefix/pk
# viewset   视图集
# basename=None 给列表视图和详细视图的路由设置别名
#               别名的规范是    列表视图: basename-list     详细视图的规范 :basename-detail
#               因为 别名的原因,所以basename不要重复,一般我们都是一prefix作为basename
router.register('api/viewset', TestModelViewSet, basename='api/viewset')

# 3. 将router生成的路由,追加到 urlpatterns
urlpatterns += router.urls
