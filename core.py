class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []

    def new_block(self):
        # Создает новый блок и вносит его в цепь
        pass

    def new_transaction(self):
        # Вносит новую транзакцию в список транзакций
        pass

    @staticmethod
    def hash(block):
        # Хеширует блок
        pass

    @property
    def last_block(self):
        # Возвращает последний блок в цепочке
        pass
