from peewee import *

database = SqliteDatabase('central_blacklist.db')

class BaseModel(Model):
    class Meta:
        database = database

class Blacklist(BaseModel):
    url = CharField(unique = True)
 

