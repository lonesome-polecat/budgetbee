# test_bank.py
import pytest
from utils.Bank import Bank
import json
import os

bank1_json = """
{           "name": "bank1",
            "amount_column": "Amount",
            "category_column": "Transaction Category",
            "description_column": "Description",
            "note_column": "Memo",
            "post_date_column": "Posting Date"
}
"""

@pytest.fixture(scope="class")
def bank1():
    bank_dict = json.loads(bank1_json)
    bank = Bank(**bank_dict)

    return bank

@pytest.fixture(scope="class")
def filename1():
    # Get sample transactions file for tests
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print("Current Working Directory:", os.getcwd())
    transactions_file_name = "bank1_sample_transactions.csv"

    return transactions_file_name


class TestBank1:

    def test_bank1_parse_transactions(self, bank1, filename1):
        transactions = bank1.get_transactions_from_csv(filename1)
        assert transactions[0].amount == "-118"
        assert transactions[-1].amount == "-6.05"