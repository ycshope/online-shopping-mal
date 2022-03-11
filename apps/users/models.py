# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    mobile=models.CharField(max_length=11,unique=True,verbose_name='手机号')
    email_active=models.BooleanField(default=False,verbose_name='邮箱状态')

    class Meta:
        db_table = 'tb_users'
        managed = True
        verbose_name = 'User Manager'
        verbose_name_plural = verbose_name
