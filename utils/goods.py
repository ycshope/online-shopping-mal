"""
分类数据
"""
from typing import OrderedDict

from apps.goods.models import GoodsCategory, GoodsChannel


#TODO:1.利用缓存提高查询效率 2.代码的逻辑不易维护,需要重构
def get_categories():
    
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
        if group_id not in categories:
            categories[group_id] = {"channels": [], "sub_cats": []}

        #2.3. 取出id,name,url作为一级目录的对象
        category_id = channel.category_id
        # print(f"category_id={category_id}")  # category_id=1

        url = channel.url
        # print(f"url={url}")  #url=http://shouji.jd.com

        try:
            category = GoodsCategory.objects.get(id=category_id)
        except Exception as e:
            print("create channel_obj error!!!")
            # return JsonResponse({'code': 400, 'errmsg': '一级目录名获取失败'})

        name = category.name
        # print(f"name={name}")  #name=手机
        channel_obj = {"id": category_id, "name": name, "url": url}

        print("create channel_obj success...")
        # print(f"channel_obj={channel_obj}")
        categories[group_id]["channels"].append(channel_obj)

        #3.生成二级目录
        #3.1 取出二级目录的id,name
        try:
            cat2_list = GoodsCategory.objects.filter(parent_id=category_id)
        except Exception as e:
            print("create cat2_obj error!!!")
            # return JsonResponse({'code': 400, 'errmsg': '二级目录名获取失败'})

        # print(f"cat2={cat2_list}")
        #cat2=<QuerySet [<GoodsCategory: 手机通讯>, <GoodsCategory: 手机配件>]>

        for cat2 in cat2_list:
            cat2_name = cat2.name
            cat2_id = cat2.id
            cat2_obj = {"id": cat2_id, "name": cat2_name, "sub_cats": []}
            print("create cat2_obj success...")
            print(f"before cat2_obj={cat2_obj}")

            try:
                cat3_list = GoodsCategory.objects.filter(parent_id=cat2_id)
            except Exception as e:
                print("create cat3_obj error!!!")
                # return JsonResponse({'code': 400, 'errmsg': '三级目录名获取失败'})

            # print(f"cat3={cat3_list}")

            #4.生成三级目录
            for cat3 in cat3_list:
                cat3_name = cat3.name
                cat3_id = cat3.id
                cat3_obj = {
                    "id": cat3_id,
                    "name": cat3_name,
                }
                # print("create cat3_obj success...")
                # print(f"cat3_obj={cat3_obj}")
                cat2_obj['sub_cats'].append(cat3_obj)

            # print(f"cat2_obj={cat2_obj}")
            categories[group_id]["sub_cats"].append(cat2_obj)

        # print(f"categories={categories[group_id]}")

    print(f"categories={dict(categories)}")
