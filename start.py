#!/usr/bin/python
# -*- coding: UTF-8 -*-

# import logging

import os
import re
from pathlib import Path

# import MySQLdb


# Create a Django project
def creProject():
    print('Creating Django project...')
    os.system("docker-compose run web django-admin startproject meiduo .")
    path = Path("meiduo")
    if path.exists():
        return True


# Deploy the Project
def depProect():
    os.system("docker-compose up -d")

    # LoadConfig
    #must runing this in linux
    os.system("docker exec meiduo-web-1 bash ./cntDatabase.sh")

    #每次配置文件迁移完等待一段事件后再重启web,BUG:每次重启都会有点问题
    # os.system("docker exec meiduo-web-1 bash -c 'sleep 5s'")

    #数据迁移<----这里估计问题很多
    os.system(
        'docker restart meiduo-web-1 && docker exec meiduo-web-1 bash -c "python manage.py makemigrations && python manage.py migrate"'
    )


# Deploy apps

if __name__ == "__main__":
    res = creProject()
    if res:
        print("\033[0;32 Creating project success.. \033[0m")
    else:
        print("\033[0;31 Creating project error!!! \033[0m")
        exit(1)

    depProect()
