# config_check.py
import os
from dotenv import load_dotenv


def check_config():
    """Kiểm tra và hiển thị thông tin cấu hình"""
    print("=== KIỂM TRA CẤU HÌNH ===")

    # Kiểm tra tệp .env
    env_exists = os.path.exists(".env")
    print(f"Tệp .env tồn tại: {'✓' if env_exists else '❌'}")

    if not env_exists:
        print("Tạo tệp .env mới với mẫu cơ bản...")
        with open(".env", "w", encoding="utf-8") as f:
            f.write("""# Cấu hình MongoDB
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB=tutien_bot

# Thông tin Bot
BOT_TOKEN=your_discord_bot_token_here
BOT_PREFIX=!
""")
        print("✓ Đã tạo tệp .env. Vui lòng điều chỉnh thông tin kết nối.")

    # Nạp biến môi trường
    load_dotenv()

    # Kiểm tra các biến cấu hình MongoDB
    mongodb_uri = os.getenv("MONGODB_URI")
    mongodb_db = os.getenv("MONGODB_DB")

    print(f"MONGODB_URI được cấu hình: {'✓' if mongodb_uri else '❌'}")
    if mongodb_uri:
        # Hiển thị URI đã che dấu thông tin nhạy cảm
        if '@' in mongodb_uri:
            prefix, rest = mongodb_uri.split('@', 1)
            masked_uri = f"mongodb+srv://****:****@{rest}"
            print(f"MONGODB_URI: {masked_uri}")
        else:
            print("❌ MONGODB_URI không đúng định dạng!")
    else:
        print("❌ MONGODB_URI chưa được cấu hình trong .env")

    print(f"MONGODB_DB được cấu hình: {'✓' if mongodb_db else '❌'}")
    if mongodb_db:
        print(f"MONGODB_DB: {mongodb_db}")
    else:
        print("❌ MONGODB_DB chưa được cấu hình trong .env")

    # Kiểm tra file config.py
    try:
        with open("config.py", "r", encoding="utf-8") as f:
            config_content = f.read()

        print("\n=== KIỂM TRA CONFIG.PY ===")

        # Kiểm tra xem có đoạn kiểm tra MongoDB không
        if "Missing MongoDB configuration" in config_content:
            print("✓ File config.py có kiểm tra cấu hình MongoDB")
            print("  Trích đoạn code:")

            # Tìm đoạn code liên quan
            lines = config_content.split('\n')
            for i, line in enumerate(lines):
                if "Missing MongoDB configuration" in line:
                    start = max(0, i - 5)
                    end = min(len(lines), i + 2)
                    print("\n".join(lines[start:end]))
        else:
            print("❓ Không tìm thấy kiểm tra MongoDB trong config.py")

    except FileNotFoundError:
        print("\n❌ Không tìm thấy file config.py")

    print("\n=== HƯỚNG DẪN KHẮC PHỤC ===")
    if not mongodb_uri or not mongodb_db:
        print("1. Mở file .env và cập nhật các thông tin sau:")
        print("   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority")
        print("   MONGODB_DB=tutien_bot")
        print("2. Thay thế username, password và cluster bằng thông tin MongoDB Atlas của bạn")
    else:
        print("1. Kiểm tra lại thông tin kết nối MongoDB trong .env")
        print("2. Đảm bảo username và password chính xác")
        print("3. Kiểm tra Whitelist IP trong MongoDB Atlas")


if __name__ == "__main__":
    check_config()