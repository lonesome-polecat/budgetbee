import tkinter as tk
import tkinter.ttk as ttk

class BudgetBeeSetup:
    def __init__(self):
        current_configs = None

    def main(self):
        # See if user has existing configurations for budget sheet
        try:
            with open("bb_config.json", "r") as f:
                contents = f.read()
                self.get_current_config(contents) # placeholder
        except BaseException as err:
            self.modify_config()


        self.root = tk.Tk()
        self.root.title("BudgetBee")
        self.main_frame = tk.Frame(self.root, width=300)
        self.main_frame.pack(side=tk.TOP, padx=10, pady=10)
        self.action_frame = tk.Frame(self.root)
        self.action_frame.pack(side=tk.BOTTOM, padx=10, pady=10)

        label = tk.Label(self.main_frame, text="Welcome to BudgetBee setup!")
        label.pack(side=tk.TOP, padx=10, pady=20)

        self.get_started_btn = tk.Button(self.action_frame, text="Get Started", command=(
            lambda: [self.modify_config()]))
        self.get_started_btn.pack(side=tk.BOTTOM, padx=10, pady=10)

        print("Beginning budget helper...")
        # TODO: Set Bank error
        # self.get_transactions('../transactions_short.csv')
        # self.get_transactions('../transactions_discover.csv')
        # self.get_categories_from_google()
        self.root.mainloop()

    def modify_config(self):
        raise NotImplementedError("This is a placeholder")

    def get_current_config(self, current_config):
        raise NotImplementedError("This is a placeholder")


if __name__ == "__main__":
    app = BudgetBeeSetup()
    app.main()