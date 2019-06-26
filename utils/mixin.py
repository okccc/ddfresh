from django.contrib.auth.decorators import login_required  # django内置认证系统的登录装饰器

class LoginRequiredMixin(object):
    """登录装饰器类"""
    @classmethod
    def as_view(cls, **initkwargs):
        # 调用父类的as_view
        view = super(LoginRequiredMixin, cls).as_view(**initkwargs)
        return login_required(view)
