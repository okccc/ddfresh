from django.conf.urls import url
from .views import RegisterView, ActiveView, LoginView, LogoutView, UserInfoView, UserOrderView, AddressView

urlpatterns = [
    # url('^register$', views.register, name='register'),
    url('^register$', RegisterView.as_view(), name='register'),  # 注册
    url('^active/(?P<token>.*)$', ActiveView.as_view(), name='active'),  # 激活
    url('^login$', LoginView.as_view(), name='login'),  # 登录
    url('^logout$', LogoutView.as_view(), name='logout'),  # 退出

    url('^$', UserInfoView.as_view(), name='user'),  # 用户中心-信息页
    url('^order$', UserOrderView.as_view(), name='order'),  # 用户中心-订单页
    url('^address$', AddressView.as_view(), name='address'),  # 用户中心-地址页

]