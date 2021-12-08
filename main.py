import asyncio
import json
import os
import time

from dotenv import load_dotenv
import requests
from web3 import Web3

load_dotenv()


INFURA_API_KEY = os.getenv('INFURA_API_KEY')
ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')

INFURA_API_URL = f'https://mainnet.infura.io/v3/{INFURA_API_KEY}'


class NFTScanner:
    TRANSFER_SIGNATURE_HASH = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
    ABI_PATH = './ABIs'

    def __init__(self, nfts, abis, web3_api_url, etherscan_api_key, wallets_filter=None):
        self.nfts = nfts
        self.abis = abis
        self.web3 = Web3(Web3.HTTPProvider(web3_api_url))
        self.etherscan_api_key = etherscan_api_key
        self.wallets_filter = wallets_filter

    def start(self):
        pass

    def _save_abi(self, address, abi):
        path = os.path.join(self.ABI_PATH, f'{address}.json')
        with open(path, 'w') as f:
            json.dump(abi, f)

    def _decode_func(self, contract_address, input):
        if self.abis.get(contract_address) is None:
            abi = self.get_abi(address=contract_address, etherscan_api_key=self.etherscan_api_key)
            self.abis[contract_address] = abi
            self._save_abi(address=contract_address, abi=abi)
        else:
            abi = self.abis[contract_address]
        contract = self.web3.eth.contract(address=contract_address, abi=abi)
        func_obj, func_params = contract.decode_function_input(input)
        return func_obj, func_params

    @staticmethod
    def get_abi(address, etherscan_api_key):
        etherscan_abi_url = 'https://api.etherscan.io/api?module=contract&action=getabi&address={}&apikey={}'
        a = json.loads(requests.get(etherscan_abi_url.format(address, etherscan_api_key)).text)
        result = a['result']
        return result


class BlockNFTScanner(NFTScanner):
    def start(self):
        event_filter = self.web3.eth.filter('latest')
        tx_callback = self.web3.eth.getTransaction
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(
                asyncio.gather(
                    self._log_loop(event_filter, tx_callback, 2)))
        finally:
            loop.close()

    async def _log_loop(self, event_filter, getTransaction, poll_interval):
        block_number = None
        while True:
            print('---------------------------------------------------')
            events = event_filter.get_all_entries()
            if block_number != events[0]['blockNumber']:
                block_number = events[0]['blockNumber']
                print('Block number', block_number)
                for event in event_filter.get_all_entries():
                    if event['address'] in self.nfts:
                        tx = getTransaction(event['transactionHash'])
                        contract_address = tx['to']
                        try:
                            func_obj, func_params = self._decode_func(contract_address=contract_address, input=tx['input'])
                            print(f'Address {tx["from"]} called {func_obj.fn_name} on {contract_address}')
                        except ValueError as e:
                            print(e)
            await asyncio.sleep(poll_interval)


class EtherscanNFTScanner(NFTScanner):
    GET_TRANSACTIONS_URL = (
        'https://api.etherscan.io/api'
        '?module=account'
        '&action=txlist'
        '&address={address}'
        '&startblock={startblock}'
        '&endblock=99999999'
        '&page=1'
        '&offset=10'
        '&sort=asc'
        '&apikey={apikey}'
    )
    GET_BLOCK_AT_TIMESTAMP_URL = (
        'https://api.etherscan.io/api'
        '?module=block'
        '&action=getblocknobytime'
        '&timestamp={timestsamp}'
        '&closest=before'
        '&apikey={apikey}'
    )

    def start(self):
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(
                asyncio.gather(
                    self._log_loop(2)))
        finally:
            loop.close()

    async def _log_loop(self, poll_interval):
        while True:
            print('---------------------------------------------------')
            block_number = json.loads(requests.get(
                self.GET_BLOCK_AT_TIMESTAMP_URL.format(timestsamp=int(time.time()), apikey=self.etherscan_api_key)
            ).text)['result']
            for address in self.wallets_filter:
                resp = requests.get(
                    self.GET_TRANSACTIONS_URL.format(
                        address=address,
                        startblock=block_number,
                        apikey=self.etherscan_api_key
                    )
                ).text
                txs = json.loads(resp)['result']
                for tx in txs:
                    contract_address = Web3.toChecksumAddress(tx['to'])
                    try:
                        func_obj, func_params = self._decode_func(contract_address=contract_address, input=tx['input'])
                        print(f'Address {tx["from"]} called {func_obj.fn_name} on {contract_address}')
                    except ValueError as e:
                        print(e)
            await asyncio.sleep(poll_interval)


def main():
    with open('nfts.json', 'r') as f:
        nfts = json.load(f)
    ABIs = {}
    abis_names = [name for name in os.listdir('ABIs') if 'json' in name]
    for abi in abis_names:
        with open(f'ABIs/{abi}', 'r') as f:
            ABIs[abi[:-5]] = json.load(f)
    nfts = nfts.values()
    nft_scanner = EtherscanNFTScanner(
        nfts=nfts,
        abis=ABIs,
        web3_api_url=INFURA_API_URL.format(INFURA_API_KEY),
        etherscan_api_key=ETHERSCAN_API_KEY,
        wallets_filter=['0x7Be8076f4EA4A4AD08075C2508e481d6C946D12b']
    )
    nft_scanner.start()


if __name__ == "__main__":
    main()