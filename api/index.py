from http.server import BaseHTTPRequestHandler
import json
from google import genai
import requests
from bs4 import BeautifulSoup
import os

# 環境変数の読み込み
API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        # CORSの事前確認に200 OKを返す
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        # どんなエラーが起きてもブラウザが拒絶しないよう、最初にヘッダーを送る
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        try:
            # データの読み取り
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            target_url = data.get('url')

            # 1. スクレイピング（失敗しても止まらないようにtryを入れる）
            try:
                res = requests.get(target_url, timeout=10)
                res.encoding = res.apparent_encoding
                soup = BeautifulSoup(res.text, 'html.parser')
                text = soup.get_text()[:5000] # 文字数を抑えて安定化
            except:
                text = "URLの取得に失敗しました。"

            # 2. Geminiで生成
            prompt = f"以下のWebサイトの内容を要約して日本語で教えてください：\n\n{text}"
            
            # 安全のため try-except で囲む
            response = client.models.generate_content(
                #model="gemini-2.0-flash",
                model="gemini-1.5-flash",
                contents=prompt
            )

            # 3. 結果の整理
            # response.text が取れない場合に備えた安全策
            if hasattr(response, 'text') and response.text:
                summary_text = response.text
            else:
                summary_text = "Geminiから有効な回答が得られませんでした。"

            result = {
                "text": summary_text,
                "audio": ""
            }
            self.wfile.write(json.dumps(result).encode('utf-8'))

        except Exception as e:
            # 万が一のプログラムエラーもJSONで返す
            error_res = {"text": f"サーバーエラーが発生しました: {str(e)}", "audio": ""}
            self.wfile.write(json.dumps(error_res).encode('utf-8'))

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write("API is active.".encode())

