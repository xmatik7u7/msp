import subprocess
import sys
import os
import glob
import requests
import zipfile
import shutil
import json
import time
import requests
from PIL import Image
from io import BytesIO

RGB = [(0, 255, 0), (0, 128, 255), (255, 0, 255)]


def run_command(command):
    """Ejecutar un comando en el sistema y verificar si fue exitoso."""
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return e


def gradient_text(text, colors):
    length = len(text)
    num_colors = len(colors)
    result = ""
    for i, char in enumerate(text):
        color_index = (i * (num_colors - 1)) // length
        t = (i * (num_colors - 1)) / length - color_index
        color1 = colors[color_index]
        color2 = colors[color_index + 1] if color_index + 1 < num_colors else colors[color_index]
        r = int(color1[0] + (color2[0] - color1[0]) * t)
        g = int(color1[1] + (color2[1] - color1[1]) * t)
        b = int(color1[2] + (color2[2] - color1[2]) * t)
        result += f'\033[38;2;{r};{g};{b}m{char}'
    return result + '\033[0m'

def force_push(branch_name, commit):
    """Forzar el push al repositorio remoto en la rama especificada."""
    print(gradient_text(f"Realizando push forzado en la rama {branch_name}", [(0, 255, 0), (0, 128, 255)]))
    try:
        run_command(["git", "update-ref", f"refs/heads/{branch_name}", commit])
        run_command(["git", "push", "--force", "origin", branch_name])
        print(gradient_text(f"Push forzado realizado con éxito en la rama {branch_name}.", [(0, 255, 0), (0, 128, 255)]))
    except subprocess.CalledProcessError as e:
        print(gradient_text(f"Error en el push forzado: {e.stderr}", [(255, 0, 0), (255, 128, 0)]))
        sys.exit(1)

def branch():
    # Cambia el directorio actual
    os.chdir(f"{glob.glob('/workspaces/*')[0]}/")
    os.system("cd /workspaces/*/")

    new_branch_name = "Minecraft_branch"

    # Obtener la URL del repositorio
    print(gradient_text("Obteniendo la URL del repositorio remoto", RGB))
    repo_url = run_command(["git", "remote", "-v"])

    # Eliminar la rama remota si existe
    print(gradient_text(f"Eliminando la rama remota", RGB))
    run_command(["git", "push", "origin", "--delete", new_branch_name])

    # Eliminar la rama local si existe
    print(gradient_text(f"Eliminando la rama local", RGB))
    os.system(f"git branch -D {new_branch_name}")

    # Limpiar el índice de Git
    run_command(["git", "rm", "-r", "--cached", "."])

    # Crear la rama
    os.system(f"git checkout -b {new_branch_name}")

    # Añadir específicamente los archivos requeridos
    archivos_excluidos = []

    for root, _, files in os.walk('servidor_minecraft'):
        for file in files:
            archivo = os.path.join(root, file)
            tamaño = os.path.getsize(archivo)
            if tamaño < 100 * 1024 * 1024:  
                run_command(["git", "add", "--force", archivo])
            else:
                archivos_excluidos.append(archivo)

    configuracion_json = 'configuracion.json'
    tamaño = os.path.getsize(configuracion_json)
    if tamaño < 100 * 1024 * 1024:
        run_command(["git", "add", "--force", configuracion_json])
    else:
        archivos_excluidos.append(configuracion_json)

    # Crear un commit tree y obtener el commit SHA
    commit_tree = run_command(["git", "write-tree"])
    commit_message = "Branch para guardar tu server_minecraft"
    commit = run_command(["git", "commit-tree", commit_tree, "-m", commit_message])

    # Push forzado
    print(gradient_text("Realizando push", RGB))
    force_push(new_branch_name, commit)

    # Generar la URL de descarga del ZIP
    user_name, repo_name = repo_url.split('/')[-2], repo_url.split('/')[-1].replace('.git', '')
    zip_url = f"https://codeload.github.com/{user_name}/{repo_name}/zip/refs/heads/{new_branch_name}".replace(" (push)", "")
    os.system("clear")
    print(gradient_text(f"\nBranch creado/actualizado localmente: {new_branch_name}\nEnlace al branch para descargar en ZIP: {zip_url}", RGB))
    url_data = {"Enlace_a_copiar": zip_url}

    with open('addons/url-del-branch.json', 'w') as url_file:
        json.dump(url_data, url_file, indent=4)
        
    if archivos_excluidos:
        print(gradient_text("\nLos siguientes archivos no fueron añadidos al branch debido a que superan los 100MB:", [(255, 0, 0), (255, 128, 0)]))
        for archivo in archivos_excluidos:
            print(archivo)

    input(gradient_text("\nPresiona cualquier tecla para continuar...", RGB))
    sys.exit(0)
    
def download_and_extract_zip(url, extract_to):
    """Descargar y extraer un archivo ZIP desde una URL."""
    local_zip_file = "repo.zip"
    
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_zip_file, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        with zipfile.ZipFile(local_zip_file, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
    finally:
        if os.path.exists(local_zip_file):
            os.remove(local_zip_file)

def link():
    zip_url2 = input(gradient_text("Introduce el enlace directo del archivo ZIP: ", RGB)).strip()

    # Descargar y extraer el archivo zip
    download_and_extract_zip(zip_url2, os.getcwd())

    # Obtener el nombre del repositorio y el branch del enlace
    repo_name2 = zip_url2.split('/')[-5]
    branch_name2 = zip_url2.split('/')[-1]

    # Formatear el nombre esperado del directorio extraído
    expected_dir_name = f"{repo_name2}-{branch_name2}"

    # Verificar si la carpeta existe
    if not os.path.isdir(expected_dir_name):
        print(gradient_text("Error: No se pudo encontrar la carpeta extraída correctamente.", RGB))
        sys.exit(1)

    # Mover archivos del directorio extraído al directorio principal
    extracted_dir = os.path.join(os.getcwd(), expected_dir_name)
    for item in os.listdir(extracted_dir):
        source_path = os.path.join(extracted_dir, item)
        target_path = os.path.join(os.getcwd(), item)
        if os.path.exists(target_path):
            if os.path.isdir(target_path):
                shutil.rmtree(target_path)
            else:
                os.remove(target_path)
        shutil.move(source_path, target_path)
    
    shutil.rmtree(extracted_dir)

    print(gradient_text("\n¡Repositorio descargado y extraído exitosamente!", RGB))
    print(gradient_text("\nDirectorio actualizado con el contenido del archivo ZIP.", RGB))
    sys.exit(0)

def DescargaDropbox():
    print(gradient_text("¡Los Modpacks están en fase experimental!", RGB))
    url = input(gradient_text(f"\nIngrese la URL del Respaldo/Modpack: ", RGB)).strip()
    dest_folder = "servidor_minecraft"

    # Verificar si la URL es de Dropbox y terminar en '0'
    if "dropbox" in url and url.endswith('0'):
        url = url[:-1] + '1'
    """Descargar y extraer un archivo ZIP en la carpeta servidor_minecraft."""
    download_folder = "descargas"
    
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    # Descargar el archivo ZIP
    print(gradient_text(f"\nDescargando archivos...", RGB))
    local_filename = os.path.join(download_folder, url.split('/')[-1])
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    # Extraer el contenido del archivo ZIP
    temp_extract_folder = os.path.join(download_folder, "temp_extract")
    if not os.path.exists(temp_extract_folder):
        os.makedirs(temp_extract_folder)
    with zipfile.ZipFile(local_filename, 'r') as zip_ref:
        zip_ref.extractall(temp_extract_folder)

    # Verificar si el archivo descargado contiene las carpetas DIM-1, DIM1 y data
    if all(os.path.exists(os.path.join(temp_extract_folder, folder)) for folder in ["data"]):
        target_folder = os.path.join(dest_folder, "world")
        
        # Crear la carpeta "world" si no existe
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)
        
        # Reemplazar los archivos en la carpeta "world"
        for item in os.listdir(temp_extract_folder):
            s = os.path.join(temp_extract_folder, item)
            d = os.path.join(target_folder, item)
            if os.path.exists(d):
                if os.path.isdir(d):
                    shutil.rmtree(d)
                else:
                    os.remove(d)
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)
    elif all(os.path.exists(os.path.join(temp_extract_folder, folder)) for folder in ["bStats"]):
        target_folder = os.path.join(dest_folder, "plugins")
        
        # Crear la carpeta "plugins" si no existe
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)
        
        # Reemplazar los archivos en la carpeta "plugins"
        for item in os.listdir(temp_extract_folder):
            s = os.path.join(temp_extract_folder, item)
            d = os.path.join(target_folder, item)
            if os.path.exists(d):
                if os.path.isdir(d):
                    shutil.rmtree(d)
                else:
                    os.remove(d)
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)
    else:
        # Reemplazar archivos en la carpeta destino
        for item in os.listdir(temp_extract_folder):
            s = os.path.join(temp_extract_folder, item)
            d = os.path.join(dest_folder, item)
            if os.path.exists(d):
                if os.path.isdir(d):
                    shutil.rmtree(d)
                else:
                    os.remove(d)
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)

    # Limpiar la carpeta de extracción temporal y el archivo descargado
    shutil.rmtree(temp_extract_folder)
    os.remove(local_filename)
    print(gradient_text(f"Todos los archivos se han movido a {dest_folder}", RGB))
    input(gradient_text("\nPresiona cualquier tecla para continuar...", RGB))
    sys.exit(0)

def Img_Url():
    os.system("clear")
    img_url = input(gradient_text("Introduce el URL de la imagen: ", RGB))

    if img_url.endswith('0'):
        img_url = img_url[:-1] + '1'

    # Crear la carpeta 'server_minecraft' si no existe
    output_dir = 'servidor_minecraft'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Obtener el enlace de descarga directo de Imgur
    download_link = img_url  # Ajustar esta línea según sea necesario
    
    # Descargar la imagen
    response = requests.get(download_link)
    response.raise_for_status()
    
    # Abrir la imagen
    img = Image.open(BytesIO(response.content))
    
    # Redimensionar la imagen a 64x64 píxeles
    img = img.resize((64, 64), Image.LANCZOS)

    # Guardar la imagen como 'server-icon.png' en la carpeta 'servidor_minecraft'
    img.save(os.path.join(output_dir, 'server-icon.png'))
    
    print(gradient_text("Imagen transformada a server icon", RGB))
    input(gradient_text("\nPresiona cualquier tecla para continuar...", RGB))
    sys.exit(0)
