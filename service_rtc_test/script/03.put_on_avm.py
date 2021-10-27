# -*- coding:utf-8 -*-

from dependent import configHTTP
import time

url = configHTTP.url_prefix_avm_manager + '/v1/avm/service_status/set'

headers = {
    "Content-Type": "application/json"
}


def setStatus(avm_id):
    data = {
        "request_id": "any id",
        "avm_id": "shenzhen_mobile_test_"+ str(avm_id),
        #"avm_id": "2cfd53351c3f",
        "status": 1     # 服务状态 0：未初始化 1：上架 2：下架
    }
    return data


if __name__ == '__main__':
    for i in range(0, 200):
        data = setStatus(i)
        c = configHTTP.HTTPRequest(url=url, method='POST', headers=headers, data=data)
        c.send_request()
        time.sleep(1)

