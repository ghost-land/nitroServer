import os
import json
import math
import urllib.parse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Logging configuration
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = "http://cdn.ghosteshop.com/Nintendo%20DS/"
BASE_IMAGE_URL = "https://cdn.ghosteshop.com/Images/ds/"
BASE_FORWARDER_URL = "http://cdn.ghosteshop.com/Nintendo%20DS%20-%20forwarders/"
BASE_IMAGE_DIR = "/var/www/ghosteshop/cdn/Images/ds/"
BASE_FORWARDER_DIR = "/var/www/ghosteshop/cdn/Nintendo DS - forwarders/"
BASE_DIR = "/var/www/ghosteshop/cdn/Nintendo DS/"

def get_file_size(file_path):
    size_bytes = os.path.getsize(file_path)
    size_mb = size_bytes / (1024 * 1024)
    logging.debug(f"File size '{file_path}': {size_mb:.2f} MB ({size_bytes} bytes)")
    return size_bytes, f"{size_mb:.2f} MB"

def parse_file_name(file_name):
    # Extract game name: everything before the first parenthesis
    name_part = file_name.split('(', 1)[0].strip()
    logging.debug(f"Game name from '{file_name}': '{name_part}'")
    return name_part

def get_region_from_path(file_path):
    parts = file_path.split(os.sep)
    if len(parts) > 2:
        region = parts[-3]  # The folder before the last folder
        logging.debug(f"Region extracted from the path '{file_path}': '{region}'")
        return region
    logging.debug(f"Region not found for path '{file_path}', defined on 'Unknown'")
    return "Unknown"

def convert_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    readable_size = f"{s} {size_name[i]}"
    logging.debug(f"Total converted size: {readable_size}")
    return readable_size

def check_image_exists_locally(image_path):
    exists = os.path.isfile(image_path)
    logging.debug(f"Local verification of file existence '{image_path}': {'exists' if exists else 'does not exist'}")
    return exists

def generate_file_info(file_path, file_name, base_image_url, base_image_dir, base_forwarder_url, base_forwarder_dir):
    region = get_region_from_path(file_path)
    name = parse_file_name(file_name)
    size_bytes, size = get_file_size(file_path)
    
    # Generate URLs
    relative_path = os.path.relpath(file_path, BASE_DIR)
    file_url = BASE_URL + urllib.parse.quote(relative_path.replace(os.sep, '/'))
    logging.debug(f"URL generated for the file '{file_path}': {file_url}")

    # Generate image paths and URLs
    parent_folder = os.path.basename(os.path.dirname(file_path))
    game_folder = os.path.join(parent_folder, name)
    game_folder_encoded = urllib.parse.quote(game_folder.replace(os.sep, '/'))
    icon_path = os.path.join(base_image_dir, game_folder, "icon.png")
    boxart_path = os.path.join(base_image_dir, game_folder, "boxart.png")
    boxart_twl_path = os.path.join(base_image_dir, game_folder, "boxart-twl.png")
    icon_url = f"{base_image_url}{game_folder_encoded}/icon.png" if check_image_exists_locally(icon_path) else None
    boxart_url = f"{base_image_url}{game_folder_encoded}/boxart.png" if check_image_exists_locally(boxart_path) else None
    boxart_twl_url = f"{base_image_url}{game_folder_encoded}/boxart-twl.png" if check_image_exists_locally(boxart_twl_path) else None

    # Generate forwarder paths and URLs
    forwarder_name = f"forwarder-{file_name.replace('.nds', '.cia')}"
    forwarder_path = os.path.join(base_forwarder_dir, region, parent_folder, forwarder_name)
    forwarder_url = f"{base_forwarder_url}{urllib.parse.quote(os.path.join(region, parent_folder, forwarder_name).replace(os.sep, '/'))}" if check_image_exists_locally(forwarder_path) else None

    return {
        "file_name": file_name,
        "game_name": name,
        "region": region,
        "file_size": size,
        "url": file_url,
        "icon_url": icon_url,
        "boxart_url": boxart_url,
        "boxart_twl_url": boxart_twl_url,
        "forwarder_url": forwarder_url,
        "size_bytes": size_bytes  # to accumulate total size
    }

def list_nds_files(base_dir, base_url, base_image_url, base_image_dir, base_forwarder_url, base_forwarder_dir):
    files_info = []
    total_size_bytes = 0

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for root, dirs, files in os.walk(base_dir):
            logging.info(f"Exploring the folder: {root}")
            for file in files:
                if file.endswith(".nds"):
                    file_path = os.path.join(root, file)
                    futures.append(executor.submit(generate_file_info, file_path, file, base_image_url, base_image_dir, base_forwarder_url, base_forwarder_dir))
        
        for future in as_completed(futures):
            file_info = future.result()
            total_size_bytes += file_info.pop("size_bytes")
            files_info.append(file_info)

    total_size_readable = convert_size(total_size_bytes)
    summary = {
        "total_files": len(files_info),
        "total_size": total_size_readable,
        "files": files_info
    }

    logging.info(f"Total number of files: {summary['total_files']}")
    logging.info(f"Total file size: {summary['total_size']}")
    return summary

def main():
    base_dir = BASE_DIR
    base_url = BASE_URL
    base_image_url = BASE_IMAGE_URL
    base_forwarder_url = BASE_FORWARDER_URL
    base_image_dir = BASE_IMAGE_DIR
    base_forwarder_dir = BASE_FORWARDER_DIR
    logging.info(f"Start of list of NDS files in directory: {base_dir}")
    summary = list_nds_files(base_dir, base_url, base_image_url, base_image_dir, base_forwarder_url, base_forwarder_dir)
    logging.info("Writing NDS file information to the JSON file")

    with open('nds_files_info.json', 'w') as json_file:
        json.dump(summary, json_file, indent=4)

    logging.info("Process successfully completed")

if __name__ == "__main__":
    main()
