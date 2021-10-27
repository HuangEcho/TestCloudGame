import time
import json
import base64
from dependent import config_HTTP
from dependent.env_self import Env

yaml_file = "../../dependent/env/env.yaml"


class RouteAvmRegister(object):
    def __init__(self):
        self.avm_env = dict

    def get_avm_env(self):
        env = Env().get_env_info(yaml_file)
        if "tunnel_agent" in env:
            self.avm_env = env["tunnel_agent"]
        else:
            print("avm_manager environment get error")

    def tunnel_route_request(self, avm_id):
        timestamp = int(time.time())
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
            "register_time": timestamp,
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
            "sign": config_HTTP.gen_tunnel_sign(timestamp),              # 鉴权sign
            "data": str(timestamp),                                     # 鉴权data
            "wait_response": 5                                   # 等待响应超时时间，单位S，若该值大于0，将等待对应msg_id的响应路由消息
        }
        return data

    def main(self):
        if isinstance(self.avm_env, dict):
            try:
                url = "http://{0}:{1}/tunnel/route".format(self.avm_env["remote_ip"], self.avm_env["ip"])
                for num in range(self.avm_env["num_start"], self.avm_env["num_end"]):
                    data = self.tunnel_route_request(num)
                    c = config_HTTP.HTTPRequest(url=url, method='POST', data=data)
                    c.send_request()
                    time.sleep(1)
            except Exception as E:
                print("error is {0}".format(E))


if __name__ == '__main__':
    RouteAvmRegister().main()

