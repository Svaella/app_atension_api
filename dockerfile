FROM python:3.9-slim

# Establecer directorio de trabajo
WORKDIR /app

# Copiar todos los archivos al contenedor
COPY . /app

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto que usará Uvicorn
EXPOSE 7860

# Ejecutar el servidor FastAPI
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]

