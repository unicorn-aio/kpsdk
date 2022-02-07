from __future__ import annotations

import asyncio
import json
import os
import uuid
from datetime import datetime, timedelta
from pprint import pprint

import urllib3
from pathlib import Path

urllib3.disable_warnings()

from requests_futures.sessions import FuturesSession
from loguru import logger
import brotli

from unicornsdk import UnicornSDK, PlatForm

def print_sensordatas(sensor_datas):
    for i in sensor_datas:
        logger.debug(i)

async def asyncmain():
    my_token = os.getenv("MYTOKEN", "TOKEN_FROM_LOGIN")
    sdk = UnicornSDK(my_token)
    device = await sdk.init_session("testid", platform=PlatForm.WINDOWS)
    useragent = device["user_agent"]

    # TODO: reqyest the site and found the url for post sensor_data
    # for example
    current_url = "https://s3.nikecdn.com/unite/mobile.html?mid=87851713624057929094625979408669721627&androidSDKVersion=2.8.1&uxid=com.nike.commerce.snkrs.droid&locale=zh_CN&backendEnvironment=identity&view=login&clientId=qG9fJbnMcBPAMGibPRGI72Zr89l8CD4R"
    akamain_url="https://s3.nikecdn.com/hNtm01h5Ctyeil9cVIO0j-n8/Eaz7kND4Eu5N/PVQiZgE/cl4/EEiMGSCA"
    bmak = sdk.get_bmak(bmak_url=akamain_url)
    _abck = "xxxx"

    # TODO: request get bmak js

    # bmak js loaded
    sensor_datas = await bmak.bmak_sensordata(url=current_url)
    print_sensordatas(sensor_datas["sensor_datas"])
    # TODO: post sensordatas
    await asyncio.sleep(1)
    _abck = "NEW_ABCK_COOKIE"


    # move mouse
    sensor_datas = await bmak.bmak_sensordata(url=current_url, move="short", _abck=_abck)
    print_sensordatas(sensor_datas["sensor_datas"])
    # TODO: post sensordatas
    await asyncio.sleep(1)
    _abck = "NEW_ABCK_COOKIE"

    await asyncio.sleep(1)

    # click mouse
    sensor_datas = await bmak.bmak_sensordata(url=current_url, click=True, _abck=_abck)
    print_sensordatas(sensor_datas["sensor_datas"])
    # TODO: post sensordatas
    _abck = "NEW_ABCK_COOKIE"



if __name__ == '__main__':
    asyncio.run(asyncmain())
