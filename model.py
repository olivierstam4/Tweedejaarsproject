import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np
from io import BytesIO
from IPython.display import Image, display
import matplotlib.dates as mdates
import base64
def preprocess(file_path):
    data = pd.read_excel(file_path, skiprows=2)
    data = data[['Date', 'Count']]
    data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
    data.dropna(subset=['Date'], inplace=True)
    data = data[data['Date'].dt.hour.between(8, 24)]
    return data

def summary(info):
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

        print(
            f"Session {int(session)} took {time_str}, with an average of "
            f"{mean_movements:.0f} movements per 5 minutes, resulting in an estimated "
            f"occupancy of {people} people\n")

def predict_occupancy_session(data, date):
    data['Date'] = pd.to_datetime(data['Date'])
    data = data.sort_values('Date')

    session_id = 0
    in_session = False
    session_labels = []

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
        q1 = counts.quantile(0.25)
        q3 = counts.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        filtered_counts = counts[
            (counts >= lower_bound) & (counts <= upper_bound)]
        return filtered_counts.mean()

    def determine_people(avg_count):
        people = avg_count / 62.5
        return round(people)

    def split_sessions_based_on_changes(data, window=5, change_threshold=50):
        new_session_id = max(data['Session']) + 1
        for session in data['Session'].unique():
            if session == 0:
                continue
            session_data = data[data['Session'] == session]
            if len(session_data) < 1:
                continue

            rolling_avg = session_data['Count'].rolling(window=window,
                                                        min_periods=2).mean()
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
            people = determine_people(avg_count)
            if people == 0:
                people = '1'
            elif people > 4:
                people = '4+'
            else:
                people = str(int(people))
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

    # Plot data for a specific day (e.g., '2024-06-12')
    img = plot_day(data, date)

    def calculate_session_stats(data):
        stats = []
        for index, session in enumerate(data['Session'].unique()):
            if session == 0:
                continue
            session_data = data[data['Session'] == session]
            avg_count = remove_outliers_and_calculate_avg(session_data['Count'])
            people = determine_people(avg_count)
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

