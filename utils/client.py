from abc import ABC, abstractmethod, abstractproperty

class client(ABC):
    """
    Abstract class to be implemented for the specific budget client - Google Sheets or Excel
    """

    budget: object
    budget_path: str

    @abstractmethod
    def download_budget(self):
        """
        Convert budget spreadsheet into data object for manipulation
        :return:
        """
        pass

    @abstractmethod
    def upload_budget(self):
        """
        Upload modified budget object to the budget spreadsheet
        :return:
        """
        pass

    def add_transaction(self):
        pass

    def test_connection(self):
        pass

