# Usamos la imagen oficial de Nginx sobre Alpine Linux
FROM nginx:alpine

# Borramos los archivos y configuraciones por defecto de Nginx
RUN rm -rf /usr/share/nginx/html/*
RUN rm /etc/nginx/conf.d/default.conf

# Copiamos tu archivo de configuración personalizado al contenedor
COPY nginx.conf /etc/nginx/conf.d/

# Copiamos todo el contenido del frontend (HTML, CSS, JS) al contenedor
COPY . /usr/share/nginx/html/

# Exponemos el puerto 8080 para Cloud Run
EXPOSE 8080

# Arrancamos Nginx
CMD ["nginx", "-g", "daemon off;"]

