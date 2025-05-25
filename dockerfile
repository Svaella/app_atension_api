FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Instala gdown primero para que esté disponible
RUN pip install --no-cache-dir gdown

# Copia todo al contenedor
COPY . /app

# Descarga el modelo desde Google Drive
RUN gdown --id 1SqN57FUdT-esT26R3HwStJe5f1Dzu3No -O Modelo1.pkl

# Instala el resto de dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto usado por Uvicorn
EXPOSE 7860

# Comando para correr el servidor FastAPI
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]

