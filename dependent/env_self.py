# create_author: HuangYaxing
# create_time: 2021/10/19 8:23 下午

import yaml
import os
yaml_path = os.path.join(os.getcwd(), os.path.join("env", "env.yaml"))


class Env(object):
    def __init__(self):
        self.config = dict
        self.env = dict

    def get_env_info(self, yaml_file=yaml_path):
        with open(yaml_file, "r") as f:
            self.config = yaml.safe_load(f)
            if "environment" in self.config:
                self.env = self.config["environment"]
                # print(self.env)


if __name__ == '__main__':
    Env().get_env_info()

