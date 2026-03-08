from http.server import BaseHTTPRequestHandler
import json
import os
import requests
from bs4 import BeautifulSoup

# 環境変数の取得
API_KEY = os.environ.get("GEMINI_API_KEY")

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            target_url = data.get('url')

            # 1. スクレイピング
            try:
                res = requests.get(target_url, timeout=10)
                res.encoding = res.apparent_encoding
                soup = BeautifulSoup(res.text, 'html.parser')
                for script in soup(["script", "style"]):
                    script.decompose()
                text = soup.get_text()[:4000].strip()
            except:
                text = "Webサイトの内容を取得できませんでした。"

            # 2. Gemini API へ直接リクエスト (SDKを使わずREST APIを使用)
            # gemini_url を以下に書き換え
            # gemini_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"
            # 上記がダメならこちら
            gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}" 
            # 最終手段
            # gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-8b:generateContent?key={API_KEY}" 
            
            payload = {
                "contents": [{
                    "parts": [{"text": f"以下の内容を日本語で要約してください：\n\n{text}"}]
                }]
            }
            
            headers = {'Content-Type': 'application/json'}
            response = requests.post(gemini_url, json=payload, headers=headers)
            res_data = response.json()

            # 3. レスポンス解析
            if "candidates" in res_data:
                summary = res_data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                summary = f"APIエラー: {json.dumps(res_data)}"

            result = {"text": summary, "audio": ""}
            self.wfile.write(json.dumps(result).encode('utf-8'))

        except Exception as e:
            error_data = {"text": f"実行エラー: {str(e)}", "audio": ""}
            self.wfile.write(json.dumps(error_data).encode('utf-8'))

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write("API is active".encode())


