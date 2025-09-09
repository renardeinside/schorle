import asyncio
from contextlib import suppress
import time
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from schorle._core import FastClient, HttpResponse
from schorle.utils import forwardable_headers


def prepare_router(client: FastClient, dev: bool) -> APIRouter:
    router = APIRouter()

    @router.get("/_next/{path:path}")
    async def _next_assets(request: Request, path: str):
        response: HttpResponse = await client.request(
            method=request.method,
            path=f"/_next/{path}",
            headers=dict(request.headers),
            query=dict(request.query_params),
            body=await request.body(),
            cookies=request.cookies,
        )
        headers = response.headers()

        async def stream():
            async for chunk in response.aiter_bytes():
                yield chunk

        return StreamingResponse(
            stream(),
            media_type=headers.get("content-type"),
            headers=headers,
            status_code=response.status,
        )

    if dev:
        # --- Next.js Dev Helper Routes ---
        @router.api_route(
            "/__nextjs_restart_dev",
            methods=["GET", "HEAD", "OPTIONS", "POST"],
            include_in_schema=False,
        )
        async def _nextjs_restart_dev(request: Request):
            response: HttpResponse = await client.request(
                method=request.method,
                path="/__nextjs_restart_dev",
                headers=dict(request.headers),
                query=dict(request.query_params),
                body=await request.body(),
                cookies=request.cookies,
            )
            headers = response.headers()

            async def stream():
                async for chunk in response.aiter_bytes():
                    yield chunk

            return StreamingResponse(
                stream(),
                media_type=headers.get("content-type"),
                headers=headers,
                status_code=response.status,
            )

        @router.api_route(
            "/__nextjs_server_status",
            methods=["GET", "HEAD", "OPTIONS", "POST"],
            include_in_schema=False,
        )
        async def _nextjs_server_status(request: Request):
            response: HttpResponse = await client.request(
                method=request.method,
                path="/__nextjs_server_status",
                headers=dict(request.headers),
                query=dict(request.query_params),
                body=await request.body(),
                cookies=request.cookies,
            )
            headers = response.headers()

            async def stream():
                async for chunk in response.aiter_bytes():
                    yield chunk

            return StreamingResponse(
                stream(),
                media_type=headers.get("content-type"),
                headers=headers,
                status_code=response.status,
            )

        @router.api_route(
            "/__nextjs_original-stack_frame",
            methods=["GET", "HEAD", "OPTIONS"],
            include_in_schema=False,
        )
        async def _nextjs_original_stack_frame(request: Request):
            response: HttpResponse = await client.request(
                method=request.method,
                path="/__nextjs_original-stack_frame",
                headers=dict(request.headers),
                query=dict(request.query_params),
                body=await request.body(),
                cookies=request.cookies,
            )
            headers = response.headers()

            async def stream():
                async for chunk in response.aiter_bytes():
                    yield chunk

            return StreamingResponse(
                stream(),
                media_type=headers.get("content-type"),
                headers=headers,
                status_code=response.status,
            )

        @router.api_route(
            "/__nextjs_source-map",
            methods=["GET", "HEAD", "OPTIONS"],
            include_in_schema=False,
        )
        async def _nextjs_source_map(request: Request):
            response: HttpResponse = await client.request(
                method=request.method,
                path="/__nextjs_source-map",
                headers=dict(request.headers),
                query=dict(request.query_params),
                body=await request.body(),
                cookies=request.cookies,
            )
            headers = response.headers()

            async def stream():
                async for chunk in response.aiter_bytes():
                    yield chunk

            return StreamingResponse(
                stream(),
                media_type=headers.get("content-type"),
                headers=headers,
                status_code=response.status,
            )

        router.add_websocket_route("/_schorle/dev-indicator", dev_indicator)
        add_hmr_route(router, client)

    return router


async def dev_indicator(ws: WebSocket):
    await ws.accept()

    async def indicator():
        while True:
            try:
                await asyncio.sleep(1)
                await ws.send_json(
                    {
                        "id": "dev-indicator",
                        "start_time": time.time(),
                    }
                )
            except Exception:
                break

    await indicator()


def add_hmr_route(router: APIRouter, client: FastClient):
    @router.websocket("/_next/webpack-hmr")
    async def hmr(ws: WebSocket):
        await ws.accept()
        upstream = await client.ws_connect(
            "/_next/webpack-hmr",
            headers=forwardable_headers(ws.headers),
            secure=False,  # set True if your upstream uses wss
        )

        async def client_to_upstream():
            """Forward messages from browser client -> upstream (Rust WS)."""
            try:
                while True:
                    msg = await ws.receive()
                    if isinstance(msg, str):
                        await upstream.send_text(msg)
                    elif isinstance(msg, (bytes, bytearray, memoryview)):
                        await upstream.send_bytes(bytes(msg))
            except WebSocketDisconnect:
                # Client disconnected - this is expected
                pass
            except asyncio.CancelledError:
                # Task cancelled - re-raise for proper cleanup
                raise
            except Exception:
                # Upstream connection closed or other error - this ends the async iteration
                pass

        async def upstream_to_client():
            """Forward messages from upstream (Rust WS) -> browser client."""
            try:
                async for m in upstream:
                    if isinstance(m, str):
                        await ws.send_text(m)
                    elif isinstance(m, (bytes, bytearray, memoryview)):
                        await ws.send_bytes(bytes(m))
            except asyncio.CancelledError:
                # Task cancelled - re-raise for proper cleanup
                raise
            except Exception:
                # Upstream connection closed or other error - this ends the async iteration
                pass

        # Run both tasks, cancel others when one finishes
        tasks = [
            asyncio.create_task(client_to_upstream()),
            asyncio.create_task(upstream_to_client()),
        ]

        try:
            # Wait for the first task to complete, then cancel the others
            done, pending = await asyncio.wait(
                tasks, return_when=asyncio.FIRST_COMPLETED
            )

            # Cancel remaining tasks
            for task in pending:
                task.cancel()

            # Wait for cancelled tasks to finish
            await asyncio.gather(*pending, return_exceptions=True)

        finally:
            # Always cleanup connections
            with suppress(Exception):
                await upstream.close()
            with suppress(Exception):
                await ws.close()
