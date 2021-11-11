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

logger = logging.getLogger(__name__)
# 增加一些ip地址
ip_path_one = random.randint(2, 10)
ip_path_two = random.randint(2, 10)
for_ip = "192.168.{0}.{1}"
package_info = "channel_id=auto_test&package_name=com.cnvcs.junqi&version_code=151"


class TestServiceRTC(object):

    # @pytest.fixture(scope="class")
    # 更改环境后，不需要再设置这个脚本了
    # def workspace(self):
    #     logger.info("workspace ready")
    #     # 注册avm
    #     RouteAvmRegister().main()
    #     # avm上报心跳
    #     RouteAvmHeartBeat().main()
    #     # 上架avm
    #     PutOnAvm().main()
    #     # 给avm打tag
    #     AvmTag().main()
    #     yield
    #     # 释放节点
    #     ReleaseNode().main()
    #     logger.info("workspace clean")

    # 如果不想跑workspace，可注释掉
    @pytest.fixture(scope="session")
    # def driver(self, workspace):
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
                url = "http://{0}:{1}/session/create".format(driver["remote_ip"], driver["port"])
                url = url + '?device_user={"auto_test":"auto_test"}'
                header = {"userid": "1", "appid": "auto_test", "x-forwarded-for": driver["x-forwarded-for"]}
                driver["token"] = json.loads(requests.get(url, headers=header).text)["data"]["token"]

        except Exception as E:
            logger.error("error is {0}".format(E))
        logger.debug("test case driver info is {0}".format(driver))
        yield driver
        # close session, 以防万一，就算失败也有一个保底的close
        if "token" in driver:
            url = "http://{0}:{1}/session/close".format(driver["remote_ip"], driver["port"])
            header = {"Session-Token": driver["token"], "x-forwarded-for": driver["x-forwarded-for"]}
            requests.get(url, headers=header)
            logger.debug("close session")
        logger.info("test case teardown")

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
        url = url + '?device_user={"auto_test11":"auto_test"}'
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
    def test_connection_allocate_v2(self, driver):
        # 使用已上线的一个游戏包信息
        logger.info("test_connection_allocate_v2 start")
        url = "http://{0}:{1}/connection/allocate/v2?{2}".format(
            driver["remote_ip"], driver["port"], package_info)
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
        assert "pooling" in check_response["data"]

    # method GET
    def test_connection_allocate_v2_token_invalid(self, driver):
        logger.info("test_connection_allocate_v2_token_invalid start")
        disposable_token = "ad31c761727fbcd2643c73fd32235a6a60a780d43a94dd2e02998ab3a9bea41b"
        url = "http://{0}:{1}/connection/allocate/v2?{2}".format(
            driver["remote_ip"], driver["port"], package_info)
        header = {"Session-Token": disposable_token,
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 700
        # sessionId没有绑定实例
        assert "get sessionToken fail" in check_response["message"]

    # method GET
    def test_connection_allocate_v2_without_channel(self, driver):
        logger.info("test_connection_allocate_v2_without_channel start")
        token = self.get_token(driver)
        url = "http://{0}:{1}/connection/allocate/v2?package_name=com.cnvcs.junqi&version_code=151".format(
            driver["remote_ip"], driver["port"])
        header = {"Session-Token": token,
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
        logger.info("test_connection_allocate_v2_channel_is_null start")
        token = self.get_token(driver)
        url = "http://{0}:{1}/connection/allocate/v2?channel_id=&package_name=com.cnvcs.junqi&version_code=151".format(
            driver["remote_ip"], driver["port"])
        header = {"Session-Token": token, "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        # 确认message里有错误信息。这种情况下，返回为 "params error"
        find_result = re.findall("params.*error", check_response["message"])
        assert len(find_result) > 0

    # method GET
    def test_connection_allocate_v2_without_pacakage_name_is_null(self, driver):
        logger.info("test_connection_allocate_v2_without_pacakage_name_is_null start")
        token = self.get_token(driver)
        url = "http://{0}:{1}/connection/allocate/v2?channel_id=auto_test&package_name=&version_code=151".format(
            driver["remote_ip"], driver["port"])
        header = {"Session-Token": token, "Peer-Id": driver["peer_id"],
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
        logger.info("test_connection_allocate_v2_without_pacakage_name start")
        token = self.get_token(driver)
        url = "http://{0}:{1}/connection/allocate/v2?channel_id=auto_test&version_code=151".format(
            driver["remote_ip"], driver["port"])
        header = {"Session-Token": token, "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        # 确认message里有错误信息。这种情况下，返回为 "params error"
        find_result = re.findall("params.*error", check_response["message"])
        assert len(find_result) > 0

    # method GET
    # 已经上线的游戏允许没有version_code；没有上线的游戏不允许没有version_code
    def test_connection_allocate_v2_without_version_code(self, driver):
        logger.info("test_connection_allocate_v2_without_version_code start")
        token = self.get_token(driver)
        url = "http://{0}:{1}/connection/allocate/v2?channel_id=auto_test&package_name=com.cnvcs.junqi".format(
            driver["remote_ip"], driver["port"])
        header = {"Session-Token": token, "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert len(check_response["message"]) > 1

    # 结果同test_connection_allocate_v2_no_version_code
    # 目前模拟的游戏没有上线，报错会有"get gameData error"
    def test_connection_allocate_v2_version_code_is_null(self, driver):
        logger.info("test_connection_allocate_v2_version_code_is_null start")
        token = self.get_token(driver)
        url = "http://{0}:{1}/connection/allocate/v2?channel_id=auto_test&package_name=com.cnvcs.junqi&version_code=".format(
            driver["remote_ip"], driver["port"])
        header = {"Session-Token": token, "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert len(check_response["message"]) > 1

    def test_connection_allocate_v2_version_code_not_int(self, driver):
        logger.info("test_connection_allocate_v2_version_code_not_int start")
        token = self.get_token(driver)
        url = "http://{0}:{1}/connection/allocate/v2?channel_id=auto_test&package_name=com.cnvcs.junqi&version_code=test".format(
            driver["remote_ip"], driver["port"])
        header = {"Session-Token": token, "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        # 确认message里有错误信息。这种情况下，返回为 "params version_code error"
        find_result = re.findall("params.*error", check_response["message"])
        assert len(find_result) > 0

    # scheduler resp status 2001, err: not found any avm
    # 这里是否要先判断channel_id是否存在？
    def test_connection_allocate_v2_param_wrong(self, driver):
        logger.info("test_connection_allocate_v2_param_wrong start")
        token = self.get_token(driver)
        url = "http://{0}:{1}/connection/allocate/v2?channel_id=wrong&package_name=com.cnvcs.junqi&version_code=151".format(
            driver["remote_ip"], driver["port"])
        header = {"Session-Token": token, "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        # 确认message里有错误信息。这种情况下，返回为 "无相应的游戏数据"
        assert len(check_response["message"]) > 1

    def test_connection_allocate_v2_mismatch_channel_id(self, driver):
        logger.info("test_connection_allocate_v2_mismatch_channel_id start")
        url = "http://{0}:{1}/connection/allocate/v2?channel_id=mismatch&package_name=com.cnvcs.junqi&version_code=151".format(
            driver["remote_ip"], driver["port"])
        header = {"Session-Token": driver["token"], "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 700
        assert "session mismatch channelId, packageName" in check_response["error"]

    def test_connection_allocate_v2_mismatch_package_name(self, driver):
        logger.info("test_connection_allocate_v2_mismatch_package_name start")
        url = "http://{0}:{1}/connection/allocate/v2?channel_id=auto_test&package_name=mismatch&version_code=151".format(
            driver["remote_ip"], driver["port"])
        header = {"Session-Token": driver["token"], "Peer-Id": driver["peer_id"],
                  "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 700
        assert "session mismatch channelId, packageName" in check_response["error"]

    # method GET
    def test_keep_alive(self, driver):
        logger.info("test_keep_alive start")
        # 绑定实例
        token = self.get_token(driver)
        self.connection_allocate_v2(driver, token)

        url = "http://{0}:{1}/session/keepalive".format(driver["remote_ip"], driver["port"])
        header = {"Session-Token": driver["token"], "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0

    # 没有绑定实例化，直接请求keep_alive
    def test_keep_alive_without_connection(self, driver):
        logger.info("test_keep_alive_without_connection start")
        # 只获取了token，没有去实例化
        token = self.get_token(driver)
        url = "http://{0}:{1}/session/keepalive".format(driver["remote_ip"], driver["port"])
        header = {"Session-Token": token, "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
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

    def test_session_close(self, driver):
        logger.info("test_session_close start")
        # 绑定实例
        token = self.get_token(driver)
        self.connection_allocate_v2(driver, token)

        url = "http://{0}:{1}/session/close".format(driver["remote_ip"], driver["port"])
        header = {"Session-Token": driver["token"], "x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0

    def test_session_close_without_token(self, driver):
        logger.info("test_session_close_without_token start")
        # 绑定实例
        token = self.get_token(driver)
        self.connection_allocate_v2(driver, token)

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
        logger.info("test_admin_connection_get start")
        # 绑定实例
        token = self.get_token(driver)
        self.connection_allocate_v2(driver, token)

        url = "http://{0}:{1}/admin/connection/get?sessionToken={2}".format(driver["remote_ip"], driver["port"],
                                                                            driver["token"])
        header = {"x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0

    def test_admin_connection_get_without_connection(self, driver):
        logger.info("test_admin_connection_get_without_connection start")
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
        logger.info("test_admin_connection_get_param_without_token start")
        # 绑定实例
        token = self.get_token(driver)
        self.connection_allocate_v2(driver, token)

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
    def test_admin_agent_msg_closed(self, driver):
        logger.info("test_admin_agent_msg_closed start")
        # 绑定实例
        token = self.get_token(driver)
        self.connection_allocate_v2(driver, token)
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

    def connection_get(self, driver):
        url = "http://{0}:{1}/admin/connection/get?sessionToken={2}".format(driver["remote_ip"], driver["port"],
                                                                            driver["token"])
        header = {"x-forwarded-for": driver["x-forwarded-for"]}
        response = RequestHttp().request_response(url=url, method="get", headers=header)
        return response

    def get_token(self, driver):
        url = "http://{0}:{1}/session/create".format(driver["remote_ip"], driver["port"])
        url = url + '?device_user={"auto_test":"auto_test"}'
        header = {"userid": "1", "appid": "auto_test", "x-forwarded-for": driver["x-forwarded-for"]}
        token = json.loads(requests.get(url, headers=header).text)["data"]["token"]
        return token


if __name__ == '__main__':
    pytest.main(["-s", "test_service_rtc.py"])

