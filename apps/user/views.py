from django.shortcuts import render, redirect, reverse, HttpResponse
from django.views.generic import View
from .models import User
import re
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer  # 加密用户身份信息生成激活token
from django.conf import settings
from celery_tasks.tasks import send_email_by_celery
from django.contrib.auth import authenticate, login  # django内置认证系统和会话保持

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
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 2.数据校验
        # 校验数据完整性
        if not all([username, password, email, allow]):
            return render(request, "register.html", {"errmsg": "数据不完整"})
        # 校验用户名
        # 校验密码
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
        user = User.objects.create_user(username, email, password)
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
            # 登录成功,跳转到首页
            response = redirect(reverse('goods:index'))
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


