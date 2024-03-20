from uuid import UUID

from litestar import WebSocket, websocket
from litestar.channels import ChannelsPlugin


@websocket("/ws/security")
async def security_handler(socket: WebSocket, channels: ChannelsPlugin) -> None:
    await socket.accept()
    async with channels.subscribe(["sec"]) as subscriber:
        async for message in subscriber.iter_events():
            await socket.send_text(message)


@websocket("/ws/applicant/{applicant_id: uuid}")
async def applicant_handler(socket: WebSocket, channels: ChannelsPlugin, applicant_id: UUID) -> None:
    await socket.accept()
    channel_name = f"applicant_{applicant_id}"
    async with channels.subscribe([channel_name]) as subscriber:
        async for message in subscriber.iter_events():
            await socket.send_text(message)
