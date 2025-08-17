from web3 import Web3, HTTPProvider
import web3
import logging
import json
from config import config

logging.basicConfig(
    filename='realtgoodoffersbot.log',  # fichier où seront enregistrés les logs
    level=logging.INFO,          # niveau minimum à logger (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(levelname)s - %(message)s'  # format des messages
)

# Parse et sauvegarde les logs. Parsing obligatoire car les données retournées par la blockchain ne sont pas JSON compatibles.
def save_logs(batch_logs, filename):
    from hexbytes import HexBytes
    good_values = []

    # juste pour vider le fichier
    with open(filename, "w") as f: pass

    with open(filename, "a") as f:
        for log in batch_logs:
            log = dict(log)
            for k, v in log.items():
                if isinstance(log[k], HexBytes):
                    log[k] = v.hex()
            log['args'] = dict(log['args'])
            good_values.append(log)
        json.dump(good_values, f, indent=2)

def get_and_save_all_logs(contract, from_block, to_block='latest'):
    # Requêter les logs de création d'offres de la blockchain
    logging.info("Récupération des logs OfferCreated...")
    try:
        logs = contract.events.OfferCreated.get_logs(from_block=from_block , to_block=to_block)
        save_logs(logs, "OfferCreated_logs.json")
    except Exception as e: logging.critical(f"Echec de la récupération/sauvegarde des logs OfferCreated : {e}")

    logging.info("Récupération des logs OfferAccepted...")
    try:
        logs = contract.events.OfferAccepted.get_logs(from_block=from_block, to_block=to_block)
        save_logs(logs, "OfferAccepted_logs.json")
    except Exception as e: logging.critical(f"Echec de la récupération/sauvegarde des logs OfferAccepted : {e}")

    logging.info("Récupération des logs OfferDeleted...")
    try:
        logs = contract.events.OfferDeleted.get_logs(from_block=from_block, to_block=to_block)
        save_logs(logs, "OfferDeleted_logs.json")
    except Exception as e: logging.critical(f"Echec de la récupération/sauvegarde des logs OfferDeleted : {e}")

    logging.info("Récupération des logs OfferUpdated...")
    try:
        logs = contract.events.OfferUpdated.get_logs(from_block=from_block, to_block=to_block)
        save_logs(logs, "OfferUpdated_logs.json")
    except Exception as e: logging.critical(f"Echec de la récupération/sauvegarde des logs OfferUpdated : {e}")

    logging.info("Sauvegarde des logs effectuée")

# Calcule les offres en cours sur le YAM et les écrit dans un fichier
def process_yam_available_offers(contract):
    logging.info("Filtrage des logs...")
    OfferCreated_logs = json.load(open("OfferCreated_logs.json", "r"))
    OfferAccepted_logs = json.load(open("OfferAccepted_logs.json", "r"))
    OfferDeleted_logs = json.load(open("OfferDeleted_logs.json", "r"))
    OfferUpdated_logs = json.load(open("OfferUpdated_logs.json", "r"))

    with open("OfferAvailable.json", "r") as f:
        OfferAvailable = json.load(f)

    with open("OfferAvailable.json", "w") as f:
        available_offers = []
        offres_ajoutees = 0
        for offer in OfferCreated_logs:
            if not any(log["args"]["offerId"] == offer['args']['offerId'] for log in OfferDeleted_logs):
                if not any(log["args"]["offerId"] == offer['args']['offerId'] for log in OfferAccepted_logs):
                    # si l'offre n'est ni dans les offres supprimées ni dans les acceptées, alors elle est dispo
                    # dernier filtre : si on peut récupérer des infos on chain, l'offre est valable
                    try:
                        contract.functions.showOffer(offer["args"]["offerId"]).call()
                        # On n'ajoute pas les offres déjà présentes sinon, le fichier grossira à l'infini
                        if not any(log["args"]["offerId"] == offer['args']['offerId'] for log in OfferAvailable):
                            available_offers.append(offer)
                            offres_ajoutees += 1
                    except web3.exceptions.ContractLogicError as e: pass
        json.dump(OfferAvailable+available_offers, f, indent=2)

        # enregistrement du dernier block pull, la prochaine fois on repart de celui-là
        if len(available_offers) > 0:
            config['blockchain']['from_block'] = str(available_offers[-1]['blockNumber'])
            with open('config.ini', 'w') as configfile: config.write(configfile)
            logging.info(f"Dernier block enregistré : {available_offers[-1]['blockNumber']}")
    logging.info(f"Logs filtrés avec succès. Offres ajoutées : {offres_ajoutees}")

# Notifie sur Telegram
def notify(msg: str):
    import requests
    TOKEN = config['telegram']['token']
    CHAT_ID = config['telegram']['chat_id']
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    response = requests.post(url, data=data)
    if response.status_code == 200:
        logging.info(f"Notification envoyée avec succès")
    else:
        logging.error(f"Impossible d'envoyer une notification : {response.text}")

def check_offers_and_send_notif(filter_file):
    offers_available = json.load(open("OfferAvailable.json", "r"))
    mytokens = open(filter_file, "r").readlines()
    for i in range(len(mytokens)): mytokens[i] = mytokens[i].replace('\n', '')

    logging.info(f"Nombre d'offres disponibles après filtrage : {len(offers_available)}")
    for offer in offers_available:
        try:
            token_data = contract.functions.tokenInfo(offer['args']['offerToken']).call()
            for myt in mytokens:
                if myt in token_data[2]:
                    token_info = contract.functions.tokenInfo(offer['args']['buyerToken']).call()

                    if round(offer['args']['amount']/10**18,2) > 0.0:
                        if round(offer['args']['price']/10**token_info[0]) < int(config['filter']['max_price']):
                            msg = f"<b>{token_data[2].replace('RealToken ', '')}</b>\n"
                            msg += "━━━━━━━━━━━━\n"
                            msg += f"<b>Qtt : </b>{round(offer['args']['amount']/10**18,2)}\n"
                            msg += f"💶 : {round(offer['args']['price']/10**token_info[0])} {token_info[2]}\n"
                            msg += f"🆔 : {offer['args']['offerId']}\n"
                            msg += f"🔗 <a href=\"https://yam.realtoken.network/offer/{offer['args']['offerId']}\">Voir sur le YAM</a>"
                            notify(msg)
                            logging.info(f"Notification envoyée : {msg}")

        except Exception as e:
            logging.critical(f"Impossible d'appliquer les filtres et d'envoyer des notifications, envoie d'une notification")
            notify(f"⚠️ CRITIQUE : Impossible d'appliquer les filtres et d'envoyer des notifications : {e}")
            raise Exception("Connexion à Gnosis échouée")


if __name__ == "__main__":
    try:
        # ABI du contrat
        contract_abi = json.load(open('ABI.json', 'r'))
    except FileNotFoundError as e:
        logging.critical(f'ABI.json introuvable, disponible ici : https://gnosisscan.io/address/0x3b9543e2851accaef9b4f6fb42fcaea5e9231589#code')
        raise e
    try:
        # 1. Connexion au nœud RPC de Gnosis Chain
        rpc_url = config['blockchain']['rpc_url']  # endpoint public
        w3 = Web3(HTTPProvider(rpc_url, request_kwargs={"timeout": 120})) # Timeout fréquent si laissé par défaut

        # 2. Adresse du PROXY du contrat du YAM. Ne pas utiliser l'adresse du YAM directement.
        proxy_contract_address = w3.to_checksum_address(config['blockchain']['proxy_contract_address'])

        if not w3.is_connected():
            logging.critical(f"Connexion à Gnosis échouée, envoie d'une notification")
            notify("⚠️ CRITIQUE : Connexion à Gnosis échouée")
            raise Exception("Connexion à Gnosis échouée")

        # 4. Instancier le contrat
        contract = w3.eth.contract(address=proxy_contract_address, abi=contract_abi)
    except Exception as e:
        logging.critical(f'Erreur lors de l\'instanciation du contrat : {e}')
        notify(f'⚠️ CRITIQUE : instanciation du contrat impossible : {e}')
        raise Exception(e)

    # Obtenir le 1er bloc à partir de la tx de déploiement du YAM
    try:
        tx_deployment = config['blockchain']['tx_deployment']
        tx_receipt = w3.eth.get_transaction_receipt(tx_deployment)
        deployment_block = tx_receipt.blockNumber
    except Exception as e:
        logging.critical(f'Erreur lors de la récupération du dernier bloc : {e}')
        notify(f'⚠️ CRITIQUE : récupération du dernier bloc impossible : {e}')
        raise Exception(e)

    import argparse
    parser = argparse.ArgumentParser(description="Tracker des offres du marché secondaire de RealT. Envoie les offres filtrées via Telegram.")
    parser.add_argument("-f", "--filter-file", required=True, help="Fichier qui contient vos tokens à tracker, ligne par ligne. L'opérateur de recherche est un \"in\". Exemple : \"14631-14633 Plymouth\\n23750 W 7 Mile\".")
    parser.add_argument("--update", action="store_true", help="Met à jour les offres en requêtant la blockchain.")
    parser.add_argument("--verbose", action="store_true", help="Activer les messages d'information")
    args = parser.parse_args()

    import sys
    if args.verbose:
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    if args.update:
        try:
            get_and_save_all_logs(contract, from_block=config['blockchain']['from_block'], to_block=config['blockchain']['to_block'])
        except Exception as e:
            logging.error(f'Obtention des logs impossible : {e}')

        process_yam_available_offers(contract)
    logging.info('En train de checker les offres...')
    check_offers_and_send_notif(args.filter_file)
    logging.info('Terminé !')