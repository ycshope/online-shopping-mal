#!/usr/bin/python
# -*- coding: UTF-8 -*-

# import logging

import MySQLdb


def checkDb():
    try:
        print('checking db ....')
        db = MySQLdb.connect(host='db',
                             port=3306,
                             user='meiduo',
                             passwd='meiduo',
                             db='meiduo',
                             charset='utf8')
    except Exception as e:
        print(f"db connect error!:{e}")
        db.close()
        return -1

    db.close()
    return True


if __name__ == "__main__":
    if (checkDb()):
        print("\033[0;32 db check success.. \033[0m")
    else:
        print("\033[0;31 db connect error!!! \033[0m")
