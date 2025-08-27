import os
from drive_handler import get_drive_service, process_drive_folder, create_category_json

# =========================================================
# CONFIGURACIÓN
# =========================================================
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'driveCredentials.json'
ROOT_FOLDER_ID = '1uz-MJd-7stYBuNF-fHyOBOhHof0xSYa-'
OUTPUT_DOCS_DIR = './docs'
OUTPUT_STATIC_IMG_DIR = './static/img'
IMAGE_CACHE_FILE = 'image_cache.json'

# =========================================================
# INICIO DEL SCRIPT
# =========================================================
if __name__ == "__main__":
    drive_service = get_drive_service(SERVICE_ACCOUNT_FILE, SCOPES)
    if drive_service:
        print("🚀 Iniciando sincronización de Google Drive a Docusaurus...")
        
        # Asegura la existencia del directorio raíz y crea su _category_.json
        if not os.path.exists(OUTPUT_DOCS_DIR):
            os.makedirs(OUTPUT_DOCS_DIR)
        create_category_json(OUTPUT_DOCS_DIR, "Revista del Colegio")
        
        process_drive_folder(
            drive_service,
            ROOT_FOLDER_ID,
            OUTPUT_DOCS_DIR,
            OUTPUT_STATIC_IMG_DIR,
            IMAGE_CACHE_FILE
        )
        print("🎉 Conversión y sincronización completa.")