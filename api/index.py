from http.server import BaseHTTPRequestHandler
import json
from google import genai
from google.genai import types
import requests
from bs4 import BeautifulSoup
import os
import base64

API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

class handler(BaseHTTPRequestHandler):
    # (do_OPTIONSは省略：元のままでOK)

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)

        target_url = data.get('url')
        query = data.get('query', '内容を要約して説明してください')

        try:
            # 1. スクレイピング
            res = requests.get(target_url, timeout=15)
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, 'html.parser')
            text = soup.get_text()[:8000]

            # ★ここで定義するのが正解です！
            prompt = f"以下の内容を要約して説明してください：\n\n{text}"

            # 2. Geminiで生成 (まずはテキストのみでテスト)
            # 音声生成(AUDIO)でエラーが出る場合、まずはテキストで成功するか確認します
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )

            # 3. レスポンス送信
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            result = {
                "text": response.text, # テキストが取れるか確認
                "audio": ""           # 一旦空でOK
            }
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            # エラーが出たら詳細を出す
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
