from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
# Create your views here.
from django.views import View


class ImageCodeView(View):
    def get(self, request, uuid):
        # 1.接收请求
        # 1.1 获取uuid
        # 2.处理请求
        # 2.1生成图片的验证码和二进制文件
        from libs.captcha.captcha import captcha
        text, image = captcha.generate_captcha()
        # 2.2将uuid和验证码绑定到redis上
        from django_redis import get_redis_connection
        redis_cli = get_redis_connection('code')
        redis_cli.setex(uuid, 100, text)
        # 3.回显请求
        # 3.1回显图片的二进制码
        # 4. 返回图片二进制
        # 因为图片是二进制 我们不能返回JSON数据
        # content_type=响应体数据类型
        # content_type 的语法形式是： 大类/小类
        # content_type (MIME类型)
        #图片： image/jpeg , image/gif, image/png
        return HttpResponse(image, content_type='image/jpeg')


class SmsCodeView(View):
    def get(self, request, mobile):
        #1.接收请求
        # 1.1 获取手机,图形验证码,和图形
        image_code = request.GET.get('image_code')
        uuid = request.GET.get('image_code_id')

        #2.验证请求
        # BUG:所有数据输入还需要做数据类型校验
        if not all([image_code, uuid]):
            return JsonResponse({'code': 400, 'errmsg': '请补全参数'})
        # 3.验证图形验证码
        # 3.1 连接redis
        from django_redis import get_redis_connection
        redis_cli = get_redis_connection('code')

        #3.2 获取图形验证码
        text = redis_cli.get(uuid)

        # NOTE:注意所有的获取都需要判断是否获取成功!!!
        # UNTEST:待测试
        if text == None:
            return JsonResponse({'code': 400, 'errmsg': '验证码过期'})
        # 获取的类型是b'text'

        #3.3 检查图形验证码是否正确
        if text.decode().lower() != image_code.lower():
            return JsonResponse({'code': 400, 'errmsg': '验证码错误'})

        # 4.生成短信验证码
        from random import randint
        sms_code = '%06d' % randint(0, 999999)

        # 方式1.常规的tcp请求,缺点是需要频繁建立tcp连接
        # #4.1.1 保存短信验证码到redis
        # redis_cli.setex(mobile, 300, sms_code)
        # # # 添加一个发送标记.有效期 60秒 内容是什么都可以
        # redis_cli.setex(f'send_flag_{mobile}', 60, 1)

        # 管道方式2管道连接
        # 4.2.1 新建管道
        pipeline = redis_cli.pipeline()

        # 4.2.2 消息放入管道
        redis_cli.setex(mobile, 300, sms_code)
        redis_cli.setex(f'send_flag_{mobile}', 60, 1)

        # 4.2.3 管道执行
        pipeline.execute()

        #5.发送验证短信
        # from libs.yuntongxun.sms import CCP
        # CCP().send_template_sms(mobile, [sms_code, 5], 1)

        #6 返回结果
        from celery_tasks.sms.tasks import celery_send_sms_code

        # delay 的参数 等同于 任务（函数）的参数
        celery_send_sms_code.delay(mobile=mobile, sms_code=sms_code)
        
        #调用worker
        #celery -A celery_tasks.tasks.py worker -l INFO
        # 7. 返回响应
        return JsonResponse({'code': 0, 'errmsg': 'ok'})
