# app.py
import os
import fitz
from flask import Flask, render_template, request, send_from_directory, jsonify
from tasks import process_video
import time
import uuid
import redis
import json
from werkzeug.utils import secure_filename
import requests


# Настройка подключения к Redis
redis_host = "localhost"  # или адрес удаленного сервера Redis
redis_port = 6379  # порт по умолчанию для Redis
redis_password = ""  # пароль, если он у вас есть
r = redis.StrictRedis(host=redis_host, port=redis_port, password=redis_password, decode_responses=True)

app = Flask(__name__)


UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_VIDEO'] = ''
app.config['UPLOAD_FOLDER'] = 'uploads/'  # Папка для сохранения файлов
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'mp4', 'mp3', 'wav', 'jpg', 'jpeg', 'png', 'gif'}  # Разрешенные расширения
PDFS_DIR = 'saved_pdf'


def some_llm_function(question, chat_history, file_id):
    return


def save_message_to_chat_history(user_id, file_id, message):
    chat_id = f"chat:{user_id}:{file_id}"  # Создаем уникальный ключ для истории чата
    r.rpush(chat_id, json.dumps(message))  # Добавляем сообщение в список Redis


def get_chat_history(user_id, file_id):
    chat_id = f"chat_{user_id}_{file_id}"  # Уникальный ID для чата
    if r.exists(chat_id):
        messages = r.lrange(chat_id, 0, -1)  # Получаем все сообщения из списка Redis
        return [json.loads(message) for message in messages]  # Десериализуем каждое сообщение
    else:
        return None


@app.route('/get-chat-history', methods=['GET'])
def get_chat():
    user_id = request.args.get('user_id')
    file_id = request.args.get('file_id')
    chat_history = get_chat_history(user_id, file_id)
    return jsonify(chat_history), 200


@app.route('/')
def index():
    return render_template('/index.html')


# Функция для проверки разрешенного расширения файла
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/upload', methods=['POST'])
def upload_file():
    # Проверяем, есть ли файл в запросе
    if 'file' not in request.files:
        return jsonify(error="No file part"), 400
    file = request.files['file']
    # Если пользователь не выбрал файл, браузер тоже может
    # отправить пустую часть без имени файла
    if file.filename == '':
        return jsonify(error="No selected file"), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)  # Убедитесь, что используете secure_filename
        # Генерируем уникальное имя файла с помощью UUID для предотвращения конфликтов имен
        ext = filename.rsplit('.', 1)[1].lower()  # Получаем расширение файла
        unique_file_id = uuid.uuid4()
        unique_filename = f"{unique_file_id}.{ext}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        return jsonify(message="File uploaded successfully", filename=unique_file_id), 200

    return jsonify(error="File type not allowed"), 400


@app.route('/upload_via_link', methods=['POST'])
def upload_via_link():
    # Проверяем, есть ли файл в запросе
    url = request.json.get('url')  # Получаем URL из тела запроса
    if not url:
        return jsonify(error="No URL provided"), 400

    # Отправляем HTTP запрос на получение файла
    try:
        response = requests.get(url)
        response.raise_for_status()  # Проверяем, что запрос выполнен успешно
    except requests.HTTPError as http_err:
        return jsonify(error=f"HTTP error occurred: {http_err}"), 400
    except Exception as err:
        return jsonify(error=f"An error occurred: {err}"), 400

        # Получаем имя файла из URL
    filename = url.rsplit('/', 1)[-1]
    # Генерируем уникальное имя файла, сохраняя исходное расширение
    extension = filename.rsplit('.', 1)[-1] if '.' in filename else ''
    unique_file_id = uuid.uuid4()
    unique_filename = f"{unique_file_id}.{extension}" if extension else str(unique_file_id)

    # Сохраняем файл
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    with open(file_path, 'wb') as f:
        f.write(response.content)

    return jsonify(message="File downloaded and saved successfully", filename=unique_file_id), 200



@app.route('/ask-question', methods=['POST'])
def ask_question():
    user_id = request.args.get('user_id')
    file_id = request.args.get('file_id')
    question = request.args.get('question')


    if get_chat_history(user_id, file_id) is None:

        filepath = os.path.join(PDFS_DIR, str(file_id) + '.pdf')
        if not os.path.exists(filepath):
            return jsonify({"error": "File not found"}), 404

        # Открываем указанный PDF-файл
        doc = fitz.open(filepath)
        # Читаем текст из PDF
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        save_message_to_chat_history(user_id, file_id, {"role": "system", "content": "Answer questions based on this document: \n" + text}) #TODO: refine prompt

    # Используем LLM для ответа на вопрос, основываясь на тексте
    chat_history = get_chat_history(user_id, file_id)
    answer = some_llm_function(question, chat_history, file_id)  # Замените на вызов вашей LLM функции
    save_message_to_chat_history(user_id, file_id, {"role": "user", "content": question})
    save_message_to_chat_history(user_id, file_id, {"role": "assistant", "content": answer})
    return jsonify(answer=answer)


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
    # Создаем папку для загрузок, если она не существует
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
