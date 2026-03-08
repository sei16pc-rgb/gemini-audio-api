from http.server import BaseHTTPRequestHandler
import json
from google import genai
import requests
from bs4 import BeautifulSoup
import os

# クライアントはリクエストのたびに生成せず、ここで初期化
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
        # 最初にCORSヘッダーを送る
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)

            target_url = data.get('url')
            query = data.get('query', '内容を要約して説明してください')

            # 1. スクレイピング
            #res = requests.get(target_url, timeout=10)
            #res.encoding = res.apparent_encoding
            #soup = BeautifulSoup(res.text, 'html.parser')
            #text = soup.get_text()[:8000]

            #print(f"DEBUG: 取得したテキストの長さ: {len(text)}") # ログ確認用
            
            #if len(text) < 50:
            #     raise Exception("Webサイトから内容を取得できませんでした（またはブロックされました）")
            prompt = "「こんにちは」という挨拶を返してください。それだけでいいです。"


            
            # 2. Geminiで生成
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            # responseの中身自体をログに出す
            print(f"DEBUG: Geminiのレスポンス: {response}")

            # 3. レスポンスの取得（確実にテキストを取得）
            # response.text が取れない場合に備えて、 candidates から直接狙います
            summary_text = response.text if response.text else "要約を生成できませんでした。"

            # 4. レスポンス送信
            result = {
                "text": summary_text,
                "audio": ""
            }
            self.wfile.write(json.dumps(result).encode())


        

        except Exception as e:
            # エラー時もJSONで返す
            error_msg = {"error": str(e)}
            self.wfile.write(json.dumps(error_msg).encode())

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write("API is running!".encode())


