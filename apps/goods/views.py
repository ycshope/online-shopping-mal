from importlib.resources import contents
from tokenize import group
from typing import OrderedDict
from unicodedata import category

from amqp import Channel
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from utils.goods import get_breadcrumb, get_categories

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
    def get(self, request, category_id):
        # 1.接收参数
        page = request.GET.get('page')
        page_size = request.GET.get('page_size')
        ordering = request.GET.get('ordering')
        # 过滤参数
        if not all([page, page_size, ordering]):
            return JsonResponse({'code': 400, 'errmsg': '请补全参数'})
        print("get listview param success...")
        print(f"page={page},page_size={page_size},ordering={ordering}")

        # 2.获取分类id
        # 3.根据分类id进行分类数据的查询验证
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except Exception as e:
            print(f"get category error...")
            return JsonResponse({'code': 400, 'errmsg': '请补全参数'})
        print("get category success...")
        print(f"category={category}")

        # 4.获取面包屑数据
        breadcrumb = get_breadcrumb(category)

        # 5.查询分类对应的sku数据，然后排序，然后分页
        from apps.goods.models import SKU
        skus = SKU.objects.filter(category=category,
                                  is_launched=True).order_by(ordering)
        # print(f"skus={skus}")
        #  [<SKU: 16: 华为 HUAWEI P10 Plus 6GB+128GB 曜石黑 移动联通电信4G手机 双卡双待>, <SKU: 15: 华为 HUAWEI P10 Plus 6GB+64GB 曜石黑 移动联通电信4G手机 双卡双待>]
        # 分页
        from django.core.paginator import Paginator

        # object_list,per_page
        # 本质还是skus,只是分了页
        paginator = Paginator(skus, per_page=page_size)

        #获取指定页码的数据
        page_skus = paginator.page(page)
        # print(f"page_skus={page_skus}")
        # <Page 1 of 3>

        sku_list = []
        #将对象转换为字典数据
        # print(f"page_skus.object_list={page_skus.object_list}")
        for sku in page_skus.object_list:
            # print(f"sku={sku.__dict__}")
            #  sku={'_state': <django.db.models.base.ModelState object at 0x7f2a44578ee0>, 
            # 'id': 16,
            #  'create_time': datetime.datetime(2018, 4, 14, 3, 20, 36, 855901, tzinfo=<UTC>),
            #  'update_time': datetime.datetime(2018, 4, 26, 10, 47, 7, 236432, tzinfo=<UTC>),
            #  'name': '华为 HUAWEI P10 Plus 6GB+128GB 曜石黑 移动联通电信4G手机 双卡双待', 
            # 'caption': '666 wifi双天线设计！徕卡人像摄影！P10徕卡双摄拍照，低至2988元！',
            #  'spu_id': 3, 'category_id': 115, 'price': Decimal('3788.00'), 'cost_price': Decimal('3588.00'), 
            # 'market_price': Decimal('3888.00'), 
            # 'stock': 5, 'sales': 0, 'comments': 0, 'is_launched': True, 
            # 'default_image': 'group1/M00/00/02/CtM3BVrRdPeAXNDMAAYJrpessGQ9777651'}
            # meiduo-web-1    
            sku_list.append({
                'id': sku.id,
                'name': sku.name,
                'price': sku.price,
                'default_image_url': sku.default_image.url
            })

        #获取总页码
        total_num = paginator.num_pages

        # 6.返回响应
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'list': sku_list,
            'count': total_num,
            'breadcrumb': breadcrumb
        })

#TODO:热销排名
#基本思路:根据分类来进行销量排名,获取指定字段
