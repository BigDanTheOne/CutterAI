# app.py
import os
import fitz
from flask import Flask, render_template, request, send_from_directory, jsonify, make_response, session, Response
import uuid
import redis
import json
from werkzeug.utils import secure_filename
import requests
import time
from utiles.summary import text_to_summary_in_parts, ask_question_gpt
from youtube_transcript_api import YouTubeTranscriptApi


# Настройка подключения к Redis
redis_host = "localhost"  # или адрес удаленного сервера Redis
redis_port = 6379  # порт по умолчанию для Redis
redis_password = ""  # пароль, если он у вас есть
r = redis.StrictRedis(host=redis_host, port=redis_port, password=redis_password, decode_responses=True)

app = Flask(__name__)


app.config['PROCESSED_VIDEO'] = ''
app.config['UPLOAD_FOLDER'] = 'uploads/'  # Папка для сохранения файлов
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'mp4', 'mp3', 'wav', 'jpg', 'jpeg', 'png', 'gif'}  # Разрешенные расширения
PDFS_DIR = 'saved_pdf'


def save_message_to_chat_history(user_id, file_id, message):
    chat_id = f"chat:{user_id}:{file_id}"  # Создаем уникальный ключ для истории чата
    r.rpush(chat_id, json.dumps(message))  # Добавляем сообщение в список Redis


def get_chat_history(user_id, file_id):
    chat_id = f"chat:{user_id}:{file_id}"  # Уникальный ID для чата
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
    user_id = request.cookies.get('user_id')
    if not user_id:
        user_id = str(uuid.uuid4())
        response = make_response(f"Your user ID is {user_id}.")
        response.set_cookie('user_id', user_id)
        return response
    else:
        return f"Your user ID is {user_id}."



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

def get_youtube_subtitles(link):
    VIDEO_ID = link.split("watch?v=")[1].split('&')[0]
    return YouTubeTranscriptApi.get_transcript(VIDEO_ID)


@app.route('/upload-youtube', methods=['POST'])
def upload_youtube():
    # Проверяем, есть ли файл в запросе
    url = request.json.get('url')
    subs = get_youtube_subtitles(url)
    combined_string = ' '.join([f"{d['text']} ({d['start']} - {d['start'] + d['duration']})" for d in subs])
    unique_file_id = uuid.uuid4()
    unique_filename = f"{unique_file_id}.txt"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    with open(file_path, 'w') as f:
        f.write(combined_string)
    return jsonify(message="File uploaded successfully", filename=unique_file_id), 200


@app.route('/ask-question', methods=['GET'])
def ask_question():
    user_id = request.args.get('user_id')
    file_id = request.args.get('file_id')
    question = request.args.get('question')


    if get_chat_history(user_id, file_id) is None:
        text = ""
        if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], str(file_id) + '.pdf')):
            # Открываем указанный PDF-файл
            doc = fitz.open(app.config['UPLOAD_FOLDER'], str(file_id) + '.pdf')
            # Читаем текст из PDF
            for page in doc:
                text += page.get_text()
            doc.close()
            save_message_to_chat_history(user_id, file_id, {"role": "system", "content": "Answer questions based on this document: \n" + text})
        elif os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], str(file_id) + '.txt')):
            with open(os.path.join(app.  config['UPLOAD_FOLDER'], str(file_id) + '.txt'), 'r') as file:
                text += file.read()
            save_message_to_chat_history(user_id, file_id, {"role": "system", "content": "Answer questions based on this document: \n" + text})

        else:
            return jsonify({"error": "File not found"}), 404

    # Используем LLM для ответа на вопрос, основываясь на тексте
    chat_history = get_chat_history(user_id, file_id)
    save_message_to_chat_history(user_id, file_id, {"role": "user", "content": question})
    chat_history = get_chat_history(user_id, file_id)


    def generate():  # Создаем генератор для потоковой передачи
        collected_messages = []
        for chunk in ask_question_gpt(chat_history):
            chunk_message = chunk.choices[0].delta.content # extract the message
            if chunk_message:
                collected_messages.append(chunk_message)  # save the message
            elif chunk_message is None and len(full_reply_content) != 0:
                save_message_to_chat_history(user_id, file_id, {"role": "assistant",
                        "content": '' if len(collected_messages) == 0 else ''.join([m for m in collected_messages])})
            full_reply_content = '' if len(collected_messages) == 0 else ''.join([m for m in collected_messages])
            yield full_reply_content

    return Response(generate(), content_type='text/plain')  # Используем Response для стриминга ответа




@app.route('/summarize', methods=['GET'])
def summarize():
    file_id = request.args.get('file_id')

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], str(file_id) + '.pdf')
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404

    # Открываем указанный PDF-файл
    doc = fitz.open(filepath)
    # Читаем текст из PDF
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()

    def generate():  # Создаем генератор для потоковой передачи
        collected_messages = []
        for chunk in text_to_summary_in_parts(text):
            chunk_message = chunk.choices[0].delta.content # extract the message
            if chunk_message:
                collected_messages.append(chunk_message)  # save the message
            full_reply_content = '' if len(collected_messages) == 0 else ''.join([m for m in collected_messages])
            yield full_reply_content

    return Response(generate(), content_type='text/plain')  # Используем Response для стриминга ответа



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
