import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')

ETHERSCAN_ABI_URL = 'https://api.etherscan.io/api?module=contract&action=getabi&address={}&apikey={}'


def main():
    already_downloaded = [abi[:-5] for abi in os.listdir('ABIs') if '.json' in abi]
    with open('nfts.json', 'r') as f:
        nfts = json.load(f)
    addresses = nfts.values()
    for id, address in enumerate(addresses):
        print(f'{id + 1}/{len(addresses)}')
        if address not in already_downloaded:
            print('Getting abi for', address)
            a = json.loads(requests.get(ETHERSCAN_ABI_URL.format(address, ETHERSCAN_API_KEY)).text)
            with open(f'ABIs/{address}.json', 'w') as f:
                json.dump(a['result'], f)
        else:
            print('ABI for', address, 'already exists')


if __name__ == "__main__":
    main()