import google.auth.exceptions
import json
import sys

from utils.Transaction import Transaction

try:
    import tkinter as tk
    import tkinter.ttk as ttk
    from tkinter import filedialog
    import os

    # Set the working directory so program works when clicked in file explorer
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print("Current Working Directory:", os.getcwd())

    from utils.Bank import Bank
    import csv
    # import google_client as gc
    import utils.googleClient as gc
    from datetime import datetime as dt
except BaseException as err:
    print(f"***ERROR: {err}\n\n Install the necessary packages:")
    import time
    time.sleep(5)

def app_error(message):
    root = tk.Tk()
    label = tk.Label(root, text=message)
    label.pack(padx=10, pady=10)
    root.mainloop()

class App():
    client = None
    trans_headers = dict()
    trans_list = []
    categories = dict()
    updateCatObject = dict()

    def __init__(self):
        self.bank = None
        self.split_current = False
        self.sub_transactions = []

    def main(self):
        try:
            self.client = gc.GoogleSheetsClient()
            self.client.connect()
        except google.auth.exceptions.RefreshError as err:
            print("Invalid token. Removing and retrying...")
            os.remove("../token.json")
            self.client = gc.GoogleSheetsClient()
            self.client.connect(retry=True)
        except BaseException as err:
            app_error(err)
            exit(1)
        finally:
            try:
                config_json = open("budget_config.json", "r").read()
                self.config = json.loads(config_json)
                self.bank_names = [x["name"] for x in self.config["banks"]]
                print(self.bank_names)
            except BaseException as err:
                app_error(err)
                exit(1)

        self.root = tk.Tk()
        self.root.title("BudgetBee")
        self.main_frame = tk.Frame(self.root, width=300)
        self.main_frame.pack(side=tk.TOP, padx=10, pady=10)
        self.action_frame = tk.Frame(self.root)
        self.action_frame.pack(side=tk.BOTTOM, padx=10, pady=10)

        label = tk.Label(self.main_frame, text="Welcome to BudgetBee!")
        label.pack(side=tk.TOP, padx=10, pady=20)

        self.get_started_btn = tk.Button(self.action_frame, text="Get Started", command=(
            lambda: [self.check_bank_window()]))
        self.get_started_btn.pack(side=tk.BOTTOM, padx=10, pady=10)

        print("Beginning budget helper...")
        self.root.mainloop()

    def select_transactions_file(self):
        self.clear(self.main_frame)
        self.clear(self.action_frame)

        label = tk.Label(self.main_frame, text="Select transactions file to upload")
        label.pack(padx=5, pady=5)
        file_row = tk.Frame(self.main_frame)
        file_row.pack(side=tk.BOTTOM, padx=10, pady=5)
        entry = tk.Entry(file_row)
        entry.pack(side=tk.RIGHT, fill=tk.X)
        upload_btn = tk.Button(file_row, text="Upload", command=(lambda: [self.upload_file(entry)]))
        upload_btn.pack(side=tk.LEFT)

        btn = tk.Button(self.action_frame, text="Next",
                        command=(lambda: [self.check_month()]))
        btn.pack()

    def upload_file(self, entry):
        file = filedialog.askopenfilename()
        try:
            print("Extracting transactions from csv...")
            self.trans_list = self.bank.get_transactions_from_csv(file)
            self.client.set_positive_or_negative(self.bank)
            entry.insert(0, file)
        except BaseException as err:
            app_error(err)


    def check_bank_window(self):
        self.clear(self.main_frame)
        self.clear(self.action_frame)

        label = tk.Label(self.main_frame, text="Which bank are you using?")
        label.pack(padx=5, pady=5)
        bank_selector = ttk.Combobox(self.action_frame, values=self.bank_names)
        bank_selector.pack(padx=5, pady=5)
        bank_selector.set(self.bank_names[0])
        btn = tk.Button(self.action_frame, text="Next", command=(lambda: [self.set_bank(bank_selector), self.select_transactions_file()]))
        btn.pack()

    def set_bank(self, bank_selector):
        bank = bank_selector.get()
        # Initialize selected bank
        bank_json = self.config.get("banks")[self.bank_names.index(bank)]
        print(bank_json)
        self.bank = Bank(**bank_json)
        print("Got this far")

    def get_categories_from_google(self, month):
        # call Google API with creds
        print("Getting categories from google sheets...")
        try:
            self.categories = self.client.get_categories(month)
            self.categories.append("Income")  # TODO: remove and put these categories in config
            self.categories.append("Record Only")
            self.categories.remove("Leftover")
            self.categories.remove("Savings Priority")
        except BaseException as err:
            app_error(err)

    def check_month(self):
        self.clear(self.main_frame)
        self.clear(self.action_frame)
        self.client.get_sheet_names()
        months = []
        for key in self.client.monthsMap.keys():
            months.append(key)

        label = tk.Label(self.main_frame, text="Which month?")
        label.pack(padx=5, pady=5)
        month_selector = ttk.Combobox(self.action_frame, values=months)
        month_selector.pack(padx=5, pady=5)
        month_selector.set(months[0])
        btn = tk.Button(self.action_frame, text="Next",
                        command=(lambda: [self.set_month(month_selector), self.start_finances()]))
        btn.pack()

    def set_month(self, month_selector):
        month = month_selector.get()
        print(month)
        self.get_categories_from_google(month)


    def start_finances(self):
        self.curr_index = -1
        self.make_fin_window()
        self.num_trans = len(self.trans_list)
        self.skipped_trans = []
        self.gone_back = False

        self.next_item()

    def make_fin_window(self):
        self.clear(self.main_frame)
        self.clear(self.action_frame)

        self.trans_frame = tk.LabelFrame(self.main_frame, text="Transaction")
        self.trans_frame.pack()

        self.date_row = tk.Frame(self.trans_frame)
        self.date_row.pack()
        self.amt_row = tk.Frame(self.trans_frame)
        self.amt_row.pack()
        self.desc_row = tk.Frame(self.trans_frame)
        self.desc_row.pack()

        date_label = tk.Label(self.date_row, text="Date :")
        date_label.pack(side=tk.LEFT, padx=5, pady=10)
        amt_label = tk.Label(self.amt_row, text="Amount :")
        amt_label.pack(side=tk.LEFT, padx=5, pady=10)
        desc_label = tk.Label(self.desc_row, text="Description :")
        desc_label.pack(side=tk.LEFT, padx=5, pady=10)

        self.split_button = tk.Button(self.amt_row, text="Split?", fg="grey", command=self.add_sub_transaction)
        self.split_button.pack(side=tk.RIGHT, padx=5, pady=10)

        self.date_val_label = tk.Label(self.date_row)
        self.date_val_label.pack(side=tk.RIGHT, padx=5, pady=10)
        self.amt_val_label = tk.Label(self.amt_row)
        self.amt_val_label.pack(side=tk.RIGHT, padx=5, pady=10)
        self.desc_val_label = tk.Label(self.desc_row)
        self.desc_val_label.pack(side=tk.RIGHT, padx=5, pady=10)

        self.category_frame = tk.Frame(self.main_frame)
        self.category_frame.pack(padx=5, pady=5)

        self.sub_transactions_frame = tk.Frame(self.category_frame)
        self.sub_transactions_frame.pack(side=tk.TOP, padx=5, pady=5)

        self.category_box = ttk.Combobox(self.category_frame, values=self.categories)
        self.category_box.pack(side=tk.TOP, padx=10, pady=10)

        self.next_btn = tk.Button(self.action_frame, text="Next", command=self.next_item)
        self.next_btn.pack(side=tk.RIGHT)
        self.skip_btn = tk.Button(self.action_frame, text="Ignore", command=(lambda: [self.next_item(skip=True)]))
        self.skip_btn.pack(side=tk.RIGHT)
        self.back_btn = tk.Button(self.action_frame, text="Back", command=self.previous_item, state=tk.DISABLED)
        self.back_btn.pack(side=tk.LEFT)
        
    def add_sub_transaction(self):
        # Do this the first time
        if not self.split_current:
            # Hide the main category box
            self.category_box.pack_forget()
            # Add Reminder
            reminder_label = tk.Label(self.sub_transactions_frame,
                                      text="Remember to add negative sign (-)" if self.bank.sign == "-" else "",
                                      fg="red")
            reminder_label.pack(side=tk.TOP, padx=5, pady=10)
        
        self.split_current = True
        self.make_sub_transaction_frame(self.sub_transactions_frame)
        self.split_button.configure(text="Split again?")

    def make_sub_transaction_frame(self, parent_frame):
        index = len(self.sub_transactions) + 1
        sub_trans_amount_frame = tk.LabelFrame(parent_frame, text=("Sub transaction " + str(index)))
        sub_trans_amount_frame.pack()

        sub_trans_amt_label = tk.Label(sub_trans_amount_frame, text="Amount:")
        sub_trans_amt_label.pack(side=tk.LEFT, padx=5, pady=10)
        sub_trans_amount_box = tk.Entry(sub_trans_amount_frame)
        sub_trans_amount_box.pack(side=tk.LEFT, padx=5, pady=10)

        sub_trans_category_label = tk.Label(sub_trans_amount_frame, text="Category:")
        sub_trans_category_label.pack(side=tk.LEFT, padx=5, pady=10)
        sub_trans_category_box = ttk.Combobox(sub_trans_amount_frame, values=self.categories)
        sub_trans_category_box.pack(side=tk.LEFT, padx=5, pady=10)

        # Add new sub transaction widgets to top-level sub_transaction_widgets list
        self.sub_transactions.append({
            "amount": sub_trans_amount_box,
            "category": sub_trans_category_box,
            "note" : ""
        })

    def clear(self, frame: tk.Frame):
        for w in frame.winfo_children():
            w.destroy()

    def next_item(self, skip=False):
        if self.split_current:
            self.split_transaction()
            return
        if not skip:
            category = self.category_box.get()
            self.trans_list[self.curr_index].category = category
            print([self.trans_list[self.curr_index].description, self.trans_list[self.curr_index].category])
            print("Updating current index")
            self.curr_index += 1
        else:
            # TODO: Need to be able to go back on ignored transaction
            # TODO: Need to be able to autofill category with prev selection if gone_back = True
            self.trans_list.pop(self.curr_index)
            self.num_trans -= 1
            print("\n*** SKIPPED ***\n")
            print(self.trans_list)
            print(self.num_trans)
            print(self.curr_index)
        if self.curr_index == self.num_trans:
            self.confirm_window()
            return
        print("Updating labels")
        if self.curr_index > 0:
            self.back_btn.config(state=tk.ACTIVE)
        self.date_val_label.config(text=self.trans_list[self.curr_index].post_date)
        self.amt_val_label.config(text=self.trans_list[self.curr_index].amount)
        self.desc_val_label.config(text=self.trans_list[self.curr_index].description)
        self.category_box.set(self.trans_list[self.curr_index].category)

    def split_transaction(self):
        self.split_current = False
        curr_trans = self.trans_list[self.curr_index]
        self.trans_list.pop(self.curr_index)

        # Increase the number of total transactions
        self.num_trans += len(self.sub_transactions)

        for sub_trans in self.sub_transactions:
            transaction = Transaction(
                curr_trans.bank_name,
                 sub_trans["amount"].get(),
                 sub_trans["category"].get(),
                 curr_trans.description,
                 curr_trans.note,
                 curr_trans.post_date
            )
            self.trans_list.insert(self.curr_index, transaction)
            self.category_box.delete(0, "end")
            self.category_box.insert(0, transaction.category)
            self.next_item()

        self.clear(self.sub_transactions_frame)
        self.split_button.configure(text="Split?")
        self.category_box.pack()

    def previous_item(self):
        print("Going back...")
        self.curr_index -= 1
        category = self.trans_list[self.curr_index].category
        self.category_box.delete(0, "end")
        self.category_box.insert(0, category)

        # Reset labels
        if self.curr_index < 1:
            self.back_btn.config(state=tk.DISABLED)
        self.date_val_label.config(text=self.trans_list[self.curr_index].post_date)
        self.amt_val_label.config(text=self.trans_list[self.curr_index].amount)
        self.desc_val_label.config(text=self.trans_list[self.curr_index].description)

    def confirm_window(self):
        # TODO: Add 'back' button to revise last transaction or any transactions
        self.clear(self.main_frame)
        self.clear(self.action_frame)

        confirm_label = tk.Label(self.main_frame, text="All finished! Do you want to attempt to upload to Google Sheets?")
        confirm_label.pack()

        yes_btn = tk.Button(self.action_frame, text="Yes", command=(lambda : [self.uploadToGoogle(), self.root.destroy()]))
        yes_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        no_btn = tk.Button(self.action_frame, text="No", command=(lambda : [self.root.destroy()]))
        no_btn.pack(side=tk.LEFT, padx=5, pady=5)

    def uploadToGoogle(self):
        print("Uploading to Google")
        self.client.upload_transactions(self.trans_list)
        print("Success!")


    def create_note_and_total(self, category_transactions: list):
        note = ""
        total = 0
        for trans in category_transactions:
            note += f"{trans['description'][:6]} {trans['date']} ({trans['amount']})\n"
            total += trans['amount']

        return note, total


if __name__ == "__main__":
    myApp = App()
    myApp.main()