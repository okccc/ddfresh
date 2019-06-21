from django.conf.urls import url
from .views import RegisterView, ActiveView, LoginView

urlpatterns = [
    # 注册
    # url('^register$', views.register, name='register'),
    url('^register$', RegisterView.as_view(), name='register'),
    # 激活
    url('^active/(?P<token>.*)$', ActiveView.as_view(), name='active'),
    # 登录
    url('^login$', LoginView.as_view(), name='login'),
]