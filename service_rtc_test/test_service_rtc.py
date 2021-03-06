# create_author: HuangYaxing
# create_time: 2021/10/19 8:19 下午

import pytest
import requests
import json
import random
import re
import time
import sys
import logging
import allure
from dependent.env_self import Env
from dependent.requests_http import RequestHttp


logger = logging.getLogger(__name__)
# 增加一些ip地址
ip_path_one = random.randint(2, 10)
ip_path_two = random.randint(2, 10)
for_ip = "192.168.{0}.{1}"
package_info = "channel_id=auto_test&package_name=com.cnvcs.junqi&version_code=151"


@allure.feature("service_rtc")
@allure.story("service_rtc-接口测试")
@allure.suite("service_rtc-接口测试")
class TestServiceRTC(object):

    @pytest.fixture(scope="session")
    def driver(self):
        logger.info("test case setup")
        env = Env()
        env.get_env_info()
        driver = env.env["service_rtc"]
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

        except Exception as E:
            logger.error("error is {0}".format(E))
        logger.debug("test case driver info is {0}".format(driver))
        yield driver
        # close session, 以防万一，就算失败也有一个保底的close
        if "token" in driver:
            self.close_session(driver, driver["token"])
            logger.debug("close session")
        logger.info("test case teardown")

    @pytest.fixture()
    def session_teardown(self, driver):
        # 暂时不需要前置条件
        yield
        if "token" in driver:
            self.close_session(driver, driver["token"])
            del driver["token"]

    # method: GET
    def test_peer_init(self, driver):
        logger.info("test_peer_init start")
        url = "http://{0}:{1}/peer/init".format(driver["remote_ip"], driver["port"])
        header = {"x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0
        assert check_response["message"] == "ok"
        assert "peerId" in check_response["data"]
        # 判断每次init生成的peer_id都不一样
        peer_id = check_response["data"]["peerId"]
        assert peer_id not in driver["peer_id"] or len(peer_id) != len(driver["peer_id"])

    # method GET
    def test_session_create(self, driver):
        logger.info("test_session_create start")
        url = "http://{0}:{1}/session/create".format(driver["remote_ip"], driver["port"])
        url = url + '?device_user={"auto_test2021":"auto_test"}'
        header = {"userid": "1", "appid": "auto_test", "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0
        assert check_response["message"] == "ok"
        assert "token" in check_response["data"]

    def test_session_create_without_device_user(self, driver):
        logger.info("test_session_create_without_device_user start")
        url = "http://{0}:{1}/session/create".format(driver["remote_ip"], driver["port"])
        header = {"userid": "1", "appid": "auto_test", "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0
        assert check_response["message"] == "ok"
        assert "token" in check_response["data"]

    def test_session_create_without_userid(self, driver):
        logger.info("test_session_create_without_userid start")
        url = "http://{0}:{1}/session/create".format(driver["remote_ip"], driver["port"])
        url = url + '?device_user={"auto_test":"auto_test"}'
        header = {"appid": "auto_test", "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "invalid params" in check_response["message"]

    def test_session_create_without_appid(self, driver):
        logger.info("test_session_create_without_appid start")
        url = "http://{0}:{1}/session/create".format(driver["remote_ip"], driver["port"])
        url = url + '?device_user={"auto_test":"auto_test"}'
        header = {"userid": "1", "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "invalid params" in check_response["message"]

    def test_session_create_without_userid_or_appid(self, driver):
        logger.info("test_session_create_without_userid_or_appid start")
        url = "http://{0}:{1}/session/create".format(driver["remote_ip"], driver["port"])
        url = url + '?device_user={"auto_test":"auto_test"}'
        header = {"x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "invalid params" in check_response["message"]

    def test_session_create_userid_not_int(self, driver):
        logger.info("test_session_create_userid_not_int start")
        url = "http://{0}:{1}/session/create".format(driver["remote_ip"], driver["port"])
        url = url + '?device_user={"auto_test":"auto_test"}'
        header = {"userid": "1", "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "invalid params" in check_response["message"]

    # method GET
    def test_connection_allocate_v2(self, driver, session_teardown):
        # 使用已上线的一个游戏包信息
        logger.info("test_connection_allocate_v2 start")
        token = self.get_token(driver, "test_connection_allocate_v2")
        url = "http://{0}:{1}/connection/allocate/v2?{2}".format(
            driver["remote_ip"], driver["port"], package_info)
        header = {"Session-Token": token, "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        # 已防万一，如果code为0，有返点，则需要close_session
        if check_response["code"] == 0:
            driver["token"] = token
        assert check_response["code"] == 0
        assert check_response["message"] == "ok"
        assert "agentIceServer" in check_response["data"] and "urls" in check_response["data"]["agentIceServer"]
        assert "iceServer" in check_response["data"] and "urls" in check_response["data"]["iceServer"]
        assert check_response["data"]["agentIceServer"]["urls"] == check_response["data"]["iceServer"]["urls"]
        assert "pooling" in check_response["data"]
        # self.close_session(driver, token)

    # method GET
    def test_connection_allocate_v2_token_invalid(self, driver, session_teardown):
        logger.info("test_connection_allocate_v2_token_invalid start")
        disposable_token = "ad31c761727fbcd2643c73fd32235a6a60a780d43a94dd2e02998ab3a9bea41b"
        url = "http://{0}:{1}/connection/allocate/v2?{2}".format(
            driver["remote_ip"], driver["port"], package_info)
        header = {"Session-Token": disposable_token,
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        # 已防万一，如果code为0，有返点，则需要close_session
        if check_response["code"] == 0:
            driver["token"] = disposable_token
        assert check_response["code"] == 700
        # invalid session
        assert len(check_response["message"]) > 1

    # method GET
    def test_connection_allocate_v2_without_channel(self, driver, session_teardown):
        logger.info("test_connection_allocate_v2_without_channel start")
        token = self.get_token(driver, "test_connection_allocate_v2_without_channel")
        url = "http://{0}:{1}/connection/allocate/v2?package_name=com.cnvcs.junqi&version_code=151".format(
            driver["remote_ip"], driver["port"])
        header = {"Session-Token": token,
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        # 已防万一，如果code为0，有返点，则需要close_session
        if check_response["code"] == 0:
            driver["token"] = token

        assert check_response["code"] > 0
        # 确认message里有错误信息。这种情况下，返回为 "params error"
        find_result = re.findall("params.*error", check_response["message"])
        assert len(find_result) > 0

    # method GET
    def test_connection_allocate_v2_channel_is_null(self, driver, session_teardown):
        logger.info("test_connection_allocate_v2_channel_is_null start")
        token = self.get_token(driver, "test_connection_allocate_v2_channel_is_null")
        url = "http://{0}:{1}/connection/allocate/v2?channel_id=&package_name=com.cnvcs.junqi&version_code=151".format(
            driver["remote_ip"], driver["port"])
        header = {"Session-Token": token, "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        # 已防万一，如果code为0，有返点，则需要close_session
        if check_response["code"] == 0:
            driver["token"] = token

        assert check_response["code"] > 0
        # 确认message里有错误信息。这种情况下，返回为 "params error"
        find_result = re.findall("params.*error", check_response["message"])
        assert len(find_result) > 0

    # method GET
    def test_connection_allocate_v2_without_package_name_is_null(self, driver, session_teardown):
        logger.info("test_connection_allocate_v2_without_pacakage_name_is_null start")
        token = self.get_token(driver, "test_connection_allocate_v2_without_package_name_is_null")
        url = "http://{0}:{1}/connection/allocate/v2?channel_id=auto_test&package_name=&version_code=151".format(
            driver["remote_ip"], driver["port"])
        header = {"Session-Token": token, "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        # 已防万一，如果code为0，有返点，则需要close_session
        if check_response["code"] == 0:
            driver["token"] = token

        assert check_response["code"] > 0
        # 确认message里有错误信息。这种情况下，返回为 "params error"
        find_result = re.findall("params.*error", check_response["message"])
        assert len(find_result) > 0

    # method GET
    def test_connection_allocate_v2_without_package_name(self, driver, session_teardown):
        logger.info("test_connection_allocate_v2_without_pacakage_name start")
        token = self.get_token(driver, "test_connection_allocate_v2_without_package_name")
        url = "http://{0}:{1}/connection/allocate/v2?channel_id=auto_test&version_code=151".format(
            driver["remote_ip"], driver["port"])
        header = {"Session-Token": token, "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        # 已防万一，如果code为0，有返点，则需要close_session
        if check_response["code"] == 0:
            driver["token"] = token

        assert check_response["code"] > 0
        # 确认message里有错误信息。这种情况下，返回为 "params error"
        find_result = re.findall("params.*error", check_response["message"])
        assert len(find_result) > 0

    # method GET
    # 已经上线的游戏允许没有version_code；没有上线的游戏不允许没有version_code
    # 测试环境里com.cnvcs.junqi已上线，允许没有version_code
    def test_connection_allocate_v2_without_version_code(self, driver, session_teardown):
        logger.info("test_connection_allocate_v2_without_version_code start")
        token = self.get_token(driver, "test_connection_allocate_v2_without_version_code")
        url = "http://{0}:{1}/connection/allocate/v2?channel_id=auto_test&package_name=com.cnvcs.junqi".format(
            driver["remote_ip"], driver["port"])
        header = {"Session-Token": token, "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        # 已防万一，如果code为0，有返点，则需要close_session
        if check_response["code"] == 0:
            driver["token"] = token

        assert check_response["code"] == 0
        # self.close_session(driver, token)

    # 结果同test_connection_allocate_v2_no_version_code
    def test_connection_allocate_v2_version_code_is_null(self, driver, session_teardown):
        logger.info("test_connection_allocate_v2_version_code_is_null start")
        token = self.get_token(driver, "test_connection_allocate_v2_version_code_is_null")
        url = "http://{0}:{1}/connection/allocate/v2?channel_id=auto_test&package_name=com.cnvcs.junqi&version_code=".format(
            driver["remote_ip"], driver["port"])
        header = {"Session-Token": token, "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        # 已防万一，如果code为0，有返点，则需要close_session
        if check_response["code"] == 0:
            driver["token"] = token

        assert check_response["code"] == 0
        # self.close_session(driver, token)

    def test_connection_allocate_v2_version_code_not_int(self, driver, session_teardown):
        logger.info("test_connection_allocate_v2_version_code_not_int start")
        token = self.get_token(driver, "test_connection_allocate_v2_version_code_not_int")
        url = "http://{0}:{1}/connection/allocate/v2?channel_id=auto_test&package_name=com.cnvcs.junqi&version_code=test".format(
            driver["remote_ip"], driver["port"])
        header = {"Session-Token": token, "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        # 已防万一，如果code为0，有返点，则需要close_session
        if check_response["code"] == 0:
            driver["token"] = token
        assert check_response["code"] > 0
        # 确认message里有错误信息。这种情况下，返回为 "params version_code error"
        find_result = re.findall("params.*error", check_response["message"])
        assert len(find_result) > 0

    # scheduler resp status 2001, err: not found any avm
    # 这里是否要先判断channel_id是否存在？
    def test_connection_allocate_v2_param_wrong(self, driver, session_teardown):
        logger.info("test_connection_allocate_v2_param_wrong start")
        token = self.get_token(driver, "test_connection_allocate_v2_param_wrong")
        url = "http://{0}:{1}/connection/allocate/v2?channel_id=wrong&package_name=com.cnvcs.junqi&version_code=151".format(
            driver["remote_ip"], driver["port"])
        header = {"Session-Token": token, "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        # 已防万一，如果code为0，有返点，则需要close_session
        if check_response["code"] == 0:
            driver["token"] = token
        assert check_response["code"] > 0
        # 确认message里有错误信息。这种情况下，返回为 "无相应的游戏数据"
        assert len(check_response["message"]) > 1

    def test_connection_allocate_v2_mismatch_channel_id(self, driver, session_teardown):
        logger.info("test_connection_allocate_v2_mismatch_channel_id start")
        token = self.get_token(driver, "test_connection_allocate_v2_mismatch_channel_id")
        url = "http://{0}:{1}/connection/allocate/v2?channel_id=mismatch&package_name=com.cnvcs.junqi&version_code=151".format(
            driver["remote_ip"], driver["port"])
        header = {"Session-Token": token, "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        # 已防万一，如果code为0，有返点，则需要close_session
        if check_response["code"] == 0:
            driver["token"] = token
        assert check_response["code"] != 0
        # assert check_response["code"] == 700
        # assert "session mismatch channelId, packageName" in check_response["message"]

    def test_connection_allocate_v2_mismatch_package_name(self, driver, session_teardown):
        logger.info("test_connection_allocate_v2_mismatch_package_name start")
        token = self.get_token(driver, "test_connection_allocate_v2_mismatch_package_name")
        url = "http://{0}:{1}/connection/allocate/v2?channel_id=auto_test&package_name=mismatch&version_code=151".format(
            driver["remote_ip"], driver["port"])
        header = {"Session-Token": token, "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        # 已防万一，如果code为0，有返点，则需要close_session
        if check_response["code"] == 0:
            driver["token"] = token

        assert check_response["code"] != 0
        # assert check_response["code"] == 700
        # assert "session mismatch channelId, packageName" in check_response["message"]

    # 定义的pool_level目前只有0,1,2 三种
    # 对于已上线的游戏，可以返回节点
    def test_connection_allocate_v2_pool_level_normal(self, driver, session_teardown):
        logger.info("test_connection_allocate_v2 start")
        token = self.get_token(driver, "test_connection_allocate_v2")
        # pool_level=0
        url = "http://{0}:{1}/connection/allocate/v2?{2}&pool_level=0".format(
            driver["remote_ip"], driver["port"], package_info)
        header = {"Session-Token": token, "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        # 已防万一，如果code为0，有返点，则需要close_session
        if check_response["code"] == 0:
            driver["token"] = token
        assert check_response["code"] == 0
        assert "params pool_level error" not in check_response["message"]

    # pool_level=1， 设置只返回pool的节点；由于游戏没有池化，这里没有节点
    # TODO: 后续考虑增加一个固定池化的节点，这里就可以验证会返回池化的点了。但是池化要占用一台设备
    def test_connection_allocate_v2_pool_level_only_pool(self, driver, session_teardown):
        logger.info("test_connection_allocate_v2 start")
        token = self.get_token(driver, "test_connection_allocate_v2")
        # pool_level=1
        url = "http://{0}:{1}/connection/allocate/v2?{2}&pool_level=1".format(
            driver["remote_ip"], driver["port"], package_info)
        header = {"Session-Token": token, "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        # 已防万一，如果code为0，有返点，则需要close_session
        if check_response["code"] == 0:
            driver["token"] = token

        assert check_response["code"] > 0
        # 保证不是报pool_level的错误
        assert "params pool_level error" not in check_response["message"]

    # pool_level=2， 排除池化节点，由于游戏没有池化，预期是返回节点信息，如果测试环境里节点都被占用了，就还是会返回错误
    def test_connection_allocate_v2_pool_level_exclude_pool(self, driver, session_teardown):
        logger.info("test_connection_allocate_v2 start")
        token = self.get_token(driver, "test_connection_allocate_v2")
        # pool_level=2
        url = "http://{0}:{1}/connection/allocate/v2?{2}&pool_level=2".format(
            driver["remote_ip"], driver["port"], package_info)
        header = {"Session-Token": token, "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        # 已防万一，如果code为0，有返点，则需要close_session
        if check_response["code"] == 0:
            driver["token"] = token
        assert check_response["code"] == 0
        # 保证不是报pool_level的错误
        assert "params pool_level error" not in check_response["message"]

    # 设置pool_level超出定义，3和-1
    def test_connection_allocate_v2_pool_level_beyond_defined(self, driver, session_teardown):
        logger.info("test_connection_allocate_v2 start")
        token = self.get_token(driver, "test_connection_allocate_v2")
        # pool_level=3
        url = "http://{0}:{1}/connection/allocate/v2?{2}&pool_level=3".format(
            driver["remote_ip"], driver["port"], package_info)
        header = {"Session-Token": token, "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        # 已防万一，如果code为0，有返点，则需要close_session
        if check_response["code"] == 0:
            driver["token"] = token

        assert check_response["code"] == 1
        assert "params pool_level error" in check_response["message"]

        # pool_level=-1
        url = "http://{0}:{1}/connection/allocate/v2?{2}&pool_level=-1".format(
            driver["remote_ip"], driver["port"], package_info)
        header = {"Session-Token": token, "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "params pool_level error" in check_response["message"]

    # 设置pool_level为字符串
    def test_connection_allocate_v2_pool_level_str(self, driver, session_teardown):
        logger.info("test_connection_allocate_v2 start")
        token = self.get_token(driver, "test_connection_allocate_v2")
        # pool_level为str类型
        url = "http://{0}:{1}/connection/allocate/v2?{2}&pool_level=test".format(
            driver["remote_ip"], driver["port"], package_info)
        header = {"Session-Token": token, "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        # 已防万一，如果code为0，有返点，则需要close_session
        if check_response["code"] == 0:
            driver["token"] = token

        assert check_response["code"] == 1
        assert "params pool_level error" in check_response["message"]

    # 设置pool_level超长数字
    def test_connection_allocate_v2_pool_level_oversize(self, driver, session_teardown):
        logger.info("test_connection_allocate_v2 start")
        token = self.get_token(driver, "test_connection_allocate_v2")
        # pool_level为超长数字
        url = "http://{0}:{1}/connection/allocate/v2?{2}&pool_level=10241024102410241024".format(
            driver["remote_ip"], driver["port"], package_info)
        header = {"Session-Token": token, "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        # 已防万一，如果code为0，有返点，则需要close_session
        if check_response["code"] == 0:
            driver["token"] = token
        assert check_response["code"] == 1
        assert "params pool_level error" in check_response["message"]

    # method GET
    def test_keep_alive(self, driver, session_teardown):
        logger.info("test_keep_alive start")
        # 绑定实例
        token = self.get_token(driver, "test_keep_alive")
        allocate_response = self.connection_allocate_v2(driver, token)
        # 已防万一，如果code为0，有返点，则需要close_session
        if json.loads(allocate_response.text)["code"] == 0:
            driver["token"] = token

        url = "http://{0}:{1}/session/keepalive".format(driver["remote_ip"], driver["port"])
        header = {"Session-Token": token, "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0
        # self.close_session(driver, token)

    # 没有绑定实例化，直接请求keep_alive
    def test_keep_alive_without_connection(self, driver, session_teardown):
        logger.info("test_keep_alive_without_connection start")
        # 只获取了token，没有去实例化
        token = self.get_token(driver, "test_keep_alive_without_connection")
        url = "http://{0}:{1}/session/keepalive".format(driver["remote_ip"], driver["port"])
        header = {"Session-Token": token, "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        # 已防万一，如果code为0，有返点，则需要close_session
        if check_response["code"] == 0:
            driver["token"] = token

        assert check_response["code"] == 700
        # # 报错 "get session token error"
        # assert len(check_response["message"]) > 1
        assert "get session token error" in check_response["message"]

    # headers中没有传入token
    def test_keep_alive_without_token(self, driver):
        logger.info("test_keep_alive_without_token start")
        url = "http://{0}:{1}/session/keepalive".format(driver["remote_ip"], driver["port"])
        header = {"x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 700
        # # 报错 "get session token error"
        # assert len(check_response["message"]) > 1
        assert "get session token error" in check_response["message"]

    # 这个需要确认一下
    def test_keep_alive_token_wrong(self, driver):
        logger.info("test_keep_alive_token_wrong start")
        disposable_token = "ad31c761727fbcd2643c73fd32235a6a60a780d43a94dd2e02998ab3a9bea41b"
        url = "http://{0}:{1}/session/keepalive".format(driver["remote_ip"], driver["port"])
        header = {"Session-Token": disposable_token, "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 700
        assert len(check_response["message"]) > 1
        # 报错为 get session token error
        # assert "invalid session token" in check_response["message"]

    def test_session_close(self, driver, session_teardown):
        logger.info("test_session_close start")
        # 绑定实例
        token = self.get_token(driver, "test_session_close")
        allocate_response = self.connection_allocate_v2(driver, token)
        # 已防万一，如果code为0，有返点，则需要close_session
        if json.loads(allocate_response.text)["code"] == 0:
            driver["token"] = token

        url = "http://{0}:{1}/session/close".format(driver["remote_ip"], driver["port"])
        header = {"Session-Token": token, "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0
        # self.close_session(driver, token)

    def test_session_close_without_token(self, driver, session_teardown):
        logger.info("test_session_close_without_token start")
        # 绑定实例
        token = self.get_token(driver, "test_session_close_without_token")
        allocate_response = self.connection_allocate_v2(driver, token)
        # 已防万一，如果code为0，有返点，则需要close_session
        if json.loads(allocate_response.text)["code"] == 0:
            driver["token"] = token

        url = "http://{0}:{1}/session/close".format(driver["remote_ip"], driver["port"])
        header = {"x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 700
        # 会报错 "invalid session token"
        assert "invalid session token" in check_response["message"]

    def test_session_close_without_connection(self, driver):
        logger.info("test_session_close_without_connection start")
        token = self.get_token(driver, "test_session_close_without_connection")
        url = "http://{0}:{1}/session/close".format(driver["remote_ip"], driver["port"])
        header = {"Session-Token": token, "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 700
        # 会报错 "invalid session token"
        # assert "invalid session token" in check_response["message"]

    # method GET
    def test_admin_connection_get(self, driver, session_teardown):
        logger.info("test_admin_connection_get start")
        # 绑定实例
        token = self.get_token(driver, "test_admin_connection_get")
        allocate_response = self.connection_allocate_v2(driver, token)
        # 已防万一，如果code为0，有返点，则需要close_session
        if json.loads(allocate_response.text)["code"] == 0:
            driver["token"] = token

        url = "http://{0}:{1}/admin/connection/get?sessionToken={2}".format(driver["remote_ip"], driver["port"],
                                                                            token)
        header = {"x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0
        # self.close_session(driver, token)

    def test_admin_connection_get_without_connection(self, driver):
        logger.info("test_admin_connection_get_without_connection start")
        token = self.get_token(driver, "test_admin_connection_get_without_connection")
        url = "http://{0}:{1}/admin/connection/get?sessionToken={2}".format(driver["remote_ip"], driver["port"],
                                                                            token)
        header = {"x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        # 会报错 "invalid session"
        assert "invalid session" in check_response["message"]

    def test_admin_connection_get_param_without_token(self, driver, session_teardown):
        logger.info("test_admin_connection_get_param_without_token start")
        # 绑定实例
        token = self.get_token(driver, "test_admin_connection_get_param_without_token")
        allocate_response = self.connection_allocate_v2(driver, token)
        # 已防万一，如果code为0，有返点，则需要close_session
        if json.loads(allocate_response.text)["code"] == 0:
            driver["token"] = token

        url = "http://{0}:{1}/admin/connection/get".format(driver["remote_ip"], driver["port"])
        header = {"x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        # 报错 "invalid params [sessionToken]"
        assert "invalid param" in check_response["message"]

    def test_admin_connection_get_token_wrong(self, driver):
        logger.info("test_admin_connection_get_token_wrong start")
        disposable_token = "ad31c761727fbcd2643c73fd32235a6a60a780d43a94dd2e02998ab3a9bea41b"
        url = "http://{0}:{1}/admin/connection/get?sessionToken={2}".format(driver["remote_ip"], driver["port"],
                                                                            disposable_token)
        header = {"x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        # 会报错 "invalid session"
        assert "invalid session" in check_response["message"]

    # method POST
    def test_admin_agent_msg_closed(self, driver, session_teardown):
        logger.info("test_admin_agent_msg_closed start")
        # 绑定实例
        token = self.get_token(driver, "test_admin_agent_msg_closed")
        allocate_response = self.connection_allocate_v2(driver, token)
        # 已防万一，如果code为0，有返点，则需要close_session
        if json.loads(allocate_response.text)["code"] == 0:
            driver["token"] = token

        node_id = json.loads(self.connection_get(driver, token).text)["data"]["connection"]["nodeId"]
        url = "http://{0}:{1}/admin/agent/msg".format(driver["remote_ip"], driver["port"])
        header = {"x-forwarded-for": driver["x-forwarded-for"]}
        data = {"node_id": node_id,
                "data": {"type": "closed", "session_id": token, "reason": "timeout", "code": 2101, "initiator": 0}}
        response = RequestHttp().request_response(url=url, method="post", headers=header, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0
        # self.close_session(driver, token)

    # @pytest.mark.skip
    # def test_admin_agent_msg_closed_without_node_id(self, driver):
    #     logger.info("test_admin_agent_msg_closed_without_node_id start")
    #     # 绑定实例
    #     url = "http://{0}:{1}/admin/agent/msg".format(driver["remote_ip"], driver["port"])
    #     header = {"x-forwarded-for": driver["x-forwarded-for"]}
    #     data = {"data": {"type": "closed", "session_id": driver["token"], "reason": "test", "code": 1}}
    #     response = RequestHttp().request_response(url=url, method="post", headers=header, data=data)
    #     assert response.status_code == 200
    #     check_response = json.loads(response.text)
    #     assert check_response["code"] == 0

    # 为终端peer调度可用的实例，并将调度结果信息绑定到peer的session会话信息中
    def connection_allocate_v2(self, driver, token):
        url = "http://{0}:{1}/connection/allocate/v2?{2}".format(
            driver["remote_ip"], driver["port"], package_info)
        header = {"Session-Token": token, "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        return response

    def connection_get(self, driver, token):
        url = "http://{0}:{1}/admin/connection/get?sessionToken={2}".format(driver["remote_ip"], driver["port"],
                                                                            token)
        header = {"x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        return response

    def get_token(self, driver, test_name):
        url = "http://{0}:{1}/session/create".format(driver["remote_ip"], driver["port"])
        device_user = 'device_user={"auto_test":"' + test_name + '"}'
        url = url + "?" + device_user
        header = {"userid": "1", "appid": "auto_test", "x-forwarded-for": driver["x-forwarded-for"]}
        token = json.loads(requests.get(url, headers=header).text)["data"]["token"]
        logger.debug("token is {0}".format(token))
        return token

    def close_session(self, driver, token):
        logger.debug("close session")
        url = "http://{0}:{1}/session/close".format(driver["remote_ip"], driver["port"])
        header = {"Session-Token": token, "x-forwarded-for": driver["x-forwarded-for"]}
        requests.get(url, headers=header)
        # close session后等待几秒
        time.sleep(7)


if __name__ == '__main__':
    pytest.main(["-s", "test_service_rtc.py"])

