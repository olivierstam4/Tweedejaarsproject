from new_useful_functions import import_file, remove_before, remove_zeros, make_bins, make_equal_bins, peaks_for_specific_timeframe, show_valid_peaks, make_sessions, calculate_session_averages, add_session_averages, surrounded_by_low_counts
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
from flask import Flask, request, redirect, url_for, render_template, send_file
import os
import pandas as pd
import logging
from io import BytesIO
import base64
from datetime import datetime
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls'}

logging.basicConfig(level=logging.DEBUG)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files or 'date' not in request.form:
        return redirect(request.url)
    file = request.files['file']
    specific_date = request.form['date']
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename) and specific_date:
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        logging.debug(f'File saved to {file_path}')
        # Process the file and get the images of the graphs
        img1, img2 = process_file(file_path, specific_date)
        logging.debug('File processed successfully')
        # Encode the images to base64 to embed them in HTML
        img1_base64 = base64.b64encode(img1.getvalue()).decode('utf-8')
        img2_base64 = base64.b64encode(img2.getvalue()).decode('utf-8')
        # Return the template with the images and the message
        return render_template('result.html', img1=img1_base64, img2=img2_base64, message='Done!', specific_date=specific_date)
    return redirect(request.url)


def show_valid_peaks(data, day, threshold, consecutive_points, offset=0):
    """
    day is formatted as yyyy-mm-dd
    threshold is the minimum value you want to classify as 'real' movement
    consecutive_points is the amount of consecutive points under the treshold you need
    """
    import matplotlib.pyplot as plt
    filtered_data, valid_peaks, session_stats = make_sessions(data, day, threshold,
                                               consecutive_points, offset)
    plt.figure(figsize=(10, 6))
    plt.plot(filtered_data['Date'], filtered_data['Count'], marker='o',
             label='Counts')
    plt.plot(filtered_data['Date'].iloc[valid_peaks],
             filtered_data['Count'].iloc[valid_peaks], 'rx',
             label='Valid Peaks')
    plt.xlabel('Date')
    plt.ylabel('Count')
    plt.title(f'Count Data with Valid Peaks of {day}')
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    img1 = BytesIO()
    plt.savefig(img1, format='png')
    img1.seek(0)
    plt.close()

    # Second plot
    filtered_data['Session'] = (filtered_data.index.isin(valid_peaks)).cumsum()
    threshold_line = [threshold] * len(filtered_data['Date'])

    plt.figure(figsize=(20, 6))
    for session, group in filtered_data.groupby('Session'):
        plt.plot(group['Date'], group['Count'], marker='o',
                 label=f'Session {session}')
    plt.plot(filtered_data['Date'], threshold_line, color='red',
             label=f'Threshold')

    plt.xlabel('Date')
    plt.ylabel('Count')
    plt.title(f'Grouped Sessions of {day}')
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    img2 = BytesIO()
    plt.savefig(img2, format='png')
    img2.seek(0)
    plt.close()

    return img1, img2, session_stats
def process_file(file_path, specific_date):
    logging.debug(f'Reading the Excel file from {file_path}')

    data = pd.read_excel(file_path, skiprows=2)
    data = data[['Date', 'Count']]
    data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
    data.dropna(subset=['Date'], inplace=True)
    data = data[data['Date'].dt.hour.between(8, 24)]

    logging.debug('Data filtered by hours')

    threshold = 0
    consecutive_points = 1
    img1, img2, session_stats  = show_valid_peaks(data, specific_date, threshold, consecutive_points)
    logging.debug('Valid peaks shown')
    return img1, img2

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)