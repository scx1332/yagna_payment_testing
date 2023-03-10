import asyncio
import sys
from datetime import datetime, timezone, timedelta
import colors
from dataclasses import dataclass
import json
import random
import requests
import string
from typing import Optional, List
import uuid
import logging

from yapapi.props import constraint, inf
from yapapi.payload import Payload
from yapapi.services import Service, ServiceState

from strategy import BadNodeFilter
from time_range import NodeRunningTimeRange

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stderr))

@dataclass
class EthnodePayload(Payload):
    runtime: str = constraint(inf.INF_RUNTIME_NAME)


class Ethnode(Service):
    uuid: str
    username: str
    password: str
    failed: bool = False
    stopped: bool = False
    addresses: List[str]
    _node_running_time_range: NodeRunningTimeRange
    node_expiry: datetime

    @staticmethod
    def generate_username() -> str:
        return "".join([random.choice(string.ascii_letters) for _ in range(8)])

    @staticmethod
    def generate_password(length: int) -> str:
        return "".join([random.choice(string.ascii_letters + string.digits) for _ in range(length)])

    def __init__(
            self,
            node_running_time_range: NodeRunningTimeRange,
            username: Optional[str] = None,
            password: Optional[str] = None,
    ):
        super().__init__()
        print(f"Creating service Ethnode...")
        self.uuid = str(uuid.uuid4())
        self.db_id = -1
        self.provider_db_id = -1
        self.username = username or self.generate_username()
        self.password = password or self.generate_password(10)
        self.addresses = list()
        self._node_running_time_range = node_running_time_range
        self.set_expiry()

    def set_expiry(self):
        self.node_expiry = self._node_running_time_range.get_expiry()

    def fail(self, blacklist_node: bool = True):
        if blacklist_node:
            BadNodeFilter.blacklist_node(self.provider_id)
        self.failed = True

    async def start(self):
        logger.info(f"Starting {self.provider_name}...")
        if self.stopped:
            return

        async for s in super().start():
            yield s

        script = self._ctx.new_script()

        service_future = script.run("service", "info")

        yield script

        try:
            service = json.loads((await service_future).stdout)
            logger.info(f"Service info: {service}")
        except Exception as e:
            logger.error(f"Failed to get service info: {e}")
            self.fail()


    @property
    def is_ready(self) -> bool:
        return self.state == ServiceState.running and not self.failed

    @property
    def is_expired(self) -> bool:
        return self.node_expiry < datetime.now(timezone.utc)

    async def run(self):
        while not self.stopped and not self.failed and not self.is_expired:
            await asyncio.sleep(1)

        return
        yield # keep this yield here otherwise function is not properly overloaded

    def stop(self):
        self.stopped = True

    async def reset(self):
        if self.failed:
            logger.info(f"Activity failed: {self}, restarting...")
        elif self.is_expired:
            logger.info(f"Node expired: {self}, restarting...")
        else:
            logger.info(f"Activity stopped for unknown reason: {self}, restarting...")

        self.set_expiry()
        self._ctx = None
        self.failed = False
        self.addresses = list()

    def to_dict(self):
        cv_inst = {}
        cv_inst["uuid"] = self.uuid
        cv_inst["addresses"] = self.addresses
        cv_inst["username"] = self.username
        cv_inst["is_ready"] = self.is_ready
        cv_inst["state"] = self.state.identifier
        cv_inst["node_expiry"] = self.node_expiry.strftime("%Y-%m-%d_%H:%M:%S")
        today = datetime.now(timezone.utc)
        cv_inst["expires_in_secs"] = (self.node_expiry - today).total_seconds()
        cv_inst["provider_id"] = self.provider_id
        cv_inst["provider_name"] = self.provider_name
        cv_inst["stopped"] = self.stopped
        return cv_inst
