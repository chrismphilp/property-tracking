import datetime as dt
import pandas as pd
import pytz


class Parser:

    @staticmethod
    def create_data_frame(data: [str]):
        columns = ["price", "type", "address", "url", "added_on"]

        temp_df = pd.DataFrame(data)
        temp_df = temp_df.transpose()

        temp_df.columns = columns
        temp_df = temp_df[temp_df["address"].notnull()]

        london_tzinfo = pytz.timezone("Europe/London")
        temp_df["search_datetime"] = dt.datetime.now(dt.timezone.utc).astimezone(london_tzinfo).strftime("%I:%M%p on %B %d, %Y")

        return temp_df
