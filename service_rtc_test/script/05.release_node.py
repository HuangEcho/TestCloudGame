
from service_rtc_test.script.utils import configHTTP
import requests

pre_url = configHTTP.url_prefix_service_rtc + '/admin/node/release?node_id={0}'

node_id = "shenzhen_mobile_test_{0}"
ip = "192.168.65.{0}"


if __name__ == '__main__':
    num = 1
    for i in range(0, 200):
        headers = {
            "Content-Type": "application/json",
            "x-forwarded-for": ip.format(num+1)
        }
        url = pre_url.format(node_id.format(i))
        response = requests.get(url, headers=headers)
        print(response.status_code, response.text)
