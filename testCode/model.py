from peewee import *

database = SqliteDatabase('blacklist.db')

class BaseModel(Model):
    class Meta:
        database = database

class Blacklist(BaseModel):
    url = CharField()
 

