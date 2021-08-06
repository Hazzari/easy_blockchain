import hashlib
import json
from dataclasses import dataclass, field
from time import time

from peewee import DoesNotExist
from playhouse.shortcuts import model_to_dict

from models import Chain


@dataclass
class Blockchain:
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
        block_string = json.dumps(model_to_dict(block), sort_keys=True).encode()
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
