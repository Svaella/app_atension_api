FROM python:3.9-slim

WORKDIR /app

RUN pip install --no-cache-dir gdown

COPY . /app

# Descarga desde Google Drive
RUN gdown --id 1dktpFWSCBeA3wo-DKIFV-36f-NnDt42v -O Modelo_atension.pkl

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 7860

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]

