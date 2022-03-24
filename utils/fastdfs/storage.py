from django.core.files.storage import Storage

# 1.你自定义的存储系统必须为 Django.core.files.storage.Storage:: 的一个子类。
# 2.Django必须能以无参数实例化你的存储系统。意味着所有设置都应从``dango.conf.settings``中获取:
# 3.在你的存储类中，除了其他自定义的方法外，还必须实现 _open() 以及 _save() 方法。关于这些方法，详情请查看下面的信息。
# 另外，如果你的类提供了本地文件存储，它必须重载 path() 方法。


# 4.您的存储类必须是：ref：deconstructible，以便在迁移中的字段上使用它时可以序列化。 只要你的字段有自己的参数：ref：serializable，你可以使用django.utils.deconstruct.deconstructible类装饰器（这是Django在FileSystemStorage上使用的）
class MyStorage(Storage):
    def _open(self, name, mode='rb'):
        pass

    def _save(self, name, content):
        pass

    def url(self, name):
        # return "meiduo-fdfs-tracker-1:8888/"+name
        return "http://image.meiduo.site:8888/"+name
