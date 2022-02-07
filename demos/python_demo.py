from __future__ import annotations

import asyncio
from typing import Optional, TYPE_CHECKING
from enum import Enum

import gzip
import base64
from requests_futures.sessions import FuturesSession
from loguru import logger

from unicornsdk import UnicornSDK

def get_proxys():
    cur_proxyuri = "http://127.0.0.1:8888"
    proxies = {
        "http": cur_proxyuri,
        "https": cur_proxyuri,
    }
    return proxies
    # return None

async def asyncmain():
    my_token = "TOKEN_FROM_LOGIN"
    sdk = UnicornSDK(token=my_token)
    with open("../tests/ips.js", "rb") as f:
        content = f.read()
        resp = await sdk.kpsdk_parse_ips(content, host="https://s3.nikecdn.com")
        for k, v in resp.items():
            if k != "body":
                logger.debug(f"{k} --> {v}")



if __name__ == '__main__':
    asyncio.run(asyncmain())
