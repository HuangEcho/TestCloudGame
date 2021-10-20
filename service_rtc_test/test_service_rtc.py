# create_author: HuangYaxing
# create_time: 2021/10/19 8:19 下午

import pytest
import yaml
import requests
from dependent.env_self import Env


class TestServiceRTC(object):
    def __init__(self):
        env = Env()
        env.get_env_info()
        self.port = env.service_rtc["port"]
        self.remote_ip = env.service_rtc["remote_ip"]

    # method: GET
    def test_peer_init(self):
        url = "http://{0}:{1}/peer/init".format(self.remote_ip, self.port)
        response = requests.get(url)
        assert response.code == 200

