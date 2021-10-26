# -*- coding:utf-8 -*-

import time
import json
import base64
from service_rtc_test.script.utils import configHTTP

url = configHTTP.url_prefix_tunnel_agent + '/tunnel/route'

ts = int(time.time())


# 当有心跳时，会自动更新节点的 running_status（程序运行状态） 为 1（在线）(离线（0: S_OFFLINE）/在线（1: S_ONLINE）)
# 当 AVM_TIMEOUT_INTERVAL 对应的时间内未上报心跳时，更新 running_status 为 0（离线）
def heart(avm_id):
    body = {
        "avm_id": "shenzhen_mobile_test_" + str(avm_id),
        # "session_info": {
        #     "session_id": "4b94e85801c742e3aa8bb0ae978ebd9b",
        #     "status": 1         # 0: S_INVALID, 1: S_READY, 2: S_QUEUEING, 3: S_CLOSED, 4: S_BACKGROUND, 5: S_PENDING, 6: S_CLOSING
        # },
        "status": 0,            # 0: S_IDLE, 1: S_SYNCING, 2: S_WAITING_REBOOT, 4: S_WAITING_UPDATE, 128: S_RUNNING
        # "running_status": 1,       # 程序运行状态(在线/离线) 0: S_OFFLINE, 1: S_ONLINE，有心跳更新状态为在线
        "service_status": 1,       # 服务状态 上架/下架/未初始化
        "ipv6": "240e:ff:a010:242:605c:8018:419b:a16a",
        "features": [
            {
                "key": "NFS",
                "val": "enable"
            }
        ],
        "section": "south china",
        # "section": "beijing",
        # "section": "not_exist",
        "apps": [
            {
                "package_name": "jp.ogapee.onscripter.release",
                "version_code": 20210831,
                "md5": "684f32f94fd636d7ab3306c2c77bf28d",
                "owner_id": 143,
                "channel": "5"
            },
            {
                "package_name": "com.bungieinc.bungiemobile",
                "version_code": 158840,
                "md5": "89d4f3557d6943f00b846756ca8e00f9",
                "owner_id": 143,
                "channel": "5"
            }
        ]
    }

    data = {
        "route": {
            "body": base64.b64encode(bytes(json.dumps(body), encoding='utf-8')).decode('utf-8'),
            "rtype": 0,
            "timestamp": int(time.time()),
            "msg_id": str(int(time.time())),
            "to_module": "avm_heartbeat",
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
        data = heart(i)
        c = configHTTP.HTTPRequest(url=url, method='POST', data=data)
        c.send_request()
        time.sleep(1)
