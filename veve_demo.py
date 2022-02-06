from __future__ import annotations

import asyncio
import os
from datetime import datetime
import urllib3

urllib3.disable_warnings()

from requests_futures.sessions import FuturesSession
from loguru import logger
import brotli

from unicornsdk import UnicornSDK, PlatForm

def now_time_ms():
    return int(datetime.now().timestamp() * 1000)


def get_proxys():
    cur_proxyuri = "http://127.0.0.1:8888"
    proxies = {
        "http": cur_proxyuri,
        "https": cur_proxyuri,
    }
    return proxies
    # return None


async def asyncmain():
    my_token = os.getenv("MYTOKEN", "TOKEN_FROM_LOGIN")
    sdk = UnicornSDK(my_token)
    # sdk = UnicornSDK("http://localhost:9000")
    device = await sdk.init_session("testid", platform=PlatForm.ANDROID)
    useragent = device["user_agent"]


    orgin = "https://mobile.api.prod.veve.me"
    # orgin = "https://web.api.prod.veve.me"
    client = FuturesSession()
    fp_url = f"{orgin}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/fp"
    resp = await asyncio.wrap_future(client.get(fp_url, headers={
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        "user-agent": useragent,
    }, proxies=get_proxys(), verify=False))

    # if True:
    if resp.status_code == 429:
        ct = resp.headers["x-kpsdk-ct"]
        # &x-kpsdk-v=i-1.4.0
        ips_url = f"{orgin}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/ips.js?KP_UIDz={ct}"

        resp = await asyncio.wrap_future(client.get(ips_url, headers={
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
            "referer": f"{orgin}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/fp",
            "user-agent": useragent,
        }, proxies=get_proxys(), verify=False,))
        ipsjs = resp.content

        kpparam = await sdk.kpsdk_parse_ips(ipsjs, host=orgin)

        tl_url = f"{orgin}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/tl"
        resp = await asyncio.wrap_future(client.post(
            tl_url,
            headers={
                "accept": "*/*",
                "content-type": "application/octet-stream",
                "accept-encoding": "gzip, deflate, br",
                "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
                "referer": f"{orgin}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/fp",
                "origin": orgin,
                "user-agent": useragent,
                "x-kpsdk-ct": kpparam["x_kpsdk_ct"]
            },
            data=kpparam["body"],
            proxies=get_proxys(), verify=False,
        ))

        logger.debug(resp.status_code)
        logger.debug(resp.text)

        x_kpsdk_ct = resp.headers["x-kpsdk-ct"]
        x_kpsdk_st = resp.headers["x-kpsdk-st"]
        st_diff = now_time_ms() - int(x_kpsdk_st)
        logger.debug(f"x_kpsdk_ct: {x_kpsdk_ct}")
        logger.debug(f"x_kpsdk_st: {x_kpsdk_st}")
        logger.debug(f"st_diff: {st_diff}")
        kpparam = await sdk.kpsdk_answer(x_kpsdk_ct, x_kpsdk_st, st_diff)
        logger.debug(kpparam)

        send_url = f"{orgin}/api/auth/totp/send"
        resp = await asyncio.wrap_future(client.post(
            send_url,
            headers={
                "accept": "*/*",
                "content-type": "application/json",
                "accept-encoding": "gzip, deflate, br",
                "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
                "client-name": "veve-web-wallet",
                "client-version": "1.2.9",
                "referer": f"{orgin}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/fp",
                "origin": "https://omi.veve.me",
                "user-agent": useragent,
                "x-kpsdk-ct": kpparam["x_kpsdk_ct"],
                "x-kpsdk-cd": kpparam["x_kpsdk_cd"],
            },
            json={"email":"xxx@yahoo.com"},
            proxies=get_proxys(), verify=False,
        ))
        logger.debug(resp.status_code)
        logger.debug(resp.text)


if __name__ == '__main__':
    asyncio.run(asyncmain())
