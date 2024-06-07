try:
    import tkinter as tk
    import csv
except BaseException as err:
    print(f"***ERROR: {err}\n\n Install the necessary packages:")
    import time
    time.sleep(5)


class App():
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



    def get_csv_file(self):
        print("")






if __name__ == "__main__":
    myApp = App()
    myApp.main()