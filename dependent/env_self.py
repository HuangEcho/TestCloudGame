# create_author: HuangYaxing
# create_time: 2021/10/19 8:23 下午

import yaml
import os
yaml_path = os.path.join(os.getcwd(), os.path.join("env", "env.yaml"))


class Env(object):
    def __init__(self):
        self.config = dict
        self.env = dict
        self.special_env = dict

    def get_env_info(self, yaml_file=yaml_path):
        with open(yaml_file, "r") as f:
            self.config = yaml.safe_load(f)
            if "environment" in self.config:
                self.env = self.config["environment"]
                # print(self.env)

    def get_special_env(self, special_name):
        # self.get_env_info()
        if special_name in self.env:
            self.special_env = self.env[special_name]
        else:
            print("{0} environment get error".format(special_name))
        return self.special_env


if __name__ == '__main__':
    Env().get_env_info()

