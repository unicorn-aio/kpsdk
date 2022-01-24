from __future__ import annotations

import asyncio
from typing import Optional, TYPE_CHECKING
from enum import Enum

import urllib3
urllib3.disable_warnings()

import gzip
import base64
from requests_futures.sessions import FuturesSession
from loguru import logger


class PlatForm(str, Enum):
    WINDOWS = "WINDOWS"
    ANDROID = "ANDROID"
    IOS = "IOS"
    OSX = "OSX"


class KpsdkVersion(str, Enum):
    v20210513 = "v20210513"
    v202107 = "v202107"


class UnicornSDK:
    def __init__(self, token, api_url="https://us.unicorn-bot.com"):
        self._api_url = api_url
        # self._api_url = "http://127.0.0.1:8001"
        self._CLIENT = FuturesSession()
        self._XSESSIONDATA = None
        self._token = token

    def get_proxys_for_sdk(self):
        cur_proxyuri = "http://127.0.0.1:8888"
        proxies = {
            "http": cur_proxyuri,
            "https": cur_proxyuri,
        }
        return proxies
        # return None

    def _get_client(self):
        return self._CLIENT

    def get_authorization(self):
        return {
            "Authorization": "Bearer " + self.access_token
        }

    @property
    def XSESSIONDATA(self):
        """
        get back the XSESSIONDATA for save
        :return:
        """
        return self._XSESSIONDATA

    @property
    def access_token(self):
        return self._token

    async def init_session(self, sessionid: str, platform: PlatForm, locale="zh_CN"):
        url = self._api_url + "/api/session/init/"
        params = {
            "sessionid": sessionid,
            "platform": platform,
            "locale": locale,
        }
        headers = self.get_authorization()
        resp = await asyncio.wrap_future(self._get_client().post(url, json=params, headers=headers, verify=False, proxies=self.get_proxys_for_sdk()))
        if resp.status_code != 200:
            raise Exception(resp.text)
        self._XSESSIONDATA = resp.cookies["XSESSIONDATA"]
        return resp.json()

    async def kpsdk_parse_ips(self, ips_content, *, ver=KpsdkVersion.v202107, host, site=None, compress_method="GZIP",
                              proxy_uri=None, cookie=None, cookiename=None):
        try:
            gzipjps = gzip.compress(ips_content)
            client = self._get_client()
            param = {
                "kpver": ver.value,
                "host": host,
                "site": site,
                "proxy_uri": proxy_uri,
                "compress_method": compress_method,
                "cookie": cookie,
                "cookiename": cookiename,
            }

            resp = await asyncio.wrap_future(client.post(self._api_url + "/api/kpsdk/ips/", params=param, headers={
                "Authorization": "Bearer " + self.access_token
            }, cookies={
                "XSESSIONDATA": self.XSESSIONDATA
            }, files={"ips_js": gzipjps}, verify=False, proxies=self.get_proxys_for_sdk()))

            if resp.status_code == 200:
                kpparam = resp.json()
                tl_body_b64 = kpparam.get("tl_body_b64")
                if tl_body_b64:
                    body = gzip.decompress(base64.b64decode(tl_body_b64))
                    kpparam["body"] = body
                return kpparam
            elif resp.status_code == 403:
                raise Exception("Not Authenticated")
            else:
                logger.error(resp.text)
                raise Exception(resp.text)
        except Exception as e:
            logger.error(repr(e))
            raise e

    async def kpsdk_answer(self, x_kpsdk_ct, x_kpsdk_st, st_diff, x_kpsdk_cr=True):
        try:
            param = {
                "x_kpsdk_ct": x_kpsdk_ct,
                "x_kpsdk_cr": x_kpsdk_cr,
                "x_kpsdk_st": x_kpsdk_st,
                "st_diff": st_diff,
            }
            client = self._get_client()
            resp = await asyncio.wrap_future(client.post(self._api_url + "/api/kpsdk/answer/", headers={
                "Authorization": "Bearer " + self.access_token
            }, cookies={
                "XSESSIONDATA": self.XSESSIONDATA
            }, json=param, verify=False, proxies=self.get_proxys_for_sdk()))

            if resp.status_code == 200:
                kpparam = resp.json()
                return kpparam
            elif resp.status_code == 403:
                raise Exception("Not Authenticated")
            else:
                logger.error(resp.text)
                raise Exception(resp.text)
        except Exception as e:
            logger.error(repr(e))
            raise e
