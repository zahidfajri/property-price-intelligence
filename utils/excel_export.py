from io import BytesIO
import pandas as pd


def create_excel_file(summary_df, listings_df):
    """
    Create an Excel file in memory with multiple sheets.
    """

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        summary_df.to_excel(
            writer,
            sheet_name="Price Summary",
            index=False
        )

        listings_df.to_excel(
            writer,
            sheet_name="Unit Listings",
            index=False
        )

    output.seek(0)

    return output