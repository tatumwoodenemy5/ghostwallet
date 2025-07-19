import time
import requests
from web3 import Web3

class GhostWalletProbe:
    def __init__(self, address, rpc_url):
        self.address = Web3.to_checksum_address(address)
        self.web3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self.web3.is_connected():
            raise ConnectionError("Unable to connect to the Ethereum node.")

    def check_nonce(self):
        return self.web3.eth.get_transaction_count(self.address)

    def check_gas_usage(self, block_window=100):
        latest_block = self.web3.eth.block_number
        total_gas = 0
        tx_count = 0
        for i in range(latest_block - block_window, latest_block):
            block = self.web3.eth.get_block(i, full_transactions=True)
            for tx in block.transactions:
                if tx['from'] == self.address or tx['to'] == self.address:
                    total_gas += tx['gas']
                    tx_count += 1
        return total_gas, tx_count

    def is_in_mempool(self):
        # Not all RPCs support this. We simulate by checking pending nonce drift.
        pending = self.web3.eth.get_transaction_count(self.address, 'pending')
        confirmed = self.web3.eth.get_transaction_count(self.address, 'latest')
        return pending > confirmed

    def activity_score(self):
        score = 0

        # Check nonce
        nonce = self.check_nonce()
        if nonce > 0:
            score += 30

        # Gas activity
        gas, txs = self.check_gas_usage()
        if gas > 0:
            score += min(30, gas // 10000)
        if txs > 0:
            score += min(20, txs * 2)

        # Mempool presence
        if self.is_in_mempool():
            score += 20

        return min(score, 100)
