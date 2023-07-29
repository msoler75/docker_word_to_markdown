# Usar una imagen de Python
FROM python:3.9

# Instalar pandoc
RUN apt-get update && apt-get install -y pandoc

# Copiar los archivos necesarios al contenedor
COPY app.py requirements.txt ./

# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Iniciar la aplicación al arrancar el contenedor
CMD ["python", "app.py"]
