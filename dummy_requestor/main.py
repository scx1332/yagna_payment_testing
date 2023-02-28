import argparse
import os
import asyncio
import sys

import colors
import requests
import time
from datetime import datetime, timezone, timedelta
from unittest import mock

from ya_activity.exceptions import ApiException
from yapapi.services import ServiceState
from yapapi import Golem

from service import Ethnode, EthnodePayload
from strategy import BadNodeFilter
from time_range import NodeRunningTimeRange
from utils import print_env_info, run_golem_example

# the timeout after we commission our service instances
# before we abort this script
STARTING_TIMEOUT = timedelta(minutes=5)

# additional expiration margin to allow providers to take our offer,
# as providers typically won't take offers that expire sooner than 5 minutes in the future
EXPIRATION_MARGIN = timedelta(minutes=5)

RUNNING_TIME_DEFAULT = 316224000
NODE_RUNNING_TIME_DEFAULT = NodeRunningTimeRange("42000,84000")

ACTIVITY_STATE_TERMINATED = "Terminated"


def _instance_not_stopped(service: Ethnode) -> bool:
    return not service.stopped


async def main(
        app_id: int,
        service_name: str,
        num_instances: int,
        running_time: int,
        node_running_time_range: NodeRunningTimeRange,
        subnet_tag: str,
        payment_driver: str,
        payment_network: str,
        local_port: int,
):
    payload = EthnodePayload(runtime=service_name)
    # monitor_task = asyncio.create_task(test_connections_loop())

    async with Golem(
            budget=10,
            payment_driver=payment_driver,
            payment_network=payment_network,
            subnet_tag=subnet_tag,
            strategy=BadNodeFilter(),
    ) as golem:
        print_env_info(golem)
        expiration = datetime.now(timezone.utc) + STARTING_TIMEOUT + EXPIRATION_MARGIN + timedelta(seconds=running_time)

        # proxy = EthnodeProxy(local_port, False)
        # await proxy.run()

        print(f"Local server listening on:\nhttp://localhost:{local_port}")

        ethnode_cluster = await golem.run_service(
            Ethnode,
            payload=payload,
            num_instances=num_instances,
            instance_params=[
                {"node_running_time_range": node_running_time_range} for _ in range(num_instances)
            ],
            respawn_unstarted_instances=True,
            expiration=expiration,
        )

        #proxy.set_cluster(ethnode_cluster)

        def available(cluster):
            return any(inst.state == ServiceState.running for inst in cluster.instances)

        while not available(ethnode_cluster):
            print(ethnode_cluster.instances)
            await asyncio.sleep(5)

        print("Cluster started")

        # wait until Ctrl-C

        while datetime.now(timezone.utc) < expiration:
            costs = {}
            state = {}

            for i in filter(lambda _i: _i._ctx, ethnode_cluster.instances):
                try:
                    costs[str(i)] = await i._ctx.get_cost()
                    s = (await i._ctx.get_raw_state()).to_dict().get("state", [None, None])[0]
                    state[str(i)] = s
                    if s == ACTIVITY_STATE_TERMINATED:
                        # restart if the activity state suggests a provider's end termination
                        i.fail(blacklist_node=False)
                except ApiException:
                    # terminate the agreement and restart the node after a costs check fails
                    i.fail(blacklist_node=False)
                    costs[str(i)] = None
                    state[str(i)] = None
                except AttributeError:
                    # just ignore the error - the instance is most likely being restarted
                    pass

            #print(ethnode_cluster.instances)
            print(costs)
            #print(state)

            try:
                await asyncio.sleep(10)
            except (KeyboardInterrupt, asyncio.CancelledError):
                break

        print(colors.cyan("Stopping..."))
        # signal the instances not to restart

        await proxy.stop()

        for instance in ethnode_cluster.instances:
            instance.stop()

        ethnode_cluster.stop()


async def main_no_proxy(args):
    print(colors.yellow(
        f"Warning - running in proxy only mode. This is not proper way of running the service. Use for development."))
    proxy = EthnodeProxy(None, args.local_port, True)
    await proxy.run()

    print(colors.cyan(f"Local server listening on:\nhttp://localhost:{args.local_port}"))
    while True:
        await asyncio.sleep(100)


if __name__ == "__main__":
    current_time_str = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S%z")
    default_log_path = os.path.join("logs", f"yapapi_{current_time_str}.log")

    parser = argparse.ArgumentParser(description="Dummy service runner")
    parser.add_argument(
        "--payment-driver", "--driver", help="Payment driver name, for example `erc20`"
    )
    parser.add_argument(
        "--payment-network",
        "--network",
        help="Payment network name, for example `rinkeby`",
    )
    parser.add_argument("--subnet-tag", help="Subnet name, for example `devnet-beta`")
    parser.add_argument(
        "--log-file",
        default=str(default_log_path),
        help="Log file for YAPAPI; default: %(default)s",
    )
    parser.add_argument(
        "--service",
        type=str,
        help="Service name",
        choices=("bor-service", "geth-service", "mumbai-service"),
        default="bor-service",
    )
    parser.add_argument(
        "--num-instances",
        type=int,
        default=1,
        help="Number of initial instances/users to create",
    )
    parser.add_argument(
        "--running-time",
        default=316224000,
        type=int,
        help=("Service expiry time " "(in seconds, default: %(default)s)"),
    )
    parser.add_argument(
        "--check-for-yagna",
        default=False,
        type=bool,
        help=("Check for yagna if docker enabled"),
    )
    parser.add_argument(
        "--node-running-time",
        default=str(NODE_RUNNING_TIME_DEFAULT),
        type=NodeRunningTimeRange,
        help=(
            "The running time range [min,max] of a single instance "
            "(in seconds, default: %(default)s)"
        ),
    )
    parser.add_argument(
        "--local-port", default=8545, type=int, help="The port the proxy is listening on."
    )

    # set_yagna_app_key_to_env("yagna");

    # payment_init_command = f"yagna payment init --sender"
    # print(f"Running command: {payment_init_command}")
    # payment_init = subprocess.Popen(payment_init_command, shell=True)
    # payment_init.communicate()

    now = datetime.now().strftime("%Y-%m-%d_%H.%M.%S")

    parser.set_defaults(log_file=f"eth-request-{now}.log")
    args = parser.parse_args()

    app_instance_id = 1

    if args.check_for_yagna:
        max_tries = 15
        for tries in range(0, max_tries):
            try:
                time.sleep(1.0)
                print("Checking for yagna if docker started")
                url = os.getenv("YAGNA_MONITOR_URL") or 'http://127.0.0.1:3333'
                resp = requests.get(url=url)
                data = resp.json()
                if data["payment_initialized"]:
                    print("Yagna detected, continuing...")
                    break
                else:
                    raise Exception("yagna in docker not initialized")
            except Exception as ex:
                print("Check for yagna startup failed: " + str(ex))
                continue

    print(colors.green(f"Patching yapapi - TODO remove in future version of yapapi"))

    patch = mock.patch(
        "yapapi.services.Cluster._instance_not_started",
        staticmethod(_instance_not_stopped),
    )
    patch.start()

    run_golem_example(
        main(
            app_id=app_instance_id,
            service_name=args.service,
            num_instances=args.num_instances,
            running_time=args.running_time,
            node_running_time_range=args.node_running_time,
            subnet_tag=args.subnet_tag,
            payment_driver=args.payment_driver,
            payment_network=args.payment_network,
            local_port=args.local_port,
        ),
        log_file=args.log_file,
    )
