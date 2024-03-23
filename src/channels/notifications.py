# @websocket("/notifications")
# async def notifications_handler(
#         socket: WebSocket,
#         channels: ChannelsPlugin,
#         request: "Request[Users, Token, Any]",
#         transaction: AsyncSession
# ) -> None:
#     await socket.accept()
#
#     if RolesEnum.security.value in get_roles(transaction, request.user.id):
#         subscriber = await channels.subscribe(['sec', 'applicant'])
#     else:
#         subscriber = await channels.subscribe(['applicant'])
#     async for message in subscriber.iter_events():
#         await socket.send_text(message)
#     await subscriber.stop()
#

# @websocket("/ws/applicant/{applicant_id: uuid}")
# async def applicant_handler(socket: WebSocket, channels: ChannelsPlugin, applicant_id: UUID) -> None:
#     await socket.accept()
#     channel_name = f"applicant_{applicant_id}"
#     subscriber = await channels.subscribe([channel_name])
#     async for message in subscriber.iter_events():
#         await socket.send_text(message)
#     await subscriber.stop()
