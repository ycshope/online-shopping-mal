import re
from dataclasses import field

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
    #长度限制
    mobile = serializers.CharField(min_length=11, max_length=11)
    #非必选,值限制
    email_active = serializers.BooleanField(required=False)
    #仅序列化时使用,反序列化时  ->也就是读的时候会读出来,写的时候这个字段不是必填
    id = serializers.IntegerField(read_only=True, min_value=1)

    # 外键字段的第一种定义方式
    # 如果我们定义的序列化器外键字段类型为IntegerField
    # 那么,我们定义的序列化器字段名必须和  数据库种的外键字段名一直
    # default_address = serializers.IntegerField()

    def validate_mobile(self, mobile):
        if re.match('^1[345789]\d{9}$', mobile):
            return mobile
        raise Exception('mobile format error!!!')

    # 更新时必须重写update方法
    def update(self, instance, validated_data):
        # instance 序列化创建时传递的对象
        # validated_data 序列化创建时 验证没有问题的数据

        # get(key,default_value)
        # 如果get的key是一个None,则使用默认值(也就是保存失败)
        instance.mobile = validated_data.get('mobile', instance.mobile)
        try:
            instance.save()
        except Exception as e:
            raise Exception('UserSerializers save error!!!')

        # 返回修改后的对象
        return instance


class AddressSerializers(serializers.Serializer):
    # user = UserSerializers()
    id = serializers.IntegerField()
    title = serializers.CharField()
    receiver = serializers.CharField()
    province = serializers.CharField()
    city = serializers.CharField()
    district = serializers.CharField()
    place = serializers.CharField()
    mobile = serializers.CharField()
    tel = serializers.CharField()
    email = serializers.EmailField()

    def validate_tel(self, tel):
        if re.match('^1[345789]\d{9}$', tel):
            return tel
        raise Exception('tel format error!!!')

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


class UserModelSerializers(serializers.ModelSerializer):
    # 重写mobilecheck
    # mobile = serializers.CharField(min_length=11, max_length=11)

    class Meta:
        model = User
        # fields = '__all__'
        # 显式指定字段
        fields = ['id', 'mobile', 'email_active', 'default_address']

        # 只读字段列表
        # read_only_fields = ['id']

        # 选项设置 <---类似schema
        extra_kwargs = {
            # '字段名' :{'选项':value}
            'mobile': {
                'min_length': 11,
                'max_length': 11
            },
            # 为了防止篡改,仅序列化时输出,属性为read-only
            'id': {
                'read_only': True
            },
            'email_active': {
                'read_only': True
            }
        }


class AddressModelSerializers(serializers.Serializer):
    class Meta:
        model = Address
        fields = '__all__'
        # exculde = ['user']
        # 显式指定字段
        # fields = [
        #     'id', 'title', 'receiver', 'province', 'city', 'district', 'place',
        #     'mobile', 'tel', 'email', 'is_deleted'
        # ]

        # 只读字段列表
        # read_only_fields = ['id', 'is_deleted']
