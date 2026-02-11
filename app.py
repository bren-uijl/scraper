import os
import requests
import base64
import logging
from flask import Flask, render_template, request, send_file, url_for
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from io import BytesIO

app = Flask(__name__)

# Logging configuratie
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def get_base64_font(url):
    """Download een font en converteer naar base64 string."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', 'font/woff2')
            encoded_string = base64.b64encode(response.content).decode('utf-8')
            return f"data:{content_type};base64,{encoded_string}"
    except Exception as e:
        logger.error(f"Font error op {url}: {e}")
    return url

def process_page(target_url):
    try:
        response = requests.get(target_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        file_count = 0
        max_files = 20

        # 1. Verwerk CSS (Link tags)
        for css in soup.find_all('link', rel='stylesheet'):
            if file_count >= max_files: break
            css_url = urljoin(target_url, css.get('href'))
            try:
                css_content = requests.get(css_url, headers=HEADERS, timeout=5).text
                new_style = soup.new_tag('style')
                new_style.string = css_content
                css.replace_with(new_style)
                file_count += 1
            except: continue

        # 2. Verwerk JavaScript (Script tags)
        for script in soup.find_all('script', src=True):
            if file_count >= max_files: break
            js_url = urljoin(target_url, script.get('src'))
            try:
                js_content = requests.get(js_url, headers=HEADERS, timeout=5).text
                new_script = soup.new_tag('script')
                new_script.string = js_content
                script.replace_with(new_script)
                file_count += 1
            except: continue

        # 3. Verwerk Fonts in bestaande Style tags (Base64 inlining)
        for style in soup.find_all('style'):
            if 'url(' in style.string if style.string else False:
                # Simpele regex-vrije vervanging voor font extensies
                for ext in ['.woff2', '.woff', '.ttf']:
                    if ext in style.string:
                        # Dit is een versimpeling; voor productie is een CSS parser beter
                        logger.info(f"Font gedetecteerd in inline style.")

        return soup.prettify()
    except Exception as e:
        logger.error(f"Scrape fout: {e}")
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/preview', methods=['POST'])
def preview():
    target_url = request.form.get('url')
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'https://' + target_url

    processed_html = process_page(target_url)
    
    if processed_html:
        # We slaan de HTML tijdelijk op in een session of we sturen het direct mee
        return render_template('preview.html', html_content=processed_html, original_url=target_url)
    return "Er is iets fout gegaan bij het scrapen van de pagina.", 400

@app.route('/download', methods=['POST'])
def download():
    html_content = request.form.get('html_content')
    buffer = BytesIO()
    buffer.write(html_content.encode('utf-8'))
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="offline_page.html", mimetype='text/html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))