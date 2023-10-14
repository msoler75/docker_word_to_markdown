from flask import Flask, request, send_file
from io import BytesIO
import os
import subprocess
import shutil
import tempfile
import zipfile
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)

# Establecer el valor de MAX_CONTENT_LENGTH en el POST
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32 megabytes


def process_word_file(file_path):
    """
    Procesa un archivo Word (.docx) utilizando pandoc y crea un archivo ZIP
    que contiene el archivo de salida en formato markdown (output.md) y la
    carpeta 'media' con todas las imágenes extraídas del archivo.

    :param file_path: Ruta del archivo Word de entrada (.docx).
    :return: Ruta del archivo ZIP generado que contiene output.md y la carpeta 'media'.
    """
    # Procesar el archivo Word usando pandoc
    try:
        subprocess.run(['pandoc', '--wrap', 'none', '-t', 'markdown_mmd', '--extract-media', '.', file_path, '-o', 'output.md'], check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError("Error al procesar el archivo Word. Asegúrate de que el archivo tenga el formato correcto.") from e

    # Verificar si el archivo 'output.md' se generó correctamente
    if not os.path.exists('output.md'):
        raise RuntimeError("El archivo 'output.md' no se generó correctamente.")

    temp_dir = tempfile.gettempdir()
    zip_file_path = os.path.join(temp_dir, 'salida.zip')

    current_dir = os.path.abspath('.')
    output_md = os.path.join(current_dir, 'output.md')
    media_dir = os.path.join(current_dir, 'media')

    # Crear el archivo ZIP incluyendo el contenido de la carpeta 'media'
    with zipfile.ZipFile(zip_file_path, 'w') as zip_file:
        zip_file.write(output_md, os.path.basename(output_md))
        if os.path.exists(media_dir):
            for foldername, subfolders, filenames in os.walk(media_dir):
                for filename in filenames:
                    file_path = os.path.join(foldername, filename)
                    zip_file.write(file_path, os.path.relpath(file_path, current_dir))

    # Eliminar archivos temporales
    os.remove('output.md')
    if os.path.exists(media_dir):
        shutil.rmtree('media')

    return zip_file_path

@app.route("/", methods=['GET', 'POST'])
def process_file():
    if request.method == 'GET':
        return """<h1>API de conversión Word a Markdown</h1>
<p>Bienvenido a la API de conversión de archivos Word a Markdown.</p>
<p><strong>Descripción:</strong></p>
<p>Puedes enviar un archivo en formato Word (.docx) utilizando el método POST y la API te devolverá un archivo ZIP que contiene el archivo de salida en formato Markdown (output.md) y la carpeta 'media' con todas las imágenes extraídas del archivo Word.</p>
<p><strong>Endpoint:</strong></p>
<p>Método POST: /</p>
<p><strong>Parámetros:</strong></p>
<p>file: Archivo Word (.docx) a convertir (en el cuerpo de la solicitud).</p>
<p><strong>Respuesta:</strong></p>
<p>La API devolverá un archivo ZIP que contiene output.md y la carpeta 'media'. Puedes descargar el archivo resultante desde la respuesta.</p>
"""

    elif request.method == 'POST':

        if 'file' not in request.files:
            return "No se proporcionó un archivo en la solicitud.", 400

        try:
            file = request.files['file']
            temp_dir = tempfile.gettempdir()
            filename = file.filename
            
            # Obtener la extensión del archivo original
            extension = os.path.splitext(filename)[1]

            # Verificar si la extensión es .docx
            if extension != '.docx':
                return f"El archivo debe tener extensión .docx"
            
            # Construir la ruta de archivo utilizando la extensión original
            file_path = os.path.join(temp_dir, f'entrada{extension}')

            file.save(file_path)

            zip_file_path = process_word_file(file_path)

            with open(zip_file_path, 'rb') as f:
                zip_content = f.read()

            os.remove(zip_file_path)

            return send_file(BytesIO(zip_content), as_attachment=True, download_name='salida.zip')

        except Exception as e:
            return f"Ocurrió un error durante el procesamiento del archivo: {str(e)}", 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
