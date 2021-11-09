# create_author: HuangYaxing
# create_time: 2021/10/19 8:19 下午

import pytest
import requests
import json
import random
import re
import os
import copy
import logging
from dependent.env_self import Env
from dependent.requests_http import RequestHttp

logger = logging.getLogger(__name__)
# 增加一些ip地址
# 测试域名console.galaxy142.com host绑定192.168.126.142再验证

# 考虑使用钉钉apk的url吧，虽然150M，但是没有防盗链啊，md5会变化呢
apk_url = "https://download.alicdn.com/wireless/dingtalk/latest/rimet_10002068.apk"
# apk_md5 = "588b2321f7af413ffe6b15a68030bac8"
apk_md5 = "b574011ba11e52e77ff169a77e183463"
apk_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Chess_v2.8.1.apk")
# service_core_domain = "http://console.galaxy142.com"
service_core_domain = "http://console.galaxy195.com"


class TestServiceRTC(object):
    @pytest.fixture(scope="session")
    def driver(self):
        # 设置默认的id值
        driver = {"customer_id": 1, "chan_id": "autotest", "channel_id": 6}

        url = "{0}/login".format(service_core_domain)
        response = requests.get(url)
        re_console = "console:token=.+?(?=;)|uc:token=.+?(?=;)"
        driver["cookie"] = ";".join(re.findall(re_console, response.headers["set-cookie"]))
        driver["headers"] = {"Content-Type": "application/json", "Cookie": driver["cookie"]}
        logger.debug("driver is {0}".format(driver))
        return driver

    @pytest.fixture()
    # 上传apk的时候，需要更新token信息
    # api-console.buffcloud.com 这个域名有绑定hosts，142和195切换需要更新hosts，等写完后，再该去env中去
    def upload_token(self, driver):
        get_token_url = "http://api-console.buffcloud.com/upload_token/get"
        token = json.loads(requests.get(get_token_url).text)["data"]["token"]
        logger.debug("token is {0}".format(token))
        return token

    @pytest.fixture()
    def upload_apk(self, driver, upload_token):
        # 先上传apk，获取apk信息
        upload_url = "http://api-console.buffcloud.com/upload/apk"
        # data里不需要有要上传的文件的字段
        data = {"uid": driver["customer_id"], "chan_id": driver["channel_id"]}
        # Headers中不需要填写Content-Type，上传后会自动填写的
        headers = {"X-Requested-With": "XMLHttpRequest", "User-Token": upload_token}
        # 这里的data不能用json格式
        response = requests.post(upload_url, data=data, headers=headers, files={"file": open(apk_file, "rb")})
        # service_core里不去校验返回信息，这个接口不是service_core返回的
        # assert response.status_code == 200
        # upload_response_info = json.loads(response.text)
        # assert upload_response_info["code"] == 0
        # assert "data" in upload_response_info
        # assert "download_url" in upload_response_info["data"]
        # assert "filemd5" in upload_response_info["data"]
        return json.loads(response.text)["data"]

    # 删除添加的游戏
    def game_delete(self, driver, gid):
        game_delete_url = "{0}/gameManage/index/internal/game/delete".format(service_core_domain)
        data = {"params": {"forward_method": "POST", "gid": gid}}
        response = RequestHttp().request_response(method="post", url=game_delete_url, data=data, headers=driver["headers"])
        return response

    def channel_list(self, driver, uid):
        url = "{0}/gameManage/index/internal/channel/list".format(service_core_domain)
        headers = driver["headers"]
        data = {"params": {"forward_method": "GET", "uid": uid}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        return response

    # method: POST
    def test_customer_list(self, driver):
        url = "{0}/gameManage/index/internal/customer/list".format(service_core_domain)
        headers = driver["headers"]
        data = {"params": {"forward_method": "GET"}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0
        assert "result" in check_response
        assert "id" in check_response["result"][0]
        for customer_info in check_response["result"]:
            if customer_info["name"] == "网心科技":
                driver["customer_id"] = customer_info["id"]

    def test_user_info_list(self, driver):
        url = "{0}/gameManage/index/internal/user/info_list".format(service_core_domain)
        headers = driver["headers"]
        data = {"params": {"forward_method": "GET"}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0
        assert "result" in check_response
        assert "id" in check_response["result"][0]
        assert "name" in check_response["result"][0]

    def test_channel_list(self, driver):
        response = self.channel_list(driver, driver["customer_id"])
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0
        assert "result" in check_response
        for channel_info in check_response["result"]:
            assert channel_info["uid"] == driver["customer_id"]
            if channel_info["name"] == "auto_test":
                driver["channel_id"] = channel_info["id"]

    # # 目前code会为0，result里为空
    # def test_channel_list_channel_id_not_exist(self, driver):
    #     response = self.channel_list(driver, 999)
    #     assert response.status_code == 200
    #     check_response = json.loads(response.text)
    #     assert check_response["code"] == 1
    #     assert "渠道不存在" in check_response["error"]

    # # 目前没有校验
    # def test_channel_list_channel_id_is_zero(self, driver):
    #     response = self.channel_list(driver, 0)
    #     assert response.status_code == 200
    #     check_response = json.loads(response.text)
    #     assert check_response["code"] == 1
    #     assert "参数错误" in check_response["error"]

    # # 目前没有判断必须传入uid，需要与研发确认是否要有这个逻辑在
    # def test_channel_list_no_uid(self, driver):
    #     url = "{0}/gameManage/index/internal/channel/list".format(service_core_domain)
    #     headers = driver["headers"]
    #     data = {"params": {"forward_method": "GET"}}
    #     response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
    #     assert response.status_code == 200
    #     check_response = json.loads(response.text)
    #     assert check_response["code"] == 1
    #     # assert "error" in check_response

    # # 没有见到验证
    # def test_channel_add_uid_not_exist(self, driver):
    #     url = "{0}/gameManage/index/internal/channel/add".format(service_core_domain)
    #     headers = driver["headers"]
    #     data = {"params": {"forward_method": "POST", "uid": 999, "chan_id": "test_test",
    #                        "name": "chan_id duplicate"}}
    #     response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
    #     assert response.status_code == 200
    #     check_response = json.loads(response.text)
    #     assert check_response["code"] == 1
    #     assert "参数错误" in check_response["error"]

    def test_channel_add_uid_is_zero(self, driver):
        url = "{0}/gameManage/index/internal/channel/add".format(service_core_domain)
        headers = driver["headers"]
        data = {"params": {"forward_method": "POST", "uid": 0, "chan_id": "test_test",
                           "name": "chan_id duplicate"}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "参数错误" in check_response["error"]

    def test_channel_add_chan_id_duplicate(self, driver):
        url = "{0}/gameManage/index/internal/channel/add".format(service_core_domain)
        headers = driver["headers"]
        data = {"params": {"forward_method": "POST", "uid": driver["customer_id"], "chan_id": "auto_test",
                           "name": "chan_id duplicate"}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "渠道ID重复" in check_response["error"]

    def test_channel_add_chan_id_is_null(self, driver):
        url = "{0}/gameManage/index/internal/channel/add".format(service_core_domain)
        headers = driver["headers"]
        data = {"params": {"forward_method": "POST", "uid": driver["customer_id"], "chan_id": "",
                           "name": "chan_id duplicate"}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "参数错误" in check_response["error"]

    def test_channel_add_chan_id_over_size(self, driver):
        url = "{0}/gameManage/index/internal/channel/add".format(service_core_domain)
        headers = driver["headers"]
        chan_id = ""
        # len(chan_id) > 32
        for _ in range(33):
            chan_id += "1"
        data = {"params": {"forward_method": "POST", "uid": driver["customer_id"], "chan_id": chan_id,
                           "name": "chan_id duplicate"}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "参数错误" in check_response["error"]

    def test_channel_add_name_is_null(self, driver):
        url = "{0}/gameManage/index/internal/channel/add".format(service_core_domain)
        headers = driver["headers"]
        data = {"params": {"forward_method": "POST", "uid": driver["customer_id"], "chan_id": "test_test",
                           "name": ""}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "参数错误" in check_response["error"]

    def test_channel_add_name_over_size(self, driver):
        url = "{0}/gameManage/index/internal/channel/add".format(service_core_domain)
        headers = driver["headers"]
        name = ""
        # len(name)>128
        for _ in range(129):
            name += "1"
        data = {"params": {"forward_method": "POST", "uid": driver["customer_id"], "chan_id": "test_test",
                           "name": name}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "参数错误" in check_response["error"]

    def test_channel_add_required_param_lost_uid(self, driver):
        url = "{0}/gameManage/index/internal/channel/add".format(service_core_domain)
        headers = driver["headers"]
        data = {"params": {"forward_method": "POST", "chan_id": "auto_test", "name": "chan_id duplicate"}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "参数错误" in check_response["error"]

    def test_channel_add_required_param_lost_chan_id(self, driver):
        url = "{0}/gameManage/index/internal/channel/add".format(service_core_domain)
        headers = driver["headers"]
        data = {"params": {"forward_method": "POST", "uid": driver["customer_id"], "name": "chan_id duplicate"}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "参数错误" in check_response["error"]

    def test_channel_add_required_param_lost_name(self, driver):
        url = "{0}/gameManage/index/internal/channel/add".format(service_core_domain)
        headers = driver["headers"]
        data = {"params": {"forward_method": "POST", "uid": driver["customer_id"], "chan_id": "test_service_core"}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "参数错误" in check_response["error"]

    def test_channel_update_modify_name(self, driver):
        cid = 0
        channel_list = json.loads(self.channel_list(driver, driver["customer_id"]).text)["result"]
        for channel in channel_list:
            if channel["chan_id"] == "auto_test":
                cid = channel["id"]
        url = "{0}/gameManage/index/internal/channel/update".format(service_core_domain)
        headers = driver["headers"]
        data = {"params": {"forward_method": "POST", "cid": cid, "name": "auto_test_1"}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0
        assert "ok" in check_response["result"]["message"].lower()

        # 把name改回测试配置
        data = {"params": {"forward_method": "POST", "cid": cid, "name": "auto_test"}}
        RequestHttp().request_response(method="post", url=url, headers=headers, data=data)

    def test_channel_update_cid_not_exist(self, driver):
        cid = 0
        channel_list = json.loads(self.channel_list(driver, driver["customer_id"]).text)["result"]
        for channel in channel_list:
            if channel["chan_id"] == "auto_test":
                cid = channel["id"] + 999
        url = "{0}/gameManage/index/internal/channel/update".format(service_core_domain)
        headers = driver["headers"]
        data = {"params": {"forward_method": "POST", "cid": cid, "name": "auto_test"}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "渠道不存在" in check_response["error"]

    def test_channel_update_cid_is_zero(self, driver):
        url = "{0}/gameManage/index/internal/channel/update".format(service_core_domain)
        headers = driver["headers"]
        data = {"params": {"forward_method": "POST", "cid": 0, "name": "auto_test"}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "参数错误" in check_response["error"]

    def test_channel_update_name_null(self, driver):
        cid = 0
        channel_list = json.loads(self.channel_list(driver, driver["customer_id"]).text)["result"]
        for channel in channel_list:
            if channel["chan_id"] == "auto_test":
                cid = channel["id"]
        url = "{0}/gameManage/index/internal/channel/update".format(service_core_domain)
        headers = driver["headers"]
        data = {"params": {"forward_method": "POST", "cid": cid, "name": ""}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "参数错误" in check_response["error"]

    def test_channel_update_lost_params(self, driver):
        cid = 0
        channel_list = json.loads(self.channel_list(driver, driver["customer_id"]).text)["result"]
        for channel in channel_list:
            if channel["chan_id"] == "auto_test":
                cid = channel["id"]
        url = "{0}/gameManage/index/internal/channel/update".format(service_core_domain)
        headers = driver["headers"]
        data = {"params": {"forward_method": "POST", "cid": cid, "name": "auto_test"}}
        # lost cid
        update_data = copy.deepcopy(data)
        update_data["params"].pop("cid")
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=update_data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "参数错误" in check_response["error"]

        # lost name
        update_data = copy.deepcopy(data)
        update_data["params"].pop("name")
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=update_data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "参数错误" in check_response["error"]

    def test_channel_detail(self, driver):
        cid = 0
        channel_list = json.loads(self.channel_list(driver, driver["customer_id"]).text)["result"]
        for channel in channel_list:
            if channel["chan_id"] == "auto_test":
                cid = channel["id"]
        url = "{0}/gameManage/index/internal/channel/detail".format(service_core_domain)
        headers = driver["headers"]
        data = {"params": {"forward_method": "GET", "cid": cid}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0
        assert "auto_test" in check_response["result"]["chan_id"]

    # # 没有校验一定要有cid不为0，返回渠道不存在
    # def test_channel_detail_cid_is_zero(self, driver):
    #     cid = 0
    #     url = "{0}/gameManage/index/internal/channel/detail".format(service_core_domain)
    #     headers = driver["headers"]
    #     data = {"params": {"forward_method": "GET", "cid": cid}}
    #     response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
    #     assert response.status_code == 200
    #     check_response = json.loads(response.text)
    #     assert check_response["code"] == 1
    #     assert "参数错误" in check_response["error"]

    def test_channel_detail_cid_not_exist(self, driver):
        url = "{0}/gameManage/index/internal/channel/detail".format(service_core_domain)
        headers = driver["headers"]
        data = {"params": {"forward_method": "GET", "cid": 999}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "渠道数据不存在" in check_response["error"]

    # # 竟然允许cid不存在？返回了channel_id为1的数据
    # def test_channel_detail_lost_param(self, driver):
    #     url = "{0}/gameManage/index/internal/channel/detail".format(service_core_domain)
    #     headers = driver["headers"]
    #     data = {"params": {"forward_method": "GET"}}
    #     response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
    #     assert response.status_code == 200
    #     check_response = json.loads(response.text)
    #     assert check_response["code"] == 1
    #     assert "参数错误" in check_response["error"]

    def test_game_list(self, driver):
        url = "{0}/gameManage/index/internal/game/list".format(service_core_domain)
        headers = driver["headers"]
        data = {"params": {"forward_method": "GET", "uid": driver["customer_id"], "channel_id": driver["channel_id"]}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0
        assert "result" in check_response
        for result_info in check_response["result"]:
            assert result_info["uid"] == driver["customer_id"]
            assert result_info["channel_id"] == driver["channel_id"]

    # # 目前没有校验
    # def test_game_list_uid_is_zero(self, driver):
    #     url = "{0}/gameManage/index/internal/game/list".format(service_core_domain)
    #     headers = driver["headers"]
    #     data = {"params": {"forward_method": "GET", "uid": 0, "channel_id": driver["channel_id"]}}
    #     response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
    #     assert response.status_code == 200
    #     check_response = json.loads(response.text)
    #     assert check_response["code"] == 1
    #     assert "参数错误" in check_response["error"]

    # # 目前没有校验
    # def test_game_list_uid_not_exist(self, driver):
    #     url = "{0}/gameManage/index/internal/game/list".format(service_core_domain)
    #     headers = driver["headers"]
    #     data = {"params": {"forward_method": "GET", "uid": 999, "channel_id": driver["channel_id"]}}
    #     response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
    #     assert response.status_code == 200
    #     check_response = json.loads(response.text)
    #     assert check_response["code"] == 1
    #     assert "参数错误" in check_response["error"]

    # # 目前没有校验
    # def test_game_list_channel_is_zaro(self, driver):
    #     url = "{0}/gameManage/index/internal/game/list".format(service_core_domain)
    #     headers = driver["headers"]
    #     data = {"params": {"forward_method": "GET", "uid": driver["customer_id"], "channel_id": 0}}
    #     response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
    #     assert response.status_code == 200
    #     check_response = json.loads(response.text)
    #     assert check_response["code"] == 1
    #     assert "参数错误" in check_response["error"]

    # # 目前没有校验
    # def test_game_list_channel_not_exist(self, driver):
    #     url = "{0}/gameManage/index/internal/game/list".format(service_core_domain)
    #     headers = driver["headers"]
    #     data = {"params": {"forward_method": "GET", "uid": driver["customer_id"], "channel_id": driver["channel_id"]}}
    #     game_data = copy.deepcopy(data)
    #
    #     # lost uid
    #     game_data["params"].pop("uid")
    #     response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
    #     assert response.status_code == 200
    #     check_response = json.loads(response.text)
    #     assert check_response["code"] == 1
    #     assert "参数错误" in check_response["error"]
    #
    #     # lost channel_id
    #     game_data["params"].pop("channel_id")
    #     response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
    #     assert response.status_code == 200
    #     check_response = json.loads(response.text)
    #     assert check_response["code"] == 1
    #     assert "参数错误" in check_response["error"]

    # 目前没有校验
    def test_game_list_lost_params(self, driver):
        url = "{0}/gameManage/index/internal/game/list".format(service_core_domain)
        headers = driver["headers"]
        data = {"params": {"forward_method": "GET", "uid": driver["customer_id"], "channel_id": 999}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "参数错误" in check_response["error"]

    def test_game_add_upload_type_local(self, driver, upload_apk):
        add_url = "{0}/gameManage/index/internal/game/add".format(service_core_domain)
        headers = driver["headers"]
        add_data = {
            "params": {
                "forward_method": "POST",
                "uid": driver["customer_id"],
                "channel_id": driver["channel_id"],
                "name": "test apk",
                "desc": "test",

                # 本地上传以及包名的数据
                "upload_type": 1,
                "download_url": upload_apk["download_url"],
                "filemd5": upload_apk["filemd5"],
                "package_name": upload_apk["package_name"],
                "version_code": upload_apk["version_code"],
                "version_name": upload_apk["version_name"],

                # 游戏类型与类别
                "category_id": 1,
                "type_ids": "17, 18",

                # 最大并发数与实例数量
                "max_concurrent": 0,
                "instance_type": 0,
                "quality": "720p",
            }
        }
        response = RequestHttp().request_response(method="post", url=add_url, data=add_data, headers=headers)
        assert response.status_code == 200
        add_response_info = json.loads(response.text)
        assert add_response_info["code"] == 0
        assert "result" in add_response_info
        gid = add_response_info["result"]["gid"]
        # 删除一下添加的游戏
        self.game_delete(driver, gid)

    def test_game_add_upload_type_url(self, driver):
        add_url = "{0}/gameManage/index/internal/game/add".format(service_core_domain)
        headers = driver["headers"]
        add_data = {
            "params": {
                "forward_method": "POST",
                "uid": driver["customer_id"],
                "channel_id": driver["channel_id"],
                "name": "test apk",
                "desc": "test",

                # 网络上传
                "upload_type": 2,
                "upload_url": apk_url,
                "md5": apk_md5,

                # 游戏类型与类别
                "category_id": 1,
                "type_ids": "17, 18",

                # 最大并发数与实例数量
                "max_concurrent": 0,
                "instance_type": 0,
                "quality": "720p",
            }
        }

        response = RequestHttp().request_response(method="post", url=add_url, data=add_data, headers=headers)
        assert response.status_code == 200
        add_response_info = json.loads(response.text)
        assert add_response_info["code"] == 0
        assert "result" in add_response_info
        gid = add_response_info["result"]["gid"]
        # 删除一下添加的游戏
        self.game_delete(driver, gid)

    def test_game_add_channel_not_exist(self, driver):
        add_url = "{0}/gameManage/index/internal/game/add".format(service_core_domain)
        headers = driver["headers"]
        data = {
            "params": {
                "forward_method": "POST",
                "uid": driver["customer_id"],
                # channel not exist
                "channel_id": 999,
                "name": "test apk",
                "desc": "test",

                # 网络上传
                "upload_type": 2,
                "upload_url": apk_url,
                "md5": apk_md5,

                # 游戏类型与类别
                "category_id": 1,
                "type_ids": "17, 18",

                # 最大并发数与实例数量
                "instance_type": 0,
                "max_concurrent": 0,
                "quality": "720p",
            }
        }
        response = RequestHttp().request_response(method="post", url=add_url, data=data,
                                                  headers=headers)
        assert response.status_code == 200
        add_response_info = json.loads(response.text)
        assert add_response_info["code"] == 1
        assert "渠道信息不存在" in add_response_info["error"]

    # # 目前没有判断uid是否存在
    # def test_game_add_uid_not_exist(self, driver):
    #     add_url = "{0}/gameManage/index/internal/game/add".format(service_core_domain)
    #     headers = driver["headers"]
    #     data = {
    #         "params": {
    #             "forward_method": "POST",
    #             # uid not exist
    #             "uid": 999,
    #             "channel_id": driver["channel_id"],
    #             "name": "test apk",
    #             "desc": "test",
    #
    #             # 网络上传
    #             "upload_type": 2,
    #             "upload_url": apk_url,
    #             "md5": apk_md5,
    #
    #             # 游戏类型与类别
    #             "category_id": 1,
    #             "type_ids": "17, 18",
    #
    #             # 最大并发数与实例数量
    #             "instance_type": 0,
    #             "max_concurrent": 0,
    #             "quality": "720p",
    #         }
    #     }
    #     response = RequestHttp().request_response(method="post", url=add_url, data=data,
    #                                               headers=headers)
    #     assert response.status_code == 200
    #     add_response_info = json.loads(response.text)
    #     assert add_response_info["code"] == 1
    #     assert "uid信息不存在" in add_response_info["error"]

    def test_game_add_lost_params(self, driver, upload_apk):
        add_url = "{0}/gameManage/index/internal/game/add".format(service_core_domain)
        headers = driver["headers"]
        data = {
            "params": {
                "forward_method": "POST",
                "uid": driver["customer_id"],
                "channel_id": driver["channel_id"],
                "name": "test apk",
                # desc 不是必填项，不校验
                "desc": "test",

                # 本地上传以及包名的数据
                "upload_type": 1,
                "download_url": upload_apk["download_url"],
                "filemd5": upload_apk["filemd5"],
                "package_name": upload_apk["package_name"],
                "version_code": upload_apk["version_code"],
                "version_name": upload_apk["version_name"],

                # 游戏类型与类别
                "category_id": 1,
                "type_ids": "17, 18",

                # 最大并发数与实例数量
                "instance_type": 0,
                "max_concurrent": 0,
                "quality": "720p",
            }
        }
        # lost uid
        lost_download_url_data = copy.deepcopy(data)
        lost_download_url_data["params"].pop("uid")
        response = RequestHttp().request_response(method="post", url=add_url, data=lost_download_url_data, headers=headers)
        assert response.status_code == 200
        add_response_info = json.loads(response.text)
        assert add_response_info["code"] == 1
        assert "uid不能为空" in add_response_info["error"]

        # lost channel_id
        lost_download_url_data = copy.deepcopy(data)
        lost_download_url_data["params"].pop("channel_id")
        response = RequestHttp().request_response(method="post", url=add_url, data=lost_download_url_data,
                                                  headers=headers)
        assert response.status_code == 200
        add_response_info = json.loads(response.text)
        assert add_response_info["code"] == 1
        assert "渠道id不能为空" in add_response_info["error"]

        # lost name
        lost_download_url_data = copy.deepcopy(data)
        lost_download_url_data["params"].pop("name")
        response = RequestHttp().request_response(method="post", url=add_url, data=lost_download_url_data,
                                                  headers=headers)
        assert response.status_code == 200
        add_response_info = json.loads(response.text)
        assert add_response_info["code"] == 1
        assert "请输入游戏名称" in add_response_info["error"]

        # lost upload_type
        lost_download_url_data = copy.deepcopy(data)
        lost_download_url_data["params"].pop("upload_type")
        response = RequestHttp().request_response(method="post", url=add_url, data=lost_download_url_data,
                                                  headers=headers)
        assert response.status_code == 200
        add_response_info = json.loads(response.text)
        assert add_response_info["code"] == 1
        assert "请选择上传游戏包方式" in add_response_info["error"]

        # lost category_id
        lost_download_url_data = copy.deepcopy(data)
        lost_download_url_data["params"].pop("category_id")
        response = RequestHttp().request_response(method="post", url=add_url, data=lost_download_url_data,
                                                  headers=headers)
        assert response.status_code == 200
        add_response_info = json.loads(response.text)
        assert add_response_info["code"] == 1
        assert "请选择游戏类别" in add_response_info["error"]

        # lost type_ids
        lost_download_url_data = copy.deepcopy(data)
        lost_download_url_data["params"].pop("type_ids")
        response = RequestHttp().request_response(method="post", url=add_url, data=lost_download_url_data,
                                                  headers=headers)
        assert response.status_code == 200
        add_response_info = json.loads(response.text)
        assert add_response_info["code"] == 1
        assert "请选择游戏类型" in add_response_info["error"]

        # 可以在download_url类似的地方，增加一个判断 != "" 的逻辑，就可以覆盖到非required的字段存在了
        # # lost instance_type
        # lost_download_url_data = copy.deepcopy(data)
        # lost_download_url_data["params"].pop("instance_type")
        # response = RequestHttp().request_response(method="post", url=add_url, data=lost_download_url_data,
        #                                           headers=headers)
        # assert response.status_code == 200
        # add_response_info = json.loads(response.text)
        # assert add_response_info["code"] == 1
        # # assert "system error" in add_response_info["error"]
        #
        # # lost max_concurrent
        # lost_download_url_data = copy.deepcopy(data)
        # lost_download_url_data["params"].pop("max_concurrent")
        # response = RequestHttp().request_response(method="post", url=add_url, data=lost_download_url_data,
        #                                           headers=headers)
        # assert response.status_code == 200
        # add_response_info = json.loads(response.text)
        # assert add_response_info["code"] == 1
        # # assert "system error" in add_response_info["error"]

        # lost quality
        lost_download_url_data = copy.deepcopy(data)
        lost_download_url_data["params"].pop("quality")
        response = RequestHttp().request_response(method="post", url=add_url, data=lost_download_url_data,
                                                  headers=headers)
        assert response.status_code == 200
        add_response_info = json.loads(response.text)
        assert add_response_info["code"] == 1
        assert "请选择播流画质" in add_response_info["error"]

    def test_game_add_upload_type_local_lost_param(self, driver, upload_apk):
        # 本地添加, 先上传apk
        add_url = "{0}/gameManage/index/internal/game/add".format(service_core_domain)
        headers = driver["headers"]
        data = {
            "params": {
                "forward_method": "POST",
                "uid": driver["customer_id"],
                "channel_id": driver["channel_id"],
                "name": "test apk",
                "desc": "test",

                # 本地上传以及包名的数据
                "upload_type": 1,
                "download_url": upload_apk["download_url"],
                "filemd5": upload_apk["filemd5"],
                "package_name": upload_apk["package_name"],
                "version_code": upload_apk["version_code"],
                "version_name": upload_apk["version_name"],

                # 游戏类型与类别
                "category_id": 1,
                "type_ids": "17, 18",

                # 最大并发数与实例数量
                "max_concurrent": 0,
                "instance_type": 0,
                "quality": "720p",
            }
        }
        # lost download_url
        lost_download_url_data = copy.deepcopy(data)
        lost_download_url_data["params"].pop("download_url")
        response = RequestHttp().request_response(method="post", url=add_url, data=lost_download_url_data,
                                                  headers=headers)
        assert response.status_code == 200
        add_response_info = json.loads(response.text)
        assert add_response_info["code"] == 1
        assert "请选择上传游戏包apk文件" in add_response_info["error"]

        # lost filemd5
        lost_download_url_data = copy.deepcopy(data)
        lost_download_url_data["params"].pop("filemd5")
        response = RequestHttp().request_response(method="post", url=add_url, data=lost_download_url_data,
                                                  headers=headers)
        assert response.status_code == 200
        add_response_info = json.loads(response.text)
        assert add_response_info["code"] == 1
        assert "请选择上传游戏包apk文件" in add_response_info["error"]

        # lost package_name
        lost_download_url_data = copy.deepcopy(data)
        lost_download_url_data["params"].pop("package_name")
        response = RequestHttp().request_response(method="post", url=add_url, data=lost_download_url_data,
                                                  headers=headers)
        assert response.status_code == 200
        add_response_info = json.loads(response.text)
        assert add_response_info["code"] == 1
        assert "请选择上传游戏包apk文件" in add_response_info["error"]

        # lost version_code
        lost_download_url_data = copy.deepcopy(data)
        lost_download_url_data["params"].pop("version_code")
        response = RequestHttp().request_response(method="post", url=add_url, data=lost_download_url_data,
                                                  headers=headers)
        assert response.status_code == 200
        add_response_info = json.loads(response.text)
        assert add_response_info["code"] == 1
        assert "请选择上传游戏包apk文件" in add_response_info["error"]

        # lost version_name
        lost_download_url_data = copy.deepcopy(data)
        lost_download_url_data["params"].pop("version_name")
        response = RequestHttp().request_response(method="post", url=add_url, data=lost_download_url_data,
                                                  headers=headers)
        assert response.status_code == 200
        add_response_info = json.loads(response.text)
        assert add_response_info["code"] == 1
        assert "请选择上传游戏包apk文件" in add_response_info["error"]

    def test_game_add_upload_type_url_lost_info(self, driver):
        add_url = "{0}/gameManage/index/internal/game/add".format(service_core_domain)
        headers = driver["headers"]
        data = {
            "params": {
                "forward_method": "POST",
                "uid": driver["customer_id"],
                "channel_id": driver["channel_id"],
                "name": "test apk",
                "desc": "test",

                # 网络上传
                "upload_type": 2,
                "upload_url": apk_url,
                "md5": apk_md5,

                # 游戏类型与类别
                "category_id": 1,
                "type_ids": "17, 18",

                # 最大并发数与实例数量
                "max_concurrent": 0,
                "instance_type": 0,
                "quality": "720p",
            }
        }
        # lost upload_url
        lost_download_url_data = copy.deepcopy(data)
        lost_download_url_data["params"].pop("upload_url")
        response = RequestHttp().request_response(method="post", url=add_url, data=lost_download_url_data, headers=headers)
        assert response.status_code == 200
        add_response_info = json.loads(response.text)
        assert add_response_info["code"] == 1
        assert "请输入游戏包下载地址" in add_response_info["error"]

        # lost md5
        lost_download_url_data = copy.deepcopy(data)
        lost_download_url_data["params"].pop("md5")
        response = RequestHttp().request_response(method="post", url=add_url, data=lost_download_url_data,
                                                  headers=headers)
        assert response.status_code == 200
        add_response_info = json.loads(response.text)
        assert add_response_info["code"] == 1
        assert "请输入上传游戏包md5值" in add_response_info["error"]


if __name__ == '__main__':
    pytest.main(["-s", "test_service_core.py"])
    # TestServiceRTC().get_token()
