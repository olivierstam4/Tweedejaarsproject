def remove_zeros(df):
    """
    Function for removing all zero values
    """
    df = df[df['Count'] > 0]
    return df

def remove_before(df, min_number):
    """
    Only keeps count values higher than min_number
    Can be used instead of remove_zeros
    """
    df = df[df['Count'] > min_number]
    return df

def import_file(sensor_type, sensor_number):
    """
    For Locus: sensor_type = 'Locus'
    For Alta: sensor_type = 'Alta'

    For sensor_number, use the one of the file, (B.253, etc)
    """
    import pandas as pd # type: ignore
    import os
    file_path = f'Data_clean/{sensor_type}_sensors/{sensor_number}_processed.xlsx'
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Sensor_type moet met een hoofdletter beginnen!.\n"
            f"Voor sensor_number, kijk naar hoe de file heet en gebruik daarvan dus de eerste 4 karakters'\n"
            f"Examples: 'Data_clean/Locus_sensors/B.253_processed.xlsx', 'Data_clean/Alta_sensors/B.254_processed.xlsx'"
        )
    
    return pd.read_excel(file_path)

def make_bins(data_file, num_bins, all_bins=False):
    """
    This function can be used to bin the data of preprocessed files

    You first need to make your data a variable by using a combination of other functions
    
    Set all_bins to True if you want to have a seperate bin for every int in the data
    """
    import matplotlib.pyplot as plt
    # Extract the 'Count' column
    counts = data_file['Count']

    if all_bins:
        num_bins = int(counts.max())
    else:
        num_bins = num_bins

    # Create the histograms
    plt.hist(counts, bins=num_bins, edgecolor='black')

    # Adding labels and title
    plt.xlabel('Count')
    plt.ylabel('Frequency')
    plt.title('Histogram of Counts')

    # Display the histogram
    plt.show()

def make_equal_bins(data_file, num_bins=4):
    """
    This function can be used to bin the data of preprocessed files

    You first need to make your data a variable by using a combination of other functions
    """
    import matplotlib.pyplot as plt
    import numpy as np
    # Extract the 'Count' column
    counts = data_file['Count']

    quantiles = np.linspace(0, 1, num_bins + 1)
    bin_edges = np.quantile(counts, quantiles)

    # Create the histograms
    plt.hist(counts, bins=bin_edges, edgecolor='black')

    # Adding labels and title
    plt.xlabel('Count')
    plt.ylabel('Frequency')
    plt.title('Histogram of Counts')

    # Display the histogram
    plt.show()