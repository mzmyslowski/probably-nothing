import asyncio
import json
import os
import time

from dotenv import load_dotenv
import requests
from web3 import Web3
from web3.exceptions import ABIFunctionNotFound, TransactionNotFound

load_dotenv()


INFURA_API_KEY = os.getenv('INFURA_API_KEY')
ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')

INFURA_API_URL = f'https://mainnet.infura.io/v3/{INFURA_API_KEY}'


class NFTScanner:
    TRANSFER_SIGNATURE_HASH = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
    ROUTER_ADDRESSES = {
        '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D': 'uniswap_v2',
        '0xe592427a0aece92de3edee1f18e0157c05861564': 'uniswap_v3'
    }
    ABI_PATH = './ABIs'

    def __init__(self, nfts, tokens, abis, web3_api_url, etherscan_api_key, wallets_filter=None):
        self.nfts = nfts
        self.tokens = tokens
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
        contract = self._get_contract(contract_address=contract_address)
        func_obj, func_params = contract.decode_function_input(input)
        return func_obj, func_params

    def _get_contract(self, contract_address):
        if self.abis.get(contract_address) is None:
            abi = self.get_abi(address=contract_address, etherscan_api_key=self.etherscan_api_key)
            self.abis[contract_address] = abi
            self._save_abi(address=contract_address, abi=abi)
        else:
            abi = self.abis[contract_address]
        contract = self.web3.eth.contract(address=contract_address, abi=abi)
        return contract

    def _handle_event(self, tx, contract_address):
        func_obj, func_params = self._decode_func(
            contract_address=contract_address,
            input=tx['input']
        )
        tx_hash = tx_hash = Web3.toJSON(tx['hash']).strip('"')
        if 'mint' in func_obj.fn_name:
            print(f'Address {tx["from"]} called {func_obj.fn_name} on {contract_address} in tx {tx_hash}')
        elif 'swap' in func_obj.fn_name and self.ROUTER_ADDRESSES.get(tx['to']) is not None:
            path = func_params['path']
            token_in = path[0]
            token_out = path[-1]

            # token_in_contract = self._get_contract(contract_address=token_in)
            # token_out_contract = self._get_contract(contract_address=token_out)
            # print(f'Address {tx["from"]} swaped {token_in_contract.functions.symbol().call()} for {token_out_contract.functions.symbol().call()} in tx {tx_hash}')
            print(
                f'Address {tx["from"]} swaped {self.tokens.get(token_in) or token_in} for {self.tokens.get(token_out) or token_out} in tx {tx_hash}')
        else:
            print(f'Handling of {func_obj.fn_name} wasn\'t implemented (tx {tx_hash}).')

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
                    self._log_loop(event_filter, tx_callback, 0.5)))
        finally:
            loop.close()

    async def _log_loop(self, event_filter, getTransaction, poll_interval):
        block_number = None
        while True:
            print('---------------------------------------------------')
            txs_already_spotted = []
            events = event_filter.get_all_entries()
            if len(events) > 0:
                new_block_number = events[0]['blockNumber']
                if block_number != new_block_number:
                    start = time.time()
                    transfer_events_count = 0
                    known_events_count = 0
                    block_number = new_block_number
                    print('Block number', block_number)
                    print('Number of txs', len(events))
                    for event in events:
                        try:
                            if (
                                    event['transactionHash'] not in txs_already_spotted and
                                    Web3.toJSON(event['topics'][0])[1:-1] == self.TRANSFER_SIGNATURE_HASH
                            ):
                                transfer_events_count += 1
                                txs_already_spotted.append(event['transactionHash'])
                                tx = getTransaction(event['transactionHash'])
                                contract_address = tx['to']
                                if self.ROUTER_ADDRESSES.get(tx['to']) is not None or self.nfts.get(tx['to']) is not None:
                                    known_events_count += 1
                                    try:
                                        self._handle_event(tx=tx, contract_address=contract_address)
                                    except ValueError as e:
                                        print(e)
                                    except ABIFunctionNotFound as e:
                                        print(e)
                        except TransactionNotFound as e:
                            print(e)
                    print('Transfer events count', transfer_events_count, f'({transfer_events_count / len(events)}%)')
                    print('Known events count', known_events_count, f'({known_events_count / len(events)}%)')
                    print('Processing block time', time.time() - start)
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
            loop.run_until_complete(asyncio.gather(self._log_loop(2)))
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
                        self._handle_event(tx=tx, contract_address=contract_address)
                    except ValueError as e:
                        print(e)
            await asyncio.sleep(poll_interval)


def main():
    with open('nfts.json', 'r') as f:
        nfts = json.load(f)
    with open('tokens.json', 'r') as f:
        tokens = json.load(f)
    ABIs = {}
    abis_names = [name for name in os.listdir('ABIs') if 'json' in name]
    for abi in abis_names:
        with open(f'ABIs/{abi}', 'r') as f:
            ABIs[abi[:-5]] = json.load(f)
    nft_scanner = BlockNFTScanner(
        nfts=nfts,
        tokens=tokens,
        abis=ABIs,
        web3_api_url=INFURA_API_URL.format(INFURA_API_KEY),
        etherscan_api_key=ETHERSCAN_API_KEY,
        # wallets_filter=['0x7Be8076f4EA4A4AD08075C2508e481d6C946D12b']
    )
    nft_scanner.start()


if __name__ == "__main__":
    main()