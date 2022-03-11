#/bin/bash
set -e


#1.backup settings
echo "backuping settings.py..."
cp meiduo/settings.py meiduo/settings.py.bak
if [ $? -ne 0 ];then
    echo "\033[31m backup error!! \033[0m"
    exit 1
fi

#2.替换settings.py的内容
echo "setting settings.py..."
cp settings.py.sample settings.py

#2.1.SECRET_KEY
#替换SECRET_KEY
# 正则表达式= SECRET_KEY = '.*'
SECRET_KEY=$(cat meiduo/settings.py | grep "SECRET_KEY = '.*'")
# echo "SECRET_KEY=$SECRET_KEY"
# BUG:如果原始字符包含某些特殊字符(#),那么会无法替换
sed -i "s#/SECRET_KEY = '.*'#/${SECRET_KEY}#" settings.py

#2.2.ROOT_URLCONF,WSGI_APPLICATION->和项目相关
#正则表达式= meiduo 全局模式
# sed -i '3s/composeexample/meiduo/g' settings.py

if [ $? -ne 0 ];then
    echo "\033[31m setting settings.py error!! \033[0m"
    exit 1
fi

echo "copying settings.py to project..."
#3.拷贝文件
cp settings.py meiduo/settings.py
if [ $? -ne 0 ];then
    echo "\033[31m copy settings.py to project error!! \033[0m"
    exit 1
fi
echo "watting 5s restart web..."
exit 0