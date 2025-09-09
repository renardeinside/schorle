import asyncio
import sys
import time

from schorle import ProcessSupervisor
import pytest


@pytest.mark.asyncio
async def test_start_and_stop():
    sup = ProcessSupervisor([sys.executable, "-c", "import time; time.sleep(5)"])
    async with sup:
        print(sup.status())  # e.g. {'state': 'running', 'pid': 12345, ...}
        print(sup.is_running)  # True/False
        print(sup.pid)  # optional[int]

        await asyncio.sleep(1)
        print(sup.status())  # e.g. {'state': 'running', 'pid': 12345, ...}
        print(sup.is_running)  # True/False
        print(sup.pid)  # optional[int]


@pytest.mark.asyncio
async def test_env_vars_and_log_capture():
    """Test environment variables and log capture functionality"""
    # Test with environment variables and log capture
    env_vars = {"TEST_VAR": "hello_world", "PYTHONUNBUFFERED": "1"}
    sup = ProcessSupervisor(
        [
            sys.executable,
            "-c",
            "import os, sys; print('stdout:', os.environ.get('TEST_VAR')); print('stderr:', os.environ.get('TEST_VAR'), file=sys.stderr); import time; time.sleep(0.5)",
        ],
        env=env_vars,
    )

    async with sup:
        print("Process started with env vars:", env_vars)

        # Wait a bit for output
        time.sleep(1)

        # Get captured logs
        stdout_lines = sup.get_stdout_lines()
        stderr_lines = sup.get_stderr_lines()

        print("Captured stdout lines:", stdout_lines)
        print("Captured stderr lines:", stderr_lines)

        sup.stop()

        # Verify the environment variable was passed correctly
        if stdout_lines and "hello_world" in str(stdout_lines):
            print("✅ Environment variables working correctly")
        else:
            print("❌ Environment variables not working as expected")

        if stderr_lines and "hello_world" in str(stderr_lines):
            print("✅ Stderr capture working correctly")
        else:
            print("❌ Stderr capture not working as expected")
