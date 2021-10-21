# create_author: HuangYaxing
# create_time: 2021/10/19 8:19 下午

import pytest
import yaml
import requests
import json
import logging
from dependent.env_self import Env

yaml_file = "../dependent/env/env.yaml"


class TestServiceRTC(object):
    # 可以把driver设置为全局变量
    # 抓包看，这里指执行了一次
    @pytest.fixture(scope="class")
    def driver(self):
        env = Env()
        env.get_env_info(yaml_file)
        driver = env.service_rtc
        try:
            if isinstance(driver, dict):
                url = "http://{0}:{1}/peer/init".format(driver["remote_ip"], driver["port"])
                driver["peer_id"] = json.loads(requests.get(url).text)["data"]["peerId"]
                url = "http://{0}:{1}/session/create".format(driver["remote_ip"], driver["port"])
                header = {"userid": "123", "appid": "test"}
                driver["token"] = json.loads(requests.get(url, headers=header).text)["data"]["token"]
        except Exception as E:
            logging.debug("error is {0}".format(E))
        return driver

    # method: GET
    # @pytest.mark.skip(reason="temporarily not running")
    def test_peer_init(self, driver):
        url = "http://{0}:{1}/peer/init".format(driver["remote_ip"], driver["port"])
        response = requests.get(url)
        logging.debug("response status code is {0}, text is {1} ".format(response.status_code, response.text))
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0
        assert check_response["message"] == "ok"
        assert "peerId" in check_response["data"]
        # driver["peer_id"] = check_response["data"]["peerId"]

    # method GET
    def test_session_create(self, driver):
        url = "http://{0}:{1}/session/create".format(driver["remote_ip"], driver["port"])
        header = {"userid": "123", "appid": "test"}
        response = requests.get(url, headers=header)
        logging.debug("response status code is {0}, text is {1} ".format(response.status_code, response.text))
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0
        assert check_response["message"] == "ok"
        assert "token" in check_response["data"]
        # driver["token"] = check_response["data"]["token"]

    # method GET
    def test_connection_allocate_v2(self, driver):
        # 固定了一些信息，具体修改的地方，我还没有很了解，后续了解后再修改
        url = "http://{0}:{1}/connection/allocate/v2?channel_id=5&package_name=jp.ogapee.onscripter.release&version_code=20210831".format(driver["remote_ip"], driver["port"])
        header = {"Session-Token": driver["token"], "Peer-Id": driver["peer_id"]}
        response = requests.get(url, headers=header)
        logging.debug("response status code is {0}, text is {1} ".format(response.status_code, response.text))
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0
        assert check_response["message"] == "ok"
        assert "agentIceServer" in check_response["data"] and "urls" in check_response["data"]["agentIceServer"]
        assert "iceServer" in check_response["data"] and "urls" in check_response["data"]["iceServer"]
        assert check_response["data"]["agentIceServer"]["urls"] == check_response["data"]["iceServer"]["urls"]

    # method GET
    def test_keep_alive(self, driver):
        url = "http://{0}:{1}/session/keepalive".format(driver["remote_ip"], driver["port"])
        header = {"Session-Token": driver["token"]}
        response = requests.get(url, headers=header)
        logging.debug("response status code is {0}, text is {1} ".format(response.status_code, response.text))
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0

    def test_session_close(self, driver):
        url = "http://{0}:{1}/session/create".format(driver["remote_ip"], driver["port"])
        header = {"userid": "123", "appid": "test"}
        token = json.loads(requests.get(url, headers=header).text)["data"]["token"]
        url = "http://{0}:{1}/session/close".format(driver["remote_ip"], driver["port"])
        header = {"Session-Token": token}
        response = requests.get(url, headers=header)
        


if __name__ == '__main__':
    pytest.main(["-s", "test_service_rtc.py"])


