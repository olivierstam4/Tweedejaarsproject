from flask import Flask, request, redirect, url_for, render_template, send_file, Response
import os
from model import *

import logging
import openpyxl
import io
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np
from io import BytesIO
import base64
import joblib


app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls'}

logging.basicConfig(level=logging.DEBUG)
app.jinja_env.globals.update(zip=zip)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def summary(info, occupancy_mode):
    output = io.StringIO()
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
            occupancy_info = f"resulting in an estimated occupancy of {people} people"
        else:
            if mean_movements < 153:
                occupancy_info = 'with an estimated occupancy of 1-2 people'
            else:
                occupancy_info = 'with an estimated occupancy of 3+ people'

        output.write(
            f"Session {int(session)} took {time_str}, with an average of "
            f"{mean_movements:.0f} movements per 5 minutes,{occupancy_info}\n\n"
        )
    return output.getvalue()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    specific_date = request.form.get('date')
    no_date = 'no_date' in request.form
    occupancy_mode = request.form.get('occupancy_mode')
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        logging.debug(f'File saved to {file_path}')

        data = pd.read_excel(file_path, skiprows=2)
        data = data[['Date', 'Count']]
        data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
        data.dropna(subset=['Date'], inplace=True)
        data = data[data['Date'].dt.hour.between(8, 24)]

        csv_file_name = f"{os.path.splitext(filename)[0]}_info_csv.csv"
        csv_file_path = os.path.join(app.config['UPLOAD_FOLDER'], csv_file_name)

        if no_date:
            img_data_list = []
            summary_list = []
            all_session_stats = []

            dates = data['Date'].dt.date.unique()
            all_data = []

            for date in dates:
                img, session_stats = process_file(data, str(date),
                                                  occupancy_mode)
                img_base64 = base64.b64encode(img).decode('utf-8')
                img_data_list.append(img_base64)
                summary_list.append(summary(session_stats, occupancy_mode))

                df = pd.DataFrame(session_stats)
                df.insert(0, 'Date', date)

                all_data.append(df)
                all_session_stats.extend(session_stats)

            csv_data = pd.concat(all_data, ignore_index=True)

            csv_data.to_csv(csv_file_path, index=False)

            return render_template('results.html', img_data_list=img_data_list,
                                   summary_list=summary_list,
                                   csv_file_name=csv_file_name)
        elif specific_date:
            img, session_stats = process_file(data, specific_date, occupancy_mode)
            logging.debug('File processed successfully')

            img_base64 = base64.b64encode(img).decode('utf-8')

            summary_text = summary(session_stats, occupancy_mode)

            csv_data = pd.DataFrame(session_stats)
            csv_data.to_csv(csv_file_path, index=False)

            return render_template('result.html', img=img_base64,
                                   message='Done!',
                                   specific_date=specific_date,
                                   summary_text=summary_text,
                                   csv_file_name=csv_file_name)
    return redirect(request.url)

def process_file(data, specific_date, occupancy_mode):
    logging.debug(f'Processing data for date: {specific_date}')

    data = data[data['Date'].dt.date == pd.to_datetime(specific_date).date()]

    logging.debug('Data filtered by specific date')

    threshold = 0
    consecutive_points = 1
    img, session_stats = predict_occupancy_session(data, specific_date, occupancy_mode)
    logging.debug('Valid peaks shown')
    return img, session_stats

@app.route('/download_csv/<filename>')
def download_csv(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename),
                     as_attachment=True)

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
