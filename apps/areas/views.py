from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from apps.areas.models import Area

"""
需求：
    获取省份信息
前端：
    当页面加载的时候，会发送axios请求，来获取 省份信息
后端：
    请求：         不需要请求参数
    业务逻辑：       查询省份信息
    响应：         JSON
    
    路由：         areas/
    步骤：
        1.查询省份信息
        2.将对象转换为字典数据
        3.返回响应
"""


# Create your views here.
class AreaView(View):
    def get(self, request):
        #1.查询省份信息

        # 1.1 如果有缓存直接用数据
        province_list = cache.get('province_list')

        # 1.2 没有缓存则查询数据库
        if province_list is None:
            provinces = Area.objects.filter(parent=None)
            #JsonResponseb不能直接返回对象数据

            #2.将对象转换为json数据-序列化
            province_list = [{
                'id': province.id,
                'name': province.name
            } for province in provinces]
            print("get province_list from db...")

        else:
            print("get province_list from cache...")

        # 保存缓存数据
        cache.set('province_list', province_list, 24 * 3600)

        #3.返回响应
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'province_list': province_list
        })


"""
需求：
    获取市,区信息
前端：
    当页面加载的时候，会发送axios请求，来获取 市,区信息
后端：
    请求：         不需要请求参数
    业务逻辑：       查询省份信息
    响应：         JSON
    
    路由：         areas/<id>/
    步骤：
        1.接收省/市id
        1.根据查询市/区信息信息
        2.将对象转换为字典数据
        3.返回响应
"""


class SubAreaView(View):
    def get(self, request, id):
        # 1.接收省/市id
        # WARINIG:id位过滤

        # 1.根据查询市/区信息信息
        # 1.1先查询缓存,缓存依赖于id
        down_level = cache.get(f'down_level:{id}')
        up_level = None
        if down_level is None:
            #1.2没有缓存查询数据库
            try:
                up_level = Area.objects.get(id=id)  #获取市/区信息
            except Area.DoesNotExist:

                print("get SubArea error!!")
                return JsonResponse({
                    'code': 400,
                    'errmsg': '市/区信息不正确',
                })
            else:
                down_level = up_level.subs.all()
                print("get down_level from db...")
                cache.set(f'down_level:{id}', down_level, 24 * 3600)
        else:
            print('\033[1;32;0mget down_level from cache... \033[0m')

        print("get SubArea success...")
        print(f"up_level={up_level},down_level={down_level}")
        area_list = [{'id': item.id, 'name': item.name} for item in down_level]

        #3.返回响应
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            #路由:this.districts = response.data.sub_data.subs;
            'sub_data': {
                'subs': area_list
            }
        })
