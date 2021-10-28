import json
from dependent.env_self import Env
from dependent.requests_http import RequestHttp


class AvmTag(object):
    def __init__(self):
        self.avm_env = dict

    def get_avm_env(self):
        env = Env()
        env.get_env_info()
        self.avm_env = env.get_special_env("avm_manager")

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
            url = "http://{0}:{1}/v1/avm/tag/add".format(self.avm_env["remote_ip"], self.avm_env["port"])
            headers = {"Content-Type": "application/json"}
            try:
                avm_ids = []
                for num in range(self.avm_env["num_start"], self.avm_env["num_end"]):
                    amv = "shenzhen_mobile_test_" + str(num)
                    avm_ids.append(amv)
                data = self.tag_data(avm_ids)
                response = RequestHttp().request_response(method="post", url=url, data=data, headers=headers)
                print(json.dumps(json.loads(response.text), indent=4))

            except Exception as E:
                print("error is {0}".format(E))


if __name__ == '__main__':
    AvmTag().main()

