import imp
import json
import re
from email import message
from itertools import count
from urllib import response

from django.http import JsonResponse
from django.shortcuts import render
# Create your views here.
from django.views import View

from apps.users.models import User


class UsernameCountView(View):
    def get(self, request, username):
        count = User.objects.filter(username=username).count()
        return JsonResponse({'code': 0, 'count': count, 'errmsg': 'ok'})


class RegisterView(View):
    def get(self, request):
        return JsonResponse({'code': 0, 'errmsg': 'ok'})

    def post(self, request):
        #1.请求数据
        body_bytes = request.body
        body_str = body_bytes.decode()
        body_dict = json.loads(body_str)

        #2.获取数据
        username = body_dict.get('username')
        password = body_dict.get('password')
        password2 = body_dict.get('password2')
        mobile = body_dict.get('mobile')
        allow = body_dict.get('allow')

        # 3.check input
        # 3.1查看数据是有空值
        # BUG:所有数据输入还需要做数据类型校验
        if not all([username, password, password2, mobile, allow]):
            return JsonResponse({'code': 400, 'errmsg': '请补全参数'})

        # 3.2 check username
        if not re.match('^[a-zA-Z0-9_-]{5,20}$', username):
            return JsonResponse({'code': 400, 'errmsg': '用户名不满足规则'})

        count = User.objects.filter(username=username).count()
        if count != 0:
            return JsonResponse({'code': 400, 'errmsg': '用户已经注册'})

        # 3.3 check modile
        if not re.match('^1[345789]\d{9}$', mobile):
            return JsonResponse({'code': 400, 'errmsg': '手机号码不满足规则'})

        # 3.4 check allow
        # checktype_only

        # 3.5 check password
        if len(password) < 8 or len(password) > 20:
            return JsonResponse({'code': 400, 'errmsg': '密码必须在8~20位'})
        if password != password2:
            return JsonResponse({'code': 400, 'errmsg': '两次输入的密码不对'})

        # print(
        #     f"username={username},password={password},password2={password2},mobile={mobile},allow={allow}"
        # )

        #4.导入数据库
        # 密码没有加密
        # User.objects.create(username=username,password=password,mobile=mobile)

        # 密码没有加密
        user = User.objects.create_user(username=username,
                                        password=password,
                                        mobile=mobile)

        # 如何设置session信息
        # request.session['user_id']=user.id

        # 系统（Django）为我们提供了 状态保持的方法
        from django.contrib.auth import login

        # request, user,
        # 状态保持 -- 登录用户的状态保持
        # user 已经登录的用户信息
        login(request, user)

        #5.返回请求
        return JsonResponse({'code': 0, 'errmsg': 'ok'})


class LoginView(View):
    def post(self, request):

        #1.请求:接收数据,验证数据
        #1.请求数据
        body_bytes = request.body
        body_str = body_bytes.decode()
        body_dict = json.loads(body_str)

        #2.业务逻辑:验证用户名和密码是否正确,session,判断是否记住登录
        #2.1获取数据
        username = body_dict.get('username')
        password = body_dict.get('password')
        remembered = body_dict.get('remembered')

        # 2.2查看数据是有空值
        # BUG:所有数据输入还需要做数据类型校验
        if not all([username, password]):
            return JsonResponse({'code': 400, 'errmsg': '请补全参数'})

        #BUG:remembered存在问题
        print(
            f"username={username},password={password},remembered={remembered}")

        # 2.3验证用户名和密码是否正确
        # check username
        if not re.match('^[a-zA-Z0-9_-]{5,20}$', username):
            return JsonResponse({'code': 400, 'errmsg': '用户名不满足规则'})
        # check password
        if len(password) < 8 or len(password) > 20:
            return JsonResponse({'code': 400, 'errmsg': '密码必须在8~20位'})

        # 确定 我们是根据手机号查询 还是 根据用户名查询
        # USERNAME_FIELD 我们可以根据 修改 User. USERNAME_FIELD 字段
        # 来影响authenticate 的查询
        # authenticate 就是根据 USERNAME_FIELD 来查询
        if re.match('^1[345789]\d{9}$', username):
            User.USERNAME_FIELD = 'mobile'
        else:
            User.USERNAME_FIELD = 'username'

        print(f"check_username_field={User.USERNAME_FIELD}")

        from django.contrib.auth import authenticate, login
        user = authenticate(username=username, password=password)

        #登录失败
        if user is None:
            return JsonResponse({'code': 400, 'errmsg': '账号或密码不正确'})

        login(request, user)

        #判断是否记住登录
        if remembered is True:
            #记住登录
            request.session.set_expiry(None)
        else:
            #不记住密码,
            request.session.set_expiry(0)

        print(request.session.items())

        #3.响应:返回JSON数据0成功,400失败
        response = JsonResponse({'code': 0, 'errmsg': 'ok'})

        #cookie设置用户名
        response.set_cookie('username', username)
        return response


from django.contrib.auth import logout


class LogoutView(View):
    def delete(self, requset):
        #1.删除sesion信息
        logout(requset)

        response = JsonResponse({'code': 0, 'errmsg': 'ok'})
        #直接退出虽然会删除session,但是cookie的username依旧保留
        #2.删除cookie信息,(前端会根据cookie来显示用户信息)
        response.delete_cookie('username')

        return response


from utils.view import LoginRequiredJSONMixin


class CenterView(LoginRequiredJSONMixin, View):
    def get(self, request):
        # request.user 就是 已经登录的用户信息
        # request.user 是来源于 中间件
        # 系统会进行判断 如果我们确实是登录用户，则可以获取到 登录用户对应的 模型实例数据
        # 如果我们确实不是登录用户，则request.user = AnonymousUser()  匿名用户
        info_data = {
            'username': request.user.username,
            'email': request.user.email,
            'mobile': request.user.mobile,
            'email_active': request.user.email_active,
        }
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'info_data': info_data
        })


"""
需求：     1.保存邮箱地址  2.发送一封激活邮件  3. 用户激活邮件

前端：
    当用户输入邮箱之后，点击保存。这个时候会发送axios请求。
    
后端：
    请求           接收请求，获取数据
    业务逻辑        保存邮箱地址  发送一封激活邮件
    响应           JSON  code=0
    
    路由          PUT     
    步骤
        1. 接收请求
        2. 获取数据
        3. 发送一封激活邮件
        4. 保存邮箱地址
        5. 返回响应
        

需求（要实现什么功能） --> 思路（ 请求。业务逻辑。响应） --> 步骤  --> 代码实现
"""


#必须是已经登录用户的实例
class EmailView(LoginRequiredJSONMixin, View):
    def put(self, request):
        #1.接收请求
        body_bytes = request.body
        body_str = body_bytes.decode()
        body_dict = json.loads(body_str)
        print(f"get email success....body_dict={body_dict}")

        #2.获取请求参数:邮箱
        email = body_dict.get('email')
        #2.1邮箱校验
        if not all([email]):
            return JsonResponse({'code': 400, 'errmsg': '请补全参数'})

        if not re.match('^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$',
                        email):
            return JsonResponse({'code': 400, 'errmsg': '邮箱不满足规则'})
        print(f"check email success....")

        #3. 发送一封激活邮件
        # from django.core.mail import send_mail
        subject = '美多商城激活邮件'
        message = ""
        # NOTE:格式不能改,必须是xxx<email>
        from_email = '美多商城<wyycshope@163.com>'
        # 邮件的内容如果是 html 这个时候使用 html_message
        html_message = "激活链接仅有效5分钟,请尽快点击"

        #3.1接收邮件
        recipient_list = [email]

        #3.2生成邮件的激活地址
        from apps.users.utils import decrypt_userid, generic_email_verify_token
        token = generic_email_verify_token(request.user.id)
        print(f"token={token}")

        verify_url = f"http://www.meiduo.site:8080/success_verify_email.html?token={token}"
        # 4.2 组织我们的激活邮件
        html_message = '<p>尊敬的用户您好！</p>' \
                       '<p>感谢您使用美多商城。</p>' \
                       f'<p>您的邮箱为：{email} 。请点击此链接激活您的邮箱：</p>' \
                       f'<p><a href="{verify_url}">{verify_url}<a></p>'

        #3.2发送邮件
        # send_mail(subject=subject,
        #           message=message,
        #           from_email=from_email,
        #           html_message=html_message,
        #           recipient_list=recipient_list)
        # celery消息队列异步实现发送邮件
        # 激活woker:
        # cd ..;celery -A celery_tasks.main worker -l INFO
        from celery_tasks.email.tasks import celery_send_email

        # delay 的参数 等同于 任务（函数）的参数
        celery_send_email.delay(subject=subject,
                                message=message,
                                from_email=from_email,
                                html_message=html_message,
                                recipient_list=recipient_list)

        #4. 保存邮箱地址
        #5. 返回响应
        return JsonResponse({'code': 0, 'errmsg': 'ok'})
