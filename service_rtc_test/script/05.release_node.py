import requests
import random
from dependent.env_self import Env

yaml_file = "../../dependent/env/env.yaml"
pre_url = "http:{0}:{1}/admin/node/release?node_id={2}"
node_id = "shenzhen_mobile_test_{0}"
# 增加一些ip地址
ip_path_one = random.randint(2, 10)
ip_path_two = random.randint(2, 10)
ip = "192.168.{0}.{1}"


class ReleaseNode(object):
    def __init__(self):
        self.rtc_env = dict

    def get_rtc_env(self):
        env = Env()
        env.get_env_info(yaml_file)
        self.rtc_env = env.get_special_env("scheduler")

    def main(self):
        self.get_rtc_env()
        global ip_path_one, ip_path_two
        if isinstance(self.rtc_env, dict):
            try:
                for num in range(self.rtc_env["num_start"], self.rtc_env["num_end"]):
                    if ip_path_two > 255:
                        ip_path_one += 1
                        ip_path_two = random.randint(2, 10)
                    else:
                        ip_path_two += 1

                    headers = {
                        "Content-Type": "application/json",
                        "x-forwarded-for": ip.format(ip_path_one, ip_path_two)
                    }
                    url = pre_url.format(self.rtc_env["remote_ip"], self.rtc_env["ip"], node_id.format(num))
                    response = requests.get(url, headers=headers)
                    print(response.status_code, response.text)
            except Exception as E:
                print("error is {0}".format(E))


if __name__ == '__main__':
    ReleaseNode().main()
