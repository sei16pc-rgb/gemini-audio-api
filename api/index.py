from http.server import BaseHTTPRequestHandler
import json
from google import genai
from google.genai import types
import requests
from bs4 import BeautifulSoup
import os
 
# APIキーはVercelの設定画面（環境変数）で後から登録します
API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)
 
class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        # CORS対応
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
 
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
 
        target_url = data.get('url')
        query = data.get('query', '内容を要約して音声で説明してください')
 
        try:
            # 1. スクレイピング
            res = requests.get(target_url, timeout=10)
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, 'html.parser')
            text = soup.get_text()[:10000]
 
            # 2. Geminiで音声生成
            config = types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoife")
                    )
                )
            )
 
            prompt = f"情報：{text}\n\n質問：{query}"
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=config
            )
 
            # 3. 音声データの抽出
            audio_base64 = ""
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    audio_base64 = part.inline_data.data
 
            # 4. レスポンス送信
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
 
            result = {
                "text": response.text,
                "audio": audio_base64
            }
            self.wfile.write(json.dumps(result).encode())
 
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            self.wfile.write(json.dumps({"error": str(e)}).encode())
def do_GET(self):
        # GETリクエストが来たら「動いてるよ！」と返す
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write("API is running! Please use POST method.".encode())
