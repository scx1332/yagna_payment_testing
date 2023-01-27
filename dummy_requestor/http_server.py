import os
import requests
import json
import logging

import aiohttp
from aiohttp import web
from sqlalchemy import func
from sqlalchemy.future import select
from sqlalchemy.orm import Session
from model import AppInfo, SerializationMode, LocalJSONEncoder, ProviderInstance
from service import Ethnode

routes = web.RouteTableDef()
aiohttp_app = web.Application()



@routes.get("/yagna/{admin_token}")
async def test(request):
    if request.match_info["admin_token"] != os.getenv("ADMIN_TOKEN", "admin"):
        return web.Response(text="Wrong admin token")
    # todo: probably cache this request
    url = os.getenv("YAGNA_MONITOR_URL") or 'http://127.0.0.1:3333'
    resp = requests.get(url=url)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=2) as result:
            if result.status == 200:
                return web.Response(text=await result.text(), content_type="application/json")

    return web.Response(text="Failed to get yagna info")


@routes.get("/test_client_endpoint/{admin_token}")
async def test(request):
    if request.match_info["admin_token"] != os.getenv("ADMIN_TOKEN", "admin"):
        return web.Response(text="Wrong admin token")
    base_url = os.getenv("GATEWAY_BASE_URL") or 'http://127.0.0.1:8545'
    allowed_endpoint = os.getenv("ALLOWED_ENDPOINT") or 'mumbai'

    return web.Response(text=f"{base_url}/rpc/{allowed_endpoint}/MAaCpE421MddDmzMLcAp")

@routes.get("/test")
async def test(request):
    return web.Response(text="whatever")
