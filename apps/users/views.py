import json
import re

from django.http import JsonResponse
# Create your views here.
from django.views import View
from requests import Response
# DRF 认证的三种方式
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication,
                                           TokenAuthentication)
from rest_framework.generics import (GenericAPIView, ListCreateAPIView,
                                     RetrieveAPIView)
from rest_framework.mixins import (CreateModelMixin, ListModelMixin,
                                   RetrieveModelMixin)
# DRF分页的两种方法
from rest_framework.pagination import (LimitOffsetPagination,
                                       PageNumberPagination)
from rest_framework.permissions import AllowAny, IsAuthenticated  # DRF权限设置
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from apps.users.models import Address, User
from apps.users.serializers import AddressSerializers
from utils.view import LoginRequiredJSONMixin


def checkPassword(password) -> bool:
    if not isinstance(password, str):
        return False

    if len(password) < 8 or len(password) > 20:
        return False
    return True


def checkEmail(email) -> bool:
    if not isinstance(email, str):
        return False

    if re.match('^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
        return True
    return False


def checkUserName(username) -> bool:
    if not isinstance(username, str):
        return False

    if re.match('^[a-zA-Z0-9_-]{5,20}$', username):
        return True
    return False


def checkModile(mobile) -> bool:
    if not isinstance(mobile, str):
        return False

    if re.match('^1[345789]\d{9}$', mobile):
        return True
    return False


def checkBool(booldata) -> bool:
    if not isinstance(booldata, bool):
        return False


# from rest_framework.request import Request
from rest_framework.response import Response

from apps.users.serializers import UserModelSerializers


# 一级视图
class TestAPIView(APIView):
    def get(self, request):
        # django -- request.GET
        # drf -- request.query_params
        query_params = request.query_params
        # id = query_params.data
        user_obj = User.objects.get(id=5)
        serializer = UserModelSerializers(instance=user_obj)
        print(f"user_dict={serializer.data}")

        # DRF默认返回类型就是json数据
        return Response(serializer.data)

    def post(self, request):
        # django --- request.POST(form)  request.body(JSON)
        # DRF --- request.data
        # 1.接收参数,获取数据
        data = request.data

        # 2.验证参数,序列化器解决
        serializer = UserModelSerializers(data=data)
        if serializer.is_valid() is False:
            return Response({'msg': 'data bad!!!'})

        # 3.保存数据
        serializer.save()

        # 4.返回响应
        return Response(serializer.data)


"""
GenericAPIView 比 APIView 拓展了一些属性和方法

属性
    queryset    设置查询结果集
    serializer_class    设置序列化器
    lookup_field    设置查询指定数据的关键字

方法
    get_queryset()  获取查询结果集
    get_serializer()    获取序列化实例
    get_object()    获取指定的数据
"""


# 二级视图
class TestGenericAPIView(GenericAPIView):
    # 查询结果集
    queryset = User.objects.get(id=5)
    # 序列化器
    serializer_class = UserModelSerializers

    def get(self, request):
        # 1.查询数据
        # user=User.objects.get(id=5)
        user = self.get_queryset()

        # 2.将结果进行序列化
        # serializer = UserModelSerializers(data=data)
        serializer = self.get_serializer(instance=user)

        # 3.返回结果
        return Response(serializer.data)

    def post(self, request):
        # 1.接收参数,获取数据
        data = request.data

        # 2.验证参数,序列化器解决
        serializer = self.get_serializer(data=data)
        if serializer.is_valid() is False:
            return Response({'msg': 'data bad!!!'})

        # 3.保存数据
        serializer.save()

        # 4.返回响应
        return Response(serializer.data)


class TestGenericDetailsAPIView(GenericAPIView):
    # 查询结果集
    queryset = User.objects.all()
    # 序列化器
    serializer_class = UserModelSerializers

    # 查询关键字必须为pk,或者通过 lookup_field修改
    def get(self, request, pk):
        # 1.查询指定数据
        # user = User.objects.get(id=pk)
        # user = self.queryset.filter(id=pk)
        # user = self.get_queryset().filter(id=pk)
        user = self.get_object()

        # 2.将结果进行序列化
        serializer = self.get_serializer(instance=user)

        # 3.返回响应
        return Response(serializer.data)


# 二级视图 +Mixin
class TestGenericMixinsAPIView(ListModelMixin, CreateModelMixin,
                               GenericAPIView):
    # 查询结果集 <---一定要是集合
    queryset = User.objects.all()
    # 序列化器
    serializer_class = UserModelSerializers

    def get(self, request):
        return self.list(request)

    def post(self, request):
        return self.create(request)


class TestDetailGenericMixinsAPIView(RetrieveModelMixin, GenericAPIView):
    # 查询结果集 <---一定要是集合
    queryset = User.objects.all()
    # 序列化器
    serializer_class = UserModelSerializers

    # 查询关键字必须为pk,或者通过 lookup_field修改
    def get(self, request, pk):
        return self.retrieve(request)


# 三级视图 TestGenericMaxAPIView，RetrieveAPIView
class TestGenericMaxAPIView(ListCreateAPIView):
    # 查询结果集 <---一定要是集合
    queryset = User.objects.all()
    # 序列化器
    serializer_class = UserModelSerializers


class TestDetailGenericMaxAPIView(RetrieveAPIView):
    # 查询结果集 <---一定要是集合
    queryset = User.objects.all()
    # 序列化器
    serializer_class = UserModelSerializers


class PageNum(PageNumberPagination):
    # 开启分页的开关
    page_size = 5
    # 设置查询字符串的key相当于开关,只有设置了这个值,一页多少条记录才生效,url参数
    page_size_query_param = 'ps'
    # 一页最多多少条记录(性能控制)
    max_page_size = 20


# 终极版本:ViewSet
class TestModelViewSet(ModelViewSet):
    # 权限设置
    # permission_classes = [AllowAny]
    # permission_classes = [IsAuthenticated]

    # 认证设置
    # authentication_classess = [BasicAuthentication]
    # authentication_classess = [SessionAuthentication]
    # authentication_classess = [TokenAuthentication]

    #单独设置分页类
    # 只有GenericAPIView和子类可以使用,APIView,ViewSet不能使用
    # pagination_class = LimitOffsetPagination
    pagination_class = PageNum

    # 查询结果集 <---一定要是集合
    queryset = User.objects.all()
    # 序列化器
    serializer_class = UserModelSerializers


# TODO:测试修改后的userview,（all）
class UsernameCountView(View):
    def get(self, request, username):
        count = User.objects.filter(username=username).count()
        return JsonResponse({'code': 0, 'count': count, 'errmsg': 'ok'})


class RegisterView(View):
    def get(self, request):
        return JsonResponse({'code': 0, 'errmsg': 'ok'})

    def post(self, request):
        #1.请求数据
        try:
            body_dict = json.loads(request.body.decode())
        except Exception as e:
            print("RegisterView.post: get body dict error!!!")
            return JsonResponse({'code': 400, 'errmsg': '输入数据有误!请重新输入'})

        print("RegisterView.post: get body dict success...")

        #2.获取数据
        username = body_dict.get('username')
        password = body_dict.get('password')
        password2 = body_dict.get('password2')
        mobile = body_dict.get('mobile')
        allow = body_dict.get('allow')

        # 3.check input

        # 3.2 check username
        if checkUserName(username) is False:
            print("RegisterView.post:checkUserName error!!!")
            return JsonResponse({'code': 400, 'errmsg': '用户名不满足规则'})

        count = User.objects.filter(username=username).count()
        if count != 0:
            return JsonResponse({'code': 400, 'errmsg': '用户已经注册'})

        # 3.3 check modile
        if checkModile(mobile) is False:
            print("RegisterView.post:checkModile error!!!")
            return JsonResponse({'code': 400, 'errmsg': '手机号码不满足规则'})

        # 3.4 check allow
        if checkBool(allow) is False:
            print("RegisterView.post:allow checkBool error!!!")
            return JsonResponse({'code': 400, 'errmsg': 'allow error!!!'})

        # 3.5 check password
        if checkPassword(password) is False or checkPassword(
                password2) is False:
            print("RegisterView.post:password checkPassword error!!!")
            return JsonResponse({'code': 400, 'errmsg': '密码必须在8~20位'})

        if password != password2:
            return JsonResponse({'code': 400, 'errmsg': '两次输入的密码不对'})

        print(f"RegisterView.post: check param success...")
        # print(
        #     f"username={username},password={password},password2={password2},mobile={mobile},allow={allow}"
        # )

        #4.导入数据库
        # 密码没有加密
        # User.objects.create(username=username,password=password,mobile=mobile)

        # 密码没有加密
        try:
            user = User.objects.create_user(username=username,
                                            password=password,
                                            mobile=mobile)
        except Exception as e:
            print(f"RegisterView.post: user create error!!!")
            return JsonResponse({'code': 400, 'errmsg': '用户注册失败,请尝试重新注册!!!'})

        print(f"RegisterView.post: user create success...")
        # 如何设置session信息
        # request.session['user_id']=user.id

        # 系统（Django）为我们提供了 状态保持的方法
        from django.contrib.auth import login

        # request, user,
        # 状态保持 -- 登录用户的状态保持
        # user 已经登录的用户信息
        login(request, user)
        print(f"RegisterView.post: user login success...")

        #5.返回请求
        return JsonResponse({'code': 0, 'errmsg': 'ok'})


#TODO:修改密码
class LoginView(View):
    def post(self, request):

        #1.请求:接收数据,验证数据
        try:
            body_dict = json.loads(request.body.decode())
        except Exception as e:
            print("LoginView.post: get body dict error!!!")
            return JsonResponse({'code': 400, 'errmsg': '输入数据有误!请重新输入'})

        print("LoginView.post: get body dict success...")
        print(f"LoginView.post: body_dict={body_dict}")

        #2.业务逻辑:验证用户名和密码是否正确,session,判断是否记住登录
        #2.1获取数据
        username = body_dict.get('username')
        password = body_dict.get('password')
        remembered = body_dict.get('remembered')

        # 2.3验证用户名和密码是否正确
        # check username
        if checkUserName(username) is False:
            print(f"LoginView.post: check checkUserName error!!!")
            return JsonResponse({'code': 400, 'errmsg': '用户名不满足规则'})

        # check password
        if checkPassword(password) is False:
            print(f"LoginView.post: check password error!!!")
            return JsonResponse({'code': 400, 'errmsg': '密码必须在8~20位'})

        #BUG:remembered存在问题
        if checkBool(remembered) is False:
            print(f"LoginView.post: check remembered error!!!")
            return JsonResponse({'code': 400, 'errmsg': '记住密码异常'})

        print(f"LoginView.post: check param success...")

        # 确定 我们是根据手机号查询 还是 根据用户名查询
        # USERNAME_FIELD 我们可以根据 修改 User. USERNAME_FIELD 字段
        # 来影响authenticate 的查询
        # authenticate 就是根据 USERNAME_FIELD 来查询
        if checkModile(username):
            User.USERNAME_FIELD = 'mobile'
        else:
            User.USERNAME_FIELD = 'username'

        print(f"LoginView.post: username_field={User.USERNAME_FIELD}")

        from django.contrib.auth import authenticate, login
        user = authenticate(username=username, password=password)

        #登录失败
        if user is None:
            print(f"LoginView.post: login fail ...")
            return JsonResponse({'code': 400, 'errmsg': '账号或密码不正确'})

        try:
            login(request, user)
        except Exception as e:
            print(f"LoginView.post: login error!!!")
            return JsonResponse({'code': 400, 'errmsg': '登录失败,请重新尝试'})

        print(f"LoginView.post: login success...")

        #判断是否记住登录
        if remembered is True:
            #记住登录
            request.session.set_expiry(None)
        else:
            #不记住密码,
            request.session.set_expiry(0)

        print(request.session.items())

        #3.响应:返回JSON数据0成功,400失败
        # 合并购物车
        from apps.carts.utils import mergeCookie2Redis
        response = mergeCookie2Redis(request=request)
        print(f"LoginView.post: mergeCookie2Redis success...")

        #cookie设置用户名
        response.set_cookie('username', username)
        return response


from django.contrib.auth import logout


class LogoutView(LoginRequiredJSONMixin, View):
    def delete(self, requset):
        #1.删除sesion信息
        logout(requset)

        response = JsonResponse({'code': 0, 'errmsg': 'ok'})
        #直接退出虽然会删除session,但是cookie的username依旧保留
        #2.删除cookie信息,(前端会根据cookie来显示用户信息)
        response.delete_cookie('username')

        return response


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
        3. 保存邮箱地址
        4. 发送一封激活邮件
        5. 返回响应
        

需求（要实现什么功能） --> 思路（ 请求。业务逻辑。响应） --> 步骤  --> 代码实现
"""


#必须是已经登录用户的实例
class EmailView(LoginRequiredJSONMixin, View):
    def put(self, request):
        #1.接收请求
        try:
            body_dict = json.loads(request.body.decode())
        except Exception as e:
            print("EmailView.put: get body dict error!!!")
            return JsonResponse({'code': 400, 'errmsg': '输入数据有误!请重新输入'})

        print("EmailView.put: get body dict success...")
        print(f"EmailView.put: body_dict={body_dict}")

        #2.获取请求参数:邮箱
        email = body_dict.get('email')

        #2.1邮箱校验
        if checkEmail(email) is False:
            print(f"EmailView.put: checkEmail error...")
            return JsonResponse({'code': 400, 'errmsg': '邮箱不满足规则'})

        print(f"EmailView.put: check parm success...")

        # 3. 保存邮箱地址
        user = request.user
        # user / request.user 就是　登录用户的　实例对象
        # user --> User
        user.email = email
        try:
            user.save()
        except Exception as e:
            print(f"EmailView.put: email save error!!!")

        print(f"EmailView.put: email save success...")

        #4. 发送一封激活邮件
        # from django.core.mail import send_mail
        subject = '美多商城激活邮件'
        message = ""
        # NOTE:格式不能改,必须是xxx<email>
        from_email = '美多商城<wyycshope@163.com>'
        # 邮件的内容如果是 html 这个时候使用 html_message
        html_message = "激活链接仅有效5分钟,请尽快点击"

        #5.1接收邮件
        recipient_list = [email]

        #5.2生成邮件的激活地址
        from apps.users.utils import generic_email_verify_token

        try:
            token = generic_email_verify_token(request.user.id)
        except Exception as e:
            print(f"EmailView.put: generic_email_verify_token error!!!")

        print(f"EmailView.put: generic_email_verify_token success...")
        print(f"EmailView.put: token={token}")

        verify_url = f"http://www.meiduo.site:8080/success_verify_email.html?token={token}"
        # 5.2 组织我们的激活邮件
        html_message = '<p>尊敬的用户您好！</p>' \
                       '<p>感谢您使用美多商城。</p>' \
                       f'<p>您的邮箱为：{email} 。请点击此链接激活您的邮箱：</p>' \
                       f'<p><a href="{verify_url}">{verify_url}<a></p>'

        #5.2发送邮件
        # send_mail(subject=subject,
        #           message=message,
        #           from_email=from_email,
        #           html_message=html_message,
        #           recipient_list=recipient_list)
        # celery消息队列异步实现发送邮件
        # 激活woker:
        # cd /code/;celery -A celery_tasks.main worker -l INFO
        from celery_tasks.email.tasks import celery_send_email

        # delay 的参数 等同于 任务（函数）的参数
        try:
            celery_send_email.delay(subject=subject,
                                    message=message,
                                    from_email=from_email,
                                    html_message=html_message,
                                    recipient_list=recipient_list)
        except Exception as e:
            print(f"EmailView.put: celery_send_email error!!!")
        print(f"EmailView.put: celery_send_email success...")
        print(f"EmailView.put: verify_url={verify_url}")

        #6. 返回响应
        return JsonResponse({'code': 0, 'errmsg': 'ok'})


'''
4. 邮件激活:
请求           接收请求，获取token参数
业务逻辑        v1:   1.根据token确定用户 2.数据库写入用户的邮箱
               v2:    1.根据token确定用户 2.让用户输入账号密码进行多因素认证 3.确定token,用户名,密码符合才允许绑定
响应           JSON  code=0

路由          get /emails/verification/?token={token}
步骤
    1. 接收请求
    2. 获取数据,过滤数据
    3. 根据token获取userid
    4. mysql邮箱激活位设置
    5. 返回响应

5. 保存邮箱地址
#6. 返回响应
'''


#BUG:需要二次验证
class EmailVerifyView(View):
    def get(self, request):
        # 1. 接收请求
        # BUG:前端错误返回没处理好
        token = request.GET.get('token')

        #  2. 获取数据,过滤数据
        if token is None:
            return JsonResponse({'code': 400, 'errmsg': '请补全参数'})

        print(f"EmailVerifyView.get: get token sucess...")
        print(f"EmailVerifyView.get: token={token}")
        #WARINIG:是否需要匹配token的正则表达式?

        from apps.users.utils import check_email_verify_token

        #   3. 根据token获取userid
        userid = check_email_verify_token(token)
        if userid is None:
            return JsonResponse({'code': 400, 'errmsg': '验证邮箱过期或验证邮箱不正确'})

        print(f"EmailVerifyView.get: get userid sucess...")
        print(f"EmailVerifyView.get: userid={userid}")

        #   4. mysql邮箱激活位设置
        try:
            user = User.objects.get(id=userid)

            #   5.修改数据
            user.email_active = True
            user.save()
        except Exception as e:
            print(f"EmailVerifyView.get: email error!!!")
            return JsonResponse({'code': 400, 'errmsg': '验证邮箱过期或验证邮箱不正确'})

        print(f"EmailVerifyView.get: email active sucess...")

        #   6. 返回响应
        return JsonResponse({'code': 0, 'errmsg': 'ok'})


"""
需求：     1.保存收获地址

前端：
    当用户输入保存收获地址之后，点击保存。这个时候会发送axios请求。
    
后端：
    请求           接收请求，获取数据
    业务逻辑       过滤输入,如果只有一个地址则为默认,保存数据
    响应           JSON  code=0,    response.data.address;  is_show_edit
    
    路由          POST   /addresses/
    步骤
        1. 接收请求
        2. 获取数据
        3. 过滤输入
        4. 判断是否有默认地址
        5. 保存数据
        6. 返回数据
        

"""


#BUG:水平越权,没有通过sessionid校验用户的身份导致任意查询
#TODO:修改默认地址,删除地址,设置默认地址,修改地址标题
class AddressView(LoginRequiredJSONMixin, View):
    def get(self, request):
        user = request.user

        #1.查询指定数据
        #注意结果是多个
        try:
            address_list_obj = Address.objects.filter(user=user,
                                                      is_deleted=False)
        except Exception as e:
            print('AddressView.get: get user address list error...')
            return JsonResponse({'code': 400, 'errmsg': '查询收获地址失败'})
        print(f"AddressView.get: get user address list success")

        #2.将来对象数据转换为字典数据
        address_list_dict = [{
            'id': address_obj.id,
            "title": address_obj.title,
            "receiver": address_obj.receiver,
            "province": address_obj.province.name,
            "city": address_obj.city.name,
            "district": address_obj.district.name,
            "place": address_obj.place,
            "mobile": address_obj.mobile,
            "tel": address_obj.tel,
            "email": address_obj.email
        } for address_obj in address_list_obj]
        # test_address_list_dict = AddressSerializers(instance=address_list_obj,
        #                                             many=True)

        print("AddressView.get: AddressSerializers success...")
        # print(f"test_address_list_dict={test_address_list_dict.data.__dir__}")
        print(f"address_list_dict={address_list_dict}")

        #3.返回响应
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'addresses': address_list_dict
        })

    #新增收获地址
    def post(self, request):
        #0.超过20个地址不然新建
        # 1. 接收请求
        try:
            body_dict = json.loads(request.body.decode())
        except Exception as e:
            print("AddressView.post: get body dict error!!!")
            return JsonResponse({'code': 400, 'errmsg': '输入数据有误!请重新输入'})

        print("AddressView.post: get body dict success...")
        print(f"AddressView.post: body_dict={body_dict}")

        # 2. 获取数据
        receiver = body_dict.get('receiver')
        mobile = body_dict.get('mobile')
        province_id = body_dict.get('province_id')
        city_id = body_dict.get('city_id')
        district_id = body_dict.get('district_id')
        place = body_dict.get('place')
        title = body_dict.get('title')  # 非必须
        email = body_dict.get('email')  # 非必须
        tel = body_dict.get('tel')  # 非必须

        # 3. 过滤输入
        # 3.1 校验必选字段:收件人,收获地址,手机
        if not all([receiver, province_id, city_id, district_id, place, title
                    ]):
            return JsonResponse({'code': 400, 'errmsg': '请补全必须参数:收件人,收获地址,手机'})

        # 3.2 各个字段的过滤
        # ERROR:收件人,地址暂时先不过滤(数据类型+正则表达式)
        if checkModile(mobile) is False:
            print(f"AddressView.post: checkModile error!!!")
            return JsonResponse({'code': 400, 'errmsg': '手机号码不满足规则'})
        print(f"AddressView.post: check necessarily pram success...")

        # 4. 保存数据
        # ERROR:其他校验暂时未做,地址暂时先不过滤(数据类型+正则表达式)

        #4.1取出非必选字段邮箱,做校验,电话号码
        if checkEmail(email) is False:
            print(f"AddressView.post: checkEmail error!!!")
            return JsonResponse({'code': 400, 'errmsg': '邮箱地址不满足规则'})

        print(f"AddressView.post: check option param success...")

        # 4.2存储数据
        from apps.areas.models import Area
        user = request.user

        #FIXED:ValueError: Cannot assign "110000": "Address.province" must be a "Area" instance.
        try:
            address = Address.objects.create(
                user=user,
                title=title,
                receiver=receiver,
                province=Area.objects.get(id=province_id),
                city=Area.objects.get(id=city_id),
                district=Area.objects.get(id=district_id),
                place=place,
                mobile=mobile,
                email=email,
                tel=tel)
        except Exception as e:
            print('AddressView.post: create user address error...')
            return JsonResponse({'code': 400, 'errmsg': '用户地址创建失败'})

        print('AddressView.post: create user address success...')

        #BUG:数据库编码问题导致无法显示
        #REF:https://www.cnblogs.com/carry-2017/p/10988212.html
        address_dict = {
            'id': address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }
        print(f'AddressView.post: address_dict={address_dict}')

        # 5. 返回数据
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'address': address_dict
        })
