# -*- coding:utf-8 -*-

import time
import json
import base64
from dependent.env_self import Env
from dependent.requests_http import RequestHttp

yaml_file = "../../dependent/env/env.yaml"


# 当有心跳时，会自动更新节点的 running_status（程序运行状态） 为 1（在线）(离线（0: S_OFFLINE）/在线（1: S_ONLINE）)
# 当 AVM_TIMEOUT_INTERVAL 对应的时间内未上报心跳时，更新 running_status 为 0（离线）
class RouteAvmHeartBeat(object):
    def __init__(self):
        self.tunnel_agent_env = dict

    def get_avm_env(self):
        env = Env()
        env.get_env_info(yaml_file)
        self.tunnel_agent_env = env.get_special_env("tunnel_agent")

    def heart_beat(self, avm_id):
        try:
            timestamp = int(time.time())
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
                "sign": RequestHttp().gen_tunnel_sign(timestamp),              # 鉴权sign
                "data": str(timestamp),                                     # 鉴权data
                "wait_response": 5                                   # 等待响应超时时间，单位S，若该值大于0，将等待对应msg_id的响应路由消息
            }
            return data
        except Exception as E:
            print("error is {0}".format(E))

    def main(self):
        self.get_avm_env()
        if isinstance(self.tunnel_agent_env, dict):
            try:
                url = "http://{0}:{1}/tunnel/route".format(self.tunnel_agent_env["remote_ip"], self.tunnel_agent_env["port"])
                for num in range(self.tunnel_agent_env["num_start"], self.tunnel_agent_env["num_end"]):
                    data = self.heart_beat(num)
                    response = RequestHttp().request_response(method="post", url=url, data=data)
                    # print(json.dumps(json.loads(response.text), indent=4))
                    print(json.dumps(json.loads(base64.b64decode(json.loads(response.text)["route"]["body"]).decode()), indent=4))
                    time.sleep(1)
            except Exception as E:
                print("error is {0}".format(E))
        else:
            print("check tunnel_agent_env")


if __name__ == '__main__':
    RouteAvmHeartBeat().main()
