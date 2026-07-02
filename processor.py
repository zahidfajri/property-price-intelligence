import pandas as pd


def load_data(csv_path):
    """
    Load CSV file into a DataFrame.
    """

    return pd.read_csv(csv_path)


def format_room_type(bedroom):
    """
    Convert bedroom number into display text.
    """

    if pd.isna(bedroom):
        return "Unknown"

    bedroom = int(bedroom)

    if bedroom == 0:
        return "Studio"

    if bedroom == 1:
        return "1 Bedroom"

    return f"{bedroom} Bedrooms"


def room_type_order(room_type):
    """
    Custom sorting order for room types.
    """

    order = {
        "Studio": 0,
        "1 Bedroom": 1,
        "2 Bedrooms": 2,
        "3 Bedrooms": 3,
        "4 Bedrooms": 4,
        "5 Bedrooms": 5,
        "Unknown": 999
    }

    return order.get(room_type, 999)


def calculate_summary(df):
    """
    Calculate summary statistics by room type.
    """

    # Create display labels
    df["Room Type"] = df["bedroom"].apply(
        format_room_type
    )

    summary = []

    grouped = df.groupby("Room Type")

    for room_type, group in grouped:

        mode_price = group["monthly_price"].mode()

        if len(mode_price) > 0:
            mode_price = mode_price.iloc[0]
        else:
            mode_price = None

        median_price = round(
            group["monthly_price"].median()
        )

        room_summary = {
            "Room Type": room_type,

            "Units Found": len(group),

            "Average Price (RM)": round(
                group["monthly_price"].mean()
            ),

            "Median Price (RM)": median_price,

            "Mode Price (RM)": mode_price,

            # Fair price = median
            "Fair Price (RM)": median_price,

            "Average Size (sqft)": round(
                group["sqft"].mean()
            )
        }

        summary.append(
            room_summary
        )

    summary_df = pd.DataFrame(summary)

    summary_df = summary_df.sort_values(
        by="Room Type",
        key=lambda col: col.map(room_type_order)
    )

    summary_df = summary_df.reset_index(
        drop=True
    )

    return summary_df


if __name__ == "__main__":

    df = load_data(
        "data/mont_kiara.csv"
    )

    summary = calculate_summary(
        df
    )

    print("\n=== PRICE SUMMARY ===\n")

    print(summary)