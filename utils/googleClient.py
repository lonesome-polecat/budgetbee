import os
import json
from utils.client import client
from utils.Bank import Bank
from utils.Transaction import Transaction
import tkinter as tk  # Eventually remove TK from googleClient (use callback functions instead)
from tkinter import messagebox  # Eventually remove

import google.auth.exceptions
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError

from google_client import TRANSACTIONS_GRID_ID

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# The ID and range of spreadsheet.
try:
  with open("budget_config.json", "r") as f:
    config = json.load(f)
    BUDGET_SHEET = config.get("sheet_id")
    TRANSACTIONS_GRID_ID = config.get("transactions_gid")
    curr_user = config.get("user")
except Exception as e:
  print(e)
  print("Reverting to defaults...")
  BUDGET_SHEET = open("google_sheet.txt", "r").read()
  TRANSACTIONS_GRID_ID = "1957578877"
  curr_user = "user"
try_again = False


class GoogleSheetsClient(client):
    """
    Client to interact with Google Sheets for retrieving, modifying, and uploading budgets
    """
    budget: any
    service = None  # Connection service
    categories = []
    categoriesMap = {}
    CAT_INDEX = 8
    AMOUNT_INDEX = 4
    NOTE_INDEX = 11
    bank = None

    class CategoryObject:
        def __init__(self, index, value, note):
            self.index = index
            self.value = value
            self.note = note

    def connect(self, retry=False):
        """Shows basic usage of the Sheets API.
        Prints values from a sample spreadsheet.
        """
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists("../token.json"):
            creds = Credentials.from_authorized_user_file("../token.json", SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "./../credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("../token.json", "w") as token:
                token.write(creds.to_json())

        try:
            self.service: Resource = build("sheets", "v4", credentials=creds)
            return True
        except HttpError as err:
            print(err)
            return False
        except google.auth.exceptions.RefreshError as err:
            print(err)
            if not retry:
                print("Removing expired token and trying to establish auth again...")
                os.remove("../token.json")
                self.connect(True)

    def download_budget(self):
        # Not implemented
        pass

    def upload_budget(self):
        # Not implemented
        pass

    def get_categories(self, month):
        try:
            # Call the Sheets API
            self.selected_month = month
            self.sheet = self.service.spreadsheets()
            result = (
                self.sheet
                .get(spreadsheetId=BUDGET_SHEET, ranges=[f"{month}!F3:G50"], # TODO: fix hardcoding
                     fields="sheets/data/rowData/values/note,sheets/data/rowData/values/userEnteredValue")
                .execute()
            )
            rowData = result.get("sheets")[0].get("data")[0].get("rowData")
            print(rowData)
            categories = []
            for i, row in enumerate(rowData):
                if row.get("values"):
                    cat = row.get("values")[0].get("userEnteredValue").get("stringValue")
                    if cat == "Leftover":
                        self.budgetEndIndex = i
                        self.savingsStartIndex = i + 1
                    categories.append(cat)
                    if len(row.get("values")) > 1 and row.get("values")[1].get("userEnteredValue"):
                        catObj = self.CategoryObject(
                            i,
                            row.get("values")[1].get("userEnteredValue").get("formulaValue") or row.get("values")[
                                1].get("userEnteredValue").get("numberValue"),
                            row.get("values")[1].get("note") or ""
                        )
                    else:
                        catObj = self.CategoryObject(
                            i,
                            "",
                            ""
                        )
                    self.categoriesMap.update({cat: catObj})
            self.categories = categories
            print(categories)
            return categories
        except HttpError as err:
            print(f"Something went wrong with fetching the categories: {err}")
            exit(1)

    def upload_transactions(self, transactions: list[Transaction]):
        if try_again:
            self.upload_expenses()
            return
        rows = []
        NUM_TRANSACTION_COLUMNS = 7
        print(F"categories = {self.categories}")

        # order by date desc (reverse the list)
        transactions = transactions[::-1]
        for tran in transactions:
            print(tran.category)
            if tran.category in self.categories:
                self.updateExpenses(tran)
            else:
                error = f"Invalid category: ({tran.category}) how did that get in there?"
                print(error)
            values = []
            # Create the transaction row
            values.append({"userEnteredValue": {"stringValue": tran.post_date}})
            values.append({"userEnteredValue": {"stringValue": tran.bank_name}})
            values.append({"userEnteredValue": {"stringValue": tran.amount}})
            values.append({"userEnteredValue": {"stringValue": tran.description}})
            values.append({"userEnteredValue": {"stringValue": tran.category}})
            values.append({"userEnteredValue": {"stringValue": curr_user}})
            values.append({"userEnteredValue": {"stringValue": tran.note}})
            rows.append({"values": values})

        # First, insert new rows at the top of the sheet
        insertRowsRequest = {
            "insertDimension": {
                "range": {
                    "sheetId": TRANSACTIONS_GRID_ID,
                    "dimension": "ROWS",
                    "startIndex": 1,
                    "endIndex": len(rows) + 1
                }
            }
        }

        # Fill the new rows with the transactions, the most recent at the top
        updateRowsRequest = {
            "updateCells": {
                "range": {
                    "sheetId": TRANSACTIONS_GRID_ID,
                    "startRowIndex": 1,
                    "endRowIndex": len(rows) + 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": NUM_TRANSACTION_COLUMNS
                },
                "rows": rows,
                "fields": "userEnteredValue"
            }
        }

        body = {"requests": [insertRowsRequest, updateRowsRequest]}
        self.sheet = self.service.spreadsheets()
        result = (
            self.sheet.batchUpdate(spreadsheetId=BUDGET_SHEET,
                                   body=body
                                   )
            .execute()
        )
        print(result)
        self.upload_expenses()

    def updateExpenses(self, tran: Transaction):
        print("******** UPDATING EXPENSES *********\n")
        cat = tran.category
        if cat == "Income" or cat == "Record Only":
            return
        if self.categoriesMap.get(cat).index < self.savingsStartIndex:
            sign = self.expenses_sign
        else:
            sign = self.savings_sign
        if self.categoriesMap.get(cat).value:
            print(self.categoriesMap.get(cat).value)
            if type(self.categoriesMap.get(cat).value) is int:
                self.categoriesMap.get(cat).value = str(self.categoriesMap.get(cat).value)
            self.categoriesMap.get(cat).value += sign + tran.amount
        else:
            self.categoriesMap.get(cat).value = "=" + sign + tran.amount
        print(self.categoriesMap.get(cat).value)

    def upload_expenses(self):
        self.sheet = self.service.spreadsheets()
        rows = []
        last_index = -1
        for category in self.categoriesMap.values():
            print(category.index)
            print(category.value)
            print(category.note)
            if not category.value:
                continue
                # Check for values that are not formula values (we just entered them on the spreadsheet) change to formula
            if type(category.value) is int:
                category.value = "=" + str(category.value)
            while category.index != last_index + 1:
                rows.append({})
                last_index += 1
            values = [{
                "userEnteredValue": {
                    "formulaValue": category.value or "="
                },
                "note": category.note or ""
            }]
            rows.append({"values": values})
            last_index += 1
        print(len(rows))
        sheetId = self.monthsMap.get(self.selected_month)
        request = {
            "updateCells": {
                "range": {
                    "sheetId": sheetId,
                    "startColumnIndex": 6,
                    "startRowIndex": 2,
                    "endColumnIndex": 7,
                    "endRowIndex": 50
                },
                "rows": rows,
                "fields": "userEnteredValue"
            }
        }
        body = {"requests": [request]}
        try:
            result = (
                self.sheet.batchUpdate(spreadsheetId=BUDGET_SHEET,
                                       body=body
                                       )
                .execute()
            )
            print(result)
        except BaseException as e:
            print(f"Error with upload: {e}")
            self.fix_data()

    def fix_data(self):
        print("Made it here")
        # Initialize fix window
        root = tk.Toplevel()
        root.title("Data Editor")

        # Dictionary to store entry widgets for later access
        entry_dict = {}

        def update_data():
            for category, entry_widget in entry_dict.items():
                new_value = entry_widget.get()
                self.categoriesMap.get(category).value = new_value
            print("Values have been updated! Try uploading again")
            messagebox.showinfo("Updated", "Values have been updated! Uploading again")
            root.destroy()
            self.upload_expenses()

        for idx, (category, values) in enumerate(self.categoriesMap.items()):
            if idx < 13:
                row = idx
                col = 0
            else:
                row = idx - 13
                col = 2
            category_label = tk.Label(root, text=category)
            category_label.grid(row=row, column=col, padx=10, pady=10)

            entry = tk.Entry(root)
            entry.insert(0, values.value)
            entry.grid(row=row, column=col + 1, padx=10, pady=10)

            entry_dict[category] = entry

        # Update button to save the changes
        update_button = tk.Button(root, text="Update", command=update_data)
        update_button.grid(row=len(self.categoriesMap), column=0, columnspan=2, pady=20)
        root.mainloop()

    def get_sheet_names(self):
        sheet = self.service.spreadsheets()
        result = sheet.get(spreadsheetId=BUDGET_SHEET).execute()
        print(result.keys())
        self.monthsMap = {}
        for tab in result.get("sheets"):
            if tab.get("properties").get("title") == "transactions":
                continue
            self.monthsMap.update({
                tab.get("properties").get("title"): tab.get("properties").get("sheetId")
            })
        print(self.monthsMap)

    def set_positive_or_negative(self, bank: Bank):
        self.expenses_sign = bank.sign
        self.savings_sign = "-" if bank.sign == "+" else "+"

