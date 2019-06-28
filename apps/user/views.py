from django.shortcuts import render, redirect, reverse, HttpResponse
from django.views.generic import View
from .models import User, Address
from apps.goods.models import GoodsSKU
import re
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer  # 加密用户身份信息生成激活token
from django.conf import settings
from celery_tasks.tasks import send_email_by_celery  # 通过celery发送激活邮件
from django.contrib.auth import authenticate, login, logout  # django内置认证系统和会话保持
from utils.mixin import LoginRequiredMixin  # 类视图的登录装饰器
from django_redis import get_redis_connection
# Create your views here.

def register(request):
    """显示注册页面和注册处理可以使用同一个视图函数"""
    if request.method == "GET":
        # GET请求说明是显示注册页面
        return render(request, "register.html")
    else:
        # POST请求说明是进行注册处理
        # 1.接收form表单数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        # 2.数据校验
        # 校验数据完整性
        if not all([username, password, email, allow]):
            return render(request, "register.html", {"errmsg": "数据不完整"})
        # 校验邮箱
        if not re.match('^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, "register.html", {"errmsg": "邮箱格式错误"})
        # 校验勾选
        if allow != 'on':
            return render(request, "register.html", {"errmsg": "请勾选同意协议"})
        # 校验用户名是否已存在
        try:
            user = User.objects.get(username=username)
        except Exception as e:
            print(e)  # User matching query does not exist.
            user = None
        if user:
            return render(request, "register.html", {"errmsg": "该用户名已存在"})
        # 3.业务处理：进行用户注册
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()
        # 4.返回应答
        # 注册成功就返回到首页
        return redirect(reverse('goods:index'))

# 类视图：dispatch方法会根据不同请求方式调用对应的处理方法
class RegisterView(View):
    """注册视图"""
    def get(self, request):
        """显示注册页面"""
        return render(request, "register.html")

    def post(self, request):
        """注册校验"""
        # 1.接收form表单数据
        username = request.POST.get('user_name')
        password1 = request.POST.get('pwd')
        password2 = request.POST.get('cpwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 2.数据校验
        # 校验数据完整性
        if not all([username, password1, password2, email, allow]):
            return render(request, "register.html", {"errmsg": "数据不完整"})
        # 校验用户名
        if not 3 <= len(username) <= 8:
            return render(request, "register.html", {"errmsg": "用户名长度必须是3~8位"})
        # 校验密码
        if not password1 == password2:
            return render(request, "register.html", {"errmsg": "两次密码输入不一致"})
        # 校验邮箱
        if not re.match('^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, "register.html", {"errmsg": "邮箱格式错误"})
        # 校验勾选
        if allow != 'on':
            return render(request, "register.html", {"errmsg": "请勾选同意协议"})
        # 校验用户名是否已存在
        try:
            user = User.objects.get(username=username)
        except Exception as e:
            print(e)  # User matching query does not exist.
            user = None
        if user:
            return render(request, "register.html", {"errmsg": "该用户名已存在"})

        # 3.进行用户注册
        # 往user表插入一条数据
        user = User.objects.create_user(username, email, password1)
        user.is_active = 0
        user.save()
        # 创建Serializer对象
        serializer = Serializer(secret_key=settings.SECRET_KEY, expires_in=3600)
        # 加密用户身份信息,生成激活token
        token = serializer.dumps({"confirm": user.id}).decode()
        # 通过celery异步发送激活邮件,delay方法将其放入任务队列,服务器会立即响应而不用等待与smtp服务器交互的时间
        send_email_by_celery.delay(email, username, token)

        # 4.注册成功就返回到首页
        return redirect(reverse('goods:index'))


class ActiveView(View):
    """激活用户"""
    def get(self, request, token):
        # 创建Serializer对象
        serializer = Serializer(secret_key=settings.SECRET_KEY, expires_in=3600)
        try:
            # 用户点击激活的请求包含之前生成的激活token,从token中解密出用户身份信息
            user_id = serializer.loads(token)["confirm"]
            # 修改数据库对应信息
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()
            # 激活成功跳转到登录页
            return redirect(reverse('user:login'))
        except Exception as e:
            print(e)
            # 激活连接已过期,请重新激活
            return HttpResponse("激活链接已过期")


class LoginView(View):
    """登录视图"""
    def get(self, request):
        """显示登录页面"""
        # 判断是否记住用户名
        if "username" in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = "checked"
        else:
            username, checked = "", ""
        return render(request, "login.html", {"username": username, "checked": checked})

    def post(self, request):
        """登录校验"""
        # 1.接收form表单数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        remember = request.POST.get('remember')
        # print(username, password)

        # 2.数据校验
        # 检验数据完整性
        if not all([username, password]):
            return render(request, "login.html", {"errmsg": "数据不完整"})
        # 校验用户名密码是否正确(用户认证)
        user = authenticate(username=username, password=password)
        # print(user)
        if user:
            # 用户名密码正确,记录用户登录状态(会话保持),会将session放入redis缓存(浏览器Cookie的sessionid就对应redis的key)
            login(request, user)
            # 获取登录后要跳转到的地址,默认首页
            next_url = request.GET.get('next', reverse('goods:index'))
            print(next_url)
            response = redirect(next_url)
            # 是否勾选了记住用户名
            if remember == 'on':
                # 勾选了就往浏览器添加cookie信息
                response.set_cookie(key="username", value=username, max_age=7*24*3600)
            else:
                # 未勾选就删除cookie信息
                response.delete_cookie(key="username")
            # 返回应答
            return response
        else:
            # 用户名或密码错误
            return render(request, "login.html", {"errmsg": "用户名或密码错误"})


class LogoutView(View):
    """退出"""
    def get(self, request):
        # 清除登录用户的session信息
        logout(request)
        # 跳转回首页
        return redirect(reverse('goods:index'))


class UserInfoView(LoginRequiredMixin, View):
    """用户中心-信息页"""

    def get(self, request):
        # 获取登录用户,django会给request对象添加一个属性request.user
        user = request.user
        print(type(user))
        # 获取默认收货地址
        address = Address.objects.get_default_address(user)
        # 连接redis
        conn = get_redis_connection('default')  # default是settings配置的CACHES
        # 遍历redis的list获取用户最新浏览的5个商品的id
        history_key = 'history_%d' % user.id
        sku_ids = conn.lrange(history_key, 0, 4)  # [2,3,1]
        # 再去数据库查询浏览商品的具体信息
        goods_list = []
        for sku_id in sku_ids:
            goods = GoodsSKU.objects.get(id=sku_id)
            goods_list.append(goods)
        # 往模板传递数据
        context = {'page': 'user', 'address': address, 'goods_list': goods_list}
        # 除了context之外,django框架会把request.user也传给模板
        return render(request, 'user_center_info.html', context)


class UserOrderView(LoginRequiredMixin, View):
    """用户中心-订单页"""
    def get(self, request):
        # 获取用户订单信息
        return render(request, "user_center_order.html", {"page": "order"})


class AddressView(LoginRequiredMixin, View):
    """用户中心-地址页"""

    def get(self, request):
        # 获取登录用户
        user = request.user
        # 获取默认收货地址
        address = Address.objects.get_default_address(user)
        # 使用模板
        return render(request, 'user_center_site.html', {'page': 'address', 'address': address})

    def post(self, request):
        """添加地址"""
        # 1.接收form表单数据
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')

        # 2.校验数据
        # 校验数据完整性
        if not all([receiver, addr, phone]):
            return render(request, 'user_center_site.html', {'errmsg': '数据不完整'})
        # 校验手机号
        if not re.match(r'^1[3|4|5|7|8][0-9]{9}$', phone):
            return render(request, 'user_center_site.html', {'errmsg': '手机格式不正确'})

        # 3.添加地址
        # 获取登录用户
        user = request.user
        # 获取默认收货地址
        address = Address.objects.get_default_address(user)
        # 如果用户已存在默认收货地址,添加的新地址不作为默认收货地址,否则作为默认收货地址
        if address:
            is_default = False
        else:
            is_default = True
        # 往address表插入一条数据
        address = Address.objects.create(user=user, receiver=receiver, addr=addr, zip_code=zip_code, phone=phone, is_default=is_default)
        address.save()
        # 刷新页面
        return redirect(reverse('user:address'))


