import json
from dependent.env_self import Env
from dependent.requests_http import RequestHttp

yaml_file = "../../dependent/env/env.yaml"


class PutOnAvm(object):
    def __init__(self):
        self.avm_env = dict

    def get_avm_env(self, file_name=yaml_file):
        env = Env()
        env.get_env_info(file_name)
        self.avm_env = env.get_special_env("avm_manager")

    def set_status(self, avm_id):
        data = {
            "request_id": "any id",
            "avm_id": "shenzhen_mobile_test_{0}".format(avm_id),
            #"avm_id": "2cfd53351c3f",
            "status": 1     # 服务状态 0：未初始化 1：上架 2：下架
        }
        return data

    def main(self, file_name=yaml_file):
        self.get_avm_env(file_name)
        if isinstance(self.avm_env, dict):
            headers = {"Content-Type": "application/json"}
            # 这个接口似乎允许高并发，不会因为频繁请求而拒绝
            url = "http://{0}:{1}/v1/avm/service_status/set".format(self.avm_env["remote_ip"], self.avm_env["port"])
            try:
                for num in range(self.avm_env["num_start"], self.avm_env["num_end"]):
                    data = self.set_status(num)
                    response = RequestHttp().request_response(method="post", url=url, data=data, headers=headers)
                    print(json.dumps(json.loads(response.text), indent=4))
            except Exception as E:
                print("error is {0}".format(E))


if __name__ == '__main__':
    PutOnAvm().main()

