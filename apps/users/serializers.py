import imp

from rest_framework import serializers

from apps.areas.serializers import AreaSerializers
from apps.users.models import Address, User

'''
定义序列化器
class 序列化器名(serializers.Serializer):
    字段名=serializers.类型(选项)

序列化器的使用
obj=models.obj.get(id=id)
data=序列化器名(instance=obj)
'''


class UserSerializers(serializers.Serializer):
    # mobile = serializers.CharField()
    # email = serializers.BooleanField()
    # 外键字段的第一种定义方式
    # 如果我们定义的序列化器外键字段类型为IntegerField
    # 那么,我们定义的序列化器字段名必须和  数据库种的外键字段名一直
    # default_address = serializers.IntegerField()
    id=serializers.IntegerField()


class AddressSerializers(serializers.Serializer):
    user = UserSerializers()
    title = serializers.CharField()
    receiver = serializers.CharField()
    province_id = serializers.IntegerField()
    city_id = serializers.IntegerField()
    district_id = serializers.IntegerField()
    place = serializers.CharField()
    mobile = serializers.CharField()
    tel = serializers.CharField()
    email = serializers.CharField()
    # is_deleted = serializers.BooleanField()

    # 外键字段的第二种定义方式
    # 如果我们期望的外键的key就是模型字段的名字,那么PrimaryKeyRelatedField就可以获取到关联模型的id值
    # queryset 在验证数据的时候,我们要告诉系统,在匹配外键数据
    # from apps.areas.models import Area

    # queryset = Area.objects.all()
    # province = serializers.PrimaryKeyRelatedField(queryset=queryset)
    # city = serializers.PrimaryKeyRelatedField(queryset=queryset)
    # district = serializers.PrimaryKeyRelatedField(queryset=queryset)

    # province = serializers.PrimaryKeyRelatedField(read_only=True)
    # city = serializers.PrimaryKeyRelatedField(read_only=True)
    # district = serializers.PrimaryKeyRelatedField(read_only=True)
