import hashlib
import json
from dataclasses import dataclass, field
from time import time

import requests
from peewee import DoesNotExist
from playhouse.shortcuts import model_to_dict

from models import Chain


@dataclass
class Blockchain:
    nodes: set = field(default_factory=set)
    current_transactions: list = field(default_factory=list)

    def __post_init__(self):
        try:
            Chain.select().order_by(Chain.index.desc()).get()
        except DoesNotExist:
            self.new_block(previous_hash=1, proof=100)

    def new_block(self, proof, previous_hash=None):
        """
        Создание нового блока в блокчейне

        :param proof: <int> Доказательства проведенной работы
        :param previous_hash: (Опционально) хеш предыдущего блока
        :return: <dict> Новый блок
        """

        try:
            last_block = Chain.select().order_by(Chain.id.desc()).get().index
            index = last_block + 1
        except DoesNotExist:
            index = 1

        block = Chain.create(index=index,
                             timestamp=time(),
                             transactions=self.current_transactions,
                             proof=proof,
                             previous_hash=previous_hash or self.hash(
                                     index), )

        # Перезагрузка текущего списка транзакций
        self.current_transactions = []
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Направляет новую транзакцию в следующий блок

        :param sender: <str> Адрес отправителя
        :param recipient: <str> Адрес получателя
        :param amount: <int> Сумма
        :return: <int> Индекс блока, который будет хранить эту транзакцию
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block.index + 1

    @property
    def last_block(self):
        return Chain.select().order_by(Chain.id.desc()).get()

    @staticmethod
    def hash(block):

        """
        Создает хэш SHA-256 блока

        :param block: <dict> Блок
        :return: <str> Хеш блока
        """

        # Упорядочиваем хеш, иначе у нас будут противоречивые хеши
        if isinstance(block, Chain):
            block = model_to_dict(block)
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_proof):
        """
        Простой алгоритм доказательства работы:
        - Найдите число p, которое, будучи хэшировано с доказательством предыдущего блока,
          дает хэш с четырьмя нулями в начале

        :param last_proof: <int> Предыдушее доказательство
        :return: <int> Найденное доказательство
        """

        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Подтверждение доказательства работы: Содержит ли hash(last_proof, proof) 4 заглавных нуля?

        :param last_proof: <int> Предыдущее доказательство
        :param proof: <int> Текущее доказательство
        :return: <bool> True, если правильно, False, если нет.
        """

        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def register_node(self, node):
        """
        Вносим новый узел в список узлов

        :param node: <str> адрес узла, пример: 'http://192.168.0.5:5000'
        :return: None
        """

        self.nodes.add(f'{node.host}:{node.port}')
        self.nodes.add(f'192.168.1.215:8001')

    def valid_chain(self, chain):
        """
        Проверяем, является ли внесенный в блок хеш корректным

        :param chain: <list> blockchain
        :return: <bool> True если она действительна, False, если нет
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            # Проверьте правильность хеша блока
            if block['previous_hash'] != self.hash(last_block):
                return False

            # Проверяем, является ли подтверждение работы корректным
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        Это наш алгоритм Консенсуса, он разрешает конфликты,
        заменяя нашу цепь на самую длинную в цепи

        :return: <bool> True, если бы наша цепь была заменена, False, если нет.
        """

        neighbours = self.nodes
        new_chain = None

        # Ищем только цепи, длиннее нашей
        max_length = Chain.select().order_by(Chain.id.desc()).get().index

        # Захватываем и проверяем все цепи из всех узлов сети
        for node in neighbours:
            try:
                response = requests.get(f'http://{node}/chain')
            except Exception:
                continue

            if response.status_code == 200:
                length = len(response.json())
                chain = response.json()

                # Проверяем, является ли длина самой длинной, а цепь - валидной
                if length > max_length and self.valid_chain(chain):
                    # ic(chain)

                    max_length = length
                    new_chain = chain

        # Заменяем нашу цепь, если найдем другую валидную и более длинную
        if new_chain:
            # Очишаем базу данных
            Chain.delete().execute()

            for x in new_chain:
                Chain.create(
                        id=x.get('id'),
                        index=x.get('index'),
                        previous_hash=x.get('previous_hash'),
                        proof=x.get('proof'),
                        timestamp=x.get('timestamp'),
                        transactions=x.get('transactions'), )

            return True

        return False
