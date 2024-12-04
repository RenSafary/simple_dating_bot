from peewee import *


db = SqliteDatabase('./database/db.db')

class BaseModel(Model):
    class Meta:
        database = db


class Users(BaseModel):
    id = IntegerField(primary_key=True)
    name_tg = CharField(max_length=255)
    name = CharField(max_length=255)
    information = TextField(null=True)
    sex = CharField(max_length=1, null=True)
    age = IntegerField(null=True)
    photo = BlobField(null=True)
    fav_sex = CharField(max_length=1, null=True)


class Liked_Users(BaseModel):
    user = ForeignKeyField(Users, backref="liked_users")
    liked_id = ForeignKeyField(Users)
    watched = BooleanField(null=True)
    mutually = BooleanField(null=True)
    date = DateField(null=True)


if __name__ == "__main__":
    db.connect()
    db.create_tables([Users, Liked_Users])
    db.close()