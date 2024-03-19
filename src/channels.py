from litestar.channels import ChannelsPlugin
from litestar.channels.backends.memory import MemoryChannelsBackend

channels_plugin = ChannelsPlugin(channels=['sec'], arbitrary_channels_allowed=True, backend=MemoryChannelsBackend())
