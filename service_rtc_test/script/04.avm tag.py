# -*- coding:utf-8 -*-

from dependent import config_HTTP
from dependent.env_self import Env

yaml_file = "../../dependent/env/env.yaml"


class AvmTag(object):
    def __init__(self):
        self.avm_env = dict

    def get_avm_env(self):
        env = Env().get_env_info(yaml_file)
        if "avm_manager" in env:
            self.avm_env = env["avm_manager"]
        else:
            print("avm_manager environment get error")

    def tag_data(self, avm_ids):
        data = {
            "request_id": "any id",
            "avm_ids": avm_ids,
            "tags": [
                "douyin",
                "not normal"
            ]
        }
        return data

    def main(self):
        self.get_avm_env()
        if isinstance(self.avm_env, dict):
            url = "http://{0}:{1}/v1/avm/tag/add".format(self.avm_env["remote_ip"], self.avm_env["ip"])
            headers = {"Content-Type": "application/json"}
            try:
                avm_ids = []
                for num in range(self.avm_env["num_start"], self.avm_env["num_end"]):
                    amv = "shenzhen_mobile_test_" + str(num)
                    avm_ids.append(amv)
                data = self.tag_data(avm_ids)
                c = config_HTTP.HTTPRequest(url=url, method='POST', headers=headers, data=data)
                c.send_request()

            except Exception as E:
                print("error is {0}".format(E))


if __name__ == '__main__':
    AvmTag().main()

