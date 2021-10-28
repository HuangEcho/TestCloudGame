# -*- coding:utf-8 -*-

from dependent import config_HTTP
from dependent.env_self import Env
import time

yaml_file = "../../dependent/env/env.yaml"


class PutOnAvm(object):
    def __init__(self):
        self.avm_env = dict

    def get_avm_env(self):
        env = Env()
        env.get_env_info(yaml_file)
        self.avm_env = env.get_special_env("avm_manager")

    def set_status(self, avm_id):
        data = {
            "request_id": "any id",
            "avm_id": "shenzhen_mobile_test_"+ str(avm_id),
            #"avm_id": "2cfd53351c3f",
            "status": 1     # 服务状态 0：未初始化 1：上架 2：下架
        }
        return data

    def main(self):
        self.get_avm_env()
        if isinstance(self.avm_env, dict):
            headers = {"Content-Type": "application/json"}
            url = "http://{0}:{1}/v1/avm/service_status/set".format(self.avm_env["remote_ip"], self.avm_env["port"])
            try:
                for num in range(self.avm_env["num_start"], self.avm_env["num_end"]):
                    data = self.set_status(num)
                    c = config_HTTP.HTTPRequest(url=url, method='POST', headers=headers, data=data)
                    c.send_request()
                    time.sleep(1)
            except Exception as E:
                print("error is {0}".format(E))


if __name__ == '__main__':
    PutOnAvm().main()

