from importlib.resources import contents
from tokenize import group
from typing import OrderedDict
from unicodedata import category

from amqp import Channel
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from utils.goods import get_categories

from apps.contents.models import ContentCategory
from apps.goods.models import GoodsCategory, GoodsChannel, GoodsChannelGroup


# Create your views here.
class IndexView(View):
    #查看商品频道和分类
    def get(self, request):
        #首页的数据:1.商品分类数 2.广告数据
        categories = get_categories()
        contents = {}
        contents_categories = ContentCategory.objects.all()
        for cat in contents_categories:
            contents[cat.key] = cat.content_set.filter(
                status=True).order_by('sequence')

        #首页的静态化后面做
        context = {'categories': categories, 'contents': contents}

        return render(request, 'index.html', context)

"""
需求：
        根据点击的分类，来获取分类数据（有排序，有分页）
前端：
        前端会发送一个axios请求， 分类id 在路由中， 
        分页的页码（第几页数据），每页多少条数据，排序也会传递过来
后端：
    请求          接收参数
    业务逻辑       根据需求查询数据，将对象数据转换为字典数据
    响应          JSON

    路由      GET     /list/category_id/skus/
    步骤
        1.接收参数
        2.获取分类id
        3.根据分类id进行分类数据的查询验证
        4.获取面包屑数据
        5.查询分类对应的sku数据，然后排序，然后分页
        6.返回响应
"""
class ListView(View):
    def get(self,request,category_id):
        pass
