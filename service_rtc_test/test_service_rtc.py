# create_author: HuangYaxing
# create_time: 2021/10/19 8:19 下午

import pytest
import yaml
import requests
import json
from dependent.env_self import Env

yaml_file = "../dependent/env/env.yaml"


class TestServiceRTC(object):
    @pytest.fixture()
    def driver(self):
        env = Env()

        env.get_env_info(yaml_file)
        return env.service_rtc

    # method: GET
    # @pytest.mark.skip(reason="temporarily not running")
    def test_peer_init(self, driver):
        url = "http://{0}:{1}/peer/init".format(driver["remote_ip"], driver["port"])
        response = requests.get(url)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0
        assert check_response["message"] == "ok"
        assert "peerId" in check_response["data"]
        driver["peer_id"] = check_response["data"]["peerId"]

    # method GET
    def test_session_create(self, driver):
        url = "http://{0}:{1}/session/create".format(driver["remote_ip"], driver["port"])
        header = {"userid": "123", "appid": "test"}
        response = requests.get(url, headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0
        assert check_response["message"] == "ok"
        assert "token" in check_response["data"]
        driver["token"] = check_response["data"]["token"]

    def connection_allocate_v2(self, driver):
        # 固定了一些信息，具体修改的地方，我还没有很了解，后续了解后再修改
        url = "http://{0}:{1}/connection/allocate/v2?channel_id=5&package_name=jp.ogapee.onscripter.release&version_code=20210831".format(driver["remote_ip"], driver["port"])
        header = {"Session-Token": driver["token"], "Peer-Id": driver["peer_id"]}
        response = requests.get(url, headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)



if __name__ == '__main__':
    pytest.main(["-s", "test_service_rtc.py"])


