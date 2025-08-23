# Notifie sur Telegram

import logging
import requests

from config import RTGOBConfig
from enums.message_type import MessageType


def notify(msg_type: MessageType, kwargs):
    config = RTGOBConfig()
    logger = logging.getLogger("RTGOB")

    msg = format(msg_type, kwargs)

    token = config["telegram"]["token"]
    chat_id = config["telegram"]["chat_id"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": msg, "parse_mode": "HTML"}
    response = requests.post(url, data=data)
    if response.status_code == 200:
        logger.info(f"Notification envoyée avec succès")
    else:
        logger.error(f"Impossible d'envoyer une notification : {response.text}")


def format(msg_type: MessageType, kwargs) -> str:
    if msg_type is MessageType.OFFER:
        token_data = kwargs.pop("token_data")
        token_info = kwargs.pop("token_info")
        offer = kwargs.pop("offer")

        msg = f"<b>{token_data[2].replace('RealToken ', '')}</b>\n"
        msg += "━━━━━━━━━━━━\n"
        msg += f"<b>Qtt : </b>{round(offer['args']['amount']/10**18,2)}\n"
        msg += (
            f"💶 : {round(offer['args']['price']/10**token_info[0])} {token_info[2]}\n"
        )
        msg += f"🆔 : {offer['args']['offerId']}\n"
        msg += f"🔗 <a href=\"https://yam.realtoken.network/offer/{offer['args']['offerId']}\">Voir sur le YAM</a>"
        return msg
    elif msg_type is MessageType.CRITICAL:
        return f"⚠️ CRITIQUE : {kwargs.pop('msg')}{' : ' if 'error_msg' in kwargs.keys() else ''}{kwargs.pop('error_msg')}"
