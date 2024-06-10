import os.path
import csv

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# The ID and range of spreadsheet.
BUDGET_SHEET = open("google_sheet.txt", "r").read()
BUDGET_SHEET_RANGE = "May!A1:K34"

class GoogleClient():
  service = None
  budgetItems = {}
  categories = []

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

  def get_sheet_values(self):
    try:
      # Call the Sheets API
      self.sheet = self.service.spreadsheets()
      result = (
        self.sheet.values()
        .get(spreadsheetId=BUDGET_SHEET, range=BUDGET_SHEET_RANGE)
        .execute()
      )
      print(result)
      values = result.get("values", [])

      if not values:
        print("No data found.")
        return

      act_index = None
      for i, row in enumerate(values):
        print(row)
        if i == 0:
          for j, col in enumerate(row):
            if col == "Actual":
              act_index = j
              break
        else:
          if (len(row) < act_index+1):
            break
          self.categories.append(row[act_index])
      print(self.categories)
      return self.categories
    except HttpError as err:
      print(err)

  def get_sheet_values_spreadsheets(self):
    try:
      # Call the Sheets API
      self.sheet = self.service.spreadsheets()
      result = (
        self.sheet
        .get(spreadsheetId=BUDGET_SHEET, ranges=["May!A1:G20"], fields="sheets/data/rowData/values/note,sheets/data/rowData/values/userEnteredValue")
        .execute()
      )
      print(result)
      rowData = result.get("sheets")[0].get("data")[0].get("rowData")
      print(rowData)
      for i, row in enumerate(rowData):
        for j in range(4, len(row.get("values"))):
          if row.get("values")[j].get("userEnteredValue"):
            print(row.get("values")[j].get("userEnteredValue").get("stringValue"))
            if row.get("values")[j].get("userEnteredValue").get("stringValue") in self.categories:
              if len(row.get("values")) == j+1:
                category = {row.get("values")[j].get("userEnteredValue").get("stringValue"): {
                  "rowIndex": i,
                  "colIndex": j + 1,
                  "value": "",
                  "note": ""
                }}
              else:
                category = {row.get("values")[j].get("userEnteredValue").get("stringValue") : {
                  "rowIndex": i,
                  "colIndex": j+1,
                  "value": row.get("values")[j+1].get("userEnteredValue").get("formulaValue") or row.get("values")[j+1].get("userEnteredValue").get("numberValue"),
                  "note": row.get("values")[j+1].get("note")
                }}
              self.budgetItems.update(category)
              continue
      print(self.budgetItems)
    except HttpError as err:
      print(err)

  def get_prev_transactions(self):
    try:
      # Call the Sheets API
      self.sheet = self.service.spreadsheets()
      result = (
        self.sheet.values()
        .get(spreadsheetId=BUDGET_SHEET, range="transactions!A1:Z100")
        .execute()
      )
      values = result.get("values", [])
      if not values:
        print("No data found.")
        # In this case, use all transactions
        # Fill out sheet with headers and recent transactions
        return

      act_index = None
      categories = []
      for i, row in enumerate(values):
        print(row)
        if i == 0:
          for j, col in enumerate(row):
            if col == "Actual":
              act_index = j
              break
        else:
          if (len(row) < act_index + 1):
            break
          categories.append(row[act_index])
      print(categories)
      return categories

    except HttpError as err:
      print(err)


  def uploadData(self):
    self.sheet = self.service.spreadsheets()
    body = {"values": [["HelloThere", "colH"], ["Hi"], ["Thirdval"]]}
    result = (
      self.sheet.values()
      .update(spreadsheetId=BUDGET_SHEET,
              range="G2:H4",
              valueInputOption="USER_ENTERED",
              body=body
              )
      .execute()
    )
    print(result)

  def uploadDataSpreadSheets(self):
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

  def upload_transactions(self, transactions):
    rows = []
    for trans in transactions:
      values = []
      for item in trans:
        values.append({"userEnteredValue": {"stringValue":item}})
      rows.append({"values": values})
    request = {"appendCells":
      {
        "sheetId": 2027281898,
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

  def test_upload_transactions(self):
    print("Extracting transactions from csv...")
    filename = '../transactions.csv'
    trans_list = []
    with open(filename, 'r') as f:
      csvFile = csv.reader(f)
      for i, line in enumerate(csvFile):
        print(line)
        trans_list.append(line)

    self.upload_transactions(trans_list)








if __name__ == "__main__":
  client = GoogleClient()
  if client.connect():
    client.test_upload_transactions()
    # client.get_sheet_values()
    # client.get_sheet_values_spreadsheets()
    # client.uploadDataSpreadSheets()
    # client.get_prev_transactions()
