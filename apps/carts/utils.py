from django.http import JsonResponse
from django_redis import get_redis_connection

from apps.carts.views import (checkCount, checkSelected, checkSku_id,
                              cookieCarts2Carts)


def mergeCookie2Redis(request):
    '''
    需求:
        登陆时,将cookie数据合并到redis
    
    步骤:
        1.读取cookie数据
        2.初始化一个字典:用于存储skuid,selected
        3.将购物车内容取出
        4.将字典数据添加到redis中  <------这样性能上来说可能更优化,通过hmset
        5.删除cookie
    '''
    # 1.读取cookie数据
    cookie_carts = cookieCarts2Carts(request=request)

    if cookie_carts is None:
        print(f"cookie_carts decode error!!!")
        print(f"mergeCookie2Redis:get cookie_carts error!!!")
        return JsonResponse({
            'code': 400,
            'errmsg': 'cookie 错误!!!',
        })

    print(f"mergeCookie2Redis:get cookie_carts success...")
    # 如果购物车为空直接提前返回
    if cookie_carts == {}:
        print(f"mergeCookie2Redis:there is no cart in cookie_carts...")
        return JsonResponse({'code': 0, 'errmsg': 'ok'})

    print(f"mergeCookie2Redis:cookie_carts={cookie_carts}")
    # {5: {'count': 3, 'selected': True}}

    # 2.遍历cookie
    for carts in cookie_carts:
        sku_id = checkSku_id(carts)
        if sku_id is None:
            print(f"mergeCookie2Redis:get carts")
            return JsonResponse({
                'code': 400,
                'errmsg': 'skuid error!!!',
            })
        
        # 2.1 取出:skuid,selected
        count = cookie_carts[sku_id].get('count')
        count = checkCount(count)
        if count is None:
            print(f"mergeCookie2Redis:check count error!!!")
            return JsonResponse({
                'code': 400,
                'errmsg': 'count error!!!',
            })
        
        selected = cookie_carts[sku_id].get('selected')
        selected = checkSelected(selected)
        if selected is None:
            print(f"mergeCookie2Redis:check selected error!!!")
            return JsonResponse({
                'code': 400,
                'errmsg': 'selected error!!!',
            })

        print(f"skuid={sku_id},count={count},selected={selected}")

        # 3.将字典数据添加到redis中
        try:
            user = request.user

            redis_cli = get_redis_connection('carts')
            pipeline = redis_cli.pipeline()

            #3.1 操作hash
            pipeline.hset(f'carts_{user.id}', sku_id, count)

            #3.2 操作set
            #有可能会被删除
            if selected:
                pipeline.sadd(f'selected_{user.id}', sku_id)
            else:
                pipeline.srem(f'selected_{user.id}', sku_id)

        except Exception as e:
            print(f"mergeCookie2Redis:logined user carts put error!!!")
            return JsonResponse({
                'code': 400,
                'errmsg': '加入购物车失败',
            })

    print(f"mergeCookie2Redis:merge cookie to redis success...")

    # 5.删除cookie
    response=JsonResponse({'code': 0, 'errmsg': 'ok'})
    try:
        #删除信息cookie和添加到redis必须同时成功
        response.delete_cookie('carts')
        pipeline.execute()
    except Exception as e:
        print("mergeCookie2Redis:remove carts from cookie error!!!")
    
    print("mergeCookie2Redis:remove carts from cookie success...")
    return response
