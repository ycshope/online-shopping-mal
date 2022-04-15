import redis
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django_redis import get_redis_connection

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
            #4.登录用户保存redis
            try:
                #4.1 连接redis
                '''
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

    def get(self, request):
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
        })
