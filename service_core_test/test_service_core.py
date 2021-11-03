# create_author: HuangYaxing
# create_time: 2021/10/19 8:19 下午

import pytest
import requests
import json
import random
import re
import os
import logging
from dependent.env_self import Env
from dependent.requests_http import RequestHttp

log = logging.getLogger("test_service_core")
# 增加一些ip地址
# 测试域名console.galaxy142.com host绑定192.168.126.142再验证

# 考虑使用钉钉apk的url吧，虽然150M，但是没有防盗链啊
# 考虑测试环境中部署几个apk的地址，后续就用那个地址来测试
apk_url = "https://download.alicdn.com/wireless/dingtalk/latest/rimet_10002068.apk"
apk_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zgxqazb_93758.apk")


class TestServiceRTC(object):
    @pytest.fixture(scope="session")
    def driver(self):
        # 设置默认的id值
        driver = {"customer_id": 1, "chan_id": "test_service_core", "channel_id": 39}

        url = "http://console.galaxy142.com/login"
        response = requests.get(url)
        re_console = "console:token=.+?(?=;)|uc:token=.+?(?=;)"
        driver["cookie"] = ";".join(re.findall(re_console, response.headers["set-cookie"]))
        driver["headers"] = {"Content-Type": "application/json", "Cookie": driver["cookie"]}
        return driver

    @pytest.fixture()
    # 上传apk的时候，需要更新token信息
    def upload_token(self, driver):
        get_token_url = "http://api-console.buffcloud.com/upload_token/get"
        token = json.loads(requests.get(get_token_url).text)["data"]["token"]
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

    # method: POST
    def test_user_list(self, driver):
        url = "http://console.galaxy142.com/gameManage/index/internal/customer/list"
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
        url = "http://console.galaxy142.com/gameManage/index/internal/channel/list"
        headers = driver["headers"]
        data = {"params": {"uid": driver["customer_id"]}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0
        assert "result" in check_response
        for channel_info in check_response["result"]:
            assert channel_info["uid"] == driver["customer_id"]
            if channel_info["name"] == "service_core测试使用":
                driver["channel_id"] = channel_info["id"]

    def test_channel_add(self, driver):
        url = "http://console.galaxy142.com/gameManage/index/internal/channel/add"
        headers = driver["headers"]
        data = {"params": {"forward_method": "POST", "uid": driver["customer_id"], "chan_id": "test_service_core",
                           "name": "chan_id duplicate"}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "渠道ID重复" in check_response["error"]

    def test_channel_add_required_param_lost_uid(self, driver):
        url = "http://console.galaxy142.com/gameManage/index/internal/channel/add"
        headers = driver["headers"]
        data = {"params": {"forward_method": "POST", "chan_id": "test_service_core", "name": "chan_id duplicate"}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "参数错误" in check_response["error"]

    def test_channel_add_required_param_lost_chan_id(self, driver):
        url = "http://console.galaxy142.com/gameManage/index/internal/channel/add"
        headers = driver["headers"]
        data = {"params": {"forward_method": "POST", "uid": driver["customer_id"], "name": "chan_id duplicate"}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "参数错误" in check_response["error"]

    def test_channel_add_required_param_lost_name(self, driver):
        url = "http://console.galaxy142.com/gameManage/index/internal/channel/add"
        headers = driver["headers"]
        data = {"params": {"forward_method": "POST", "uid": driver["customer_id"], "chan_id": "test_service_core"}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 1
        assert "参数错误" in check_response["error"]

    def test_game_list(self, driver):
        url = "http://console.galaxy142.com/gameManage/index/internal/game/list"
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

    def test_add(self, driver, upload_apk):
        # 本地添加
        add_url = "http://console.galaxy142.com/gameManage/index/internal/game/add"
        headers = driver["headers"]
        add_data = {
            "params": {
                "forward_method": "POST",
                "uid": driver["customer_id"],
                "channel_id": driver["channel_id"],
                "desc": "test",
                "name": "test apk",
                "download_url": upload_apk["download_url"],
                "file_md5": upload_apk["filemd5"],
                "package_name": upload_apk["package_name"],
                "instance_type": 0,
                "max_concurrent": 0,
                "quality": "720p",
                "category_id": 1,
                "type_ids": "17, 18",
                "upload_type": 1,
                "version_code": upload_apk["version_code"],
                "version_name": upload_apk["version_name"]
            }
        }
        response = RequestHttp().request_response(method="post", url=add_url, data=add_data, headers=headers)
        print(response.status_code, response.text)
        assert response.status_code == 200
        add_response_info = json.loads(response.text)
        assert add_response_info["code"] == 0
        assert "result" in add_response_info
        gid = add_response_info["result"]["gid"]
        print(gid)


if __name__ == '__main__':
    pytest.main(["-s", "test_service_core.py"])
    # TestServiceRTC().get_token()
