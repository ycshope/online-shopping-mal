from fdfs_client.client import Fdfs_client, get_tracker_conf

tracker_conf = get_tracker_conf('utils/fastdfs/client.conf')
client = Fdfs_client(tracker_conf)

#文件上传
result = client.upload_by_filename('./requirements.txt')
print(result)
# {'Group name': b'group1', 'Remote file_id': b'group1/M00/00/00/rBMGZWCeGhqAR_vRAAIAABZebgw.sqlite', 'Status': 'Upload successed.', 'Local file name': './db.sqlite3', 'Uploaded size': '128.00KB', 'Storage IP': b'101.133.225.166'}
# 访问地址即可下载：http://101.133.225.166:8888/group1/M00/00/00/rBMGZWCeGhqAR_vRAAIAABZebgw.sqlite


#文件下载
# result = client.download_to_file('./lqz.sqlite', b'group1/M00/00/00/rBMGZWCeGxaAFWqfAAIAABZebgw.sqlite')
# print(result)


# #文件删除
# result = client.delete_file(b'group1/M00/00/00/rBMGZWCeGhqAR_vRAAIAABZebgw.sqlite')
# print(result)
# ('Delete file successed.', b'group1/M00/00/00/rBMGZWCeGhqAR_vRAAIAABZebgw.sqlite', b'101.133.225.166')

# #列出所有的group信息
# result = client.list_all_groups()
# print(result)
