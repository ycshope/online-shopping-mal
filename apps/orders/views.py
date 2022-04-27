from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
# Create your views here.
from django.views import View
from django_redis import get_redis_connection
from utils.view import LoginRequiredJSONMixin

from apps.goods.models import SKU

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
