from __future__ import annotations

import asyncio
from typing import Optional, TYPE_CHECKING
from enum import Enum

import urllib3
urllib3.disable_warnings()

import gzip
import base64
from datetime import datetime
from requests_futures.sessions import FuturesSession
import requests
from dateutil import parser
import configparser
from loguru import logger


def parse_from_iso8601_to_local(dt_str):
    if not dt_str:
        return None
    return parser.isoparse(dt_str).astimezone()

def now_time_s():
    return int(datetime.now().timestamp())



class PlatForm(str, Enum):
    WINDOWS = "WINDOWS"
    ANDROID = "ANDROID"
    IOS = "IOS"
    OSX = "OSX"


class KpsdkVersion(str, Enum):
    v20210513 = "v20210513"
    v202107 = "v202107"


class UnicornSDK:
    AUTH = {
        "access_token": None
    }
    CFG = configparser.ConfigParser(interpolation=None)

    def __init__(self, token=None, api_url="https://us.unicorn-bot.com"):
        self._api_url = api_url
        # self._api_url = "http://127.0.0.1:9000"
        self._CLIENT = FuturesSession()
        self._XSESSIONDATA = None
        self._token = token
        self.device_info = None

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

    @XSESSIONDATA.setter
    def XSESSIONDATA(self, v):
        self._XSESSIONDATA = v

    @property
    def access_token(self):
        return self._token or self.AUTH.get("access_token")

    @property
    def api_url(self):
        return self._api_url or self.CFG.get("api_url")

    @classmethod
    def load_settings(cls, CFG_PATH):
        cls.CFG.read(CFG_PATH)

    @classmethod
    def save_settings(cls, CFG_PATH):
        with open(CFG_PATH, "w", encoding="utf8") as f:
            cls.CFG.write(f)

    @classmethod
    def check_auth(cls, CFG_PATH):
        cls.load_settings(CFG_PATH)

        settings = cls.CFG
        do_login = False
        if not settings["auth"].get("access_token"):
            do_login = True

        if not settings["auth"].get("refresh_token_expiration") or parse_from_iso8601_to_local(
                settings["auth"]["refresh_token_expiration"]).timestamp() - now_time_s() < 3600 * 24:
            do_login = True

        # 剩余时长小于一小时直接刷新一个
        if not settings["auth"].get("access_token_expiration") or parse_from_iso8601_to_local(
                settings["auth"]["access_token_expiration"]).timestamp() - now_time_s() < 3600:
            do_login = True

        if do_login:
            if not settings["auth"].get("username") or not settings["auth"].get("password"):
                raise Exception("missing auth info!")
            cls.login(settings)

        cls.set_auth(access_token=settings["auth"]["access_token"])
        cls.save_settings(CFG_PATH)

    @classmethod
    def login(cls, settings=None):
        assert settings
        assert settings["auth"]["username"]
        assert settings["auth"]["password"]
        param = {
            "username": settings["auth"]["username"],
            # "email": settings["auth"].get("email"),
            "password": settings["auth"]["password"],
        }
        api_url = settings["auth"]["api_url"]
        resp = requests.post(api_url + "/auth/login/", json=param, timeout=30)

        if resp.status_code == 200:
            j = resp.json()
            settings["auth"]["access_token"] = j["access_token"]
            settings["auth"]["refresh_token"] = j["refresh_token"]
            settings["auth"]["access_token_expiration"] = j["access_token_expiration"]
            settings["auth"]["refresh_token_expiration"] = j["refresh_token_expiration"]
        else:
            raise Exception(f"Login Faild! {resp.text}")

    @classmethod
    def set_auth(cls, *, access_token):
        cls.AUTH["access_token"] = access_token


    async def init_session(self, sessionid: str, platform: PlatForm, locale="zh_CN"):
        url = self.api_url + "/api/session/init/"
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
        self.device_info = resp.json()
        return self.device_info

    def load_state(self, bundle):
        self._XSESSIONDATA = bundle.get("XSESSIONDATA")
        self.device_info = bundle.get("device_info")

    def save_state(self, bundle):
        bundle["XSESSIONDATA"] = self._XSESSIONDATA
        bundle["device_info"] = self.device_info


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

            resp = await asyncio.wrap_future(client.post(self.api_url + "/api/kpsdk/ips/", params=param, headers={
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
            resp = await asyncio.wrap_future(client.post(self.api_url + "/api/kpsdk/answer/", headers={
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

    def get_bmak(self, bmak_url, timezoneoffset=None):
        return Bmak(
            bmak_url=bmak_url,
            timezoneoffset=timezoneoffset,
            sdk=self
        )


    async def bmak_sensordata(
            self, *,
            forminfo="", forminfo_cns="", url=None, bmak_url=None, _abck=None, newpage=False,
            timezoneoffset=None, input=None, element=None, element_type=None, click=False, move=None):

        try:
            param = {
                "_abck": _abck,
                "newpage": newpage,
                "input": input,
                "element": element,
                "element_type": element_type,
                "click": click,
                "move": move,
            }
            if url is not None:
                param["url"] = url
            if bmak_url:
                param["bmak_url"] = bmak_url
            if forminfo is not None:
                param["forminfo"] = forminfo
            if forminfo_cns is not None:
                param["forminfo_cns"] = forminfo_cns
            if timezoneoffset:
                param["timezoneoffset"] = timezoneoffset

            client = self._get_client()
            resp = await asyncio.wrap_future(client.post(self.api_url + "/api/bmak/sensordata/", json=param, headers={
                "Authorization": "Bearer " + self.access_token
            }, cookies={
                "XSESSIONDATA": self.XSESSIONDATA
            }, verify=False, proxies=self.get_proxys_for_sdk()))

            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 403:
                raise Exception("Not Authenticated")
            else:
                logger.error(resp.text)
                raise Exception(resp.text)
        except Exception as e:
            logger.error(repr(e))
            raise e

class Bmak:

    def __init__(self,
                 bmak_url,
                 timezoneoffset=None,
                 sdk:UnicornSDK=None):
        self.sdk = sdk
        self.bmak_url=bmak_url
        self.timezoneoffset = timezoneoffset
        self.newpage = True

    def ab(self, str):
        """
        hash element name or id
        """
        if not str:
            return -1
        try:
            t = 0
            for r in str:
                n = ord(r)
                if n < 128:
                    t += n
            return t
        except Exception as e:
            logger.error("ab() failed! " + str)
            return -2

    async def bmak_sensordata(
            self, *,
            url,
            _abck=None,
            input:str=None, element=None, element_type=None,
            click=False,
            move=None,
            forminfo="", forminfo_cns="",

    ):
        """
        gen sensor from api
        :param url: current page url
        :param _abck: current _abck cookie
        :param input: generate keyboard event for the str, when use input, you should also set element / element_type
        :param element: the name or id or the input element
        :param element_type: only need when you want to generate input password event, set it to ”password“
        :param click: generate click event
        :param move: generate mouse move event, set to "short" / "long“
        :param forminfo:
        :param forminfo_cns:
        :return:
        """

        ret = await self.sdk.bmak_sensordata(
            url=url,
            bmak_url=self.bmak_url,
            timezoneoffset=self.timezoneoffset,
            newpage=self.newpage,
            input=input, element=element, element_type=element_type,
            click=click,
            move=move,
            forminfo=forminfo, forminfo_cns=forminfo_cns
        )
        self.newpage=False
        return ret
