import time
import json
import base64
from dependent.env_self import Env
from dependent.requests_http import RequestHttp


class RouteAvmRegister(object):
    def __init__(self):
        self.tunnel_agent_env = dict

    def get_avm_env(self):
        env = Env()
        env.get_env_info()
        self.tunnel_agent_env = env.get_special_env("tunnel_agent")

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
            "sign": RequestHttp().gen_tunnel_sign(timestamp),              # 鉴权sign
            "data": str(timestamp),                                     # 鉴权data
            "wait_response": 5                                   # 等待响应超时时间，单位S，若该值大于0，将等待对应msg_id的响应路由消息
        }
        return data

    def main(self):
        self.get_avm_env()
        if isinstance(self.tunnel_agent_env, dict):
            try:
                url = "http://{0}:{1}/tunnel/route".format(self.tunnel_agent_env["remote_ip"], self.tunnel_agent_env["port"])
                for num in range(self.tunnel_agent_env["num_start"], self.tunnel_agent_env["num_end"]):
                    data = self.tunnel_route_request(num)
                    response = RequestHttp().request_response(url=url, method="post", data=data)
                    # response = requests.post(url, data=json.dumps(data))
                    # print(json.dumps(json.loads(response.text), indent=4))
                    # print(json.dumps(json.loads(base64.b64decode(json.loads(response.text)["route"]["body"]).decode()),
                    #                  indent=4))
                    time.sleep(1)
            except Exception as E:
                print("error is {0}".format(E))
        else:
            print("check tunnel_agent_env")


if __name__ == '__main__':
    RouteAvmRegister().main()