import json
import logging
import requests

from config import RTGOBConfig
from enums.message_type import MessageType


def notify(msg_type: MessageType, kwargs):
    config = RTGOBConfig()
    logger = logging.getLogger("RTGOB")

    data = format(msg_type, kwargs)
    data["topic"] = config["ntfy"]["topic"]

    server = config["ntfy"]["server"]
    url = server

    response = requests.post(url, data=json.dumps(data))
    if response.status_code == 200:
        logger.info(f"Notification envoyée avec succès")
    else:
        logger.error(f"Impossible d'envoyer une notification : {response.text}")


def format(msg_type: MessageType, kwargs) -> dict:
    if msg_type is MessageType.OFFER:
        token_data = kwargs.pop("token_data")
        token_info = kwargs.pop("token_info")
        offer = kwargs.pop("offer")

        data = {}

        data["title"] = token_data[2].replace("RealToken ", "")

        msg = "━━━━━━━━━━━━\n"
        msg += f"Qtt : {round(offer['args']['amount']/10**18,2)}\n"
        msg += (
            f"💶 : {round(offer['args']['price']/10**token_info[0])} {token_info[2]}\n"
        )
        msg += f"🆔 : {offer['args']['offerId']}\n"

        data["message"] = msg
        data["tags"] = ["loudspeaker"]
        data["priority"] = 3
        data["actions"] = [
            {
                "action": "view",
                "label": "🔗 YAM",
                "url": f"https://yam.realtoken.network/offer/{offer['args']['offerId']}",
            }
        ]

        return data
    elif msg_type is MessageType.CRITICAL:
        data = {}
        data["title"] = "CRITIQUE"
        data["message"] = (
            f"{kwargs.pop('msg')}{' : ' if 'error_msg' in kwargs.keys() else ''}{kwargs.pop('error_msg')}"
        )
        data["tags"] = ["warning"]
        data["priority"] = 5
        return data
