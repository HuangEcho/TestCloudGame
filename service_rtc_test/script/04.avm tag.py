# -*- coding:utf-8 -*-

from service_rtc_test.script.utils import configHTTP

url = configHTTP.url_prefix_avm_manager + '/v1/avm/tag/add'

headers = {
    "Content-Type": "application/json"
}
avm_ids = []
for i in range(0, 200):
    amv = "shenzhen_mobile_test_"+ str(i)
    avm_ids.append(amv)

data = {
    "request_id": "any id",
    "avm_ids": avm_ids,
    "tags": [
        "douyin",
        "not normal"
    ]
}


if __name__ == '__main__':
    c = configHTTP.HTTPRequest(url=url, method='POST', headers=headers, data=data)
    c.send_request()

