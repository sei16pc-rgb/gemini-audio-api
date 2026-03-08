from http.server import BaseHTTPRequestHandler
import json
import os
import requests
from bs4 import BeautifulSoup
from google import genai

# 環境変数の取得
API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        # CORS対策：最初に必ず送る
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        try:
            # 1. リクエストボディの解析
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            target_url = data.get('url')

            # 2. スクレイピング
            try:
                res = requests.get(target_url, timeout=10)
                res.encoding = res.apparent_encoding
                soup = BeautifulSoup(res.text, 'html.parser')
                # 不要なタグを除去してテキスト抽出
                for script in soup(["script", "style"]):
                    script.decompose()
                text = soup.get_text()[:5000].strip()
            except Exception as e:
                text = f"スクレイピングエラー: {str(e)}"

            # 3. Gemini 1.5 Flash で生成（最も安定しているモデル）
            prompt = f"以下の内容を日本語で短く要約してください：\n\n{text}"
            
            # 最新ライブラリの標準的な呼び出し方
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt
            )

            # 4. レスポンスの組み立て
            # response.text が存在しない場合の安全策
            summary = "要約を生成できませんでした。"
            if response and response.text:
                summary = response.text

            result = {
                "text": summary,
                "audio": ""
            }
            self.wfile.write(json.dumps(result).encode('utf-8'))

        except Exception as e:
            # プログラム上のエラーをブラウザに伝える
            error_data = {"text": f"実行エラーが発生しました: {str(e)}", "audio": ""}
            self.wfile.write(json.dumps(error_data).encode('utf-8'))

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write("API is running".encode())
