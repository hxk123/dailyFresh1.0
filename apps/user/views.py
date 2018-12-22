from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.http import HttpResponse
from django.views.generic import View
import re
from user.models import User
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, SignatureExpired
from django.conf import settings
from celery_tasks.tasks import send_register_active_email
from django.contrib.auth import authenticate, login


# Create your views here.


def register(request):
    if request.method == 'GET':
        return render(request, 'register.html')
    else:
        # 进行注册处理
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 进行数据校验
        if not all([username, password, email]):
            # 数据不完整
            return render(request, 'register.html', {'errmsg':'数据不完整'})

        # 校验邮箱
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg':'邮箱格式不正确'})

        # 是否同意协议
        if allow != 'on':
            return render(request, 'register.html', {'errmsg':'请同意协议'})

        # 校验用户名是否重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户不存在
            user = None

        if user:
             # 用户存在
            return render(request, 'register.html', {'errmsg':'用户已存在'})

        # 进行业务处理
        user = User.objects.create_user(username, email, password)
        # 用户是否激活
        user.is_active = 0
        user.save()

        # 返回应答
        return redirect(reverse('goods:index'))


# 类视图
class RegisterView(View):
    '''注册类'''
    def get(self, request):
        '''显示注册页面'''
        return render(request , 'register.html')

    def post(self, request):
        '''进行注册处理'''
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 进行数据校验
        if not all([username, password, email]):
            # 数据不完整
            return render(request, 'register.html', {'errmsg': '数据不完整'})

        # 校验邮箱
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

        # 是否同意协议
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})

        # 校验用户名是否重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户不存在
            user = None

        if user:
            # 用户存在
            return render(request, 'register.html', {'errmsg': '用户已存在'})

        # 进行业务处理
        user = User.objects.create_user(username, email, password)
        # 用户是否激活
        user.is_active = 0
        user.save()

        # 加密用户的身份信息,生成激活 token
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        # 给用户的id加密
        token = serializer.dumps(info)# 返回的是 bytes
        token = token.decode()# 解码,成为字符串

        # 发送激活邮件 : 激活链接 http://127.0.0.1:8000/user/active/3
        # 让 broker 去发邮件,异步发送
        send_register_active_email.delay(email, username, token)

        # subject = '信者云小店欢迎信息'
        # message = ''
        # sender = settings.EMAIL_FROM
        # receiver = [email]
        # html_message = '<h1>亲爱的%s,恭喜您成为本店的会员</h1>请点击下面的链接进行激活<br><a href="http://127.0.0.1:8000/user/active/%s">' \
        #                'http://127.0.0.1:8000/user/active/%s</a>' % (username, token, token)
        # # 是阻塞执行的函数
        # send_mail(subject, message, sender, receiver, html_message=html_message)

        # 返回应答
        return redirect(reverse('goods:index'))


class ActiveView(View):
    '''用户激活'''
    def get(self, request, token):
        '''进行用户激活'''
        # 进行解密, 获取要激活的用户信息
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)
            # 获取待激活的用户 id
            user_id = info['confirm']

            # 根据id获取用户信息
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()
            # 跳转到登录页面
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            # 激活连接已过期
            return HttpResponse('激活链接已过期')


class LoginView(View):
    '''登录'''
    def get(self, request):
        '''显示登录页面'''
        # 首先判断是否记住了用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''
        return render(request, 'login.html', {'username':username, 'checked':checked})

    def post(self, request):
        '''登录校验'''
        # 接收数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')

        # 校验数据
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '数据不完整'})

        # 业务处理: 登录校验
        user = authenticate(username=username, password=password)
        if user is not None:
            # 用户名和密码正确
            if user.is_active:
                # 用户已激活
                # 记录用户的登录状态
                login(request, user)

                # 回到首页
                response = redirect(reverse('goods:index'))

                # 判断是否记住用户名
                remember = request.POST.get('remember')

                if remember == 'on':
                    # 记住用户名 就存到 cookie 里
                    response.set_cookie('username', username, max_age=7*24*3600)
                else:
                    response.delete_cookie('username')

                # 返回response
                return response

            else:
                # 用户未激活
                return render(request, 'login.html', {'errmsg': '用户未激活'})
        else:
            # 用户名或密码错误
            return render(request, 'login.html', {'errmsg': '用户名或密码错误'})

        # 返回应答

