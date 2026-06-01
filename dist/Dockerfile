# Imagen oficial y liviana de Nginx
FROM nginx:alpine

# Limpiamos el directorio por defecto y la configuración vieja
RUN rm -rf /usr/share/nginx/html/*
RUN rm -f /etc/nginx/conf.d/default.conf

# Copiamos nuestro nginx.conf personalizado directamente al destino
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiamos el HTML, CSS y JS al contenedor
COPY index.html /usr/share/nginx/html/
COPY style.css /usr/share/nginx/html/
COPY app.js /usr/share/nginx/html/

# Exponer el puerto requerido por Cloud Run
EXPOSE 8080

# Iniciar Nginx
CMD ["nginx", "-g", "daemon off;"]
