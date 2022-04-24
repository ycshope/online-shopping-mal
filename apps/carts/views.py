from cgi import print_arguments
from select import select
from xmlrpc.client import boolean

import redis
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django_redis import get_redis_connection
from requests import delete

# Create your views here.
"""
1.  京东的网址 登录用户可以实现购物车，未登录用户可以实现购物车      v
    淘宝的网址 必须是登录用户才可以实现购物车
    
2.  登录用户数据保存在哪里？    服务器里        mysql/redis
                                        mysql
                                        redis           学习， 购物车频繁增删改查
                                        mysql+redis
    未登录用户数据保存在哪里？   客户端
                                        cookie      

3.  保存哪些数据？？？
    
    redis:
            user_id,sku_id(商品id),count(数量),selected（选中状态）
    
    cookie:
            sku_id,count,selected,
    
4.  数据的组织

    redis:
            user_id,    sku_id(商品id),count(数量),selected（选中状态）
            
            hash
            user_id:
                    sku_id:count
                    xxx_sku_id:selected
                    
            1：  
                    1:10
                    xx_1: True
                    
                    2:20
                    xx_2: False
                    
                    3:30
                    xx_3: True
            13个地方的空间
            
            进一步优化！！！
            为什么要优化呢？？？
            redis的数据保存在 内存中  我们应该尽量少的占用redis的空间
            
            user_id:
                    sku_id:count
                    
            
            selected 
            
            
            
            user_1:         id:数量
                            1: 10 
                            2: 20
                            3: 30
            记录选中的商品
            1,3
            
            
            
            user_1
                    1: 10 
                    2: 20
                    3: 30
            selected_1: {1,3}
            
            10个空间
            
            
             user_1
                    1: 10 
                    2: -20
                    3: 30
            
            7个空间    
"""
import base64
import json
import pickle

from django.views import View

from apps.goods.models import SKU


def CheckSku_id(sku_id):
    try:
        sku_id = int(sku_id)
    except Exception as e:
        return None
    if sku_id < 0:
        return None

    try:
        sku = SKU.objects.get(id=sku_id)
    except Exception as e:
        return None
    return sku


def CheckCount(count):
    try:
        count = int(count)
    except Exception as e:
        return None
    if count < 0:
        return None
    return count


def CheckSelected(selected):
    try:
        selected = bool(selected)
    except Exception as e:
        return None
    return selected


class CartsView(View):
    """
    前端：
        我们点击添加购物车之后， 前端将 商品id ，数量 发送给后端

    后端：
        请求：         接收参数，验证参数
        业务逻辑：       根据商品id查询数据库看看商品id对不对
                      数据入库
                        登录用户入redis
                            连接redis
                            获取用户id
                            hash
                            set
                            返回响应
                        未登录用户入cookie
                            先有cookie字典
                            字典转换为bytes
                            bytes类型数据base64编码
                            设置cookie
                            返回响应
        响应：         返回JSON
        路由：     POST  /carts/
        步骤：
                1.接收数据
                2.验证数据
                3.判断用户的登录状态
                4.登录用户保存redis
                    4.1 连接redis
                    4.2 操作hash
                    4.3 操作set
                    4.4 返回响应
                5.未登录用户保存cookie
                    5.1 先有cookie字典
                    5.2 字典转换为bytes
                    5.3 bytes类型数据base64编码
                    5.4 设置cookie
                    5.5 返回响应
        """
    def post(self, request):
        #1.接收数据
        #{"sku_id":3,"count":1}
        body_dict = json.loads(request.body.decode())
        print(f"post cart success...")
        print(f"body_dict={body_dict}")

        sku_id = body_dict.get('sku_id')
        count = body_dict.get('count')

        #2.验证数据
        if not all([sku_id, count]):
            print(f"post cart param error!!!")
            return JsonResponse({'code': 400, 'errmsg': '请补全参数'})
        print(f"post cart param success...")
        print(f"sku_id={sku_id},count={count}")

        #2.1 check sku_id
        sku = CheckSku_id(sku_id=sku_id)
        if sku is None:
            print(f"check sku_id error!!!")
            return JsonResponse({
                'code': 400,
                'errmsg': 'sku_id error!!!',
            })

        print(f"check sku_id success...")

        #2.2 TODO:check count
        count = CheckCount(count)
        if count is None:
            print(f"check count error!!!")
            return JsonResponse({
                'code': 400,
                'errmsg': 'count error!!!',
            })

        #3.判断用户的登录状态
        user = request.user
        if user.is_authenticated:
            print(f"logined user opt...")
            # redis:
            # user_id,sku_id(商品id),count(数量),selected（选中状态）

            #4.登录用户保存redis
            try:
                #4.1 连接redis
                '''
                redis:
                    user_id,sku_id(商品id),count(数量),selected（选中状态）
                
                hash
                user_id:
                        sku_id:count
                        xxx_sku_id:selected
                        
                1：  
                        1:10
                '''
                redis_cli = get_redis_connection('carts')
                #4.2 操作hash
                redis_cli.hset(f'carts_{user.id}', sku_id, count)

                #4.3 操作set
                redis_cli.sadd(f'selected_{user.id}', sku_id)
                #4.4 返回响应
            except Exception as e:
                print(f"logined user carts add error!!!")
                return JsonResponse({
                    'code': 400,
                    'errmsg': '加入购物车失败',
                })
            else:
                print(f"logined user carts add success...")
                return JsonResponse({
                    'code': 0,
                    'errmsg': 'ok',
                })
        else:
            print(f"anoyoums user opt...")
            """
                cookie:
                    sku_id,count,selected,
                cookie:
                    {
                        sku_id: {count:xxx,selected:xxxx},
                        sku_id: {count:xxx,selected:xxxx},
                        sku_id: {count:xxx,selected:xxxx},
                    }
        
            """
            #5.未登录用户保存cookie
            # {16： {count:3,selected:True}}
            # 5.0 先读取cookie数据
            cookie_carts = request.COOKIES.get('carts')

            if cookie_carts:
                # 对加密的数据解密
                try:
                    carts = pickle.loads(base64.b64decode(cookie_carts))
                except Exception as e:
                    print(f"cookie_carts decode error!!!")
                    return JsonResponse({
                        'code': 0,
                        'errmsg': 'cookie 错误!!!',
                    })

            else:
                #5.1 先有cookie字典
                carts = {}
            print(f"cookie_carts={carts}")

            # 判断新增的商品 有没有在购物车里
            if sku_id in carts:
                # 购物车中 已经有该商品id
                # 数量累加
                ## {16： {count:3,selected:True}}
                #WARINING:COOKIE可能被篡改
                origin_count = carts[sku_id]['count']
                count += origin_count

            carts[sku_id] = {'count': count, 'selected': True}
            print(f"obj_carts={carts}")

            #5.2 字典转换为bytes
            bytes_carts = pickle.dumps(carts)

            #5.3 bytes类型数据base64编码
            cookie_carts = base64.b64encode(bytes_carts)

            #5.4 设置cookie
            response = JsonResponse({'code': 0, 'errmsg': 'ok'})

            # cookie_carts=b'gASVIAAAAAAAAAB9lEsOfZQojAVjb3VudJRLZIwIc2VsZWN0ZWSUiHVzLg=='
            response.set_cookie('carts',
                                cookie_carts.decode(),
                                max_age=3600 * 24)

            #5.5 返回响应
            return response

    """
        前端:
            提交get请求,并传输cookie
            将商品sku_id,数量,选中状态取出
            cart_skus:{
                sku_id:{
                    price:x
                    count:x
                    selected:
                }
            }
        后端：
            请求:
                接收cookie
            业务逻辑:
                判断用户是否登录,cookie解密后，查询价格
            响应:
                返回sku_id,价格,数量,选中状态

            路由: GET /carts/
            步骤:
                1.判断用户是否登录
                2.用户登录查询redis
                    2.1 操作hash获取skuid
                    2.2 操作hash获取count
                    2.3 操作操作set获取状态sku_id
                3.未登录用户查询cookie
                    3.0 解码,校验数据
                        如果为空返回{}
                    3.1 获取sku_id,count,selected信息
                4.根据商品的skuid查询信息
                    4.1 校验skuid
                    4.3 查询skuid的商品信息
                5.返回数据
        """

    def get(self, request):
        #  1.判断用户是否登录
        user = request.user
        if user.is_authenticated:
            print(f"get user:{user} carts...")

            redis_cli = get_redis_connection('carts')

            #         2.用户登录查询redis
            #             2.1 获取购物车信息 hash
            sku_id_counts = redis_cli.hgetall(f'carts_{user.id}')
            # {b'5': b'10', b'8': b'3'}   解读=> {sku_id1:count1,sku_id2:count2...}
            # print(f"sku_id_counts={sku_id_counts}")

            #             2.2 获取选中信息 set
            selectd_ids = redis_cli.smembers(f'selected_{user.id}')
            # {b'5', b'8'}
            # print(f"selectd_ids={selectd_ids}")

            #             2.3 将格式转换为和cookie一样
            carts = {}
            # cookie_carts={11: {'count': 1, 'selected': True}}
            for btypes_sku_id in sku_id_counts.keys():
                count = sku_id_counts[btypes_sku_id].decode()
                sku_id = int(btypes_sku_id.decode())
                selected = btypes_sku_id in selectd_ids
                # print(f"sku_id={sku_id},count={count},selected={selected}")
                carts[sku_id] = {'count': count, 'selected': selected}
        else:
            print(f"anonymous user")

            cookie_carts = request.COOKIES.get('carts')

            if cookie_carts:
                #3.未登录用户查询cookie
                #3.0 解码,校验数据
                #    如果为空返回{}
                #3.1 获取skuid
                #3.2 获取count
                #3.3 获取状态
                try:
                    carts = pickle.loads(base64.b64decode(cookie_carts))
                except Exception as e:
                    print(f"cookie_carts decode error!!!")
                    return JsonResponse({
                        'code': 0,
                        'errmsg': 'cookie 错误!!!',
                    })

            else:
                carts = {}

        print(f"cookie_carts={carts}")

        # 4.根据商品的skuid查询信息
        sku_ids = carts.keys()

        # 可以遍历查询
        # 也可以用 in
        try:
            #  4.1 TODO:校验sku_id,获取商品信息
            # BUG:skus没有校验
            skus = SKU.objects.filter(id__in=sku_ids)
        except Exception as e:
            print(f"get skus info error!!!")
            return JsonResponse({'code': 0, 'errmsg': 'ok'})

        print(f"query skus info success...")
        print(f"skus={skus}")
        cart_skus = []

        #4.2 取出商品信息
        for sku in skus:
            price = int(sku.price)
            #BUG:数量没有校验,而且存在空指针可能
            count = int(carts[sku.id]['count'])
            amount = price * count
            cart_skus.append({
                'id': sku.id,
                'price': price,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                #BUG:selected没有校验,而且存在空指针可能
                'selected': carts[sku.id]['selected'],  #选中状态
                'count': count,  # 数量 强制转换一下
                'amount': amount  #总价格
            })

        print(f"get skus info success...")
        print(f"cart_skus={cart_skus}")
        #6.返回数据
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'cart_skus': cart_skus,
        })

    #TODO:优化代码,这部分和post基本一样
    def put(self, request):
        #1.接收数据
        #{"sku_id":3,"count":1}
        body_dict = json.loads(request.body.decode())
        print(f"put cart success...")
        print(f"body_dict={body_dict}")

        sku_id = body_dict.get('sku_id')
        count = body_dict.get('count')
        selected = body_dict.get('selected')

        #2.验证数据
        if not all([sku_id, count]):
            print(f"post cart param error!!!")
            return JsonResponse({'code': 400, 'errmsg': '请补全参数'})
        print(f"post cart param success...")
        print(f"sku_id={sku_id},count={count}")

        #2.1 check sku_id
        sku = CheckSku_id(sku_id=sku_id)
        if sku is None:
            print(f"check sku_id error!!!")
            return JsonResponse({
                'code': 400,
                'errmsg': 'sku_id error!!!',
            })

        print(f"check sku_id success...")

        #2.2 TODO:check count
        count = CheckCount(count)
        if count is None:
            print(f"check count error!!!")
            return JsonResponse({
                'code': 400,
                'errmsg': 'count error!!!',
            })

        print(f"check count success...")

        #2.3 check selected
        selected = CheckSelected(selected)
        if count is None:
            print(f"check selected error!!!")
            return JsonResponse({
                'code': 400,
                'errmsg': 'selected error!!!',
            })

        print(f"check selected success...")

        #3.判断用户的登录状态
        user = request.user
        if user.is_authenticated:
            print(f"logined user opt...")

            #3.登录用户保存redis
            try:
                #3.1 连接redis
                redis_cli = get_redis_connection('carts')

                #3.2 操作hash
                redis_cli.hset(f'carts_{user.id}', sku_id, count)

                #3.3 操作set
                #有可能会被删除
                if selected:
                    redis_cli.sadd(f'selected_{user.id}', sku_id)
                else:
                    redis_cli.srem(f'selected_{user.id}', sku_id)

                #3.4 返回响应
            except Exception as e:
                print(f"logined user carts put error!!!")
                return JsonResponse({
                    'code': 400,
                    'errmsg': '加入购物车失败',
                })

            else:
                print(f"logined user carts put success...")
                return JsonResponse({
                    'code': 0,
                    'errmsg': 'ok',
                    'cart_sku': {
                        'count': count,
                        'selected': selected
                    }
                })
        else:
            print(f"anoyoums user opt...")

            #5.未登录用户保存cookie
            # 5.0 先读取cookie数据
            cookie_carts = request.COOKIES.get('carts')

            if cookie_carts:
                # 对加密的数据解密
                try:
                    carts = pickle.loads(base64.b64decode(cookie_carts))
                except Exception as e:
                    print(f"cookie_carts decode error!!!")
                    return JsonResponse({
                        'code': 0,
                        'errmsg': 'cookie 错误!!!',
                    })

            else:
                #5.1 先有cookie字典
                carts = {}

            print("decode cookie success...")
            print(f"cookie_carts={carts}")

            #6.更新数据
            carts[sku_id] = {'count': count, 'selected': selected}

            print("update cookie success...")
            print(f"obj_carts={carts}")

            #7.序列化

            #7.1  dict ->bytes ->base64
            cookie_carts = base64.b64encode(pickle.dumps(carts))

            #7.2 设置cookie
            response = JsonResponse({
                'code': 0,
                'errmsg': 'ok',
                'cart_sku': {
                    'count': count,
                    'selected': selected
                }
            })

            # cookie_carts=b'gASVIAAAAAAAAAB9lEsOfZQojAVjb3VudJRLZIwIc2VsZWN0ZWSUiHVzLg=='
            response.set_cookie('carts',
                                cookie_carts.decode(),
                                max_age=3600 * 24)

            #4.3 返回响应
            return response

    def delete(self, request):
        response = JsonResponse({
                'code': 0,
                'errmsg': 'ok'
                
            })

        #4.3 返回响应
        return response
