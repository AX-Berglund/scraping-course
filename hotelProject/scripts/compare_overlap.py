import pandas as pd
import argparse


def load_data(file1, file2):
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)
    return df1, df2

def process_dataframe(df):
    """
    Preprocess the 'hotel_name' column in the dataframe to standardize names by:
    - Converting to lowercase
    - Replacing accented characters with unaccented equivalents
    - Removing spaces, special characters, and digits
    - Removing common keywords like 'hotel'

    Parameters:
        df (pd.DataFrame): Dataframe with a 'hotel_name' column to preprocess.

    Returns:
        pd.DataFrame: Dataframe with the preprocessed 'hotel_name' column.
    """
    df['hotel_name_original'] = df['hotel_name']
    df['hotel_name'] = (
        df['hotel_name']
        .str.lower()
        .str.replace('ô', 'o')
        .str.replace('é', 'e')
        .str.replace('è', 'e')
        .str.replace('hotel', '')
        .str.replace('1', '')
        .str.replace('2', '')
        .str.replace('3', '')
        .str.replace('4', '')
        .str.replace('5', '')
        .str.replace('6', '')
        .str.replace('7', '')
        .str.replace('8', '')
        .str.replace('9', '')
        .str.replace('[^a-zA-Z0-9]', '', regex=True)  # Remove all special characters
    )

    # round dates to seconds to avoid floating point errors
    df['start_date'] = pd.to_datetime(df['start_date']).dt.round('s')
    df['end_date'] = pd.to_datetime(df['end_date']).dt.round('s')
    return df

def check_overlap_with_time(df1, df2):
    """
    Adds a column 'overlap' to df1 indicating whether its rows overlap with any row in df2
    where the hotel names match.

    Parameters:
        df1 (pd.DataFrame): First dataframe with 'start_date', 'end_date', and 'hotel_name' columns.
        df2 (pd.DataFrame): Second dataframe with 'start_date', 'end_date', and 'hotel_name' columns.

    Returns:
        pd.DataFrame: Updated df1 with a new boolean column 'overlap'.
    """
    def overlaps(row1, row2):
        return not (row1['end_date'] < row2['start_date'] or row1['start_date'] > row2['end_date'])

    overlaps_list = []
    for _, row1 in df1.iterrows():
        is_overlapping = any(
            row1['hotel_name'] == row2['hotel_name'] and overlaps(row1, row2)
            for _, row2 in df2.iterrows()
        )
        overlaps_list.append(is_overlapping)

    df1['overlap_name_and_time'] = overlaps_list
    return df1


def print_names_of_hotels_that_overlap(df):
    """
    Print the names of hotels that overlap between the two datasets.

    Parameters:
        df (pd.DataFrame): Dataframe with a 'hotel_name' column and an 'overlap' column.
    """    
    overlapping_hotels = df[df['overlap_name_and_time'] == True]['hotel_name_original'].unique()
    print("These hotels overlap:")
    for hotel in overlapping_hotels:
        print(hotel)

def main():
    parser = argparse.ArgumentParser(description='Compare overlap between two datasets')
    parser.add_argument('file1', type=str, help='Path to the first file')
    parser.add_argument('file2', type=str, help='Path to the second file')
    args = parser.parse_args()


    df1, df2 = load_data(args.file1, args.file2)

    df1 = process_dataframe(df1)
    df2 = process_dataframe(df2)

    df1_with_overlap = check_overlap_with_time(df1, df2)

    print_names_of_hotels_that_overlap(df1_with_overlap)

if __name__ == "__main__":
    main()