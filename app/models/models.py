import peewee

database = peewee.SqliteDatabase("Blockchain.db", check_same_thread=False)


class Chain(peewee.Model):
    class Meta:
        database = database

    index = peewee.BigIntegerField()
    timestamp = peewee.IntegerField()
    proof = peewee.IntegerField()
    previous_hash = peewee.BigIntegerField()
    transactions = peewee.CharField()
    # asd = peewee.VirtualField()


database.create_tables([Chain])
