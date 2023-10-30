# app.py
import os
from flask import Flask, render_template, request, send_from_directory
from tasks import process_video
import time

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_VIDEO'] = ''


@app.route('/')
def index():
    return render_template('/index.html')

@app.route('/uploads', methods=['POST'])
def upload():
    # Получите файл из запроса и сохраните его на сервере
    video = request.files['video']
    video.save(os.path.join(app.config['UPLOAD_FOLDER'], 'uploaded_video.mp4'))

    # Запустите асинхронную задачу для обработки видео
    process_video.delay(os.path.join(app.config['UPLOAD_FOLDER'], 'uploaded_video.mp4'))

    return render_template('/processing.html')

@app.route('/check_status')
def check_status():
    # Проверьте статус обработки видео и верните результат пользователю
    # Можно использовать какую-то базу данных для отслеживания состояния обработки
    # Верните оставшееся время или другую информацию о состоянии обработки
    if app.config['PROCESSED_VIDEO']:
        return 'Video processing complete!'
    else:
        return 'Processing video. Please wait...'

@app.route('/download_processed_video')
def download_processed_video():
    # Верните обработанное видео пользователю для скачивания
    return send_from_directory(app.config['UPLOAD_FOLDER'], 'uploaded_video.mp4', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)