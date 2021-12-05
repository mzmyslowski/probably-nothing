import asyncio
import json
import os

from dotenv import load_dotenv
import requests
from web3 import Web3

load_dotenv()


INFURA_API_KEY = os.getenv('INFURA_API_KEY')
ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')

ETHERSCAN_ABI_URL = 'https://api.etherscan.io/api?module=contract&action=getabi&address={}&apikey={}'
INFURA_API_URL = f'https://mainnet.infura.io/v3/{INFURA_API_KEY}'

TRANSFER_SIGNATURE_HASH = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'


def handle_event(event, tx):
    abi_endpoint = ETHERSCAN_ABI_URL.format(tx['to'], ETHERSCAN_API_KEY)
    abi = json.loads(requests.get(abi_endpoint).text)
    if abi['message'] == 'OK':
        contract = web3.eth.contract(address=tx["to"], abi=abi["result"])
        func_obj, func_params = contract.decode_function_input(tx["input"])
        print('Name of the called function:', func_obj.fn_name)


async def log_loop(event_filter, getTransaction, poll_interval):
    while True:
        print('---------------------------------------------------')
        for event in event_filter.get_all_entries():
            if Web3.toJSON(event['topics'][0])[1:-1] == TRANSFER_SIGNATURE_HASH:
                tx = getTransaction(event['transactionHash'])
                handle_event(event, tx)
        await asyncio.sleep(poll_interval)


def main():
    event_filter = web3.eth.filter('latest')
    tx_callback = web3.eth.getTransaction
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            asyncio.gather(
                log_loop(event_filter, tx_callback, 2)))
    finally:
        loop.close()


if __name__ == "__main__":
    web3 = Web3(Web3.HTTPProvider(INFURA_API_URL))
    main()