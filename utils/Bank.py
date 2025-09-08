# Bank.py

class Bank:
    name: str
    amount_column: str
    category_column: str
    description_column: str
    note_column: str
    post_date_column: str

    def __init__(self, **bank_json):
        self.__dict__.update(bank_json)