# create_author: HuangYaxing
# create_time: 2021/10/19 8:23 下午

import yaml

yaml_path = "env/env.yaml"


class Env(object):
    def __init__(self):
        self.config = ""

        self.service_rtc = dict

        self.token = ""
        self.peer_id = ""

    def get_env_info(self, yaml_file=yaml_path):
        with open(yaml_file, "r") as f:
            config = yaml.safe_load(f)
            self.config = config
            if "service_rtc" in config:
                self.service_rtc = config["service_rtc"]


if __name__ == '__main__':

    Env().get_env_info()

