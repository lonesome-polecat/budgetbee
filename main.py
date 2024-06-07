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
    transByCat = {}

    def main(self):
        self.root = tk.Tk()
        self.root.title("BudgetBee")
        self.label = tk.Label(self.root, text="Welcome to BudgetBee!").pack()

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



    def get_csv_file(self):
        print("")






if __name__ == "__main__":
    myApp = App()
    myApp.main()