from app.core.models.main._base import MainTable


class User(MainTable, table=True):
    name: str
    email: str
    phone: str
    address: str
    password_hash: str
