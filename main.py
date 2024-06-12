try:
    import tkinter as tk
    import tkinter.ttk as ttk
    import csv
    import google_client as gc
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
    trans_by_cat = dict()
    categories = dict()
    updateCatObject = dict()
    isCCCU = True
    isDiscover = False
    POST_DATE = "Posting Date"

    def main(self):
        self.root = tk.Tk()
        self.root.title("BudgetBee")
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(side=tk.TOP)
        self.action_frame = tk.Frame(self.root)
        self.action_frame.pack(side=tk.BOTTOM)

        label = tk.Label(self.main_frame, text="Welcome to BudgetBee!")
        label.pack(side=tk.TOP, padx=10, pady=20)

        self.get_started_btn = tk.Button(self.action_frame, text="Get Started", command=(
            lambda: [self.check_bank_window()]))
        self.get_started_btn.pack(side=tk.BOTTOM, padx=10, pady=10)

        print("Beginning budget helper...")
        self.get_transactions('../transactions_short.csv')
        # self.get_transactions('../transactions_discover.csv')
        self.get_categories_from_google()
        self.root.mainloop()

    def check_bank_window(self):
        self.clear(self.main_frame)
        self.clear(self.action_frame)

        label = tk.Label(self.main_frame, text="Which bank are you using?")
        label.pack()
        bank_selector = ttk.Combobox(self.action_frame, values=["CCCU", "Discover"], textvariable="CCCU")
        bank_selector.pack()
        btn = tk.Button(self.action_frame, text="Next", command=(lambda: [self.set_bank(bank_selector), self.start_finances()]))
        btn.pack()

    def set_bank(self, bank_selector):
        bank = bank_selector.get()
        print(bank)
        if bank == "Discover":
            self.isCCCU = False
            self.isDiscover = True
            self.POST_DATE = "Post Date"
        else:
            bank = "CCCU"
            self.isCCCU = True
            self.isDiscover = False
            self.POST_DATE = "Posting Date"

        self.client.set_indices(bank)
        self.remove_duplicate_transactions()

    def remove_duplicate_transactions(self):
        last = self.client.get_last_transaction("CCCU" if self.isCCCU else "Discover")
        if not last:
            return
        last_date = dt.strptime(last[self.trans_headers[self.POST_DATE]], "%m/%d/%Y")
        for i, tran in enumerate(self.trans_list):
            tran_date = dt.strptime(tran[self.trans_headers[self.POST_DATE]], "%m/%d/%Y")
            print(tran)
            if tran_date < last_date:
                continue
            else:
                self.trans_list = self.trans_list[i:]
                print(self.trans_list)
                break

    def get_transactions(self, filename):
        print("Extracting transactions from csv...")
        with open(filename, 'r') as f:
            csvFile = csv.reader(f)
            for i, line in enumerate(csvFile):
                print(line)
                if i == 0:
                    for i, header in enumerate(line):
                        self.trans_headers.update({header: i})
                else:
                    self.trans_list.append(line)
            print(self.trans_headers)
            print(self.trans_list)
            self.trans_list = self.trans_list[::-1]
        # Now trans_list is populated and ordered by date (reverse)

    def get_categories_from_google(self):
        # call Google API with creds
        print("Getting categories from google sheets...")
        try:
            self.client = gc.GoogleClient()
            self.client.connect()
            self.categories = self.client.get_categories()
        except BaseException as err:
            app_error(err)

    def start_finances(self):
        self.make_fin_window()
        self.curr_index = -1
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

        self.date_val_label = tk.Label(self.date_row)
        self.date_val_label.pack(side=tk.RIGHT, padx=5, pady=10)
        self.amt_val_label = tk.Label(self.amt_row)
        self.amt_val_label.pack(side=tk.RIGHT, padx=5, pady=10)
        self.desc_val_label = tk.Label(self.desc_row)
        self.desc_val_label.pack(side=tk.RIGHT, padx=5, pady=10)

        self.category_box = ttk.Combobox(self.action_frame, values=self.categories)
        self.category_box.pack(side=tk.TOP, padx=10, pady=10)

        self.next_btn = tk.Button(self.action_frame, text="Next", command=self.next_item)
        self.next_btn.pack(side=tk.RIGHT)
        self.skip_btn = tk.Button(self.action_frame, text="Skip", command=(lambda: [self.next_item(True)]))
        self.skip_btn.pack(side=tk.RIGHT)
        self.back_btn = tk.Button(self.action_frame, text="Back", state=tk.DISABLED)
        self.back_btn.pack(side=tk.LEFT)

    def clear(self, frame: tk.Frame):
        for w in frame.winfo_children():
            w.destroy()

    def next_item(self, skip=False):
        if not skip:
            category = self.category_box.get()
            self.trans_list[self.curr_index][self.trans_headers[("Transaction Category" if self.isCCCU else "Category")]] = category
            print(self.trans_list[self.curr_index])
            if not self.trans_by_cat.get(category):
                self.trans_by_cat.update({category: []})
            # This does not allow going back yet
            self.trans_by_cat.get(category).append(self.trans_list[self.curr_index])
            print("Updating current index")
            self.curr_index += 1
        else:
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
        self.date_val_label.config(text=self.trans_list[self.curr_index][self.trans_headers[self.POST_DATE]])
        self.amt_val_label.config(text=self.trans_list[self.curr_index][self.trans_headers["Amount"]])
        self.desc_val_label.config(text=self.trans_list[self.curr_index][self.trans_headers["Description"]])

    def set_category(self, i, trans, category, notes=None):
        # Update both sets of data in parallel
        trans["category"] = category
        self.trans_list[i][self.trans_headers["category"]] = category
        if notes:
            trans["notes"] = notes
            self.trans_list[i][self.trans_headers["notes"]] = notes
        self.trans_by_cat[category].append(trans)

    def confirm_window(self):
        self.clear(self.main_frame)
        self.clear(self.action_frame)

        confirm_label = tk.Label(self.main_frame, text="All finished! Do you want to attempt to upload to Google Sheets?")
        confirm_label.pack()

        yes_btn = tk.Button(self.action_frame, text="Yes", command=(lambda : [self.save_backup_csv(), self.uploadToGoogle(), self.root.destroy()]))
        yes_btn.pack()
        no_btn = tk.Button(self.action_frame, text="No", command=(lambda : [self.save_backup_csv(), self.root.destroy()]))
        no_btn.pack()

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

    def save_backup_csv(self):
        # This works - leaves a blank row in between each row though
        try:
            with open(f"updated_transx_bak.csv", "w") as f:
                writer = csv.writer(f)
                writer.writerow(self.trans_headers.keys())
                writer.writerows(self.trans_list)
            return True
        except BaseException as err:
            print(f"Error: {err}")
            return False








if __name__ == "__main__":
    myApp = App()
    myApp.main()