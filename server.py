import os
import requests
from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime
from PIL import Image

BOT_TOKEN = "8766614802:AAEFEF8EkszbjcvAIjGT8m0GHCfEQK6Cwe4"
ADMIN_ID = 6426208853

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__, static_folder="static", static_url_path="/static")


def compress_image(path):
    try:
        img = Image.open(path)
        img.thumbnail((1280, 1280))

        base, _ = os.path.splitext(path)
        compressed_path = base + "_compressed.jpg"

        img.convert("RGB").save(
            compressed_path,
            "JPEG",
            quality=70,
            optimize=True
        )

        return compressed_path
    except Exception:
        return path


def telegram_send_message(text: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(
        url,
        json={
            "chat_id": ADMIN_ID,
            "text": text
        },
        timeout=30
    )


def telegram_send_photo(filepath: str, caption: str = ""):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    compressed_path = compress_image(filepath)

    with open(compressed_path, "rb") as f:
        requests.post(
            url,
            data={
                "chat_id": ADMIN_ID,
                "caption": caption
            },
            files={
                "photo": f
            },
            timeout=30
        )


@app.route("/")
def root():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/index.html")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/submit", methods=["POST"])
def submit():
    try:
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        city = request.form.get("city", "").strip()
        citizenship = request.form.get("citizenship", "").strip()
        job = request.form.get("job", "").strip()
        license_country = request.form.get("license_country", "").strip() or "Не требуется"
        car = request.form.get("car", "").strip() or "Не требуется"
        price = request.form.get("price", "").strip() or "Не требуется"
        comment = request.form.get("comment", "").strip() or "Нет"

        if job == "Водитель (на своей машине)":
            registration_phone = request.form.get("registration_phone", "").strip() or "Не указано"
        else:
            registration_phone = "Не требуется"

        tg_user_id = request.form.get("tg_user_id", "").strip()
        tg_username = request.form.get("tg_username", "").strip() or "нет"
        tg_full_name = request.form.get("tg_full_name", "").strip() or "Не указано"

        if not name or not phone or not city or not citizenship or not job:
            return jsonify({"ok": False, "error": "Заполните обязательные поля"}), 400

        passport_front = request.files.get("passport_front")
        passport_registration = request.files.get("passport_registration")

        driver_license_front = request.files.get("driver_license_front")
        driver_license_back = request.files.get("driver_license_back")

        sts_front = request.files.get("sts_front")
        sts_back = request.files.get("sts_back")
        own_driver_license_front = request.files.get("own_driver_license_front")
        own_driver_license_back = request.files.get("own_driver_license_back")

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        safe_name = name.replace(" ", "_")
        safe_phone = phone.replace("+", "").replace(" ", "").replace("-", "")

        user_folder = f"{safe_name}_{safe_phone}_{timestamp}"
        user_path = os.path.join(UPLOAD_DIR, user_folder)
        os.makedirs(user_path, exist_ok=True)

        def save_file(file_storage, filename):
            if not file_storage:
                return None

            ext = os.path.splitext(file_storage.filename)[1] or ".jpg"
            path = os.path.join(user_path, f"{filename}{ext}")
            file_storage.save(path)
            return path

        passport_front_path = save_file(passport_front, "passport_front")
        passport_registration_path = save_file(passport_registration, "passport_registration")

        driver_license_front_path = None
        driver_license_back_path = None
        sts_front_path = None
        sts_back_path = None
        own_driver_license_front_path = None
        own_driver_license_back_path = None

        if job == "Водитель (Аренда)":
            driver_license_front_path = save_file(driver_license_front, "driver_license_front")
            driver_license_back_path = save_file(driver_license_back, "driver_license_back")

        if job == "Водитель (на своей машине)":
            sts_front_path = save_file(sts_front, "sts_front")
            sts_back_path = save_file(sts_back, "sts_back")
            own_driver_license_front_path = save_file(own_driver_license_front, "own_driver_license_front")
            own_driver_license_back_path = save_file(own_driver_license_back, "own_driver_license_back")

        text = (
            "📥 НОВАЯ ЗАЯВКА ИЗ MINI APP\n\n"
            f"👤 Имя: {name}\n"
            f"📱 Телефон: {phone}\n"
            f"{f'📞 Номер для регистрации: {registration_phone}\\n' if job == 'Водитель (на своей машине)' else ''}"
            f"🏙 Город: {city}\n"
            f"🌍 Гражданство: {citizenship}\n"
            f"💼 Направление: {job}\n"
            f"{f'🪪 Страна водительского удостоверения: {license_country}\\n' if job == 'Водитель (Аренда)' else ''}"
            f"🚗 Автомобиль: {car}\n"
            f"{f'💰 Стоимость: {price}\\n' if job != 'Водитель (на своей машине)' else ''}"
            f"💬 Комментарий: {comment}\n\n"
            f"👤 Username: @{tg_username}\n"
            f"🆔 Telegram ID: {tg_user_id if tg_user_id else 'не передан'}\n"
            f"📛 Имя в Telegram: {tg_full_name}\n\n"
            f"📁 Папка с файлами: {user_folder}"
        )

        telegram_send_message(text)

        files_to_send = [
            (passport_front_path, "Паспорт — лицевая сторона"),
            (passport_registration_path, "Паспорт — прописка"),
        ]

        if job == "Водитель (Аренда)":
            files_to_send.extend([
                (driver_license_front_path, "Права — лицевая сторона"),
                (driver_license_back_path, "Права — обратная сторона"),
            ])

        if job == "Водитель (на своей машине)":
            files_to_send.extend([
                (sts_front_path, "СТС — лицевая сторона"),
                (sts_back_path, "СТС — обратная сторона"),
                (own_driver_license_front_path, "Права — лицевая сторона"),
                (own_driver_license_back_path, "Права — обратная сторона"),
            ])

        for path, caption in files_to_send:
            if path:
                telegram_send_photo(path, f"{caption}\n{name}")

        return jsonify({
            "ok": True,
            "message": "Заявка успешно отправлена"
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
    app.run(host="0.0.0.0", port=port)
