# Usamos la imagen oficial de Nginx sobre Alpine Linux
FROM nginx:alpine

# Borramos los archivos por defecto de Nginx
RUN rm -rf /usr/share/nginx/html/*

# Copiamos todo el contenido de tu frontend al contenedor
COPY . /usr/share/nginx/html/

# Truco para Cloud Run: Modificamos la configuración de Nginx para que escuche en el puerto 8080 en lugar del 80
RUN sed -i 's/listen[:[:space:]]*80;/listen 8080;/g' /etc/nginx/conf.d/default.conf

# Exponemos el puerto 8080 que es el que espera Cloud Run
EXPOSE 8080

# Arrancamos Nginx
CMD ["nginx", "-g", "daemon off;"]
