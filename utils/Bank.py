# Bank.py
import csv

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

    cat_index: int
    amt_index: int
    note_index: int


    def __init__(self, **bank_json):
        self.__dict__.update(bank_json)

    def set_indices(self):
        pass

    def get_transactions(self, filename):
        print("Extracting transactions from csv...")
        # TODO: Refactor get_transactions

