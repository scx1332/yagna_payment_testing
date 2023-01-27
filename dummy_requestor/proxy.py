import os
import asyncio
import json
import sys
import traceback

import aiohttp
from aiohttp import web
from datetime import datetime, timedelta, timezone
import random
import typing

from yapapi.services import Cluster
from yapapi.agreements_pool import AgreementsPool

from http_server import aiohttp_app, routes
from rpcproxy import RpcProxy
from service import Ethnode

from jinja2 import Environment, FileSystemLoader, select_autoescape

INSTANCES_RETRY_INTERVAL_SEC = 1
INSTANCES_RETRY_TIMEOUT_SEC = 30

MAX_RETRIES = 3

from logging import getLogger

logger = getLogger("yapapi...ethnode_requestor.proxy")

# allowed_endpoints = ["rinkeby", "polygon", "mumbai"]

env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape()
)

allowed_endpoint = os.getenv("ALLOWED_ENDPOINT") or 'mumbai'
polygon_backup_rpc_url = os.getenv("POLYGON_BACKUP_RPC") or "https://bor.golem.network"
mumbai_backup_rpc_url = os.getenv("MUMBAI_BACKUP_RPC") or "https://rpc-mumbai.maticvigil.com"
rinkeby_rpc_url = os.getenv("RINKEBY_BACKUP_RPC") or "http://1.geth.testnet.golem.network:55555"


class EthnodeProxy:
    def __init__(self, port: int, proxy_only_mode):
        self._request_count = 0
        self._request_lock = asyncio.Lock()
        self._cluster: Cluster = None
        self._port = port
        self._app_task: asyncio.Task = None

    def set_cluster(self, cluster: Cluster[Ethnode]):
        self._cluster = cluster

    async def get_instance(self) -> Ethnode:
        instances = [i for i in self._cluster.instances if i.is_ready]
        if not instances:
            return None

        async with self._request_lock:
            self._request_count += 1
            return instances[self._request_count % len(instances)]

    async def _hello(self, request: web.Request) -> web.Response:
        # test response
        if request.match_info["admin_token"] != os.getenv("ADMIN_TOKEN", "admin"):
            return web.Response(text=json.dumps({"token": "invalid"}), content_type="application/json")
        return web.Response(text=json.dumps({"token": "OK"}), content_type="application/json")

    async def _instances_endpoint(self, request: web.Request) -> web.Response:
        # test response
        if request.match_info["admin_token"] != os.getenv("ADMIN_TOKEN", "admin"):
            return web.Response(text="Wrong admin token")
        return web.Response(text=json.dumps(await self.get_cluster_info()), content_type="application/json")

    async def _offers_endpoint(self, request: web.Request) -> web.Response:
        if request.match_info["admin_token"] != os.getenv("ADMIN_TOKEN", "admin"):
            return web.Response(text="Wrong admin token")

        def convert_timestamps(d: dict):
            for k, v in d.items():
                if isinstance(v, datetime):
                    d[k] = v.timestamp()
                elif isinstance(v, dict):
                    convert_timestamps(v)
            return d

        agreements_pool: AgreementsPool = self._cluster.service_runner._job.agreements_pool  # noqa

        output = {
            "offers": [
                convert_timestamps(o.proposal._proposal.proposal.to_dict())  # noqa
                for o in agreements_pool._offer_buffer.values()  # noqa
            ],
            "agreements": [
                convert_timestamps(a.agreement_details.raw_details.to_dict())  # noqa
                for a in agreements_pool._agreements.values()  # noqa
            ]
        }

        return web.Response(text=json.dumps(output), content_type="application/json")

    async def get_cluster_info(self):
        cv = cluster_view = {}
        if self._cluster:
            cv["exists"] = True
            cv["runtime"] = self._cluster.payload.runtime
            cv["instances"] = {}
            for idx, instance in enumerate(self._cluster.instances):
                cv["instances"][instance.uuid] = instance.to_dict()
                inst = cv["instances"][instance.uuid]
        else:
            cv["exists"] = False
        return cv

    async def _main_endpoint(self, request: web.Request) -> web.Response:
        if request.match_info["admin_token"] != os.getenv("ADMIN_TOKEN", "admin"):
            return web.Response(text="Wrong admin token")
        template = env.get_template("index.html")
        base_url = os.getenv("GATEWAY_BASE_URL") or 'http://127.0.0.1:8545'
        admin_token = os.getenv("ADMIN_TOKEN", "admin")
        page = template.render(hello="template_test", base_url=base_url, admin_token=admin_token)
        return web.Response(text=page, content_type="text/html")

    async def run(self):
        """
        run a local HTTP server, listening on the specified port and passing subsequent requests to
        the :meth:`~HttpProxyService.handle_request` of the specified cluster in a round-robin
        fashion
        """

        aiohttp_app.router.add_route("*", "/info/{admin_token}", handler=self._main_endpoint)
        aiohttp_app.router.add_route("*", "/hello/{admin_token}", handler=self._hello)
        aiohttp_app.router.add_route("*", "/instances/{admin_token}", handler=self._instances_endpoint)
        aiohttp_app.router.add_route("*", "/offers/{admin_token}", handler=self._offers_endpoint)
        aiohttp_app.add_routes(routes)
        self._app_task = asyncio.create_task(
            web._run_app(aiohttp_app, port=self._port, handle_signals=False, print=None)  # noqa
        )

        # runner = web.ServerRunner(web.Server(self._request_handler))  # type: ignore
        # await runner.setup()
        # self._site = web.TCPSite(runner, port=self._port)
        # await self._site.start()

    async def stop(self):
        assert self._app_task, "Not started, call `run` first."
        self._app_task.cancel()
        await asyncio.gather(*[self._app_task])
