import os
import json
import math
import urllib.parse
import logging

# Configuration du logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = "http://cdn.ghosteshop.com/Nintendo%20DS/"
BASE_DIR = "/var/www/ghosteshop/cdn/Nintendo DS/"

def get_file_size(file_path):
    size_bytes = os.path.getsize(file_path)
    size_mb = size_bytes / (1024 * 1024)
    logging.debug(f"Taille du fichier '{file_path}': {size_mb:.2f} MB ({size_bytes} bytes)")
    return size_bytes, f"{size_mb:.2f} MB"

def parse_file_name(file_name):
    # Extract game name: everything before the first parenthesis
    name_part = file_name.split('(', 1)[0].strip()
    logging.debug(f"Nom du jeu extrait de '{file_name}': '{name_part}'")
    return name_part

def get_region_from_path(file_path):
    parts = file_path.split(os.sep)
    if len(parts) > 1:
        region = parts[-3]  # The folder before the last folder
        logging.debug(f"Région extraite du chemin '{file_path}': '{region}'")
        return region
    logging.debug(f"Région non trouvée pour le chemin '{file_path}', définie sur 'Unknown'")
    return "Unknown"

def convert_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    readable_size = f"{s} {size_name[i]}"
    logging.debug(f"Taille totale convertie: {readable_size}")
    return readable_size

def list_nds_files(base_dir, base_url):
    files_info = []
    total_size_bytes = 0

    for root, dirs, files in os.walk(base_dir):
        logging.info(f"Exploration du dossier: {root}")
        for file in files:
            if file.endswith(".nds"):
                file_path = os.path.join(root, file)
                file_name = file
                
                region = get_region_from_path(file_path)
                name = parse_file_name(file_name)
                size_bytes, size = get_file_size(file_path)
                total_size_bytes += size_bytes

                # Generate the URL
                relative_path = os.path.relpath(file_path, BASE_DIR)
                file_url = base_url + urllib.parse.quote(relative_path.replace(os.sep, '/'))
                logging.debug(f"URL générée pour le fichier '{file_path}': {file_url}")
                
                files_info.append({
                    "file_name": file_name,
                    "game_name": name,
                    "region": region,
                    "file_size": size,
                    "url": file_url
                })

    total_size_readable = convert_size(total_size_bytes)
    summary = {
        "total_files": len(files_info),
        "total_size": total_size_readable,
        "files": files_info
    }

    logging.info(f"Nombre total de fichiers: {summary['total_files']}")
    logging.info(f"Taille totale des fichiers: {summary['total_size']}")
    return summary

def main():
    base_dir = BASE_DIR
    base_url = BASE_URL
    logging.info(f"Début de la liste des fichiers NDS dans le répertoire: {base_dir}")
    summary = list_nds_files(base_dir, base_url)
    logging.info("Écriture des informations des fichiers NDS dans le fichier JSON")

    with open('nds_files_info.json', 'w') as json_file:
        json.dump(summary, json_file, indent=4)

    logging.info("Processus terminé avec succès")

if __name__ == "__main__":
    main()
