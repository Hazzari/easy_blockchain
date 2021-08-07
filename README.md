# Simply blockchain


Реализация простого варианта blockchain.

- Сервер - FastAPI
- DB - SQLite
- ORM - peewee

### API:
```text
/docs - Список API
/mine - Майнить новый блок
/transactions/new - Новая транзакция
/chain - Список всех блоков
/nodes/register - Регистрация новой ноды
/nodes/resolve - Разрешить конфликт(Консенсус)
```
Настройка виртуальной среды
```shell
poetry update 
```
Запуск сервера
```shell
cd easy_blockchain
uvicorn server:app --reload
```

#### Запуск в Docker:
```shell
docker-compose build
docker-compose up -d'
```
Подключаться по адресу localhost:5000

