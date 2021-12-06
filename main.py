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


def get_abi(address):
    a = json.loads(requests.get(ETHERSCAN_ABI_URL.format(address, ETHERSCAN_API_KEY)).text)
    result = a['result']
    with open(f'ABIs/{address}.json', 'w') as f:
        json.dump(result, f)
    ABIs[address] = result


def handle_event(event, tx):
    if ABIs.get(tx['to']) is None:
        get_abi(address=tx['to'])
    abi = ABIs[tx['to']]
    try:
        contract = web3.eth.contract(address=tx["to"], abi=abi)
        func_obj, func_params = contract.decode_function_input(tx["input"])
        print(f'Address {tx["from"]} called {func_obj.fn_name} on {event["address"]}')
    except ValueError as e:
        print(e)


async def log_loop(event_filter, getTransaction, poll_interval):
    block_number = None
    while True:
        print('---------------------------------------------------')
        events = event_filter.get_all_entries()
        if block_number != events[0]['blockNumber']:
            block_number = events[0]['blockNumber']
            print('Block number', block_number)
            for event in event_filter.get_all_entries():
                if event['address'] in nfts_addresses:
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
    with open('nfts.json', 'r') as f:
        nfts = json.load(f)
    ABIs = {}
    abis_names = [name for name in os.listdir('ABIs') if 'json' in name]
    for abi in abis_names:
        with open(f'ABIs/{abi}', 'r') as f:
            ABIs[abi[:-5]] = json.load(f)
    nfts_addresses = nfts.values()
    web3 = Web3(Web3.HTTPProvider(INFURA_API_URL))
    main()