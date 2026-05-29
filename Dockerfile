# 1. Usar una imagen ligera oficial de Python
FROM python:3.11-slim

# 2. Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# 3. Copiar e instalar las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiar el resto del código del proyecto
COPY . .

# 5. CORRECCIÓN: Ejecutar Uvicorn permitiendo que Cloud Run defina el puerto dinámicamente con $PORT
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
# 1. Usar una imagen ligera oficial de Python
FROM python:3.11-slim

# 2. Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# 3. Copiar e instalar las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiar el resto del código del proyecto
COPY . .

# === AÑADE ESTAS DOS LÍNEAS CON TUS LLAVES REALES ===
ENV GOOGLE_MAPS_API_KEY="TU_LLAVE_DE_MAPS_AQUÍ"
ENV GEMINI_API_KEY="TU_LLAVE_DE_GEMINI_AQUÍ"

# 5. Ejecutar Uvicorn
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
