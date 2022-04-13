from django.shortcuts import render

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
            
            7个空间    """