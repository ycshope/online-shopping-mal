from rest_framework import serializers

'''
定义序列化器
class 序列化器名(serializers.Serializer):
    字段名=serializers.类型(选项)

序列化器的使用
obj=models.obj.get(id=id)
data=序列化器名(instance=obj)
'''

class AreaSerializers(serializers.Serializer):
    name = serializers.CharField()
    parent = serializers.CharField()
