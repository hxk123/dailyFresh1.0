from django.conf.urls import url
from .views import *

urlpatterns = [
    # url(r'^register$', register, name='register'),
    url(r'^register$', RegisterView.as_view(), name='register'),# 注册
    url(r'^active/(?P<token>.*)$', ActiveView.as_view(), name='active'),# 用户激活
    url(r'^login$', LoginView.as_view(), name='login'),# 用户登录

]