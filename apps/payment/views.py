from django.shortcuts import render

# Create your views here.
#与支付宝的交互只需要干两件事
#1.生成支付宝连接
#2.接收支付id
"""
需求:
    当用户点击去支付时,需要生成一个跳转的连接
前端:
    axios request:发送支付id
后端:
    请求:
        接收支付id
    业务逻辑:
        校验支付id,请求alipay生成一个对用的连接
    响应:
        返回支付连接

    路由:
        payment/order_id/
    步骤:
        1. 接收order_id
        2. 校验order_id
        3. 读取app的key
        4. 创建alipay实例
        5. 与支付宝交互
        6. 拼接连接
"""
from alipay import AliPay, AliPayConfig
from django.http import JsonResponse
from django.views import View
from meiduo.settings import (ALIPAY_APPID, ALIPAY_DEBUG,
                             ALIPAY_PUBLIC_KEY_PATH, ALIPAY_RETURN_URL,
                             ALIPAY_URL, APP_PRIVATE_KEY_PATH)
from utils.view import LoginRequiredJSONMixin

from apps.orders.models import OrderInfo


#转换器确定是32位的数字后,这里只负责从数据库获取
def checkOrderId(order_id, user, status):
    #NOTE:校验order_id,用户信息,状态信息
    try:
        order_id_obj = OrderInfo.objects.get(order_id=order_id,
                                             user=user,
                                             status=status)
    except Exception as e:
        return None
    return order_id_obj


#读取公私钥
def getPaymentKeys():
    try:
        app_private_key_string = open(APP_PRIVATE_KEY_PATH).read()
        alipay_public_key_string = open(ALIPAY_PUBLIC_KEY_PATH).read()
    except Exception as e:
        return None, None
    return app_private_key_string, alipay_public_key_string


class PayUrlView(LoginRequiredJSONMixin, View):
    #ref
    # https://www.cnblogs.com/jrri/p/11669349.html
    def get(self, request, order_id):

        # 1. 接收order_id
        print(f"PayUrlView.GET:get order_id success...")
        print(f"PayUrlView.GET:order_id={order_id}")

        # 2. 校验order_id
        user = request.user
        status = OrderInfo.ORDER_STATUS_ENUM["UNPAID"]

        order_id_obj = checkOrderId(order_id=order_id,
                                    user=user,
                                    status=status)

        if order_id_obj is None:
            print(f"PayUrlView.GET:check param error!!!")
            return JsonResponse({'code': 400, 'errmsg': '支付订单失败!请检查订单信息'})

        print(f"PayUrlView.GET:check param success...")
        print(f"PayUrlView.GET:order_id_obj={order_id_obj}")

        # 3. 读取app的key
        app_private_key_string, alipay_public_key_string = getPaymentKeys()
        if app_private_key_string is None or alipay_public_key_string is None:
            print(f"PayUrlView.GET:app private key  error!!!")
            return JsonResponse({'code': 400, 'errmsg': '密钥加载失败'})

        print(f"PayUrlView.GET:getPayment Keys success...")

        # 4. 创建alipay实例
        try:
            alipay = AliPay(
                appid=ALIPAY_APPID,
                app_notify_url=None,  # 默认回调url
                app_private_key_string=app_private_key_string,
                alipay_public_key_string=alipay_public_key_string,
                sign_type="RSA2",
                debug=ALIPAY_DEBUG,  # 上线则改为False , 沙箱True
            )
        except Exception as e:
            print("PayUrlView.GET:create alipayObj error!!!")
            return JsonResponse({'code': 400, 'errmsg': '生成跳转连接失败'})
        print("PayUrlView.GET:create alipayObj success...")

        # 页面接口示例：alipay.trade.page.pay
        try:
            order_string = alipay.api_alipay_trade_page_pay(
                out_trade_no=order_id,
                total_amount=str(order_id_obj.total_amount),
                subject='支付订单:%s' % order_id,
                return_url=ALIPAY_RETURN_URL,
                notify_url=None,
            )
        except Exception as e:
            print("PayUrlView.GET:alipay.trade.page.pay url error!!!")
            return JsonResponse({'code': 400, 'errmsg': '生成跳转连接失败'})

        print(f"order_string={order_string}")

        alipay_url = 'https://openapi.alipaydev.com/gateway.do?' + order_string
        print("PayUrlView.GET:get alipay.trade.page.pay url success...")
        print(f"PayUrlView.GET:alipay_url={alipay_url}")

        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'alipay_url': alipay_url
        })


"""
前端:
        当用户支付完成之后,会跳转到 指定商品页面
        页面中的请求 查询字符串中有 支付相关信息
        前端把这些数据提交给后端就可以了
后端:
    请求:         接收数据
    业务逻辑:       查询字符串转换为字典,验证数据,验证没有问题获取支付宝交易流水号
                  改变订单状态
    响应: 
    路由:     PUT     payment/status/
    步骤:
        1. 接收数据
        2. 查询字符串转换为字典 验证数据
        3. 验证没有问题获取支付宝交易流水号
        4. 改变订单状态
        5. 返回响应

"""
from apps.payment.models import Payment


class PaymentStatusView(LoginRequiredJSONMixin, View):
    def put(self, request):
        #  1. 接收数据
        data = request.GET
        user = request.user

        # 2. 查询字符串转换为字典 验证数据
        # for django users
        data = data.dict()
        # data={'charset': 'utf-8',
        # 'out_trade_no': '20220430093714130717000000007',
        #  'method': 'alipay.trade.page.pay.return',
        # 'total_amount': '6499.00',
        #  'trade_no': '2022043022001454390511363332',
        # 'auth_app_id': '2021000117675026',
        # 'version': '1.0', 'app_id': '2021000117675026',
        # 'sign_type': 'RSA2',
        # 'seller_id': '2088621955972156',
        # 'timestamp': '2022-04-30 17:38:00'}

        # sign must be popped out
        signature = data.pop("sign")
        # signature=Euk9Ng+/pa3uD1CJCNkbH/SjV9scZLLoYXsHXHWumrpLbB9bbDKeZZP/
        # OEQOLFxXJi5vUC3BOcy6TuBhy4JEHG/MNdVwpwLEBwk52nE5faoEP7Ui5ezxCu6WUU5a8I0Yeq4DYDSjru/
        # iqyz5155m8B2jnur2H8meB3JmT1VO50gGo1fuUhQSEMmiz6TaLDi/
        # xM8EzHdWok7Esi5X+iILahImy5JkoZzG203eO2mtC8dFXJsLuN5xFLiGlXBGBRrSYFPkqj1zUBENQh/
        # M6JXCBLoov/WlVNOcu5cWOH+QpKt/G4ojkfv/lUf+WT1Tq933yfviO8z0XQ8fKwo2fTzM7Q==

        print(f"PaymentStatusView.PUT:create payment dict success...")
        print(f"PaymentStatusView.PUT:signature={signature}")
        print(f"PaymentStatusView.PUT:data={data}")

        # verification
        app_private_key_string, alipay_public_key_string = getPaymentKeys()
        if app_private_key_string is None or alipay_public_key_string is None:
            print(f"PaymentStatusView.PUT:app private key  error!!!")
            return JsonResponse({'code': 400, 'errmsg': '密钥加载失败'})

        print(f"PaymentStatusView.PUT:getPayment Keys success...")

        # 创建支付宝实例
        try:
            alipay = AliPay(
                appid=ALIPAY_APPID,
                app_notify_url=None,  # 默认回调url
                app_private_key_string=app_private_key_string,
                alipay_public_key_string=alipay_public_key_string,
                sign_type="RSA2",
                debug=ALIPAY_DEBUG,  # 上线则改为False , 沙箱True
                config=AliPayConfig(timeout=15)  # 可选, 请求超时时间
            )
        except Exception as e:
            print(f"PaymentStatusView.PUT:create alipay obj error!!!")
            JsonResponse({'code': 400, 'errmsg': 'create alipay obj error!!!'})

        print(f"PaymentStatusView.PUT:create alipay obj success...")

        #校验数据
        success = alipay.verify(data, signature)

        #BUG:检查订单支付未支付情况下没有解决,需要做回滚
        if success:
            print(f"PaymentStatusView.PUT:alipay verify signature success...")
            # 3. 验证没有问题获取支付宝交易流水号
            trade_no = data.get('trade_no')
            order_id = data.get('out_trade_no')
            print(
                f"PaymentStatusView.PUT:trade_no={trade_no},order_id={order_id}"
            )

            #检查oder_id
            order = checkOrderId(order_id=order_id,
                                 user=user,
                                 status=OrderInfo.ORDER_STATUS_ENUM["UNPAID"])

            try:
                Payment.objects.create(trade_id=trade_no, order=order)
            except Exception as e:
                print("PaymentStatusView.PUT:Payment object create error!!!")
                return JsonResponse({'code': 400, 'errmsg': '订单失败'})
            print("PaymentStatusView.PUT:Payment object create success...")

            # 4. 改变订单状态
            #BUG:更新订单失败情况下没有解决,需要做回滚
            try:
                OrderInfo.objects.filter(
                    order_id=order_id,
                    user=user,
                    status=OrderInfo.ORDER_STATUS_ENUM["UNPAID"]).update(
                        status=OrderInfo.ORDER_STATUS_ENUM['UNSEND'])
            except Exception as e:
                print("PaymentStatusView.PUT:update OrderInfo error!!!")
                return JsonResponse({'code': 400, 'errmsg': '订单失败'})
            print("PaymentStatusView.PUT:update OrderInfo success...")

            # 5. 返回响应
            return JsonResponse({
                'code': 0,
                'errmsg': 'ok',
                'trade_id': trade_no
            })
        else:
            print(f"PaymentStatusView.PUT:alipay verify signature error!!!")
            return JsonResponse({'code': 400, 'errmsg': '请到个人中心的订单中查询订单状态'})
