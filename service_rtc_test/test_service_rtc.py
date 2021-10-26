# create_author: HuangYaxing
# create_time: 2021/10/19 8:19 下午

import pytest
import requests
import json
import random
import logging
from dependent.env_self import Env

log = logging.getLogger("test_service_rtc")
yaml_file = "../dependent/env/env.yaml"
# 增加一些ip地址
ip_path_one = random.randint(2, 10)
ip_path_two = random.randint(0, 50)
for_ip = "192.168.{0}.{1}"


class TestServiceRTC(object):
    # 可以把driver设置为全局变量
    # 抓包看，这里指执行了一次
    @pytest.fixture(scope="function")
    def driver(self):
        env = Env()
        env.get_env_info(yaml_file)
        driver = env.service_rtc
        global ip_path_one, ip_path_two
        if ip_path_two >= 255:
            ip_path_one += 1
            ip_path_two = random.randint(0, 50)
        else:
            ip_path_two += 1
        try:
            if isinstance(driver, dict):
                driver["x-forwarded-for"] = for_ip.format(ip_path_one, ip_path_two)
                url = "http://{0}:{1}/peer/init".format(driver["remote_ip"], driver["port"])
                header = {"x-forwarded-for": driver["x-forwarded-for"]}
                driver["peer_id"] = json.loads(requests.get(url, headers=header).text)["data"]["peerId"]
                url = "http://{0}:{1}/session/create".format(driver["remote_ip"], driver["port"])
                header = {"userid": "123", "appid": "test", "x-forwarded-for": driver["x-forwarded-for"]}
                driver["token"] = json.loads(requests.get(url, headers=header).text)["data"]["token"]

                # 要先绑定，才能获取session
                url = "http://{0}:{1}/connection/allocate/v2?channel_id=5&package_name=jp.ogapee.onscripter.release&version_code=20210831".format(
                    driver["remote_ip"], driver["port"])
                header = {"Session-Token": driver["token"], "Peer-Id": driver["peer_id"],
                          "x-forwarded-for": driver["x-forwarded-for"]}
                requests.get(url, headers=header)
                url = "http://{0}:{1}/admin/connection/get?sessionToken={2}".format(driver["remote_ip"], driver["port"],
                                                                                    driver["token"])
                header = {"x-forwarded-for": driver["x-forwarded-for"]}
                driver["node_id"] = json.loads(requests.get(url, headers=header).text)["data"]["connection"]["nodeId"]

        except Exception as E:
            log.debug("error is {0}".format(E))
        print(driver)
        yield driver
        # close session, 以防万一，就算失败也有一个保底的close
        if "token" in driver:
            url = "http://{0}:{1}/session/close".format(driver["remote_ip"], driver["port"])
            header = {"Session-Token": driver["token"], "x-forwarded-for": driver["x-forwarded-for"]}
            requests.get(url, headers=header)

    # method: GET
    # @pytest.mark.skip(reason="temporarily not running")
    def test_peer_init(self, driver):
        url = "http://{0}:{1}/peer/init".format(driver["remote_ip"], driver["port"])
        header = {"x-forwarded-for": driver["x-forwarded-for"]}
        response = self.request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0
        assert check_response["message"] == "ok"
        assert "peerId" in check_response["data"]

    # method GET
    def test_session_create(self, driver):
        url = "http://{0}:{1}/session/create".format(driver["remote_ip"], driver["port"])
        header = {"userid": "123", "appid": "test", "x-forwarded-for": driver["x-forwarded-for"]}
        response = self.request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0
        assert check_response["message"] == "ok"
        assert "token" in check_response["data"]

    def test_session_create_no_userid(self, driver):
        url = "http://{0}:{1}/session/create".format(driver["remote_ip"], driver["port"])
        header = {"appid": "test", "x-forwarded-for": driver["x-forwarded-for"]}
        response = self.request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "invalid params" in check_response["message"]

    def test_session_create_no_appid(self, driver):
        url = "http://{0}:{1}/session/create".format(driver["remote_ip"], driver["port"])
        header = {"userid": "123", "x-forwarded-for": driver["x-forwarded-for"]}
        response = self.request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "invalid params" in check_response["message"]

    def test_session_create_no_header(self, driver):
        url = "http://{0}:{1}/session/create".format(driver["remote_ip"], driver["port"])
        header = {"x-forwarded-for": driver["x-forwarded-for"]}
        response = self.request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "invalid params" in check_response["message"]

    # method GET
    def test_connection_allocate_v2(self, driver):
        # 固定了一些信息，具体修改的地方，我还没有很了解，后续了解后再修改
        url = "http://{0}:{1}/connection/allocate/v2?channel_id=5&package_name=jp.ogapee.onscripter.release&version_code=20210831".format(
            driver["remote_ip"], driver["port"])
        header = {"Session-Token": driver["token"], "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = self.request_response(url=url, method="get", headers=header)
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
        header = {"Session-Token": driver["token"], "x-forwarded-for": driver["x-forwarded-for"]}
        response = self.request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0

    # method POST
    def test_sdk_info(self, driver):
        url = "http://{0}:{1}/sdk/info".format(driver["remote_ip"], driver["port"])
        header = {"Session-Token": driver["token"], "x-forwarded-for": driver["x-forwarded-for"]}
        data = {"sdk_version": "test_1.0.0", "sdk_type": "android", "os": "android 10"}
        response = self.request_response(url=url, method="post", headers=header, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0

    # method GET
    def test_admin_connection_get(self, driver):
        url = "http://{0}:{1}/admin/connection/get?sessionToken={2}".format(driver["remote_ip"], driver["port"],
                                                                            driver["token"])
        header = {"x-forwarded-for": driver["x-forwarded-for"]}
        response = self.request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0

    # 自己生成一个sessionid，再去close
    def test_session_close(self, driver):
        url = "http://{0}:{1}/peer/init".format(driver["remote_ip"], driver["port"])
        header = {"x-forwarded-for": driver["x-forwarded-for"]}
        peer_id = json.loads(requests.get(url, headers=header).text)["data"]["peerId"]
        # 获取一个token
        url = "http://{0}:{1}/session/create".format(driver["remote_ip"], driver["port"])
        header = {"userid": "123", "appid": "test", "x-forwarded-for": driver["x-forwarded-for"]}
        token = json.loads(requests.get(url, headers=header).text)["data"]["token"]

        # 要先绑定，才能获取session
        url = "http://{0}:{1}/connection/allocate/v2?channel_id=5&package_name=jp.ogapee.onscripter.release&version_code=20210831".format(
            driver["remote_ip"], driver["port"])
        header = {"Session-Token": token, "Peer-Id": peer_id, "x-forwarded-for": driver["x-forwarded-for"]}
        requests.get(url, headers=header)

        url = "http://{0}:{1}/session/close".format(driver["remote_ip"], driver["port"])
        header = {"Session-Token": token, "x-forwarded-for": driver["x-forwarded-for"]}
        response = self.request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0

    # method POST
    def test_admin_agent_msg_closed(self, driver):
        url = "http://{0}:{1}/admin/agent/msg".format(driver["remote_ip"], driver["port"])
        header = {"sessionToken": driver["token"], "x-forwarded-for": driver["x-forwarded-for"]}
        data = {"node_id": driver["node_id"],
                "data": {"type": "closed", "session_id": driver["token"], "reason": "test", "code": 1}}
        response = self.request_response(url=url, method="post", headers=header, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0

    def request_response(self, **kwargs):
        # 暂时只写两种方法，如果有新增的，再增加，都保证至少有url和headers
        try:
            if "method" in kwargs:
                if kwargs["method"] == "get":
                    response = requests.get(url=kwargs["url"], headers=kwargs["headers"])
                elif kwargs["method"] == "post":
                    response = requests.post(url=kwargs["url"], data=json.dumps(kwargs["data"]),
                                             headers=kwargs["headers"])
                else:
                    response = "error method"
                if isinstance(response, dict):
                    log.debug("response status_code is {0}, response text is {1}".format(response["status_code"],
                                                                                         response["text"]))
                return response
        except Exception as E:
            print("error is {0}".format(E))


if __name__ == '__main__':
    pytest.main(["-s", "test_service_rtc.py"])
