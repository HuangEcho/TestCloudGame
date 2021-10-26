# -*- coding:utf-8 -*-

import time
import json
import base64
from service_rtc_test.script.utils import configHTTP

url = configHTTP.url_prefix_tunnel_agent + '/tunnel/route'

ts = int(time.time())


def reg(avm_id):
    body = {
        # "avm_id": ":".join(["%02x".upper() % x for x in map(lambda x: random.randint(0, 255), range(6))]),
        "avm_id": "shenzhen_mobile_test_" + str(avm_id),
        "avm_name": "nanning_telecom",
        "rom_ver": "3.4.425",
        "local_ip": "192.168.66.23",
        "host_ip": "202.103.228.231",    # 202.103.228.231 南宁电信
        "section": "south china",
        "android_ver": "7.1",
        "model": "rk3399",
        "generation": "3g",
        "feature": "[{\"key\":\"NFS\",\"val\":\"enable\"}]",
        "ipv6": "",
        "status": 1,
        "register_time": ts,
        "unregister_time": 0
    }

    data = {
        "route": {
            "body": base64.b64encode(bytes(json.dumps(body), encoding='utf-8')).decode('utf-8'),
            "rtype": 0,
            "timestamp": int(time.time()),
            "msg_id": str(int(time.time())),
            "to_module": "avm_register",
            "from_module": "tunnel_agent",
            "to": "avm_manager_json",
            "from": "tunnel_agent"
            },
        "sign": configHTTP.gen_tunnel_sign(ts),              # 鉴权sign
        "data": str(ts),                                     # 鉴权data
        "wait_response": 5                                   # 等待响应超时时间，单位S，若该值大于0，将等待对应msg_id的响应路由消息
    }
    return data


if __name__ == '__main__':
    for i in range(0, 200):
        data = reg(i)
        c = configHTTP.HTTPRequest(url=url, method='POST', data=data)
        c.send_request()
        time.sleep(1)

