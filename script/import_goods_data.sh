#!/bin/bash
#NOTE:web没有部署mysql,所以只能去mysql容器直接执行
mysql -uroot -pmysql meiduo < goods_data.sql
