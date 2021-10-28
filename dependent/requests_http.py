import hashlib
import json
import requests
import logging

request_log = logging.getLogger("request_http")


class RequestHttp(object):
    def gen_tunnel_sign(self, body):
        buss_id = 'onehitng.cloud_gaming'
        key = '2jKgQK0fWeQz/KDDlqxobNPomXOMJhB3y7c/OTLo0lko7geG4gk7hfiqafapa59Y'

        x = hashlib.sha512()
        x.update((str(body) + buss_id + key).encode(encoding='utf-8'))

        import binascii
        m = hashlib.md5()
        m.update(x.digest())
        sign = binascii.b2a_hex(m.digest()).decode()
        return sign

    def request_response(self, **kwargs):
        # 暂时只写两种方法，如果有新增的，再增加
        try:
            if "method" in kwargs:
                if kwargs["method"] == "get":
                    if "headers" in kwargs:
                        response = requests.get(url=kwargs["url"], headers=kwargs["headers"])
                    else:
                        response = requests.get(url=kwargs["url"])
                elif kwargs["method"] == "post":
                    if "headers" in kwargs:
                        response = requests.post(url=kwargs["url"], data=json.dumps(kwargs["data"]),
                                                 headers=kwargs["headers"])
                    else:
                        response = requests.post(url=kwargs["url"], data=json.dumps(kwargs["data"]))
                else:
                    response = "error method"
                    request_log.error("input method error. excepted get or post, actual is {0}".format(kwargs["method"]))
                request_log.info("response status_code is {0}".format(response.status_code))
                request_log.info("response text is {0}".format(response.text))
                return response
            else:
                request_log.error("need input method")
        except Exception as E:
            print("error is {0}".format(E))


if __name__ == '__main__':
    RequestHttp()
