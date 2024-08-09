import os.path
import csv
import tkinter as tk
from tkinter import messagebox

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# The ID and range of spreadsheet.
BUDGET_SHEET = open("google_sheet.txt", "r").read()
BUDGET_SHEET_RANGE = "May!F3:F31"
try_again = False

class GoogleClient():
  service = None
  categories = []
  categoriesMap = {}
  CAT_INDEX = 8
  AMOUNT_INDEX = 4
  NOTE_INDEX = 11
  isCCCU = True
  isDiscover = False

  class CategoryObject:
    def __init__(self, index, value, note):
      self.index = index
      self.value = value
      self.note = note

  def connect(self):
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
      self.service : Resource = build("sheets", "v4", credentials=creds)
      return True
    except HttpError as err:
      print(err)
      return False

  def set_indices(self, bank):
    if bank == "Discover":
      self.isDiscover = True
      self.isCCCU = False
      self.CAT_INDEX = 4
      self.AMOUNT_INDEX = 3
      self.NOTE_INDEX = 5
    else:
      self.isDiscover = False
      self.isCCCU = True
      self.CAT_INDEX = 8
      self.AMOUNT_INDEX = 4
      self.NOTE_INDEX = 11

  def get_last_transaction(self, bank):
    sheet = self.service.spreadsheets()
    result = sheet.values().get(
      spreadsheetId=BUDGET_SHEET,
      range="transactions!A2:M"
    ).execute()
    values = result.get("values")
    if not values:
      return []
    last_tran = []
    if bank == "CCCU":
      for i in range(len(values)-1, 0, -1):
        print(i)
        print(values[i])
        if len(values[i]) > 7:
          last_tran = values[i]
          break
      print(last_tran)
      return last_tran
    elif bank == "Discover":
      for i in range(len(values)-1, 0, -1):
        if len(values[i]) < 7:
          last_tran = values[i]
          break
      print(last_tran)
      return last_tran

  def get_categories(self, month):
    try:
      # Call the Sheets API
      self.selected_month = month
      self.sheet = self.service.spreadsheets()
      result = (
        self.sheet
        .get(spreadsheetId=BUDGET_SHEET, ranges=[f"{month}!F3:G31"],
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
            self.savingsStartIndex = i+1
            continue
          categories.append(cat)
          if len(row.get("values")) > 1 and row.get("values")[1].get("userEnteredValue"):
            catObj = self.CategoryObject(
              i,
              row.get("values")[1].get("userEnteredValue").get("formulaValue") or row.get("values")[1].get("userEnteredValue").get("numberValue"),
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
      print(err)

  def test_uploadDataSpreadSheets(self):
    self.sheet = self.service.spreadsheets()
    request = {
      "updateCells": {
        "range": {
          "sheetId": 1456670933,
          "startColumnIndex": 6,
          "startRowIndex": 3,
          "endColumnIndex": 7,
          "endRowIndex": 4
        },
        "rows": [
          {
            "values" : {
              "note": "My note is here!"
            }
          }
        ],
        "fields": "note"
      }
    }
    body = {"requests" : [request]}
    result = (
      self.sheet.batchUpdate(spreadsheetId=BUDGET_SHEET,
              body=body
              )
      .execute()
    )
    print(result)

  def upload_transactions(self, transactions: list[list[str]]):
    if try_again:
      self.uploadExpenses()
      return
    rows = []
    print(F"categories = {self.categories}")
    for tran in transactions:
      print(tran[self.CAT_INDEX])
      if tran[self.CAT_INDEX] in self.categories:
        self.updateExpenses(tran)
      else:
        error = f"Invalid category: ({tran[self.CAT_INDEX]}) how did that get in there?"
        print(error)
      values = []
      for item in tran:
        values.append({"userEnteredValue": {"stringValue":item}})
      rows.append({"values": values})
    transSheetId = 2020165441
    # original / test transSheetId = 215826180
    request = {"appendCells":
      {
        "sheetId": transSheetId,
        "rows": rows,
        "fields": "userEnteredValue"
      }
    }

    body = {"requests": [request]}
    self.sheet = self.service.spreadsheets()
    result = (
      self.sheet.batchUpdate(spreadsheetId=BUDGET_SHEET,
                             body=body
                             )
      .execute()
    )
    print(result)
    self.uploadExpenses()

  def updateExpenses(self, tran: list):
    print("******** UPDATING EXPENSES *********\n")
    cat = tran[self.CAT_INDEX]
    if cat == "Income" or cat == "Unknown":
      return
    if self.categoriesMap.get(cat).index < self.savingsStartIndex:
      sign = "-" if self.isCCCU else "+"
    else:
      sign = "+" if self.isCCCU else "-"
    if self.categoriesMap.get(cat).value:
      print(self.categoriesMap.get(cat).value)
      if type(self.categoriesMap.get(cat).value) is int:
        self.categoriesMap.get(cat).value = str(self.categoriesMap.get(cat).value)
      self.categoriesMap.get(cat).value += sign + tran[self.AMOUNT_INDEX]
    else:
      self.categoriesMap.get(cat).value = "=" + sign + tran[self.AMOUNT_INDEX]
    print(self.categoriesMap.get(cat).value)

  def test_upload_transactions(self):
    print("Extracting transactions from csv...")
    filename = '../transactions_short.csv'
    # filename = '../transactions_discover.csv'
    trans_list = []
    with open(filename, 'r') as f:
      csvFile = csv.reader(f)
      for i, line in enumerate(csvFile):
        print(line)
        trans_list.append(line)

    self.upload_transactions(trans_list)
    # self.uploadExpenses()
    print("ALL DONE!!!")

  def uploadExpenses(self):
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
          "endRowIndex": 31
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
    # Initialize fix window
    root = tk.Tk()
    root.title("Data Editor")

    # Dictionary to store entry widgets for later access
    entry_dict = {}
    def update_data():
      for category, entry_widget in entry_dict.items():
        for value_key in self.categoriesMap[category]:
          new_value = entry_widget.get()
          self.categoriesMap.get(category).value = new_value
      print("Values have been updated! Try uploading again")
      messagebox.showinfo("Updated", "Values have been updated! Try uploading again")
      root.destroy()

    for idx, (category, values) in enumerate(self.categoriesMap.items()):
      category_label = tk.Label(root, text=category)
      category_label.grid(row=idx, column=0, padx=10, pady=10)

      entry = tk.Entry(root)
      entry.insert(0, list(values.values())[0])
      entry.grid(row=idx, column=1, padx=10, pady=10)

      entry_dict[category] = entry

    # Update button to save the changes
    update_button = tk.Button(root, text="Update", command=update_data)
    update_button.grid(row=len(self.categoriesMap), column=0, columnspan=2, pady=20)


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




if __name__ == "__main__":
  client = GoogleClient()
  if client.connect():
    client.get_sheet_names()
    # client.set_indices("Discover")
    # client.get_last_transaction("Discover")
    # client.get_categories()
    # client.test_upload_transactions()
    print("\n\n")
    # client.get_category_values_notes()
    # print(client.expenses)
    # client.uploadDataSpreadSheets()
    # client.get_prev_transactions()
