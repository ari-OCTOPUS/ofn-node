FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# داده و فایل‌های وضعیت در مسیرهای پایدار (volume)
ENV LANGAR_DB=/app/data/langar.db
ENV LANGAR_STATE=/app/data/langar_state.pickle
CMD ["python", "main.py"]
