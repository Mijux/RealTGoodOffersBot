import logging
from config import RTGOBConfig

from enums.message_type import MessageType
from notification.telegram import notify as telegram_notify
from notification.ntfy import notify as ntfy_notify


def notifying(msg_type: MessageType, **kwargs):
    config = RTGOBConfig()

    if config.has_telegram:
        telegram_notify(msg_type, kwargs)

    if config.has_ntfy:
        ntfy_notify(msg_type, kwargs)
