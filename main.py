from __future__ import annotations

import asyncio
from typing import Optional, TYPE_CHECKING
from enum import Enum

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
    v202107 = "v202107"


class UnicornSDK:
    def __init__(self):
        self._api_url = "https://us.unicorn-bot.com"
        self._CLIENT = FuturesSession()

    def _get_client(self):
        return self._CLIENT


    @property
    def XSESSIONDATA(self):
        """
        get back the XSESSIONDATA for save
        :return:
        """
        return "ibYw7Y2j5afulcG8xa2u+BaLkq1m5529PmJsUXWi5txMerGYm7Opw5jfwUh2UcEtOcMTWnPxpT0qsnnMqp7jD04IOlRvGYAgb/TpIjVIRQzQ0+lWk8HHrpYG2fZv6lcq"

    @property
    def access_token(self):
        return "xxx"

    async def kpsdk_parse_ips(self, ips_content, *, ver=KpsdkVersion.v202107, host, compress_method="GZIP",
                              proxy_uri=None, cookie=None, cookiename=None):
        try:
            gzipjps = gzip.compress(ips_content)
            client = self._get_client()
            param = {
                "kpver": ver.value,
                "host": host,
                "proxy_uri": proxy_uri,
                "compress_method": compress_method,
                "cookie": cookie,
                "cookiename": cookiename,
            }

            resp = await asyncio.wrap_future(client.post(self._api_url + "/api/kpsdk/ips/", params=param, headers={
                "Authorization": "Bearer " + self.access_token
            }, cookies={
                "XSESSIONDATA": self.XSESSIONDATA
            }, files={"ips_js": gzipjps}))

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



async def asyncmain():
    sdk = UnicornSDK()
    with open("./tests/ips.js", "rb") as f:
        content = f.read()
        resp = await sdk.kpsdk_parse_ips(content, host="https://s3.nikecdn.com")
        logger.debug(resp)



if __name__ == '__main__':
    asyncio.run(asyncmain())
