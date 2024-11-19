# Используем официальный образ Python 3.12
FROM python:3.12-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Обновляем список пакетов и устанавливаем необходимые зависимости
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    unixodbc \
    unixodbc-dev \
    curl \
    gnupg && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 && \
    rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей в контейнер
COPY ./requirements.txt .
COPY ./requirements-dev.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements-dev.txt


# Копируем все файлы проекта в контейнер
COPY app/ .

#CMD [ "find", "." ]
ENTRYPOINT ["python"]
CMD ["api.py"]