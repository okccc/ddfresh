"""ddfresh URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin

urlpatterns = [
    # project的admin页面 http://ip:port/admin
    url(r'^admin/', admin.site.urls),
    url(r'^tinymce/', include('tinymce.urls')),  # 富文本编辑器
    url(r'^search', include('haystack.urls')),  # 全文检索框架
    # 将app的urls添加到project的主urls,此处的namespace和视图函数的name可用作反向解析
    url(r'^user/', include('apps.user.urls', namespace='user')),  # 用户模块
    url(r'^cart/', include('apps.cart.urls', namespace='cart')),  # 购物车模块
    url(r'^order/', include('apps.order.urls', namespace='order')),  # 订单模块
    # 因为进首页就是商品模块,所以不用添加正则,放最后面
    url(r'^', include('apps.goods.urls', namespace='goods')),  # 商品模块
]
