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
    if sensor_type == 'Locus':
        file_path = f'Data_clean/{sensor_type}_sensors/{sensor_number}_processed.xlsx'
    elif sensor_type == 'Alta':
        file_path = f'Data_clean/{sensor_type}_sensors/{sensor_number}_combined.xlsx'
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Sensor_type moet met een hoofdletter beginnen!.\n"
            f"Voor sensor_number, kijk naar hoe de file heet en gebruik daarvan dus de eerste 4 karakters'\n"
            f"Examples: 'Data_clean/Locus_sensors/B.253_processed.xlsx', 'Data_clean/Alta_sensors/B.254_processed.xlsx'"
        )
    file = pd.read_excel(file_path)
    file.dropna(subset=['Count'], inplace=True)
    return file

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

def surrounded_by_low_counts(index, series, threshold=10, num_points=3):
    precede = series[max(0, index - num_points):index]
    return all(precede <= threshold) if len(precede) == num_points else False

def peaks_for_specific_timeframe(data, start_time, end_time):
    """
    Time and date formatted as yyyy-mm-dd hh-mm-ss
    """

    import matplotlib.pyplot as plt
    mask = (data['Date'] >= start_time) & (data['Date'] <= end_time)
    filtered_data = data.loc[mask]

    plt.figure(figsize=(10, 6))
    plt.plot(filtered_data['Date'], filtered_data['Count'], marker='o')
    plt.xlabel('Date')
    plt.ylabel('Count')
    plt.title('Count Data between {} and {}'.format(start_time, end_time))
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def show_valid_peaks(data, day, threshold, consecutive_points):
    """
    day is formatted as yyyy-mm-dd 
    threshold is the minimum value you want to classify as 'real' movement
    consecutive_points is the amount of consecutive points under the treshold you need
    """
    import matplotlib.pyplot as plt
    from scipy.signal import find_peaks

    mask = data['Date'].dt.strftime('%Y-%m-%d') == day
    filtered_data = data.loc[mask].reset_index(drop=True)

    peaks, _ = find_peaks(filtered_data['Count'], height=filtered_data['Count'].mean())

    valid_peaks = [index for index in peaks if surrounded_by_low_counts(index, filtered_data['Count'], threshold, consecutive_points)]

    plt.figure(figsize=(10, 6))
    plt.plot(filtered_data['Date'], filtered_data['Count'], marker='o', label='Counts')
    plt.plot(filtered_data['Date'].iloc[valid_peaks], filtered_data['Count'].iloc[valid_peaks], 'rx', label='Valid Peaks')
    plt.xlabel('Date')
    plt.ylabel('Count')
    plt.title(f'Count Data with Valid Peaks of {day}')
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    filtered_data['Session'] = (filtered_data.index.isin(valid_peaks)).cumsum()

    plt.figure(figsize=(10, 6))
    for session, group in filtered_data.groupby('Session'):
        plt.plot(group['Date'], group['Count'], marker='o', label=f'Session {session}')

    plt.xlabel('Date')
    plt.ylabel('Count')
    plt.title(f'Grouped Sessions of {day}')
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()