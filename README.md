# RealTGoodOffersBot

**On-chain** retrieval of RealT secondary market offers (YAM). Filtering of offers via a customizable configuration and sending of offers via Telegram.

## Overview

The tool pulls logs directly from the blockchain. These logs are produced by some functions in the proxy smart contract. The proxy contract address must be set in the `config.ini` file (configuration part bellow). 

Currently, these logs are available : 

- offer created
- offer accepted
- offer deleted
- offer updated (pulled but not used)

The tool pulls these logs and delete deleted offers from the created logs. Then, it does the same with accepted offers. Finally, the tool checks the remaining offers with the smart contract function `showOffer` to verify if the offer is available on chain. 

Then, filters (`max_price` and the filter file) are applyied. The filter files contains the properties name you're looking for, one per line. The operator to match the propertie name is 'in', or 'contains'. Matching offers triggers your own Telegram bot (configuration part bellow) and send a notification with the offer's informations.

The bot writes in the `config.ini` file the last pulled block number. Next time, the bot will only pulls new offers so you don't have to pull from the genesis block each time. That's why the first execution (with `from_block`=0) takes time (~20min).

## Installation

First, you have to install the tool and its dependencies. I'm using `venv` for convenience.

```
git clone https://github.com/nathan-out/RealTGoodOffersBot.git
cd RealTGoodOffersBot
python -m venv RealTGoodOffersBot_venv
source RealTGoodOffersBot_venv/bin/activate
pip install -r requirements

# Test the installation
python .\realtgoodoffersbot.py
# This command must return bellow
usage: realtgoodoffersbot.py [-h] -f FILTER_FILE [--update] [--verbose]
realtgoodoffersbot.py: error: the following arguments are required: -f/--filter-file
```

## Usage

If you want to stay up to date, you have to provides `--update` param. This will pulls the logs from the blockchain and apply your filters. If you don't provide this param, it will only browse the logs already pulled.

To get a full-automated system, I encourage you to set-up a cron task on a VPS.

Use the param `--verbose` to get more information during execution. Wether or not, the tool will write a `realtgoodoffersbot.log` log file.

## Configuration

### Filter file

The tool relies on a filter file (`-f`) to check if a given transaction is interesting to you. This file must contains one token name per line, the operator is **'is'** or **'contains'**. 

For example, if your filter file is :

```
2815 Woodland Grove
1 Holdings W Arizona
Texas
Holdings
```

The bot will send you a notification for the first two properties, but also for all the properties located in Texas, and all the Holdings.

### Config file

**You have to create this file :**`config.ini`. It **must** contains the following informations:

```ini
[blockchain]
# this number will be overwritten after the 1st execution
from_block = 0
to_block = latest
# you may want to change it if a new YAM version was deployed
tx_deployment = 0x2c2553445fba875b64e8124c7519d79b988451250a614cdde825463922e536b0
# you may want to change it if a new YAM version was deployed
proxy_contract_address = 0xC759AA7f9dd9720A1502c104DaE4F9852bb17C14
# I think this attribute will never change
rpc_url = https://rpc.gnosis.gateway.fm

[telegram]
# see Telegram documentation to create your own bot
token = 
chat_id = 

[filter]
# max price for an offer
max_price = 
```

### ABI.json

An ABI (Application Binary Interface) describes the interface of a smart contract (functions, events, data types) and allows tools such as Web3.py to interact with it correctly from the outside.

`ABI.json` contains these informations (available on Gnosisscan). You may have to update it if the smart contract is uptaded.