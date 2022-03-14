from abc import abstractclassmethod

from django.db import models


class BaseModel(models.Model):
    #为模型补充字段
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_time = models.DateTimeField(auto_now_add=True, verbose_name="更新时间")

    class Meta:
        abstract = True #说明是抽象基类模型,用于继承使用,数据库迁移时不会创建basemodel的表
