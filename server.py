from uuid import uuid4

from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from core import Blockchain

app = FastAPI()
node_identifier = str(uuid4()).replace('-', '')
blockchain = Blockchain()


class Transactions(BaseModel):
    # Схема транзакции
    sender: str
    recipient: str
    amount: int


@app.exception_handler(RequestValidationError)
def validation_exception_handler():
    # Не валидные данные
    return PlainTextResponse('Missing values', status_code=400)


@app.get("/mine", status_code=status.HTTP_200_OK)
def mine():
    # Мы запускаем алгоритм подтверждения работы, чтобы получить следующее подтверждение…
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # Мы должны получить вознаграждение за найденное подтверждение
    # Отправитель “0” означает, что узел заработал крипто-монету
    blockchain.new_transaction(
            sender="0",
            recipient=node_identifier,
            amount=1,
    )

    # Создаем новый блок, путем внесения его в цепь
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return response


@app.post("/transactions/new", status_code=status.HTTP_201_CREATED)
def new_transaction(transactions: Transactions):
    # Создание новой транзакции
    index = blockchain.new_transaction(sender=transactions.sender,
                                       recipient=transactions.recipient,
                                       amount=transactions.amount, )

    response = {'message': f'Transaction will be added to Block {index}'}
    return response


@app.get('/chain')
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return response, 200
