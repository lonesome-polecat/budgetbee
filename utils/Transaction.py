# Transaction.py

class Transaction:
    bank_name: str
    amount: float
    category: str
    description: str
    note: str
    post_date: str

    def __init__(self, *args):
        self.bank_name = args[0]
        self.amount = args[1]
        self.category = args[2]
        self.description = args[3]
        self.note = args[4]
        self.post_date = args[5]

