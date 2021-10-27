# -*- coding:utf-8 -*-

import re
import json
import base64
import hashlib
import requests


url_prefix_tunnel_agent = 'http://10.10.74.3:12334'
url_prefix_avm_manager = 'http://10.10.74.3:9696'
url_prefix_scheduler = 'http://10.10.74.3:10086'
url_prefix_service_rtc = "http://10.10.74.3:9996"


def gen_tunnel_sign(body):
    """
    generate sign for tunnel_agent
    :param body:
    :return:
    """
    buss_id = 'onehitng.cloud_gaming'
    key = '2jKgQK0fWeQz/KDDlqxobNPomXOMJhB3y7c/OTLo0lko7geG4gk7hfiqafapa59Y'

    x = hashlib.sha512()
    x.update((str(body) + buss_id + key).encode(encoding='utf-8'))
    # print((str(body) + buss_id + key).encode(encoding='utf-8'), list(x.digest()))

    import binascii
    m = hashlib.md5()
    m.update(x.digest())
    # m5 = list(m.digest())
    sign = binascii.b2a_hex(m.digest()).decode()
    # print(m5, sign)
    return sign


class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return obj.__str__()
        return json.JSONEncoder.default(self, obj)


class HTTPRequest:

    def __init__(self, url, method, headers=None, data=None, output_response=True, output_curl=True, output_data=False):
        self.url = url
        self.method = method
        self.headers = headers
        self.data = data
        self.output_response = output_response
        self.response = None
        if output_curl:
            self.output_curl()
        if output_data and self.data:
            print(json.dumps(obj=self.data, ensure_ascii=False, sort_keys=True, indent=4, cls=DateEncoder))

    def output_curl(self):
        curl = "curl -X %s -s '%s'" % (self.method, self.url)
        if self.headers:
            for k, v in self.headers.items():
                curl += " -H'%s:%s'" % (k, v)
        if self.data:
            # curl += " -d'%s'" % json.dumps(self.data).encode('utf8').decode('unicode_escape')   # for case which has Chinese
            curl += " -d'%s'" % json.dumps(self.data, separators=(",", ":"), ensure_ascii=False)  # for case which has Chinese

        print(curl)

    def send_request(self):
        req = None
        try:
            if self.method == 'POST':
                request_method = requests.post
            elif self.method == 'PUT':
                request_method = requests.put
            elif self.method == 'DELETE':
                request_method = requests.delete
            else:
                request_method = requests.get

            if not re.findall(pattern='l1.api.data.p2cdn.com', string=self.url):
                self.data = json.dumps(self.data, cls=DateEncoder)
            if not re.findall(pattern='cmdb.onething.net', string=self.url):
                if self.headers is None:
                    self.headers = {}
                elif "X-Forwarded-For" not in self.headers:
                    self.headers["X-Forwarded-For"] = "115.223.255.25"

            if self.headers and self.data:
                req = request_method(url=self.url, data=self.data, headers=self.headers)
            elif self.headers:
                req = request_method(url=self.url, headers=self.headers)
            elif self.data:
                req = request_method(url=self.url, data=self.data)
            else:
                req = request_method(url=self.url)

            # print(req.status_code)
            # for k, v in req.request.headers.items():
            #     print(k, ":", v)
            #
            # print()

            if "Content-Disposition" in req.headers:
                for k, v in req.headers.items():
                    print(k, ":", v)

            dict_json = json.loads(req.content.decode(encoding='utf-8'))

            if dict_json is not None:
                if re.findall(pattern='tunnel/route', string=self.url):
                    # print(base64.b64decode(dict_json['route']['body']))
                    try:
                        self.response = json.loads(base64.b64decode(dict_json['route']['body']).decode('utf-8'))
                    except TypeError:
                        self.response = dict_json
                    except (UnicodeDecodeError, json.decoder.JSONDecodeError):
                        self.response = base64.b64decode(dict_json['route']['body'])
                else:
                    self.response = dict_json

                if self.output_response:
                    print(json.dumps(obj=self.response, indent=4, sort_keys=True).encode('utf8').decode('unicode_escape'))
                else:
                    return self.response
            else:
                print("接口请求未返回任何数据")

        except json.decoder.JSONDecodeError:
            # print("\033[0;31m%s\033[0m\n\n%s" % (e, req.content.decode(encoding='utf-8')))
            print("response:\n" + req.content.decode(encoding='utf-8'))


if __name__ == '__main__':
    data = {
        "req_id": "",
        "filter": {},
        "like": {},
        "page_index": 1,
        "page_size": 2
    }
    hr = HTTPRequest(url=url_prefix_scheduler + '/v1/query/avms', method='POST', headers={'Content-Type': 'application/json'}, data=data)
    hr.send_request()
