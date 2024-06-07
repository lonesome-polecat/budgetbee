try:
    import tkinter as tk
    import csv
except BaseException as err:
    print(f"***ERROR: {err}\n\n Install the necessary packages:")
    import time
    time.sleep(5)


class App():
    trans_headers = dict()
    trans_list = []
    trans_by_cat = {}

    def main(self):
        self.root = tk.Tk()
        self.root.title("BudgetBee")
        self.label = tk.Label(self.root, text="Welcome to BudgetBee!").pack(side=tk.TOP, padx=10, pady=20)

        print("Beginning budget helper...")
        self.get_transactions('../transactions.csv')
        self.root.mainloop()

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
        # Now trans_list is populated and ordered by date

    def get_categories_from_google(self):
        # call Google API with creds
        print("Getting categories from google sheets...")

    def set_category(self, i, trans, category, notes=None):
        # Update both sets of data in parallel
        trans["category"] = category
        self.trans_list[i][self.trans_headers["category"]] = category
        if notes:
            trans["notes"] = notes
            self.trans_list[i][self.trans_headers["notes"]] = notes
        self.trans_by_cat[category].append(trans)


    def get_csv_file(self):
        print("")

    def create_note_and_total(self, category_transactions: list):
        note = ""
        total = 0
        for trans in category_transactions:
            note += f"{trans['description'][:6]} {trans['date']} ({trans['amount']})\n"
            total += trans['amount']

        return note, total

    def save_backup_csv(self):
        try:
            with open(f"updated_transx_bak.csv", "w+") as f:
                for trans in self.trans_list:
                    csv.writer(f, "w", trans)  # This is likely not how it works, want to write each array as line of csv
            return True
        except BaseException as err:
            print(f"Error: {err}")
            return False








if __name__ == "__main__":
    myApp = App()
    myApp.main()