#0.celery运行 设置django的环境
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meiduo.settings')

#1.创建celery实例
from celery import Celery

# 参数1： main 设置脚本路径就可以了。 脚本路径是唯一的
app = Celery('celery_tasks')

#2.设置broker
#通过加载配置文件来设置broker
app.config_from_object('celery_tasks.config')

#3.需要celery 自动检测指定包的任务
#autodiscover_tasks参数是列表
#列表中的元素是tasks的路径
app.autodiscover_tasks(['celery_tasks.sms'])
