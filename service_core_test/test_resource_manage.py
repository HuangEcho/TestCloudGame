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

# 考虑使用钉钉apk的url吧，虽然150M，但是没有防盗链啊
# 考虑测试环境中部署几个apk的地址，后续就用那个地址来测试
apk_url = "https://download.alicdn.com/wireless/dingtalk/latest/rimet_10002068.apk"
apk_md5 = "588b2321f7af413ffe6b15a68030bac8"
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

    # method: POST
    def test_user_list(self, driver):
        url = "{0}/gameManage/index/internal/customer/list".format(service_core_domain)
        headers = driver["headers"]
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data={})
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0
        assert "result" in check_response
        assert "id" in check_response["result"][0]
        for customer_info in check_response["result"]:
            if customer_info["name"] == "网心科技":
                driver["customer_id"] = check_response["result"][0]["id"]

    def test_channel_list(self, driver):
        url = "{0}/gameManage/index/internal/channel/list".format(service_core_domain)
        headers = driver["headers"]
        data = {"params": {"uid": driver["customer_id"]}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0
        assert "result" in check_response
        for channel_info in check_response["result"]:
            assert channel_info["uid"] == driver["customer_id"]
            if channel_info["name"] == "auto_test":
                driver["channel_id"] = channel_info["id"]

    # 没有channel删除接口，这里只覆盖channel异常场景
    def test_channel_add(self, driver):
        url = "{0}/gameManage/index/internal/channel/add".format(service_core_domain)
        headers = driver["headers"]
        data = {"params": {"forward_method": "POST", "uid": driver["customer_id"], "chan_id": "auto_test",
                           "name": "chan_id duplicate"}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "渠道ID重复" in check_response["error"]

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

    def test_add_upload_type_local(self, driver, upload_apk):
        # 本地添加, 先上传apk
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

    def test_add_lost_params(self, driver, upload_apk):
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

    def test_add_upload_type_local_lost_param(self, driver, upload_apk):
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

    # def test_add_uid_not_match_channel_id(self, driver, upload_apk):
    #     add_url = "{0}/gameManage/index/internal/game/add".format(service_core_domain)
    #     headers = driver["headers"]
    #     data = {
    #         "params": {
    #             "forward_method": "POST",
    #             "uid": driver["customer_id"] + 99,
    #             "channel_id": driver["channel_id"],
    #             "name": "test apk",
    #             "desc": "test",
    #
    #             # 本地上传以及包名的数据
    #             "upload_type": 1,
    #             "download_url": upload_apk["download_url"],
    #             "filemd5": upload_apk["filemd5"],
    #             "package_name": upload_apk["package_name"],
    #             "version_code": upload_apk["version_code"],
    #             "version_name": upload_apk["version_name"],
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
    #     # 这里判断了system error ? 是数据库不允许插入么？
    #     # assert "uid不能为空" in add_response_info["error"]

    def test_add_upload_type_url(self, driver):
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

    def test_add_upload_type_url_lost_info(self, driver):
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
