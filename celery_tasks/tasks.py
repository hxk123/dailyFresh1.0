# 使用celery
from celery import Celery
from django.core.mail import send_mail
from django.conf import settings
import time

# 在任务处理者一端添加djang初始化
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dailyFresh.settings")
django.setup()


# 创建一个Celery类的实例对象

app = Celery('celery_tasks.task', broker='redis://127.0.0.1:6379/8')

# 定义任务函数
@app.task
def send_register_active_email(to_email, username, token):
    '''发送激活邮件'''
    # 组织邮件信息
    subject = '信者云小店欢迎信息'
    message = ''
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    html_message = '<h1>亲爱的%s,恭喜您成为本店的会员</h1>请点击下面的链接进行激活<br><a href="http://127.0.0.1:8000/user/active/%s">' \
                   'http://127.0.0.1:8000/user/active/%s</a>' % (username, token, token)
    # 是阻塞执行的函数
    send_mail(subject, message, sender, receiver, html_message=html_message)
    time.sleep(5)