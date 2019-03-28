import hashlib
import json
from time import time
from textwrap import dedent
from uuid import uuid4

from flask import Flask, jsonify, request, render_template


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.new_block(previous_hash=1, proof=100)  # This is the genesis bloc

    def new_block(self, proof, previous_hash=None):
        block = {
            "index": len(self.chain) + 1,
            "transactions": self.current_transactions,
            "proof": proof,
            "previous_hash": previous_hash or self.hash(self.chain[-1]),
        }

        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        self.current_transactions.append({
            "sender": sender,
            "recipient": recipient,
            "amount": amount,
        })

        return self.last_block["index"]+1

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        print(block_string)
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def test_block(self, proof):
        block = {
            "index": len(self.chain) + 1,
            "transactions": self.current_transactions,
            "proof": proof,
            "previous_hash": self.hash(self.chain[-1]),
        }
        return block

    def proof_of_work(self):
        proof = 0
        test = self.test_block(proof)
        while self.valid_proof(self, test) is False:
            proof += 1
            test = self.test_block(proof)
        return proof

    @staticmethod
    def valid_proof(self, block):
        guess_hash = self.hash(block)
        return guess_hash[:4] == "0000"


app = Flask(__name__, static_folder ="./client/dist/static", template_folder="./client/dist")
node_identifier = str(uuid4()).replace('-', '')
blockchain = Blockchain()

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new Transaction
    index = blockchain.new_transaction(
        values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/mine', methods=['GET'])
def mine():
    # We run the proof of work algorithm to get the next proof...
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work()

    # We must receive a reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin.
    # blockchain.new_transaction(
    #     sender="0",
    #     recipient=node_identifier,
    #     amount=1,
    # )

    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    print("=== last block here")
    print(last_block)
    return jsonify(response), 200

@app.route('/transactions', methods =['GET'])
def current_transactions():
    response = blockchain.current_transactions
    return jsonify(response), 200

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200
