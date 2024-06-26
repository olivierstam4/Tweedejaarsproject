import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np
from io import BytesIO
from IPython.display import Image, display
import matplotlib.dates as mdates
import base64
import joblib


def preprocess(file_path: str):
    """"
    input: raw excel file path
    output: cleaned pandas DataFrame with Date and Count columns

    Deals with the raw excel files, Skips first two white lines and only
    uses the Date and Count, will also drop NaN values and closed hours.
    """
    data = pd.read_excel(file_path, skiprows=2)
    data = data[['Date', 'Count']]
    data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
    data.dropna(subset=['Date'], inplace=True)
    data = data[data['Date'].dt.hour.between(8, 24)]
    return data


def summary(info, occupancy_mode):
    """
    input: a dictionary of info gotten from the predict_occupancy_session and
    the desired occupancy mode (grouped or exact)
    output: prints a summary of the sessions
    """
    for index, row in info.iterrows():
        session = row['Session']
        total_time = row['Num_Points'] * 5
        hours = total_time // 60
        minutes = total_time % 60
        mean_movements = row['Mean']
        people = row['People']

        if hours > 0:
            time_str = f"{int(hours)} hour(s) and {int(minutes)} minute(s)"
        else:
            time_str = f"{int(minutes)} minute(s)"

        if occupancy_mode == 'Exact':
            if people == '1':
                occupancy_info = f"resulting in an estimated occupancy of {people} person"
            else:
                occupancy_info = f"resulting in an estimated occupancy of {people} people"
        else:
            if mean_movements < 153:
                occupancy_info = 'with an estimated occupancy of 1-2 people'
            else:
                occupancy_info = 'with an estimated occupancy of 3+ people'

        print(f"Session {int(session)} took {time_str}, with an average of "
              f"{mean_movements:.0f} movements per 5 minutes,{occupancy_info}\n\n"
              )


# load the classification
neigh = joblib.load('nearest_neighbors_model.pkl')
occupancies = joblib.load('occupancies.pkl')


def find_nearest_occupancy(count):
    """
    input: average count of the session
    output: the nearest occupancy class.

    Handeling the estimation.
    """
    distance, index = neigh.kneighbors(np.array([[count]]),
                                       return_distance=True)
    nearest_occupancy = occupancies[index[0][0]]
    return nearest_occupancy


def predict_occupancy_session(data, date, occupancy_mode='Exact'):
    """"
    This function handles the session classification and extracting information
    """
    data['Date'] = pd.to_datetime(data['Date'])
    data = data.sort_values('Date')

    # start values
    session_id = 0
    in_session = False
    session_labels = []

    # loop through the data
    for i in range(len(data)):
        if data['Count'].iloc[i] > 0 and not in_session:
            in_session = True
            session_id += 1

        if in_session:
            session_labels.append(session_id)
        else:
            session_labels.append(0)

        if in_session and data['Count'].iloc[i] < 5:
            in_session = False

    data['Session'] = session_labels

    session_counts = data['Session'].value_counts()
    valid_sessions = session_counts[session_counts >= 6].index
    data.loc[~data['Session'].isin(valid_sessions), 'Session'] = 0

    def remove_outliers_and_calculate_avg(counts):
        """"
        Handling the outliers with the interquartile range
        """
        q1 = counts.quantile(0.25)
        q3 = counts.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        filtered_counts = counts[
            (counts >= lower_bound) & (counts <= upper_bound)]
        return filtered_counts.mean()

    def split_sessions_based_on_changes(data, window=25, change_threshold=10):
        """
        Rolling average handling
        """
        new_session_id = max(data['Session']) + 1
        for session in data['Session'].unique():
            if session == 0:
                continue
            session_data = data[data['Session'] == session]
            if len(session_data) < 1:
                continue

            rolling_avg = session_data['Count'].rolling(window=window,
                                                        min_periods=20).mean()
            session_data = session_data.copy()
            session_data['Rolling_Avg'] = rolling_avg

            prev_avg = rolling_avg.iloc[0]
            for i in range(1, len(session_data)):
                current_avg = rolling_avg.iloc[i]
                if abs(current_avg - prev_avg) > change_threshold:
                    data.loc[session_data.index[i:], 'Session'] = new_session_id
                    new_session_id += 1
                    break
                prev_avg = current_avg

    split_sessions_based_on_changes(data)
    session_counts = data['Session'].value_counts()
    valid_sessions = session_counts[session_counts >= 6].index
    data.loc[~data['Session'].isin(valid_sessions), 'Session'] = 0

    def plot_day(data, date):
        """
        plotting the data
        """
        date = str(date).split()[0]
        start_date = datetime.strptime(date, '%Y-%m-%d')
        end_date = start_date + timedelta(days=1)
        day_data = data[
            (data['Date'] >= start_date) & (data['Date'] < end_date)]

        plt.figure(figsize=(15, 7))
        plt.plot(np.array(day_data['Date']), np.array(day_data['Count']),
                 label='Noise', color='black', linewidth=1, alpha=0.5)

        unique_sessions = day_data['Session'].unique()

        for index, session in enumerate(unique_sessions[1:]):
            session_data = day_data[day_data['Session'] == session]
            volume = len(session_data)
            avg_count = remove_outliers_and_calculate_avg(session_data['Count'])
            people = find_nearest_occupancy(avg_count)
            if occupancy_mode == 'Exact':
                if people == 0:
                    people = '1'
                elif people > 4:
                    people = '4+'
                else:
                    people = str(int(people))
            else:
                if avg_count < 153:
                    people = '1-2'
                else:
                    people = '3+'
            if people == '1':
                label = f'Session {index + 1}: estimated {people} person'
            else:
                label = f'Session {index + 1}: estimated {people} people'

            color = None

            plt.plot(np.array(session_data['Date']),
                     np.array(session_data['Count']), label=label, linewidth=2,
                     alpha=0.5)

        plt.title(
            f'Occupancy for the sessions on {date}')
        plt.xlabel('Time of day')
        plt.ylabel('Movement Count')
        plt.legend()
        ax = plt.gca()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.xticks(rotation=45)
        img_buf = BytesIO()
        plt.savefig(img_buf, format='png')
        plt.close()
        img_buf.seek(0)

        return img_buf.getvalue()

    img = plot_day(data, date)

    def calculate_session_stats(data):
        stats = []
        for index, session in enumerate(data['Session'].unique()):
            if session == 0:
                continue
            session_data = data[data['Session'] == session]
            avg_count = remove_outliers_and_calculate_avg(session_data['Count'])
            people = find_nearest_occupancy(avg_count)
            if people == 0:
                people = '1'
            elif people > 4:
                people = '4+'
            else:
                people = str(int(people))
            total = session_data['Count'].sum()
            mean = session_data['Count'].mean()
            std = session_data['Count'].std()
            num_points = len(session_data)
            # you can append info very easily here if you wish. This is just a
            # start example.
            stats.append({
                'Session': index,
                'Total': total,
                'Mean': mean,
                'Std': std,
                'Num_Points': num_points,
                'People': people,
            })
        return stats

    session_stats = calculate_session_stats(data)
    session_stats_df = pd.DataFrame(session_stats)
    return img, session_stats_df


def unique_days(data):
    """
    prints all the unique days of a dataframe
    """
    unique_dates = data['Date'].dt.date.unique()
    for date in unique_dates:
        print(date)
