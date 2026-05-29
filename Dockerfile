# 1. Usar una imagen ligera oficial de Python
FROM python:3.11-slim

# 2. Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# 3. Copiar e instalar las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiar el resto del código del proyecto
COPY . .

# 5. Ejecutar la app con Uvicorn en el puerto que asigne Cloud Run dinámicamente
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

