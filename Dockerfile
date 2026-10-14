FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY . .

RUN python backend/train_model.py

EXPOSE 7860

CMD ["python", "backend/app.py"]
