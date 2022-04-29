import json
from itertools import count
from unicodedata import decimal

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
# Create your views here.
from django.views import View
from django_redis import get_redis_connection
from utils.view import LoginRequiredJSONMixin

from apps.goods.models import SKU
from apps.orders.models import OrderGoods, OrderInfo

"""
需求：
    提交订单页面的展示
前端：
        发送一个axios请求来获取 地址信息和购物车中选中商品的信息
后端：
    请求：         必须是登录用户才可以访问
    业务逻辑：      地址信息，购物车中选中商品的信息
    响应：         JSON
    路由：
            GET     orders/settlement/
    步骤：
        
        1.获取用户信息
        2.地址信息
            2.1 查询用户的地址信息 [Address,Address,...]
            2.2 将对象数据转换为字典数据
        3.购物车中选中商品的信息
            3.1 连接redis
            3.2 hash        {sku_id:count,sku_id:count}
            3.3 set         [1,2]
            3.4 重新组织一个 选中的信息
            3.5 根据商品的id 查询商品的具体信息 [SKU,SKU,SKu...]
            3.6 需要将对象数据转换为字典数据
"""


#BUG:未登录用户依旧可以访问
class OrderSettlementView(LoginRequiredJSONMixin, View):
    def get(self, request):
        from apps.users.models import Address

        # 1.获取用户信息
        user = request.user

        # 2.地址信息
        #     2.1 查询用户的地址信息 [Address,Address,...]
        try:
            address_list_obj = Address.objects.filter(user=user,
                                                      is_deleted=False)
        except Exception as e:
            print('OrderSettlement:GET  user address  list error...')
            return JsonResponse({'code': 400, 'errmsg': '查询收获地址失败'})
        print(f"OrderSettlement:GET user address list success")
        print(f"OrderSettlement:address_list_obj={address_list_obj}")

        #     2.2 将对象数据转换为字典数据
        address_list = []
        for address_obj in address_list_obj:
            address_list.append({
                'id': address_obj.id,
                "receiver": address_obj.receiver,
                "province": address_obj.province.name,
                "city": address_obj.city.name,
                "district": address_obj.district.name,
                "place": address_obj.place,
                "mobile": address_obj.mobile,
            })
        print(f"OrderSettlement:GET create user address list success")
        print(f"OrderSettlement:address_list={address_list}")

        # 3.购物车中选中商品的信息
        #     3.1 连接redis
        redis_cli = get_redis_connection('carts')
        pipeline = redis_cli.pipeline()
        #     3.2 hash        {sku_id:count,sku_id:count}
        pipeline.hgetall(f'carts_{user.id}')
        #     3.3 set         [1,2]
        pipeline.smembers(f'selected_{user.id}')
        #返回的结果是先后送进piple的顺寻
        sku_id_counts, selectd_ids = pipeline.execute()

        print(f"OrderSettlement:GET selectd_ids from redis success...")
        print(f"OrderSettlement:selectd_ids={selectd_ids}")

        #     3.4 重新组织一个 选中的信息
        skus = []

        #     3.5 根据商品的id 查询商品的具体信息 [SKU,SKU,SKu...]
        for selectd_id in selectd_ids:

            count = int(sku_id_counts.get(selectd_id))
            selectd_id = selectd_id.decode()

            try:
                sku = SKU.objects.get(id=selectd_id)
            except Exception as e:
                print(f"OrderSettlement:GET  get selectd_id info error!!!")
                return JsonResponse({
                    'code': 400,
                    'errmsg': 'get selectd_id info error!!!'
                })

            price = int(sku.price)
            #     3.6 需要将对象数据转换为字典数据
            # NOTE:多读前端代码,确定目标需要接收什么内容
            skus.append({
                'id': selectd_id,
                'name': sku.name,
                'count': count,
                'price': price,
                'default_image_url': sku.default_image.url
            })

        print(f"OrderSettlement:GET create skus obj success...")
        print(f"OrderSettlement:GET skus={skus}")

        # decimal   -- 货币类型
        # 小数会有很多问题
        from decimal import Decimal
        freight = Decimal('10')

        # 前端计算总价,不消耗服务器资源,消耗客户端资源
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'context': {
                'addresses': address_list,
                'skus': skus,
                'freight': freight
            }
        })


"""
需求:
    点击订单,生成订单

前端: 
    发送 address_id,pay_method,接收订单id
    由于商品信息都存储在后端,所以只需要知道一些动态的数据即可
后端:
    请求：接收地址信息和支付方式
    业务逻辑: 
        根据address_id,pay_method,和OrderSettlementView提交的信息取出,并生成一个随机的订单号和状态(默认未支付)
    返回:
        订单id
    路由:POST /orders/commit/
    步骤:
        1.接收信请求
        2.验证数据
        3.数据入库 生成订单(订单基本信息和订单商品信息表)
            Q:先保存订单 基本信息 还是订单 商品信息表
            A:主表是基本信息,外键是订单编号
            3.1 保存订单基本信息 
                order_id 主键 (自己生成)
                支付状态由支付方式决定
                总数量,总金额,运费->均通过redis获取,
                由于 3.2还会再获取sku信息,所以先让total_count=total_amount=0;等3.2结束后再计算

            3.2 保存订单商品信息表 
                连接redis
                获取hash
                获取set
                重新组织一个数据,这个数据是选中的商品的信息
                判断库存是否充足
                充足则库存减少,销量增加
                不足则下单失败
                保存订单商品信息

            3.3 更新价格

        4.返回响应

    优化后
        一。接收请求     user,address_id,pay_method
        二。验证数据
        order_id 主键（自己生成）
        支付状态由支付方式决定
        总数量，总金额， = 0
        运费
        三。数据入库     生成订单（订单基本信息表和订单商品信息表）
            1.先保存订单基本信息
                
            2 再保存订单商品信息
              2.1 连接redis
              2.2 获取hash
              2.3 获取set   
              2.4 遍历选中商品的id，
                最好重写组织一个数据，这个数据是选中的商品信息
                {sku_id:count,sku_id:count}
            
              2.5 遍历 根据选中商品的id进行查询
              2.6 判断库存是否充足，
              2.7 如果不充足，下单失败
              2.8 如果充足，则库存减少，销量增加
              2.9 累加总数量和总金额
              2.10 保存订单商品信息
          3.更新订单的总金额和总数量
          4.将redis中选中的商品信息移除出去
        四。返回响应
"""


def checkMethod(pay_method):
    try:
        pay_method = int(pay_method)
    except Exception as e:
        return None

    if pay_method not in [
            OrderInfo.PAY_METHODS_ENUM['CASH'],
            OrderInfo.PAY_METHODS_ENUM['ALIPAY']
    ]:
        return None

    return pay_method


class OrderCommitView(LoginRequiredJSONMixin, View):
    def post(self, request):
        # 一。接收请求     user,address_id,pay_method
        body_dict = json.loads(request.body.decode())
        print(f"OrderCommitView.POST:get order commit success...")
        print(f"body_dict={body_dict}")

        # 二。验证数据
        address_id = body_dict.get('address_id')
        pay_method = body_dict.get('pay_method')

        #均不能为空
        if not all([address_id, pay_method]):
            print(f"OrderCommitView.POST:get param error!!!")
            return JsonResponse({'code': 400, 'errmsg': '请补全参数'})

        print(f"address_id={address_id},pay_method={pay_method}")

        #校验method
        pay_method = checkMethod(pay_method=pay_method)
        if pay_method is None:
            print('OrderCommitView.POST:check  pay_method error...')
            return JsonResponse({'code': 400, 'errmsg': 'pay_method error'})

        #校验地址id
        from apps.users.models import Address
        user = request.user
        try:
            address_list_obj = Address.objects.filter(user=user,
                                                      is_deleted=False)
            address = address_list_obj.get(id=address_id)
        except Exception as e:
            print('OrderCommitView.POST:check  address_id error...')
            return JsonResponse({'code': 400, 'errmsg': '用户地址id不存在'})

        print('OrderCommitView.POST:check address_id success...')

        #生成订单信息
        # order_id 主键（自己生成）
        #oder_id由下单时间和用户id决定
        from datetime import datetime

        from django.utils import timezone

        order_id = timezone.localtime().strftime(
            '%Y%m%d%H%M%S%f') + '%09d' % user.id

        # 支付状态由支付方式决定
        #BUG
        if pay_method == OrderInfo.PAY_METHODS_ENUM['ALIPAY']:
            status = OrderInfo.ORDER_STATUS_ENUM['UNPAID']
        else:
            status = OrderInfo.ORDER_STATUS_ENUM['UNSEND']

        # 总数量，总金额， = 0
        total_count = 0
        from decimal import Decimal

        #注意货币类型
        total_amount = Decimal('0')
        freight = Decimal('10.0')

        #事务开始
        from django.db import transaction

        with transaction.atomic():

            #事务开始的存档点
            point = transaction.savepoint()

            try:
                order_base_obj = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    total_count=total_count,
                    total_amount=total_amount,
                    freight=freight,
                    pay_method=pay_method,
                    status=status)

            except Exception as e:
                print('OrderCommitView.POST:create order_base_obj error!!!')
                return JsonResponse({'code': 400, 'errmsg': '订单信息生成失败'})

            print('OrderCommitView.POST:create order_base_obj success..')
            print(f"order_id={order_id}")

            #  三。数据入库     生成订单（订单基本信息表和订单商品信息表）
            #     2 再保存订单商品信息
            #       2.1 连接redis
            try:
                redis_cli = get_redis_connection('carts')
                pipeline = redis_cli.pipeline()
                #       2.2 获取hash
                pipeline.hgetall(f'carts_{user.id}')
                #       2.3 获取set
                pipeline.smembers(f'selected_{user.id}')
                sku_id_counts, selectd_ids = pipeline.execute()

                carts = {}
                #       2.4 遍历选中商品的id，
                for sku_id in selectd_ids:
                    #         最好重写组织一个数据，这个数据是选中的商品信息
                    #         {sku_id:count,sku_id:count}
                    count = int(sku_id_counts[sku_id])
                    carts[int(sku_id)] = count
                print(f"carts={carts}")
            except Exception as e:
                print('OrderCommitView.POST:create order_obj error!!!')
                return JsonResponse({'code': 400, 'errmsg': '订单信息生成失败'})

            #       2.5 遍历 根据选中商品的id进行查询
            for sku_id, count in carts.items():
                #获取单价
                try:
                    sku = SKU.objects.get(id=sku_id)
                except Exception as e:
                    print('OrderCommitView.POST:query price error!!!')
                    return JsonResponse({'code': 400, 'errmsg': '订单信息生成失败'})

                #       2.6 判断库存是否充足，
                #       2.7 如果不充足，下单失败
                if sku.stock < count:
                    #读取回档
                    print(
                        f"OrderCommitView.POST:sku={sku} stock insufficient!!!"
                    )
                    transaction.savepoint_rollback(point)
                    return JsonResponse({'code': 400, 'errmsg': '库存数量不足'})

                #       2.8 如果充足，则库存减少，销量增加
                # 模拟高并发场景
                oldStock = sku.stock
                newStock = sku.stock - count
                newSales = sku.sales + count
                from time import sleep
                sleep(7)

                #乐观锁
                res = SKU.objects.filter(id=sku_id,
                                         stock=oldStock).update(stock=newStock,
                                                                sales=newSales)

                #如果是后到的,那么filter找不到结果,回滚
                if res == 0:
                    transaction.savepoint_rollback(point)
                    return JsonResponse({'code': 400, 'errmsg': '请重新下单...'})

                #       2.9 累加总数量和总金额
                order_base_obj.total_count += count
                order_base_obj.total_amount += (count * sku.price)
                #       2.10 保存订单商品信息 <--循环外面做

                #   3.更新订单的总金额和总数量
                #BUG:数据库同步问题,sku_id->sku
                try:
                    order_goods_obj = OrderGoods.objects.create(
                        order=order_base_obj,
                        sku=sku,
                        count=count,
                        price=sku.price)
                except Exception as e:
                    print('OrderCommitView.POST:OrderGoods create error!!!')
                    return JsonResponse({'code': 400, 'errmsg': '订单信息生成失败'})
                print('OrderCommitView.POST:OrderGoods create success...')
                print(
                    f'OrderCommitView.POST:order_goods_obj={order_goods_obj}')
                #   4.将redis中选中的商品信息移除出去

                order_base_obj.save()

                #事务的提交点
                # transaction.savepoint_commit(point)
        # 四。返回响应
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'order_id': order_id})


"""
解决高并发产生的超卖问题:
1.队列
2.锁
    悲观锁:查询时直接加锁,别人无法操作,但容易产生死锁现象,采用不多
    死锁例子:
    甲: 1 3 5 7
    乙: 2 4 7 5

    1.甲在操作5结束后查询7被乙锁住
    2.乙在操作7结束后查询5被甲锁住
"""
