import json
import os

from dotenv import load_dotenv

from scanners import BlockNFTScanner, EtherscanNFTScanner
from mail_factory import SMTPEmail

load_dotenv()


INFURA_API_KEY = os.getenv('INFURA_API_KEY')
ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')

RECEIVERS = json.loads(os.getenv('RECEIVERS'))

INFURA_API_URL = f'https://kovan.infura.io/v3/{INFURA_API_KEY}'


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
    smtp_email = SMTPEmail(receivers=RECEIVERS)
    nft_scanner = EtherscanNFTScanner(
        nfts=nfts,
        tokens=tokens,
        abis=ABIs,
        web3_api_url=INFURA_API_URL.format(INFURA_API_KEY),
        etherscan_api_key=ETHERSCAN_API_KEY,
        send_mails=smtp_email.send_email,
        wallets_filter=['0x10a3cEEB91D4f01FD5F43BB6FD1f1A2881847BdE']
    )
    nft_scanner.start()


if __name__ == "__main__":
    main()