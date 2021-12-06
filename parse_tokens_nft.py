from bs4 import BeautifulSoup
import json
import os
import requests
import time


def main():
    while 'nfts.json' in os.listdir():
        input('nfts.json file already exists! Delete it and hit enter.')
    nft_dict = {}
    for i in range(1, 250):
        print(i)
        headers = {'User-Agent': 'Mozilla/5.0'}
        a = requests.get(f'https://etherscan.io/tokens-nft?ps=100&p={i}', headers=headers).text
        soup = BeautifulSoup(a)
        nft_list = soup.find_all('a', attrs={'class': 'text-primary'})
        for nft in nft_list:
            nft_dict[nft.string] = nft.get('title')
        time.sleep(0.1)
        with open('nfts.json', 'w') as f:
            json.dump(nft_dict, f)


if __name__ == "__main__":
    main()
