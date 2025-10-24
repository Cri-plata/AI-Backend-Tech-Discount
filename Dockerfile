# Usamos una imagen oficial de Python como base.
# Es una buena práctica usar una versión específica.
FROM python:3.11-slim

# Establecemos variables de entorno para Python.
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Creamos y establecemos el directorio de trabajo dentro del contenedor.
WORKDIR /app

# Copiamos el archivo de dependencias primero.
# Esto aprovecha el caché de Docker para no reinstalar todo cada vez.
COPY requirements.txt /app/

# Instalamos las dependencias.
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copiamos el resto del código del proyecto al contenedor.
COPY . /app/

# El comando por defecto que se ejecutará cuando el contenedor inicie.
# Inicia el servidor de desarrollo de Django.
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]