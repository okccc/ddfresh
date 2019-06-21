"""
celery：将注册、上传、图形处理等耗时任务放到后台异步执行而不影响用户其他操作
celery的处理者worker也需要任务代码,需将工程代码复制一份到celery执行目录
启动命令：celery -A celery_tasks.tasks worker -l info
"""
import celery
from django.conf import settings
from django.core.mail import send_mail  # django自带发邮件功能

# django项目启动时wsgi.py会加载系统配置文件,而celery处理任务是不需要启动django项目的,所以在任务处理者端要导入配置文件,不然tasks.py报错
# import os
# from django.core.wsgi import get_wsgi_application
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ddfresh.settings")
# application = get_wsgi_application()

# 创建Celery对象
app = celery.Celery("celery_tasks.tasks", broker="redis://:redis666@192.168.152.11:6379/1")

# 定义任务函数
@app.task  # 装饰后可以使用delay方法
def send_email_by_celery(email, username, token):
    """通过celery发送激活邮件"""
    # 主题
    subject = '天天生鲜欢迎信息'
    # 正文
    message = ''
    # 收件人看到的发件人
    from_email = settings.EMAIL_FROM
    # 收件人
    recipient_list = [email]
    # 包含html标签的正文
    html_message = '<h1>%s, 欢迎注册会员</h1>请点击下面链接激活您的账户<br/><a href="http://192.168.152.11:9999/user/active/%s"></a>' % (username, token)
    # html_message参数可以转义html标签
    send_mail(subject, message, from_email, recipient_list, html_message=html_message)

