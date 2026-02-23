import requests
from flask import Flask, Response, request

app = Flask(__name__)

# De site die je wilt 'vangen'
TARGET_SITE = "https://trajectklas.nl"

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(path):
    # Bouw de volledige URL naar de doelsite
    url = f"{TARGET_SITE}/{path}"
    
    # Stuur alle headers en data door van de gebruiker naar de doelsite
    headers = {key: value for (key, value) in request.headers if key != 'Host'}
    
    # Voer het verzoek uit naar de chatbot server
    resp = requests.request(
        method=request.method,
        url=url,
        headers=headers,
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False
    )

    # Maak een response object om terug te sturen naar de browser
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
               if name.lower() not in excluded_headers]

    response = Response(resp.content, resp.status_code, headers)
    return response

if __name__ == "__main__":
    app.run(port=5000)
