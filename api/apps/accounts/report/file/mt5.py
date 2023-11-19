from matplotlib import pyplot as plt
import pandas as pd

FILE_EXTENSION = "ReportHistory.xlsx"
NEXT_TABLE = "Orders"


class Data:
    def __init__(self, xlsx_file_extension):
        self.file = pd.read_excel(xlsx_file_extension, usecols="A:O", skiprows=6)

        self.closed_position_time = pd.to_datetime(self.get_column("Time"))
        self.closed_position_profits = self.get_column("Profit")
        self.cumulative_profits = self.get_cumulative_profits(
            self.closed_position_profits
        )

    def table_length(self, table):
        for i, element in enumerate(table):
            if element == NEXT_TABLE or str(element) == "nan":
                return i

    def get_column(self, column_name):
        return self.file[column_name][: self.table_length(self.file[column_name])]

    def get_cumulative_profits(self, profits):
        cumulative_profits = []

        for i in range(len(profits)):
            if i == 0:
                cumulative_profits.append(round(profits[i], 2))
            else:
                cumulative_profits.append(
                    round(profits[i] + cumulative_profits[i - 1], 2)
                )
        return cumulative_profits
