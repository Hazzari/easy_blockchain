from asyncio import sleep
from uuid import uuid4

from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from core import Blockchain
from models import Chain


app = FastAPI()
node_identifier = str(uuid4()).replace('-', '')
blockchain = Blockchain()


class Transactions(BaseModel):
    # Схема транзакции
    sender: str
    recipient: str
    amount: int


class Node(BaseModel):
    # Схема ноды
    host: str
    port: str


@app.exception_handler(RequestValidationError)
def validation_exception_handler():
    # Не валидные данные
    return PlainTextResponse('Missing values', status_code=400)


@app.get("/mine", status_code=status.HTTP_200_OK)
async def mine():
    # Мы запускаем алгоритм подтверждения работы, чтобы получить следующее подтверждение…
    last_block = blockchain.last_block
    last_proof = last_block.proof
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
        'index': block.index,
        'transactions': block.transactions,
        'proof': block.proof,
        'previous_hash': block.previous_hash,
    }
    await sleep(1)
    return response


@app.post("/transactions/new", status_code=status.HTTP_201_CREATED)
def new_transaction(transactions: Transactions):
    # Создание новой транзакции
    index = blockchain.new_transaction(sender=transactions.sender,
                                       recipient=transactions.recipient,
                                       amount=transactions.amount, )

    response = {'message': f'Transaction will be added to Block {index}'}
    return response


@app.get('/chain', status_code=status.HTTP_200_OK)
def full_chain():
    return [x.__data__ for x in Chain.select()]


@app.post('/nodes/register', status_code=status.HTTP_201_CREATED)
def register_nodes(node: Node):
    blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return response


@app.get('/nodes/resolve', status_code=status.HTTP_200_OK)
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Наша цепь была заменена',
            'new_chain': [x.__data__ for x in Chain.select()]
        }
    else:
        response = {
            'message': 'Наша сеть авторитетная',
            'chain': [x.__data__ for x in Chain.select()]
        }
    return response
