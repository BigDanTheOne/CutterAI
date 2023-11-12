FROM python
WORKDIR /app
COPY . /app
RUN python -m pip install -r requirements.txt

# Сделайте порт 5000 доступным для мира вне контейнера
EXPOSE 5000

# Определите переменные среды
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Запустите приложение при запуске контейнера
CMD ["flask", "run"]
