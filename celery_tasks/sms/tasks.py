# 生产者 -- 任务，函数
# 1. 这个函数 必须要让celery的实例的 task装饰器 装饰
# 2. 需要celery 自动检测指定包的任务

from celery_tasks.main import app
from libs.yuntongxun.sms import CCP


@app.task
def celery_send_sms_code(mobile, sms_code):
    print(f"mobile={mobile},sms_code={sms_code}")
    # NOTE:注意实例化
    ccp = CCP()
    ccp.send_template_sms(to=mobile, datas=[sms_code, 1], temp_id=1)
