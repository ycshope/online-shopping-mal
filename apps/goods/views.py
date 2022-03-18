from tokenize import group
from typing import OrderedDict
from unicodedata import category

from amqp import Channel
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from apps.goods.models import GoodsCategory, GoodsChannel, GoodsChannelGroup


# Create your views here.
class IndexView(View):
    #查看商品频道和分类
    def get(self, request):
        # 1.先取出所有的一级category,按照group_id,sequence排序
        categories = OrderedDict()
        channels = GoodsChannel.objects.order_by('group_id', 'sequence')
        #  <QuerySet [<GoodsChannel: 手机>, <GoodsChannel: 相机>, <GoodsChannel: 数码>,
        # <GoodsChannel: 电脑>, <GoodsChannel: 办公>, <GoodsChannel: 家用电器>,
        # <GoodsChannel: 家居>, <GoodsChannel: 家具>, <GoodsChannel: 家装>,
        #  <GoodsChannel: 厨具>, <GoodsChannel: 男装>, <GoodsChannel: 女装>,
        # <GoodsChannel: 童装>, <GoodsChannel: 内衣>, <GoodsChannel: 女鞋>,
        # <GoodsChannel: 箱包>, <GoodsChannel: 钟表>, <GoodsChannel: 珠宝>,
        # <GoodsChannel: 男鞋>, <GoodsChannel: 运动>, '...(remaining elements truncated)...']>
        print("order_by channels sucess...")
        print(f"channels={channels}")

        for channel in channels:
            #2.生成一级目录

            #2.1 取出group_id
            # print(f"channel={channel}")  # channel=手机
            group_id = channel.group_id
            # print(f"group_id={group_id}")  # group_id=1

            #2.2 如果字典没有key=group_id,那就生成新的字典
            # if group_id not in categories:
            #     categories[group_id] = {"channels": [], "sub_cats": []}

            #2.3. 取出id,name,url作为一级目录的对象
            category_id = channel.category_id
            # print(f"category_id={category_id}")  # category_id=1

            url = channel.url
            # print(f"url={url}")  #url=http://shouji.jd.com

            try:
                category = GoodsCategory.objects.get(id=category_id)
            except Exception as e:
                print("create channel_obj error!!!")
                return JsonResponse({'code': 400, 'errmsg': '一级目录名获取失败'})

            name = category.name
            # print(f"name={name}")  #name=手机
            channel_obj = {"id": category_id, "name": name, "url": url}

            print("create channel_obj success...")
            print(f"channel_obj={channel_obj}")
            # categories[group_id]["channels"] =

        return JsonResponse({'code': 0, 'errmsg': 'ok'})
