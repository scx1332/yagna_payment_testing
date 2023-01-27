"""Utilities for yapapi example scripts."""
import os
import asyncio
import argparse
import colors
from datetime import datetime, timezone
from pathlib import Path
import tempfile


from yapapi import (
    Golem,
    NoPaymentAccountError,
    __version__ as yapapi_version,
)
from yapapi.log import enable_default_logger


def format_usage(usage):
    return {
        "current_usage": usage.current_usage,
        "timestamp": usage.timestamp.isoformat(sep=" ") if usage.timestamp else None,
    }


def print_env_info(golem: Golem):
    print(
        f"yapapi version: {colors.yellow(yapapi_version)}\n"
        f"Using subnet: {colors.yellow(golem.subnet_tag)}, "
        f"payment driver: {colors.yellow(golem.payment_driver)}, "
        f"and network: {colors.yellow(golem.payment_network)}\n"
    )


def run_golem_example(example_main, log_file=None):
    if log_file:
        enable_default_logger(
            log_file=log_file,
            debug_activity_api=True,
            debug_market_api=True,
            debug_payment_api=True,
            debug_net_api=True,
        )

    loop = asyncio.get_event_loop()
    task = loop.create_task(example_main)

    try:
        loop.run_until_complete(task)
    except NoPaymentAccountError as e:
        handbook_url = (
            "https://handbook.golem.network/requestor-tutorials/"
            "flash-tutorial-of-requestor-development"
        )
        print(
            colors.red(
                f"No payment account initialized for driver `{e.required_driver}` "
                f"and network `{e.required_network}`.\n\n"
                f"See {handbook_url} on how to initialize payment accounts for a requestor node."
            )
        )
    except KeyboardInterrupt:
        print(
            colors.yellow(
                "Shutting down gracefully, please wait a short while "
                "or press Ctrl+C to exit immediately..."
            )
        )
        task.cancel()
        try:
            loop.run_until_complete(task)
            print(colors.yellow(f"Shutdown completed, thank you for waiting!"))
        except (asyncio.CancelledError, KeyboardInterrupt):
            pass
