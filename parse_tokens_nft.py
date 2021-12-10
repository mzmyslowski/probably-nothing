from bs4 import BeautifulSoup
import json
import os
import requests
import time

HEADERS = {'User-Agent': 'Mozilla/5.0'}


def main():
    file_to_save = input('Type name of the json file to save addresses: ')
    while file_to_save in os.listdir():
        file_to_save = input(f'{file_to_save} already exists. Type name of the json file to save addresses: ')
    to_download = input('Type T for Tokens or N for NFTs: ')
    while to_download not in ['N', 'T']:
        to_download = input('Don\'t joke around. Type T for Tokens or N for NFTs: ')
    pages = int(input('Type number of pages to download: '))
    addresses_dict = {}
    for i in range(1, pages):
        print(f'{i}/{pages}')
        a = requests.get(f'https://etherscan.io/tokens?ps=100&p={i}', headers=HEADERS).text
        soup = BeautifulSoup(a, 'html.parser')
        nft_list = soup.find_all('a', attrs={'class': 'text-primary'})
        for nft in nft_list:
            if to_download == 'T':
                addresses_dict[nft.string] = nft.get('href').replace('/token/', '')
            else:
                addresses_dict[nft.string] = nft.get('title')
        time.sleep(0.05)
        with open(file_to_save, 'w') as f:
            json.dump(addresses_dict, f)


if __name__ == "__main__":
    main()
