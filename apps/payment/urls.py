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

from apps.payment.views import PaymentStatusView, PayUrlView

# id需要转换器
urlpatterns = [
    #路由匹配的顺序性, payment/123/不符合1才走payment/status
    #但是 payment/status?xxxx符合payment/<order_id>/
    path('payment/status/', PaymentStatusView.as_view()),
    path('payment/<order_id>/', PayUrlView.as_view()),
]
