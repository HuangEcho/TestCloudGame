# create_author: HuangYaxing
# create_time: 2021/10/19 8:19 下午

import pytest
import requests
import json
import time
import re
import os
import copy
import logging
import allure
from dependent.env_self import Env
from dependent.mysql_operation import MysqlOperation
from dependent.requests_http import RequestHttp

logger = logging.getLogger(__name__)
# 增加一些ip地址
# 测试域名console.galaxy142.com host绑定192.168.126.142再验证

# 考虑使用钉钉apk的url吧，虽然150M，但是没有防盗链啊，md5会变化呢
apk_url = "https://download.alicdn.com/wireless/dingtalk/latest/rimet_10002068.apk"
# apk_md5 = "588b2321f7af413ffe6b15a68030bac8"
apk_md5 = "b574011ba11e52e77ff169a77e183463"
apk_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Chess_v2.8.1.apk")


@allure.feature("service_core")
@allure.story("service_core-业务模块")
@allure.suite("service_core-业务模块")
class TestServiceRTC(object):
    @pytest.fixture(scope="session")
    def driver(self):
        logger.info("test case setup")
        env = Env()
        env.get_env_info()
        environment = env.env["service_core"]
        
        # 设置默认的id值
        driver = {"customer_id": 1, "chan_id": "autotest", "channel_id": 6, "test_domain": environment["domain"]}

        url = "{0}/login".format(driver["test_domain"])
        response = requests.get(url)
        re_console = "console:token=.+?(?=;)|uc:token=.+?(?=;)"
        driver["cookie"] = ";".join(re.findall(re_console, response.headers["set-cookie"]))
        driver["headers"] = {"Content-Type": "application/json", "Cookie": driver["cookie"]}
        logger.debug("driver is {0}".format(driver))

        # 查询到test apk任务的id，调用delete接口删除任务，不要直接删除数据库里数据
        mysql_env = environment["mysql"]
        db = MysqlOperation().connect_mysql(mysql_env)
        # sql = "delete from buffcloud_core.game_manage where name like 'test apk';"
        # MysqlOperation().commit_mysql(db, sql)
        sql = "select id from buffcloud_core.game_manage where name='test apk';"
        # gids为tuple类型
        gids = MysqlOperation().query_mysql(db, sql)
        logger.debug("query gid is {0}".format(gids))
        MysqlOperation().close_mysql(db)
        if len(gids) > 0:
            for gid in gids:
                # gid还是tuple类型
                self.game_delete(driver, int(gid[0]))
                logger.debug("detele task, gid is {0}".format(gid))

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
        game_delete_url = "{0}/gameManage/index/internal/game/delete".format(driver["test_domain"])
        data = {"params": {"forward_method": "POST", "gid": gid}}
        response = RequestHttp().request_response(method="post", url=game_delete_url, data=data, headers=driver["headers"])
        return response

    def channel_list(self, driver, uid):
        url = "{0}/gameManage/index/internal/channel/list".format(driver["test_domain"])
        headers = driver["headers"]
        data = {"params": {"forward_method": "GET", "uid": uid}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        return response

    def url_data(self, driver):
        data = {
            "params": {
                "forward_method": "POST",
                "uid": driver["customer_id"],
                "channel_id": driver["channel_id"],
                "name": "test apk",
                "desc": "test",

                # 本地上传以及包名的数据
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
        return data

    def local_data(self, driver, upload_apk):
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
        return data

    # method: POST
    def test_customer_list(self, driver):
        url = "{0}/gameManage/index/internal/customer/list".format(driver["test_domain"])
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
        url = "{0}/gameManage/index/internal/user/info_list".format(driver["test_domain"])
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
    #     url = "{0}/gameManage/index/internal/channel/list".format(driver["test_domain"])
    #     headers = driver["headers"]
    #     data = {"params": {"forward_method": "GET"}}
    #     response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
    #     assert response.status_code == 200
    #     check_response = json.loads(response.text)
    #     assert check_response["code"] == 1
    #     # assert "error" in check_response

    # # 没有见到验证
    # def test_channel_add_uid_not_exist(self, driver):
    #     url = "{0}/gameManage/index/internal/channel/add".format(driver["test_domain"])
    #     headers = driver["headers"]
    #     data = {"params": {"forward_method": "POST", "uid": 999, "chan_id": "test_test",
    #                        "name": "chan_id duplicate"}}
    #     response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
    #     assert response.status_code == 200
    #     check_response = json.loads(response.text)
    #     assert check_response["code"] == 1
    #     assert "参数错误" in check_response["error"]

    def test_channel_add_uid_is_zero(self, driver):
        url = "{0}/gameManage/index/internal/channel/add".format(driver["test_domain"])
        headers = driver["headers"]
        data = {"params": {"forward_method": "POST", "uid": 0, "chan_id": "test_test",
                           "name": "chan_id duplicate"}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "参数错误" in check_response["error"]

    def test_channel_add_chan_id_duplicate(self, driver):
        url = "{0}/gameManage/index/internal/channel/add".format(driver["test_domain"])
        headers = driver["headers"]
        data = {"params": {"forward_method": "POST", "uid": driver["customer_id"], "chan_id": "auto_test",
                           "name": "chan_id duplicate"}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "渠道ID重复" in check_response["error"]

    def test_channel_add_chan_id_is_null(self, driver):
        url = "{0}/gameManage/index/internal/channel/add".format(driver["test_domain"])
        headers = driver["headers"]
        data = {"params": {"forward_method": "POST", "uid": driver["customer_id"], "chan_id": "",
                           "name": "chan_id duplicate"}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "参数错误" in check_response["error"]

    def test_channel_add_chan_id_over_size(self, driver):
        url = "{0}/gameManage/index/internal/channel/add".format(driver["test_domain"])
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
        url = "{0}/gameManage/index/internal/channel/add".format(driver["test_domain"])
        headers = driver["headers"]
        data = {"params": {"forward_method": "POST", "uid": driver["customer_id"], "chan_id": "test_test",
                           "name": ""}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "参数错误" in check_response["error"]

    def test_channel_add_name_over_size(self, driver):
        url = "{0}/gameManage/index/internal/channel/add".format(driver["test_domain"])
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
        url = "{0}/gameManage/index/internal/channel/add".format(driver["test_domain"])
        headers = driver["headers"]
        data = {"params": {"forward_method": "POST", "chan_id": "auto_test", "name": "chan_id duplicate"}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "参数错误" in check_response["error"]

    def test_channel_add_required_param_lost_chan_id(self, driver):
        url = "{0}/gameManage/index/internal/channel/add".format(driver["test_domain"])
        headers = driver["headers"]
        data = {"params": {"forward_method": "POST", "uid": driver["customer_id"], "name": "chan_id duplicate"}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "参数错误" in check_response["error"]

    def test_channel_add_required_param_lost_name(self, driver):
        url = "{0}/gameManage/index/internal/channel/add".format(driver["test_domain"])
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
        url = "{0}/gameManage/index/internal/channel/update".format(driver["test_domain"])
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
        url = "{0}/gameManage/index/internal/channel/update".format(driver["test_domain"])
        headers = driver["headers"]
        data = {"params": {"forward_method": "POST", "cid": 999, "name": "auto_test"}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "渠道不存在" in check_response["error"]

        url = "{0}/gameManage/index/internal/channel/update".format(driver["test_domain"])
        headers = driver["headers"]
        data = {"params": {"forward_method": "POST", "cid": -1, "name": "auto_test"}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "渠道不存在" in check_response["error"]

    def test_channel_update_cid_is_zero(self, driver):
        url = "{0}/gameManage/index/internal/channel/update".format(driver["test_domain"])
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
        url = "{0}/gameManage/index/internal/channel/update".format(driver["test_domain"])
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
        url = "{0}/gameManage/index/internal/channel/update".format(driver["test_domain"])
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
        url = "{0}/gameManage/index/internal/channel/detail".format(driver["test_domain"])
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
    #     url = "{0}/gameManage/index/internal/channel/detail".format(driver["test_domain"])
    #     headers = driver["headers"]
    #     data = {"params": {"forward_method": "GET", "cid": cid}}
    #     response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
    #     assert response.status_code == 200
    #     check_response = json.loads(response.text)
    #     assert check_response["code"] == 1
    #     assert "参数错误" in check_response["error"]

    def test_channel_detail_cid_not_exist(self, driver):
        url = "{0}/gameManage/index/internal/channel/detail".format(driver["test_domain"])
        headers = driver["headers"]
        data = {"params": {"forward_method": "GET", "cid": 999}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "渠道数据不存在" in check_response["error"]

        url = "{0}/gameManage/index/internal/channel/detail".format(driver["test_domain"])
        headers = driver["headers"]
        data = {"params": {"forward_method": "GET", "cid": -1}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "渠道数据不存在" in check_response["error"]

    # # 竟然允许cid不存在？返回了channel_id为1的数据
    # def test_channel_detail_lost_param(self, driver):
    #     url = "{0}/gameManage/index/internal/channel/detail".format(driver["test_domain"])
    #     headers = driver["headers"]
    #     data = {"params": {"forward_method": "GET"}}
    #     response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
    #     assert response.status_code == 200
    #     check_response = json.loads(response.text)
    #     assert check_response["code"] == 1
    #     assert "参数错误" in check_response["error"]

    def test_game_list(self, driver):
        url = "{0}/gameManage/index/internal/game/list".format(driver["test_domain"])
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
    #     url = "{0}/gameManage/index/internal/game/list".format(driver["test_domain"])
    #     headers = driver["headers"]
    #     data = {"params": {"forward_method": "GET", "uid": 0, "channel_id": driver["channel_id"]}}
    #     response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
    #     assert response.status_code == 200
    #     check_response = json.loads(response.text)
    #     assert check_response["code"] == 1
    #     assert "参数错误" in check_response["error"]

    # 目前没有校验
    # def test_game_list_uid_not_exist(self, driver):
    #     url = "{0}/gameManage/index/internal/game/list".format(driver["test_domain"])
    #     headers = driver["headers"]
    #     data = {"params": {"forward_method": "GET", "uid": 999, "channel_id": driver["channel_id"]}}
    #     response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
    #     assert response.status_code == 200
    #     check_response = json.loads(response.text)
    #     assert check_response["code"] == 1
    #     assert "参数错误" in check_response["error"]
    #
    #     url = "{0}/gameManage/index/internal/game/list".format(driver["test_domain"])
    #     headers = driver["headers"]
    #     data = {"params": {"forward_method": "GET", "uid": -1, "channel_id": driver["channel_id"]}}
    #     response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
    #     assert response.status_code == 200
    #     check_response = json.loads(response.text)
    #     assert check_response["code"] == 1
    #     assert "参数错误" in check_response["error"]

    # # 目前没有校验
    # def test_game_list_channel_is_zero(self, driver):
    #     url = "{0}/gameManage/index/internal/game/list".format(driver["test_domain"])
    #     headers = driver["headers"]
    #     data = {"params": {"forward_method": "GET", "uid": driver["customer_id"], "channel_id": 0}}
    #     response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
    #     assert response.status_code == 200
    #     check_response = json.loads(response.text)
    #     assert check_response["code"] == 1
    #     assert "参数错误" in check_response["error"]

    # # 目前没有校验
    # def test_game_list_channel_id_not_exist(self, driver):
    #     url = "{0}/gameManage/index/internal/game/list".format(driver["test_domain"])
    #     headers = driver["headers"]
    #     data = {"params": {"forward_method": "GET", "uid": driver["customer_id"], "channel_id": 999}}
    #     response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
    #     assert response.status_code == 200
    #     check_response = json.loads(response.text)
    #     assert check_response["code"] == 1
    #     assert "参数错误" in check_response["error"]
    #
    #     url = "{0}/gameManage/index/internal/game/list".format(driver["test_domain"])
    #     headers = driver["headers"]
    #     data = {"params": {"forward_method": "GET", "uid": driver["customer_id"], "channel_id": -1}}
    #     response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
    #     assert response.status_code == 200
    #     check_response = json.loads(response.text)
    #     assert check_response["code"] == 1
    #     assert "参数错误" in check_response["error"]

    # # 目前没有校验
    # def test_game_list_lost_params(self, driver):
    #     url = "{0}/gameManage/index/internal/game/list".format(driver["test_domain"])
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

    def test_game_add_upload_type_local(self, driver, upload_apk):
        add_url = "{0}/gameManage/index/internal/game/add".format(driver["test_domain"])
        headers = driver["headers"]
        data = self.local_data(driver, upload_apk)
        response = RequestHttp().request_response(method="post", url=add_url, data=data, headers=headers)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0
        assert "result" in check_response
        gid = check_response["result"]["gid"]
        # 删除一下添加的游戏
        time.sleep(1)
        self.game_delete(driver, gid)

    def test_game_add_upload_type_url(self, driver):
        add_url = "{0}/gameManage/index/internal/game/add".format(driver["test_domain"])
        headers = driver["headers"]
        data = self.url_data(driver)

        response = RequestHttp().request_response(method="post", url=add_url, data=data, headers=headers)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0
        assert "result" in check_response
        gid = check_response["result"]["gid"]
        # 删除一下添加的游戏
        time.sleep(1)
        self.game_delete(driver, gid)

    def test_game_add_uid_is_zero(self, driver):
        add_url = "{0}/gameManage/index/internal/game/add".format(driver["test_domain"])
        headers = driver["headers"]
        data = copy.deepcopy(self.url_data(driver))

        # uid设置为0
        data["params"]["uid"] = 0
        response = RequestHttp().request_response(method="post", url=add_url, data=data,
                                                  headers=headers)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "uid不能为空" in check_response["error"]

    # # 目前没有判断uid是否存在
    # def test_game_add_uid_not_exist(self, driver):
    #     add_url = "{0}/gameManage/index/internal/game/add".format(driver["test_domain"])
    #     headers = driver["headers"]
    #     data = copy.deepcopy(self.url_data(driver))
    #
    #     # uid设置为999，不存在
    #     data["params"]["uid"] = 999
    #     response = RequestHttp().request_response(method="post", url=add_url, data=data,
    #                                               headers=headers)
    #     assert response.status_code == 200
    #     check_response = json.loads(response.text)
    #     assert check_response["code"] == 1
    #     assert "uid信息不存在" in check_response["error"]
    #
    #     data["params"]["uid"] = -1
    #     response = RequestHttp().request_response(method="post", url=add_url, data=data,
    #                                               headers=headers)
    #     assert response.status_code == 200
    #     check_response = json.loads(response.text)
    #     assert check_response["code"] == 1
    #     assert "uid信息不存在" in check_response["error"]

    def test_game_add_channel_id_is_zero(self, driver):
        add_url = "{0}/gameManage/index/internal/game/add".format(driver["test_domain"])
        headers = driver["headers"]
        data = copy.deepcopy(self.url_data(driver))

        data["params"]["channel_id"] = 0
        response = RequestHttp().request_response(method="post", url=add_url, data=data,
                                                  headers=headers)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "渠道id不能为空" in check_response["error"]

    def test_game_add_channel_id_not_exist(self, driver):
        add_url = "{0}/gameManage/index/internal/game/add".format(driver["test_domain"])
        headers = driver["headers"]
        data = copy.deepcopy(self.url_data(driver))

        # channel_id设置为999
        data["params"]["channel_id"] = 999
        response = RequestHttp().request_response(method="post", url=add_url, data=data,
                                                  headers=headers)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "渠道信息不存在" in check_response["error"]

        # channel_id设置为-1
        data["params"]["channel_id"] = -1
        response = RequestHttp().request_response(method="post", url=add_url, data=data,
                                                  headers=headers)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "渠道信息不存在" in check_response["error"]

    def test_game_add_name_is_null(self, driver):
        add_url = "{0}/gameManage/index/internal/game/add".format(driver["test_domain"])
        headers = driver["headers"]
        data = copy.deepcopy(self.url_data(driver))

        # name设置为空
        data["params"]["name"] = ""
        response = RequestHttp().request_response(method="post", url=add_url, data=data, headers=headers)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "请输入游戏名称" in check_response["error"]

    def test_game_add_upload_type_is_zero(self, driver):
        add_url = "{0}/gameManage/index/internal/game/add".format(driver["test_domain"])
        headers = driver["headers"]
        data = copy.deepcopy(self.url_data(driver))
        # upload_type设置为0
        data["params"]["upload_type"] = 0
        response = RequestHttp().request_response(method="post", url=add_url, data=data, headers=headers)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "请选择上传游戏包方式" in check_response["error"]

    def test_game_add_upload_type_not_exist(self, driver):
        add_url = "{0}/gameManage/index/internal/game/add".format(driver["test_domain"])
        headers = driver["headers"]
        data = copy.deepcopy(self.url_data(driver))
        # upload_type设置为99
        data["params"]["upload_type"] = 99
        response = RequestHttp().request_response(method="post", url=add_url, data=data, headers=headers)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "参数错误" in check_response["error"]

        # upload_type设置为-1
        data["params"]["upload_type"] = -1
        response = RequestHttp().request_response(method="post", url=add_url, data=data, headers=headers)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "参数错误" in check_response["error"]

    def test_game_add_category_id_is_zero(self, driver):
        add_url = "{0}/gameManage/index/internal/game/add".format(driver["test_domain"])
        headers = driver["headers"]
        data = copy.deepcopy(self.url_data(driver))

        # category_id设置为0
        data["params"]["category_id"] = 0
        response = RequestHttp().request_response(method="post", url=add_url, data=data, headers=headers)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "请选择游戏类别" in check_response["error"]

    # # 目前没有校验category_id不存在的情况
    # def test_game_add_category_id_not_exist(self, driver):
    #     add_url = "{0}/gameManage/index/internal/game/add".format(driver["test_domain"])
    #     headers = driver["headers"]
    #     data = copy.deepcopy(self.url_data(driver))
    #     # 游戏类别设置为99
    #     data["params"]["category_id"] = 99
    #     response = RequestHttp().request_response(method="post", url=add_url, data=data, headers=headers)
    #     assert response.status_code == 200
    #     check_response = json.loads(response.text)
    #     assert check_response["code"] == 1
    #     assert "请选择游戏类别" in check_response["error"]
    #
    #     # 游戏类别设置为-1
    #     data["params"]["category_id"] = -1
    #     response = RequestHttp().request_response(method="post", url=add_url, data=data, headers=headers)
    #     assert response.status_code == 200
    #     check_response = json.loads(response.text)
    #     assert check_response["code"] == 1
    #     assert "请选择游戏类别" in check_response["error"]

    def test_game_add_type_ids_is_null(self, driver):
        add_url = "{0}/gameManage/index/internal/game/add".format(driver["test_domain"])
        headers = driver["headers"]
        data = copy.deepcopy(self.url_data(driver))
        data["params"]["type_ids"] = ""
        response = RequestHttp().request_response(method="post", url=add_url, data=data, headers=headers)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "请选择游戏类型" in check_response["error"]

    # # 目前没有校验
    # def test_game_add_type_ids_has_not_exist_type(self, driver):
    #     add_url = "{0}/gameManage/index/internal/game/add".format(driver["test_domain"])
    #     headers = driver["headers"]
    #     data = copy.deepcopy(self.url_data(driver))
    #     # 设置type_ids为不存在的类型
    #     data["params"]["type_ids"] = "-1,0"
    #     response = RequestHttp().request_response(method="post", url=add_url, data=data, headers=headers)
    #     assert response.status_code == 200
    #     check_response = json.loads(response.text)
    #     assert check_response["code"] == 1
    #     assert "请选择游戏类型" in check_response["error"]

    # # 没有校验
    # def test_game_add_instance_type_not_exist(self, driver):
    #     add_url = "{0}/gameManage/index/internal/game/add".format(driver["test_domain"])
    #     headers = driver["headers"]
    #     data = copy.deepcopy(self.url_data(driver))
    #
    #     # instance_type设置为99
    #     data["params"]["instance_type"] = 99
    #     response = RequestHttp().request_response(method="post", url=add_url, data=data, headers=headers)
    #     assert response.status_code == 200
    #     check_response = json.loads(response.text)
    #     assert check_response["code"] == 1
    #     assert "参数错误" in check_response["error"]
    #
    #     # instance_type设置为-1
    #     data["params"]["instance_type"] = -1
    #     response = RequestHttp().request_response(method="post", url=add_url, data=data, headers=headers)
    #     assert response.status_code == 200
    #     check_response = json.loads(response.text)
    #     assert check_response["code"] == 1
    #     assert "参数错误" in check_response["error"]

    # # 没有校验
    # def test_game_add_max_concurrent_not_exist(self, driver):
    #     add_url = "{0}/gameManage/index/internal/game/add".format(driver["test_domain"])
    #     headers = driver["headers"]
    #     data = copy.deepcopy(self.url_data(driver))
    #     data["params"]["max_concurrent"] = -1
    #     response = RequestHttp().request_response(method="post", url=add_url, data=data, headers=headers)
    #     assert response.status_code == 200
    #     check_response = json.loads(response.text)
    #     assert check_response["code"] == 1
    #     assert "参数错误" in check_response["error"]

    def test_game_add_quality_is_null(self, driver):
        add_url = "{0}/gameManage/index/internal/game/add".format(driver["test_domain"])
        headers = driver["headers"]
        data = copy.deepcopy(self.url_data(driver))
        data["params"]["quality"] = ""
        response = RequestHttp().request_response(method="post", url=add_url, data=data, headers=headers)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "请选择播流画质" in check_response["error"]

    def test_game_add_upload_type_local_params_is_null(self, driver, upload_apk):
        add_url = "{0}/gameManage/index/internal/game/add".format(driver["test_domain"])
        headers = driver["headers"]
        data = self.local_data(driver, upload_apk)

        # download_url为空
        data_lost_params = copy.deepcopy(data)
        data_lost_params["params"]["download_url"] = ""
        response = RequestHttp().request_response(method="post", url=add_url, data=data_lost_params, headers=headers)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "请选择上传游戏包apk文件" in check_response["error"]

        # filemd5为空
        data_lost_params = copy.deepcopy(data)
        data_lost_params["params"]["filemd5"] = ""
        response = RequestHttp().request_response(method="post", url=add_url, data=data_lost_params, headers=headers)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "请选择上传游戏包apk文件" in check_response["error"]

        # package_name为空
        data_lost_params = copy.deepcopy(data)
        data_lost_params["params"]["package_name"] = ""
        response = RequestHttp().request_response(method="post", url=add_url, data=data_lost_params, headers=headers)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "请选择上传游戏包apk文件" in check_response["error"]

        # version_code为0或者负数
        data_lost_params = copy.deepcopy(data)
        data_lost_params["params"]["version_code"] = 0
        response = RequestHttp().request_response(method="post", url=add_url, data=data_lost_params, headers=headers)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "请选择上传游戏包apk文件" in check_response["error"]

        # version_name为空
        data_lost_params = copy.deepcopy(data)
        data_lost_params["params"]["version_name"] = ""
        response = RequestHttp().request_response(method="post", url=add_url, data=data_lost_params, headers=headers)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "请选择上传游戏包apk文件" in check_response["error"]

    # # 没有校验
    # def test_game_add_upload_type_local_version_code_is_negative_number(self, driver, upload_apk):
    #     add_url = "{0}/gameManage/index/internal/game/add".format(driver["test_domain"])
    #     headers = driver["headers"]
    #     data = copy.deepcopy(self.local_data(driver, upload_apk))
    #     data["params"]["version_code"] = -1
    #     response = RequestHttp().request_response(method="post", url=add_url, data=data, headers=headers)
    #     assert response.status_code == 200
    #     check_response = json.loads(response.text)
    #     assert check_response["code"] == 1
    #     assert "请选择上传游戏包apk文件" in check_response["error"]

    def test_game_add_upload_type_url_params_is_null(self, driver, upload_apk):
        add_url = "{0}/gameManage/index/internal/game/add".format(driver["test_domain"])
        headers = driver["headers"]
        data = self.url_data(driver)

        # upload_url为空
        data_lost_params = copy.deepcopy(data)
        data_lost_params["params"]["upload_url"] = ""
        response = RequestHttp().request_response(method="post", url=add_url, data=data_lost_params, headers=headers)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "请输入游戏包下载地址" in check_response["error"]

        # md5为空
        data_lost_params = copy.deepcopy(data)
        data_lost_params["params"]["md5"] = ""
        response = RequestHttp().request_response(method="post", url=add_url, data=data_lost_params, headers=headers)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "请输入上传游戏包md5值" in check_response["error"]

    def test_game_add_lost_params(self, driver, upload_apk):
        add_url = "{0}/gameManage/index/internal/game/add".format(driver["test_domain"])
        headers = driver["headers"]
        data = self.url_data(driver)
        # lost uid
        data_lost_params = copy.deepcopy(data)
        data_lost_params["params"].pop("uid")
        response = RequestHttp().request_response(method="post", url=add_url, data=data_lost_params, headers=headers)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "uid不能为空" in check_response["error"]

        # lost channel_id
        data_lost_params = copy.deepcopy(data)
        data_lost_params["params"].pop("channel_id")
        response = RequestHttp().request_response(method="post", url=add_url, data=data_lost_params,
                                                  headers=headers)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "渠道id不能为空" in check_response["error"]

        # lost name
        data_lost_params = copy.deepcopy(data)
        data_lost_params["params"].pop("name")
        response = RequestHttp().request_response(method="post", url=add_url, data=data_lost_params,
                                                  headers=headers)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "请输入游戏名称" in check_response["error"]

        # lost upload_type
        data_lost_params = copy.deepcopy(data)
        data_lost_params["params"].pop("upload_type")
        response = RequestHttp().request_response(method="post", url=add_url, data=data_lost_params,
                                                  headers=headers)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "请选择上传游戏包方式" in check_response["error"]

        # lost category_id
        data_lost_params = copy.deepcopy(data)
        data_lost_params["params"].pop("category_id")
        response = RequestHttp().request_response(method="post", url=add_url, data=data_lost_params,
                                                  headers=headers)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "请选择游戏类别" in check_response["error"]

        # lost type_ids
        data_lost_params = copy.deepcopy(data)
        data_lost_params["params"].pop("type_ids")
        response = RequestHttp().request_response(method="post", url=add_url, data=data_lost_params,
                                                  headers=headers)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "请选择游戏类型" in check_response["error"]

        # 可以在download_url类似的地方，增加一个判断 != "" 的逻辑，就可以覆盖到非required的字段存在了
        # # lost instance_type
        # data_lost_params = copy.deepcopy(data)
        # data_lost_params["params"].pop("instance_type")
        # response = RequestHttp().request_response(method="post", url=add_url, data=data_lost_params,
        #                                           headers=headers)
        # assert response.status_code == 200
        # check_response = json.loads(response.text)
        # assert check_response["code"] == 1
        # # assert "system error" in check_response["error"]
        #
        # # lost max_concurrent
        # data_lost_params = copy.deepcopy(data)
        # data_lost_params["params"].pop("max_concurrent")
        # response = RequestHttp().request_response(method="post", url=add_url, data=data_lost_params,
        #                                           headers=headers)
        # assert response.status_code == 200
        # check_response = json.loads(response.text)
        # assert check_response["code"] == 1
        # # assert "system error" in check_response["error"]

        # lost quality
        data_lost_params = copy.deepcopy(data)
        data_lost_params["params"].pop("quality")
        response = RequestHttp().request_response(method="post", url=add_url, data=data_lost_params,
                                                  headers=headers)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        logger.debug("response error is {0}".format(check_response["error"]))
        assert check_response["code"] == 1
        assert "请选择播流画质" in check_response["error"]

    def test_game_add_upload_type_local_lost_param(self, driver, upload_apk):
        # 本地添加, 先上传apk
        add_url = "{0}/gameManage/index/internal/game/add".format(driver["test_domain"])
        headers = driver["headers"]
        data = self.local_data(driver, upload_apk)
        # lost download_url
        data_lost_params = copy.deepcopy(data)
        data_lost_params["params"].pop("download_url")
        response = RequestHttp().request_response(method="post", url=add_url, data=data_lost_params, headers=headers)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "请选择上传游戏包apk文件" in check_response["error"]

        # lost filemd5
        data_lost_params = copy.deepcopy(data)
        data_lost_params["params"].pop("filemd5")
        response = RequestHttp().request_response(method="post", url=add_url, data=data_lost_params, headers=headers)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "请选择上传游戏包apk文件" in check_response["error"]

        # lost package_name
        data_lost_params = copy.deepcopy(data)
        data_lost_params["params"].pop("package_name")
        response = RequestHttp().request_response(method="post", url=add_url, data=data_lost_params, headers=headers)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "请选择上传游戏包apk文件" in check_response["error"]

        # lost version_code
        data_lost_params = copy.deepcopy(data)
        data_lost_params["params"].pop("version_code")
        response = RequestHttp().request_response(method="post", url=add_url, data=data_lost_params, headers=headers)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "请选择上传游戏包apk文件" in check_response["error"]

        # lost version_name/internal/channel/update
        data_lost_params = copy.deepcopy(data)
        data_lost_params["params"].pop("version_name")
        response = RequestHttp().request_response(method="post", url=add_url, data=data_lost_params, headers=headers)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "请选择上传游戏包apk文件" in check_response["error"]

    def test_game_add_upload_type_url_lost_info(self, driver):
        add_url = "{0}/gameManage/index/internal/game/add".format(driver["test_domain"])
        headers = driver["headers"]
        data = self.url_data(driver)
        # lost upload_url
        data_lost_params = copy.deepcopy(data)
        data_lost_params["params"].pop("upload_url")
        response = RequestHttp().request_response(method="post", url=add_url, data=data_lost_params, headers=headers)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "请输入游戏包下载地址" in check_response["error"]

        # lost md5
        data_lost_params = copy.deepcopy(data)
        data_lost_params["params"].pop("md5")
        response = RequestHttp().request_response(method="post", url=add_url, data=data_lost_params, headers=headers)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "请输入上传游戏包md5值" in check_response["error"]


if __name__ == '__main__':
    pytest.main(["-s", "test_service_core.py"])
    # TestServiceRTC().get_token()
