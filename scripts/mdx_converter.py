import os
import re
import requests
import urllib.parse
from bs4 import BeautifulSoup
import json # Necesario para guardar el cache de imagenes

def download_image(url, local_path):
    """Descarga una imagen solo si no existe localmente."""
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    if not os.path.exists(local_path):
        try:
            r = requests.get(url, stream=True, timeout=10)
            if r.status_code == 200:
                with open(local_path, "wb") as f:
                    for chunk in r.iter_content(1024):
                        f.write(chunk)
                print(f"🖼️ Guardada imagen: {local_path}")
                return True
        except requests.exceptions.RequestException as e:
            print(f"❌ Error al descargar imagen de {url}: {e}")
    return False

def save_if_changed(file_path, content):
    """Guarda el archivo solo si su contenido ha cambiado."""
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            if f.read().strip() == content.strip():
                print(f"⚡ Sin cambios: {file_path}")
                return False
    
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Guardado: {file_path}")
    return True

def get_document_sample(html_data, max_length=200):
    """Extrae el primer párrafo o una muestra del documento."""
    soup = BeautifulSoup(html_data, 'html.parser')
    first_p = soup.find('p')
    if first_p:
        text = first_p.get_text(strip=True)
        if len(text) > max_length:
            return text[:max_length] + '...'
        return text
    
    body_text = soup.body.get_text(strip=True)
    if body_text:
        if len(body_text) > max_length:
            return body_text[:max_length] + '...'
        return body_text
    
    return "No hay una descripción disponible."

def get_first_image_url(html_data):
    """Extrae la URL de la primera imagen en el documento."""
    soup = BeautifulSoup(html_data, 'html.parser')
    first_img = soup.find('img')
    if first_img and first_img.get('src'):
        return first_img.get('src')
    return None

def convert_to_mdx(element, img_subfolder, image_cache, output_static_img_dir):
    """Convierte un elemento HTML y sus hijos a MDX, gestionando el registro de imágenes."""
    if element.name is None:
        return element.string.replace("\n", "\n\n") if element.string else ""

    if element.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
        text = element.get_text(strip=True)
        return f"{'#' * int(element.name[1])} {text}\n\n"
    elif element.name == "p":
        content = "".join([convert_to_mdx(child, img_subfolder, image_cache, output_static_img_dir) for child in element.children])
        return f"{content}\n\n"
    elif element.name == "br":
        return "\n"
    elif element.name == "blockquote":
        text = element.get_text(strip=True)
        return f"> {text}\n\n"
    elif element.name in ["ul", "ol"]:
        list_items = ""
        for idx, li in enumerate(element.find_all("li", recursive=False), start=1):
            prefix = "- " if element.name == "ul" else f"{idx}. "
            list_items += f"{prefix}{''.join([convert_to_mdx(child, img_subfolder, image_cache, output_static_img_dir) for child in li.children])}\n"
        return list_items + "\n"
    elif element.name == "table":
        return process_table(element) + "\n"
    elif element.name == "img":
        src = element.get("src", "")
        alt = element.get("alt", "")
        
        if src in image_cache:
            img_name = image_cache[src]
            print(f"⚡ Imagen ya en caché: {img_name}")
        else:
            img_hash = abs(hash(src)) % (10**8)
            img_name = f"img_{img_hash}.png"
            local_img_path = os.path.join(output_static_img_dir, img_subfolder, img_name)
            download_image(src, local_img_path)
            image_cache[src] = img_name
        
        return f"![{alt}](/img/{img_subfolder}/{img_name})\n\n"
    elif element.name == "a":
        url = element.get('href', '#')
        
        if "google.com/url?q=" in url:
            parsed_url = urllib.parse.urlparse(url)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            if 'q' in query_params:
                url = query_params['q'][0]
        
        youtube_pattern = re.compile(r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})')
        match = youtube_pattern.search(url)
        
        if match:
            video_id = match.group(1)
            return f"<VideoPlayer src=\"{video_id}\" />\n\n"
        
        text = element.get_text(strip=True)
        return f"[{text}]({url})"
    elif element.name in ["strong", "b"]:
        return f"**{''.join([convert_to_mdx(child, img_subfolder, image_cache, output_static_img_dir) for child in element.children])}**"
    elif element.name in ["em", "i"]:
        return f"*{''.join([convert_to_mdx(child, img_subfolder, image_cache, output_static_img_dir) for child in element.children])}*"
    elif element.name == "span" and element.has_attr("style"):
        color_code_match = re.search(r"color:\s*([^;]+)", element["style"])
        if color_code_match:
            color_code = color_code_match.group(1).strip()
            content = "".join([convert_to_mdx(child, img_subfolder, image_cache, output_static_img_dir) for child in element.children])
            return f"<ColorText color=\"{color_code}\">{content}</ColorText>"

    return "".join([convert_to_mdx(child, img_subfolder, image_cache, output_static_img_dir) for child in element.children])


def process_table(table_tag):
    """Convierte una tabla HTML a Markdown."""
    rows = table_tag.find_all("tr")
    if not rows:
        return ""
    
    md_lines = []
    
    headers = [cell.get_text(strip=True) for cell in rows[0].find_all(["th", "td"])]
    md_lines.append("| " + " | ".join(headers) + " |")
    md_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    
    for row in rows[1:]:
        cells = [cell.get_text(strip=True) for cell in row.find_all(["th", "td"])]
        md_lines.append("| " + " | ".join(cells) + " |")
        
    return "\n".join(md_lines) + "\n"

def convert_html_to_mdx_final(html_data, img_subfolder, image_cache, output_static_img_dir):
    """Punto de entrada principal para la conversión de HTML a MDX."""
    soup = BeautifulSoup(html_data, "lxml")
    mdx_content_parts = []
    
    for element in soup.body.find_all(True, recursive=False):
        mdx_content = convert_to_mdx(element, img_subfolder, image_cache, output_static_img_dir)
        if mdx_content:
            mdx_content_parts.append(mdx_content)
            
    return "\n".join(mdx_content_parts)