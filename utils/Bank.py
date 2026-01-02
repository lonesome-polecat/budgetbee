# Bank.py
import csv
from utils.Transaction import Transaction

class Bank:
    """
    Holds bank information necessary for parsing transactions csv
    """
    name: str
    amount_column: str
    category_column: str
    description_column: str
    note_column: str
    post_date_column: str
    sign: str

    headers: dict

    cat_index: int
    amt_index: int
    note_index: int


    def __init__(self, **bank_json):
        self.__dict__.update(bank_json)
        self.headers = dict()

    def set_indices(self):
        # Headers must already be set using get_transactions_from_csv()
        # Else raise IndexError
        if len(self.headers) < 3:
            raise IndexError("Not enough headers")
        self.cat_index = self.headers.get(self.category_column)
        self.amt_index = self.headers.get(self.amount_column)
        self.note_index = self.headers.get(self.note_column)

    def get_transactions_from_csv(self, filename):
        transactions: list[Transaction] = []
        print("Extracting transactions from csv...")
        with open(filename, 'r') as f:
            csvFile = csv.reader(f)
            for i, line in enumerate(csvFile):
                if i == 0:
                    for i, header in enumerate(line):
                        self.headers.update({header: i})
                else:
                    # This fields MUST stay in this order - refer to Transaction class
                    transaction = Transaction(
                        self.name,
                        line[self.headers.get(self.amount_column)],
                        line[self.headers.get(self.category_column)],
                        line[self.headers.get(self.description_column)],
                        line[self.headers.get(self.note_column)],
                        line[self.headers.get(self.post_date_column)],
                    )
                    transactions.append(transaction)

        print(self.headers)
        # Set indices for
        self.set_indices()

        # order by date (reverse)
        return transactions[::-1]

