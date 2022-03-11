from django.urls.converters import register_converter


#定义转换器
class UsernameConverter:
    regex = '[a-zA-Z0-9-]{5,20}'

    def to_python(self, value):
        return value

class UUIDConverter:
    regex = '[\w-]+'

    def to_python(self, value):
        return str(value)
