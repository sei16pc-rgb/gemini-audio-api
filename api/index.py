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
    def do_OPTIONS(self):
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
        query = data.get('query', '内容を要約して説明してください')

        try:
            # 1. スクレイピング
            res = requests.get(target_url, timeout=15)
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, 'html.parser')
            text = soup.get_text()[:8000] # 文字数を少し減らして安定化

            # 2. Geminiで生成（AUDIOを指定）
            # 音声出力に対応しているモデル名を明示
            model_name = "models/gemini-2.0-flash-001" 
            
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoife")
                        )
                    )
                )
            )

            # 3. 音声データの抽出（テキストは今回は取得不可）
            audio_base64 = ""
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    # bytes形式をbase64文字列に変換
                    audio_base64 = base64.b64encode(part.inline_data.data).decode('utf-8')

            # 4. レスポンス送信
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            # 音声生成時は response.text が取れないため、仮のメッセージを返す
            result = {
                "text": "要約音声の生成が完了しました。",
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
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write("API is running! Please use POST method.".encode())

