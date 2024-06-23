from model import *
from flask import Flask, request, redirect, url_for, render_template, send_file
import os
import logging
import base64
import pandas as pd
import io
from jinja2 import Environment

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls'}

logging.basicConfig(level=logging.DEBUG)

# Add zip to Jinja2 environment
app.jinja_env.globals.update(zip=zip)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config[
        'ALLOWED_EXTENSIONS']


def summary(info):
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

        output.write(
            f"Session {int(session)} took {time_str}, with an average of "
            f"{mean_movements:.0f} movements per 5 minutes, resulting in an estimated "
            f"occupancy of {people} people\n\n"
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

        if no_date:
            img_data_list = []
            summary_list = []

            dates = data['Date'].dt.date.unique()
            for date in dates:
                img, session_stats = process_file(data, str(date))
                img_base64 = base64.b64encode(img).decode('utf-8')
                img_data_list.append(img_base64)
                summary_list.append(summary(session_stats))

            return render_template('results.html', img_data_list=img_data_list,
                                   summary_list=summary_list)
        elif specific_date:
            # Process the file and get the images of the graphs
            img, session_stats = process_file(data, specific_date)
            logging.debug('File processed successfully')

            # Encode the images to base64 to embed them in HTML
            img_base64 = base64.b64encode(img).decode('utf-8')

            # Generate the summary text
            summary_text = summary(session_stats)

            # Return the template with the images and the message
            return render_template('result.html', img=img_base64,
                                   message='Done!',
                                   specific_date=specific_date,
                                   summary_text=summary_text)
    return redirect(request.url)

def process_file(data, specific_date):
    logging.debug(f'Processing data for date: {specific_date}')

    data = data[data['Date'].dt.date == pd.to_datetime(specific_date).date()]

    logging.debug('Data filtered by specific date')

    threshold = 0
    consecutive_points = 1
    img, session_stats = predict_occupancy_session(data, specific_date)
    logging.debug('Valid peaks shown')
    return img, session_stats


if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
