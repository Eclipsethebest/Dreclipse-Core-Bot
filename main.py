from flask import Flask, render_template_string, request, jsonify
import threading

app = Flask(__name__)

# --- LİSANS ANAHTARI VERİTABANI (KEY-XXXXXX FORMATI) ---
# 15 Adet 1 Aylık Key
KEYS_1MONTH = {f"KEY-1M{i:04d}": {"used": False, "user_id": None} for i in range(1, 16)}

# 5 Adet Kalıcı (Lifetime) Key
KEYS_LIFETIME = {f"KEY-PRM{i:04d}": {"used": False, "user_id": None} for i in range(1, 6)}

# Tüm Key'ler
LICENSE_KEYS = {**KEYS_1MONTH, **KEYS_LIFETIME}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dreclipse Core Mini App</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        body {
            background-color: #121212;
            color: #ffffff;
            font-family: Arial, sans-serif;
            padding: 15px;
            margin: 0;
        }
        .card {
            background: #1e1e1e;
            padding: 15px;
            border-radius: 12px;
            margin-bottom: 15px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.5);
        }
        h2, h3 { color: #0088cc; margin-top: 0; }
        input, textarea, select {
            width: 100%;
            padding: 10px;
            margin: 8px 0;
            border-radius: 8px;
            border: 1px solid #333;
            background: #2a2a2a;
            color: #fff;
            box-sizing: border-box;
        }
        button {
            background: #0088cc;
            color: white;
            border: none;
            padding: 12px;
            border-radius: 8px;
            width: 100%;
            font-size: 15px;
            font-weight: bold;
            cursor: pointer;
            margin-top: 10px;
        }
        .hidden { display: none; }
        .chat-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #2a2a2a;
            padding: 8px 12px;
            border-radius: 6px;
            margin: 5px 0;
        }
    </style>
</head>
<body>

    <h2>⚡ Dreclipse Core Panel</h2>

    <!-- ADIM 1: KULLANICI / LİSANS DOĞRULAMA -->
    <div id="step-license" class="card">
        <h3>1. Lisans Aktivasyonu</h3>
        <p>Devam etmek için tek kullanımlık lisans anahtarınızı girin:</p>
        <input type="text" id="license-key" placeholder="KEY-XXXXXX">
        <button onclick="activateLicense()">Lisansı Doğrula</button>
        <p id="lic-status" style="color: red;"></p>
    </div>

    <!-- ADIM 2: TELEGRAM HESAP BAĞLAMA -->
    <div id="step-auth" class="card hidden">
        <h3>2. Telegram Hesabını Bağla</h3>
        <p>Userbot'un çalışması için telefon numaranızı girin:</p>
        <input type="text" id="phone" placeholder="+905xxxxxxxxx">
        <button onclick="sendOtp()">Onay Kodu Gönder</button>
        
        <div id="otp-area" class="hidden">
            <input type="text" id="otp" placeholder="Telegram Onay Kodu (OTP)">
            <button onclick="verifyOtp()">Hesabı Bağla</button>
        </div>
    </div>

    <!-- ADIM 3: USERBOT KONTROL PANELİ -->
    <div id="step-bot" class="card hidden">
        <h3>3. Bot Kontrol Paneli</h3>
        <p style="color: #00ffcc;">Lisans: <span id="lic-type">-</span></p>
        
        <button onclick="fetchChats()">Sohbetleri & Grupları Getir</button>
        
        <div id="chats-list" style="margin-top: 10px;"></div>

        <hr style="border-color: #333; margin: 15px 0;">

        <h3>Mesaj Gönderici</h3>
        <textarea id="msg-text" rows="3" placeholder="Gönderilecek Mesaj..."></textarea>
        <input type="number" id="msg-count" placeholder="Kaç Adet Gönderilsin? (Örn: 5)">
        <input type="number" id="msg-delay" placeholder="Gecikme Süresi (Milisaniye / ms - Örn: 1000)">
        
        <button onclick="startSending()" style="background: #28a745;">Botu Başlat & Gönder</button>
        <p id="send-status" style="color: #00ffcc;"></p>
    </div>

    <script>
        let tg = window.Telegram.WebApp;
        tg.expand();

        function activateLicense() {
            let key = document.getElementById("license-key").value.trim();
            fetch('/api/activate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({key: key, user_id: tg.initDataUnsafe?.user?.id || "demo_user"})
            })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    document.getElementById("step-license").classList.add("hidden");
                    document.getElementById("step-auth").classList.remove("hidden");
                    document.getElementById("lic-type").innerText = data.type;
                } else {
                    document.getElementById("lic-status").innerText = data.message;
                }
            });
        }

        function sendOtp() {
            alert("Onay kodu Telegram hesabınıza gönderildi!");
            document.getElementById("otp-area").classList.remove("hidden");
        }

        function verifyOtp() {
            document.getElementById("step-auth").classList.add("hidden");
            document.getElementById("step-bot").classList.remove("hidden");
        }

        function fetchChats() {
            let list = document.getElementById("chats-list");
            list.innerHTML = `
                <div class="chat-item"><label><input type="checkbox" value="1"> Kripto Duyuru Grubu</label></div>
                <div class="chat-item"><label><input type="checkbox" value="2"> Sohbet & Muhabbet</label></div>
                <div class="chat-item"><label><input type="checkbox" value="3"> Userbot Destek Grubu</label></div>
            `;
        }

        function startSending() {
            let count = document.getElementById("msg-count").value;
            let delay = document.getElementById("msg-delay").value;
            document.getElementById("send-status").innerText = `Bot Başlatıldı! ${count} adet mesaj ${delay}ms aralıklarla gönderiliyor...`;
            tg.HapticFeedback.notificationOccurred("success");
        }
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/activate", methods=["POST"])
def activate():
    data = request.json
    key = data.get("key")
    user_id = data.get("user_id")

    if key in LICENSE_KEYS:
        if LICENSE_KEYS[key]["used"]:
            return jsonify({"success": False, "message": "Bu lisans anahtarı daha önce kullanılmış!"})
        
        LICENSE_KEYS[key]["used"] = True
        LICENSE_KEYS[key]["user_id"] = user_id
        
        key_type = "1 Aylık" if "KEY-1M" in key else "Kalıcı (Lifetime)"
        return jsonify({"success": True, "type": key_type})
    
    return jsonify({"success": False, "message": "Geçersiz Lisans Anahtarı!"})

def run_web():
    app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.start()
