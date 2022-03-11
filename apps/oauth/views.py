from urllib import response

from django.http import JsonResponse
from django.shortcuts import redirect, render

"""
Create your views here.
3.1 准备工作                        -----------------------------------准备好了

    # QQ登录参数
    # 我们申请的 客户端id
    QQ_CLIENT_ID = '101474184'          appid
    # 我们申请的 客户端秘钥
    QQ_CLIENT_SECRET = 'c6ce949e04e12ecc909ae6a8b09b637c'   appkey
    # 我们申请时添加的: 登录成功后回调的路径
    QQ_REDIRECT_URI = 'http://www.meiduo.site:8080/oauth_callback.html'

3.2 放置 QQ登录的图标（目的： 让我们点击QQ图标来实现第三方登录）  ------------- 前端做好了

3.3 根据oauth2.0 来获取code 和 token                      ---------------我们要做的
    对于应用而言，需要进行两步：
    1. 获取Authorization Code；            表面是一个链接，实质是需要用户同意，然后获取code

    2. 通过Authorization Code获取Access Token

3.4 通过token换取 openid                                ----------------我们要做的
    openid是此网站上唯一对应用户身份的标识，网站可将此ID进行存储便于用户下次登录时辨识其身份，
    或将其与用户在网站上的原有账号进行绑定。

把openid 和 用户信息 进行一一对应的绑定

生成用户绑定链接 ----------》获取code   ------------》获取token ------------》获取openid --------》保存openid

生成用户绑定链接

前端： 当用户点击QQ登录图标的时候，前端应该发送一个axios(Ajax)请求

后端：
    请求
    业务逻辑        调用QQLoginTool 生成跳转链接
    响应            返回跳转链接 {"code":0,"qq_login_url":"http://xxx"}
    路由          GET   qq/authorization/
    步骤      
            1. 生成 QQLoginTool 实例对象
            2. 调用对象的方法生成跳转链接
            3. 返回响应
            
404 路由不匹配
405 方法不被允许（你没有实现请求对应的方法）
"""
from django.views import View
from meiduo import settings
from QQLoginTool.QQtool import OAuthQQ


class QQLoginURLView(View):
    def get(self, request):
        # 1. 生成 QQLoginTool 实例对象
        # client_id appid
        # client_secret appsecret
        # redis_uri 跳转页面
        # state csrftoken

        qq = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                     client_secret=settings.QQ_CLIENT_SECRET,
                     redirect_uri=settings.QQ_REDIRECT_URI,
                     state='test')
        #     2. 调用对象的方法生成跳转链接
        qq_login_url = qq.get_qq_url()
        #     3. 返回响应
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'login_url': qq_login_url
        })


"""

需求： 获取code，通过code换取token，再通过token换取openid

前端：
        应该获取 用户同意登录的code。把这个code发送给后端
后端：
    请求          获取code
    业务逻辑       通过code换取token，再通过token换取openid
                根据openid进行判断
                如果没有绑定过，则需要绑定
                如果绑定过，则直接登录
    响应          
    路由          GET         oauth_callback/?code=xxxxx
    步骤
        1. 获取code
        2. 通过code换取token
        3. 再通过token换取openid
        4. 根据openid进行判断
        5. 如果没有绑定过，则需要绑定
        6. 如果绑定过，则直接登录

"""
import json
import re

from django.contrib.auth import login

from apps.oauth.models import OAuthQQUser
from apps.users.models import User


class OauthQQView(View):
    def get(self, request):
        # 1. 获取code
        code = request.GET.get('code')
        if code is None:
            return JsonResponse({'code': 400, 'errmsg': '参数不全'})

        # 2. 通过code换取token
        # BUG:state不是随机值,存在CSRF
        qq = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                     client_secret=settings.QQ_CLIENT_SECRET,
                     redirect_uri=settings.QQ_REDIRECT_URI,
                     state='test')

        # 3. 再通过token换取openid
        token = qq.get_access_token(code)
        print(f"token={token}")

        # 4. 根据openid进行判断
        openid = qq.get_open_id(token)
        print(f"openid={openid}")

        try:
            qquser = OAuthQQUser.objects.get(openid=openid)
        # 5. 如果没有绑定过，则需要绑定
        except OAuthQQUser.DoesNotExist:
            #返回openid并要求绑定
            print("qquser doesnotexist.....")

            #加密openid
            from apps.oauth.utils import encrypt_openid
            access_token = encrypt_openid(openid)
            print(f"encrypt_openid={access_token}")

            response = JsonResponse({
                'code': 400,
                'access_token': access_token
            })
            return response

        # 6. 如果绑定过，则直接登录
        else:
            #WAITING:分支未测试
            print("qquser exist login.....")
            #6.1设置session
            login(request, qquser.user)

            #6.2 设置cookie
            response = JsonResponse({'code': 0, 'errmsg': 'ok'})

            #cookie设置用户名
            print(f"username={qquser.user.username}")

            response.set_cookie('username', qquser.user.username)
            return response

    def post(self, request):
        #1.接收请求
        body_bytes = request.body
        body_str = body_bytes.decode()
        body_dict = json.loads(body_str)
        print(f"POST:body_dict={body_dict}")

        #2.获取请求参数 手机,密码,openid,验证码
        mobile = body_dict.get('mobile')
        password = body_dict.get('password')
        access_token = body_dict.get('access_token')
        sms_code = body_dict.get('sms_code')

        #3.根据手机号进行用户信息的查询
        # 3.1所有输入均不能为空
        if not all([mobile, password, access_token, sms_code]):
            return JsonResponse({'code': 400, 'errmsg': '请补全参数'})
        #3.2校验密码
        if len(password) < 8 or len(password) > 20:
            return JsonResponse({'code': 400, 'errmsg': '密码必须在8~20位'})
        #3.3校验手机号
        if not re.match('^1[345789]\d{9}$', mobile):
            return JsonResponse({'code': 400, 'errmsg': '用户名不满足规则'})
        #3.4 校验验证码
        #3.4.1链接redis取出验证码
        from django_redis import get_redis_connection
        redis_conn = get_redis_connection('code')
        sms_code_server = redis_conn.get(f'{mobile}').decode()
        print(f"get sms_code_server={sms_code_server},sms_code={sms_code}")

        #3.4.2 校验验证码
        if sms_code_server is None:
            return JsonResponse({'code': 400, 'errmsg': '验证码失效'})

        if sms_code_server != sms_code:
            return JsonResponse({'code': 400, 'errmsg': '验证码错误'})

        #3.5 openid校验
        #FIXED:openid的重放,openid被返回到了前端可以实现劫持;被加密后的openid仅有效3分钟,除非破解加密算法
        from apps.oauth.utils import decrypt_openid

        openid = decrypt_openid(access_token)
        print(f"encrypt_openid={access_token},openid={openid}")
        if openid is None:
            return JsonResponse({'code': 400, 'errmsg': '参数确实'})

        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            print(f"User DoesNotExist registring new user.....")
            #5.查询到用户手机号没有注册:创建一个user信息再绑定
            user = User.objects.create_user(username=mobile,
                                            password=password,
                                            mobile=mobile)
        else:
            #4.查询到用户手机号已经注册:判断密码是否正确,绑定用户和openid信息
            print(f"User Exist binding user.....")
            if not user.check_password(password):
                return JsonResponse({'code': 400, 'errmsg': '密码错误'})
            #WARING:如果我改了openid呢?

        OAuthQQUser.objects.create(user=user, openid=openid)
        #6.保存请求
        login(request, user)
        #7.返回信息
        response = JsonResponse({'code': 0, 'errmsg': 'ok'})
        print(f"username={user.username}")
        response.set_cookie('username', user.username)

        return response
