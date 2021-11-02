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

log = logging.getLogger("test_service_core")
# 增加一些ip地址
# 测试域名console.galaxy142.com host绑定192.168.126.142再验证


class TestServiceRTC(object):
    @pytest.fixture(scope="session")
    def driver(self):
        # 设置默认的id值
        driver = {"customer_id": 1, "chan_id": "test_service_core", "id": 39}

        url = "http://console.galaxy142.com/login"
        response = requests.get(url)
        re_console = "console:token=.+?(?=;)|uc:token=.+?(?=;)"
        driver["cookie"] = ";".join(re.findall(re_console, response.headers["set-cookie"]))
        return driver

    # method: POST
    def test_user_list(self, driver):
        url = "http://console.galaxy142.com/gameManage/index/internal/customer/list"
        headers = {"Content-Type": "application/json", "Cookie": driver["cookie"]}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data={})
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0
        # 不确定要校验那些参数，要不先不写了，获取第一个id吧
        if "result" in check_response and len(check_response["result"]) > 0:
            assert "id" in check_response["result"][0]
            for customer_info in check_response["result"]:
                if customer_info["name"] == "网心科技":
                    driver["customer_id"] = check_response["result"][0]["id"]

    def test_channel_list(self, driver):
        url = "http://console.galaxy142.com/gameManage/index/internal/channel/list"
        headers = {"Content-Type": "application/json", "Cookie": driver["cookie"]}
        data = {"params": {"uid": driver["customer_id"]}}
        response = RequestHttp().request_response(method="post", url=url, headers=headers, data=data)
        assert response.status_code == 200
        check_response = json.loads(response.text)
        assert check_response["code"] == 0
        if "result" in check_response and len(check_response["result"]) > 0:
            for channel_info in check_response["result"]:
                assert channel_info["uid"] == driver["customer_id"]
                if channel_info["name"] == "service_core测试使用":
                    driver["id"] = channel_info["id"]
        print(driver)


if __name__ == '__main__':
    pytest.main(["-s", "test_service_core.py"])
    # TestServiceRTC().get_token()
