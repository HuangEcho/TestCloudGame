# create_author: HuangYaxing
# create_time: 2021/10/19 8:19 下午

import pytest
import requests
import json
import random
import re
import logging
from dependent.env_self import Env
from dependent.requests_http import RequestHttp

from service_rtc_test.script.route_avm_register import RouteAvmRegister
from service_rtc_test.script.route_avm_heartbeat import RouteAvmHeartBeat
from service_rtc_test.script.put_on_avm import PutOnAvm
from service_rtc_test.script.avm_tag import AvmTag
from service_rtc_test.script.release_node import ReleaseNode

log = logging.getLogger("test_service_rtc")
# 增加一些ip地址
ip_path_one = random.randint(2, 10)
ip_path_two = random.randint(2, 10)
for_ip = "192.168.{0}.{1}"


class TestServiceRTC(object):

    @pytest.fixture(scope="class")
    def workspace(self):
        log.info("workspace ready")
        # 注册avm
        RouteAvmRegister().main()
        # avm上报心跳
        RouteAvmHeartBeat().main()
        # 上架avm
        PutOnAvm().main()
        # 给avm打tag
        AvmTag().main()
        yield
        # 释放节点
        ReleaseNode().main()
        log.info("workspace clean")

    # 如果不想跑workspace，可注释掉
    @pytest.fixture(scope="function")
    def driver(self, workspace):
    # def driver(self):
        log.info("test case setup")
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
                url = "http://{0}:{1}/session/create".format(driver["remote_ip"], driver["port"])
                header = {"userid": "123", "appid": "test", "x-forwarded-for": driver["x-forwarded-for"]}
                driver["token"] = json.loads(requests.get(url, headers=header).text)["data"]["token"]

        except Exception as E:
            log.debug("error is {0}".format(E))
        log.debug("test case driver info is {0}".format(driver))
        yield driver
        # close session, 以防万一，就算失败也有一个保底的close
        if "token" in driver:
            url = "http://{0}:{1}/session/close".format(driver["remote_ip"], driver["port"])
            header = {"Session-Token": driver["token"], "x-forwarded-for": driver["x-forwarded-for"]}
            requests.get(url, headers=header)
            log.debug("close session")
        log.info("test case teardown")

    # method: GET
    def test_peer_init(self, driver):
        self.start_case_log("test_peer_init")
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
        self.start_case_log("test_session_create")
        url = "http://{0}:{1}/session/create".format(driver["remote_ip"], driver["port"])
        header = {"userid": "123", "appid": "test", "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0
        assert check_response["message"] == "ok"
        assert "token" in check_response["data"]

    def test_session_create_without_userid(self, driver):
        self.start_case_log("test_session_create_without_userid")
        url = "http://{0}:{1}/session/create".format(driver["remote_ip"], driver["port"])
        header = {"appid": "test", "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "invalid params" in check_response["message"]

    def test_session_create_without_appid(self, driver):
        self.start_case_log("test_session_create_without_appid")
        url = "http://{0}:{1}/session/create".format(driver["remote_ip"], driver["port"])
        header = {"userid": "123", "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "invalid params" in check_response["message"]

    def test_session_create_without_userid_or_appid(self, driver):
        self.start_case_log("test_session_create_without_userid_or_appid")
        url = "http://{0}:{1}/session/create".format(driver["remote_ip"], driver["port"])
        header = {"x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "invalid params" in check_response["message"]

    def test_session_create_userid_not_int(self, driver):
        self.start_case_log("test_session_create_userid_not_int")
        url = "http://{0}:{1}/session/create".format(driver["remote_ip"], driver["port"])
        header = {"userid": "test", "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "invalid params" in check_response["message"]

    # method GET
    def test_connection_allocate_v2(self, driver):
        # 固定了一些信息，具体修改的地方，我还没有很了解，后续了解后再修改
        self.start_case_log("test_connection_allocate_v2")
        url = "http://{0}:{1}/connection/allocate/v2?channel_id=5&package_name=jp.ogapee.onscripter.release&version_code=20210831".format(
            driver["remote_ip"], driver["port"])
        header = {"Session-Token": driver["token"], "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0
        assert check_response["message"] == "ok"
        assert "agentIceServer" in check_response["data"] and "urls" in check_response["data"]["agentIceServer"]
        assert "iceServer" in check_response["data"] and "urls" in check_response["data"]["iceServer"]
        assert check_response["data"]["agentIceServer"]["urls"] == check_response["data"]["iceServer"]["urls"]

    # method GET
    def test_connection_allocate_v2_token_invalid(self, driver):
        self.start_case_log("test_connection_allocate_v2_token_invalid")
        disposable_token = "ad31c761727fbcd2643c73fd32235a6a60a780d43a94dd2e02998ab3a9bea41b"
        url = "http://{0}:{1}/connection/allocate/v2?channel_id=5&package_name=jp.ogapee.onscripter.release&version_code=20210831".format(
            driver["remote_ip"], driver["port"])
        header = {"Session-Token": disposable_token,
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 700
        # 可能会session过期 "session is expire"，或者session无效 "invalid session"
        # assert "invalid session" in check_response["message"]

    # method GET
    def test_connection_allocate_v2_without_channel(self, driver):
        self.start_case_log("test_connection_allocate_v2_without_channel")
        url = "http://{0}:{1}/connection/allocate/v2?package_name=jp.ogapee.onscripter.release&version_code=20210831".format(
            driver["remote_ip"], driver["port"])
        header = {"Session-Token": driver["token"], "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        # 确认message里有错误信息。这种情况下，返回为 "params error"
        find_result = re.findall("params.*error", check_response["message"])
        assert len(find_result) > 0

    # method GET
    def test_connection_allocate_v2_channel_is_null(self, driver):
        self.start_case_log("test_connection_allocate_v2_channel_is_null")
        url = "http://{0}:{1}/connection/allocate/v2?channel_id=&package_name=jp.ogapee.onscripter.release&version_code=20210831".format(
            driver["remote_ip"], driver["port"])
        header = {"Session-Token": driver["token"], "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        # 确认message里有错误信息。这种情况下，返回为 "params error"
        find_result = re.findall("params.*error", check_response["message"])
        assert len(find_result) > 0

    # method GET
    def test_connection_allocate_v2_without_pacakage_name(self, driver):
        self.start_case_log("test_connection_allocate_v2_without_pacakage_name")
        url = "http://{0}:{1}/connection/allocate/v2?channel_id=5&package_name=&version_code=20210831".format(
            driver["remote_ip"], driver["port"])
        header = {"Session-Token": driver["token"], "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        # 确认message里有错误信息。这种情况下，返回为 "params error"
        find_result = re.findall("params.*error", check_response["message"])
        assert len(find_result) > 0

    # method GET
    def test_connection_allocate_v2_pacakage_name_is_null(self, driver):
        self.start_case_log("test_connection_allocate_v2_pacakage_name_is_null")
        url = "http://{0}:{1}/connection/allocate/v2?channel_id=5&version_code=20210831".format(
            driver["remote_ip"], driver["port"])
        header = {"Session-Token": driver["token"], "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        # 确认message里有错误信息。这种情况下，返回为 "params error"
        find_result = re.findall("params.*error", check_response["message"])
        assert len(find_result) > 0

    # method GET
    # 已经上线的游戏，允许没有version_code;没有上线的游戏，要求必须有version_code
    # 目前模拟的游戏没有上线，报错会有"get gameData error"
    def test_connection_allocate_v2_without_version_code(self, driver):
        self.start_case_log("test_connection_allocate_v2_without_version_code")
        url = "http://{0}:{1}/connection/allocate/v2?channel_id=5&package_name=jp.ogapee.onscripter.release".format(
            driver["remote_ip"], driver["port"])
        header = {"Session-Token": driver["token"], "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert len(check_response["message"]) > 1

    # 结果同test_connection_allocate_v2_no_version_code
    # 目前模拟的游戏没有上线，报错会有"get gameData error"
    def test_connection_allocate_v2_version_code_is_null(self, driver):
        self.start_case_log("test_connection_allocate_v2_version_code_is_null")
        url = "http://{0}:{1}/connection/allocate/v2?channel_id=5&package_name=jp.ogapee.onscripter.release&version_code=".format(
            driver["remote_ip"], driver["port"])
        header = {"Session-Token": driver["token"], "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert len(check_response["message"]) > 1

    def test_connection_allocate_v2_version_code_not_int(self, driver):
        self.start_case_log("test_connection_allocate_v2_version_code_not_int")
        url = "http://{0}:{1}/connection/allocate/v2?channel_id=5&package_name=jp.ogapee.onscripter.release&version_code=test".format(
            driver["remote_ip"], driver["port"])
        header = {"Session-Token": driver["token"], "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        # 确认message里有错误信息。这种情况下，返回为 "params version_code error"
        find_result = re.findall("params.*error", check_response["message"])
        assert len(find_result) > 0

    # scheduler resp status 2001, err: not found any avm
    def test_connection_allocate_v2_param_wrong(self, driver):
        self.start_case_log("test_connection_allocate_v2_param_wrong")
        url = "http://{0}:{1}/connection/allocate/v2?channel_id=wrong&package_name=jp.ogapee.onscripter.release&version_code=20211027".format(
            driver["remote_ip"], driver["port"])
        header = {"Session-Token": driver["token"], "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        # 确认message里有错误信息。这种情况下，返回为 "scheduler resp status 2001, err: not found any avm"
        assert len(check_response["message"]) > 1

    # method GET
    def test_keep_alive(self, driver):
        self.start_case_log("test_keep_alive")
        # 绑定实例
        self.connection_allocate_v2(driver)

        url = "http://{0}:{1}/session/keepalive".format(driver["remote_ip"], driver["port"])
        header = {"Session-Token": driver["token"], "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0

    # 没有绑定实例化，直接请求keep_alive
    def test_keep_alive_without_connection(self, driver):
        self.start_case_log("test_keep_alive_without_connection")
        url = "http://{0}:{1}/session/keepalive".format(driver["remote_ip"], driver["port"])
        header = {"Session-Token": driver["token"], "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 700
        # # 报错 "get session token error"
        # assert len(check_response["message"]) > 1
        assert "get session token error" in check_response["message"]

    # headers中没有传入token
    def test_keep_alive_without_token(self, driver):
        self.start_case_log("test_keep_alive_without_token")
        url = "http://{0}:{1}/session/keepalive".format(driver["remote_ip"], driver["port"])
        header = {"x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 700
        # # 报错 "get session token error"
        # assert len(check_response["message"]) > 1
        assert "get session token error" in check_response["message"]

    def test_keep_alive_token_wrong(self, driver):
        self.start_case_log("test_keep_alive_token_wrong")
        disposable_token = "ad31c761727fbcd2643c73fd32235a6a60a780d43a94dd2e02998ab3a9bea41b"
        url = "http://{0}:{1}/session/keepalive".format(driver["remote_ip"], driver["port"])
        header = {"Session-Token": disposable_token, "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 700
        # # 报错 "invalid session token"
        # assert len(check_response["message"]) > 1
        assert "invalid session token" in check_response["message"]

    def test_session_close(self, driver):
        self.start_case_log("test_session_close")
        # 绑定实例
        self.connection_allocate_v2(driver)

        url = "http://{0}:{1}/session/close".format(driver["remote_ip"], driver["port"])
        header = {"Session-Token": driver["token"], "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0

    def test_session_close_without_token(self, driver):
        self.start_case_log("test_session_close_without_token")
        # 绑定实例
        self.connection_allocate_v2(driver)

        url = "http://{0}:{1}/session/close".format(driver["remote_ip"], driver["port"])
        header = {"x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 700
        # 会报错 "invalid session token"
        assert "invalid session token" in check_response["message"]

    def test_session_close_without_connection(self, driver):
        self.start_case_log("test_session_close_without_connection")
        url = "http://{0}:{1}/session/close".format(driver["remote_ip"], driver["port"])
        header = {"Session-Token": driver["token"], "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 700
        # 会报错 "invalid session token"
        assert "invalid session token" in check_response["message"]

    # method GET
    def test_admin_connection_get(self, driver):
        self.start_case_log("test_admin_connection_get")
        # 绑定实例
        self.connection_allocate_v2(driver)

        url = "http://{0}:{1}/admin/connection/get?sessionToken={2}".format(driver["remote_ip"], driver["port"],
                                                                            driver["token"])
        header = {"x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0

    def test_admin_connection_get_without_connection(self, driver):
        self.start_case_log("test_admin_connection_get_without_connection")
        url = "http://{0}:{1}/admin/connection/get?sessionToken={2}".format(driver["remote_ip"], driver["port"],
                                                                            driver["token"])
        header = {"x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        # 会报错 "invalid session"
        assert "invalid session" in check_response["message"]

    def test_admin_connection_get_param_without_token(self, driver):
        self.start_case_log("test_admin_connection_get_param_without_token")
        # 绑定实例
        self.connection_allocate_v2(driver)

        url = "http://{0}:{1}/admin/connection/get".format(driver["remote_ip"], driver["port"])
        header = {"x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        # 报错 "invalid params [sessionToken]"
        assert "invalid param" in check_response["message"]

    def test_admin_connection_get_token_wrong(self, driver):
        self.start_case_log("test_admin_connection_get_token_wrong")
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
    def test_admin_agent_msg_closed(self, driver):
        self.start_case_log("test_admin_agent_msg_closed")
        # 绑定实例
        self.connection_allocate_v2(driver)
        node_id = json.loads(self.connection_get(driver).text)["data"]["connection"]["nodeId"]
        url = "http://{0}:{1}/admin/agent/msg".format(driver["remote_ip"], driver["port"])
        header = {"x-forwarded-for": driver["x-forwarded-for"]}
        data = {"node_id": node_id,
                "data": {"type": "closed", "session_id": driver["token"], "reason": "test", "code": 1}}
        response = RequestHttp().request_response(url=url, method="post", headers=header, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0

    # @pytest.mark.skip
    # def test_admin_agent_msg_closed_without_node_id(self, driver):
    #     self.start_case_log("test_admin_agent_msg_closed_without_node_id")
    #     # 绑定实例
    #     url = "http://{0}:{1}/admin/agent/msg".format(driver["remote_ip"], driver["port"])
    #     header = {"x-forwarded-for": driver["x-forwarded-for"]}
    #     data = {"data": {"type": "closed", "session_id": driver["token"], "reason": "test", "code": 1}}
    #     response = RequestHttp().request_response(url=url, method="post", headers=header, data=data)
    #     assert response.status_code == 200
    #     check_response = json.loads(response.text)
    #     assert check_response["code"] == 0

    # 为终端peer调度可用的实例，并将调度结果信息绑定到peer的session会话信息中
    def connection_allocate_v2(self, driver):
        url = "http://{0}:{1}/connection/allocate/v2?channel_id=5&package_name=jp.ogapee.onscripter.release&version_code=20210831".format(
            driver["remote_ip"], driver["port"])
        header = {"Session-Token": driver["token"], "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        return response

    def connection_get(self, driver):
        url = "http://{0}:{1}/admin/connection/get?sessionToken={2}".format(driver["remote_ip"], driver["port"],
                                                                            driver["token"])
        header = {"x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        return response

    def start_case_log(self, name):
        log.info("{0}: {1} start".format(self.__class__.__name__, name))


if __name__ == '__main__':
    pytest.main(["-s", "test_service_rtc.py"])

