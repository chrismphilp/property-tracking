import datetime as dt
import pandas as pd


class Parser:

    @staticmethod
    def create_data_frame(data: [str]):
        columns = ["price", "type", "address", "url", "added_on"]

        temp_df = pd.DataFrame(data)
        temp_df = temp_df.transpose()

        temp_df.columns = columns
        temp_df = temp_df[temp_df["address"].notnull()]

        temp_df["search_datetime"] = dt.datetime.now().strftime("%I:%M%p on %B %d, %Y")

        return temp_df
