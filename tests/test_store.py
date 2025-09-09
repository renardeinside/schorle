from schorle import SocketStore
from schorle import FastClient
import pytest
import os

os.environ["SCHORLE_FC_LOG"] = "debug"
os.environ["SCHORLE_STORE_LOG"] = "debug"


@pytest.mark.asyncio
async def test_store():
    socket_path = "/tmp/test.sock"
    store = SocketStore(socket_path=str(socket_path))
    await store.start()

    store.set("test", b"test")

    client = FastClient(base_url="http://localhost", socket_path=socket_path)
    resp = await client.request("GET", "/test")
    assert resp.status == 200
    resp_body = await resp.read()
    assert resp_body == b"test"
