from dotenv import load_dotenv
load_dotenv()

from web3.auto.infura import w3
from web3 import Web3
import requests
import time
import json
import os
import math
import codecs
import time


ABI_CACHE = {}


def get_abi(contract_addr):
    url_abi = f'https://api.etherscan.io/api?module=contract&action=getabi&address={contract_addr}'
    r = requests.get(url_abi)
    if r.status_code != 200:
        print(r.text)
    result = r.json()
    ABI_CACHE[contract_addr] = json.loads(result['result'])


def main(args):
    """
    Execute an eth transaction based on information from .env
    """
    THRESHOLD = int(os.environ.get('THRESHOLD'))
    BASE_FEE = int(os.environ.get('BASE_FEE'))
    PRIORITY_FEE = int(os.environ.get('PRIORITY_FEE'), 1)
    CONTRACT_ADDR = os.environ.get('CONTRACT_ADDR')
    FUNCTION_NAME = os.environ.get('FUNCTION_NAME')
    WALLET_ADDR = os.environ.get('WALLET_ADDR')
    value = os.environ.get('ETH_VALUE', 0)
    nonce = w3.eth.get_transaction_count(WALLET_ADDR)

    get_abi(CONTRACT_ADDR)
    contract = load_contract(CONTRACT_ADDR)

    # poll the gas price until its below our target
    gas_price = load_gas_price()
    while THRESHOLD < gas_price:
        time.sleep(5)
        gas_price = load_gas_price()
    
    priority_fee = Web3.toWei(PRIORITY_FEE, 'gwei')
    base_fee = Web3.toWei(BASE_FEE, 'gwei')
    transaction = {
        'from': WALLET_ADDR,
        'value': Web3.toWei(value, 'ether'),
        'nonce': nonce,
        'maxPriorityFeePerGas': priority_fee,
        'maxFeePerGas': base_fee + priority_fee
    }
    gas_estimate = getattr(contract.functions, FUNCTION_NAME)(args).estimateGas(transaction)
    # buffer gas limit in case estimate is incorrect
    transaction['gas'] = math.floor(gas_estimate * 1.2)

    txn = getattr(contract.functions, FUNCTION_NAME)(args).buildTransaction(transaction)
    


if __name__ == '__main__':
    main()