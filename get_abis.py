import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')

ETHERSCAN_ABI_URL = 'https://api.etherscan.io/api?module=contract&action=getabi&address={}&apikey={}'


def main():
    addresses_file = input('Type name of the file with addresses: ')
    while not os.path.exists(addresses_file):
        addresses_file = input(f'{addresses_file} doesn\'t exists. Type name of the file with addresses: ')
    path_to_save = input('Type path to save addresses (e.g. ABIs/tokens/): ')
    if not os.path.exists(path_to_save):
        os.makedirs(path_to_save)
    already_downloaded = [abi[:-5] for abi in os.listdir(path_to_save) if '.json' in abi]
    with open(addresses_file, 'r') as f:
        nfts = json.load(f)
    addresses = nfts.values()
    for id, address in enumerate(addresses):
        print(f'{id + 1}/{len(addresses)}')
        if address not in already_downloaded:
            print('Getting abi for', address)
            a = json.loads(requests.get(ETHERSCAN_ABI_URL.format(address, ETHERSCAN_API_KEY)).text)
            path_to_file = os.path.join(path_to_save, f'{address}.json')
            with open(path_to_file, 'w') as f:
                json.dump(a['result'], f)
        else:
            print('ABI for', address, 'already exists')


if __name__ == "__main__":
    main()