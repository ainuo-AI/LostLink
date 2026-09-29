"""通用 HTTP 中间件。"""

from collections.abc import Awaitable, Callable
from uuid import uuid4

from starlette.requests import Request
from starlette.types import ASGIApp


class RequestIdMiddleware:
    """为每个请求生成服务端可信的唯一编号，并写入响应头。"""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
        self,
        scope: dict,
        receive: Callable[[], Awaitable[dict]],
        send: Callable[[dict], Awaitable[None]],
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = uuid4().hex
        request = Request(scope)
        request.state.request_id = request_id

        async def send_with_request_id(message: dict) -> None:
            # 在响应开始时追加请求编号，便于客户端报告问题时提供关联线索。
            if message["type"] == "http.response.start":
                # 这里只追加一个原始响应头，不能构造临时 Response，否则会把它的
                # `Content-Length: 0` 一并加入，导致真实 HTTP 客户端忽略响应正文。
                message.setdefault("headers", []).append(
                    (b"x-request-id", request_id.encode("ascii"))
                )
            await send(message)

        await self.app(scope, receive, send_with_request_id)
