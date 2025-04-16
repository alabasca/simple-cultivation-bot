# mongodb_test.py
import motor.motor_asyncio
import certifi
import asyncio
import os
import urllib.parse
from dotenv import load_dotenv
import sys


# Hàm URL-encode username và password từ URI
def encode_credentials_in_uri(uri):
    if not uri or '@' not in uri:
        return uri

    # Chia URI thành các phần để mã hóa username và password
    try:
        prefix, rest = uri.split('://', 1)
        credentials_host, db_part = rest.split('@', 1)

        if ':' in credentials_host:
            username, password = credentials_host.split(':', 1)

            # Mã hóa username và password
            encoded_username = urllib.parse.quote_plus(username)
            encoded_password = urllib.parse.quote_plus(password)

            # Nếu username/password đã thay đổi, cập nhật URI
            if username != encoded_username or password != encoded_password:
                new_uri = f"{prefix}://{encoded_username}:{encoded_password}@{db_part}"
                print(f"URI đã được mã hóa. Ký tự đặc biệt đã được xử lý.")
                return new_uri
    except Exception as e:
        print(f"Lỗi khi mã hóa URI: {e}")

    # Trả về URI gốc nếu không có thay đổi hoặc có lỗi
    return uri


async def test_mongodb_connection(uri=None, db_name=None):
    # Nạp biến môi trường từ file .env
    load_dotenv()

    # Sử dụng tham số hoặc lấy từ biến môi trường
    uri = uri or os.getenv('MONGODB_URI')
    db_name = db_name or os.getenv('MONGODB_DB', 'tutien_bot')

    if not uri:
        print("❌ Không tìm thấy MongoDB URI!")
        print("Vui lòng cung cấp URI qua tham số hoặc trong tệp .env")
        return False

    # Mã hóa URI nếu cần
    encoded_uri = encode_credentials_in_uri(uri)
    if encoded_uri != uri:
        print(f"Đã phát hiện và mã hóa ký tự đặc biệt trong URI")
        uri = encoded_uri

    print("\n=== TEST KẾT NỐI MONGODB ===")
    print(f"Database: {db_name}")
    print("URI format check:", "✓ Hợp lệ" if '@' in uri else "❌ Không hợp lệ")

    try:
        # Kết nối với timeout ngắn để kiểm tra nhanh
        client = motor.motor_asyncio.AsyncIOMotorClient(
            uri,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )

        print("\nĐang kiểm tra kết nối đến server...")
        await client.admin.command('ping')
        print("✓ Kết nối đến MongoDB server thành công!")

        print("\nĐang kiểm tra quyền truy cập database...")
        db = client[db_name]
        collections = await db.list_collection_names()
        print(f"✓ Truy cập database '{db_name}' thành công!")
        print(f"✓ Số lượng collections: {len(collections)}")
        if collections:
            print(f"✓ Collections: {', '.join(collections)}")
        else:
            print("ℹ️ Database chưa có collection nào")

        print("\nĐang kiểm tra quyền ghi...")
        try:
            # Tạo collection test
            test_collection = 'test_connection'
            await db.create_collection(test_collection)
            print(f"✓ Tạo collection '{test_collection}' thành công!")

            # Thêm document test
            test_doc = {"test": "connection", "timestamp": "test"}
            result = await db[test_collection].insert_one(test_doc)
            print(f"✓ Thêm document vào '{test_collection}' thành công!")

            # Xóa collection test
            await db.drop_collection(test_collection)
            print(f"✓ Xóa collection '{test_collection}' thành công!")
        except Exception as e:
            print(f"❌ Lỗi khi thử quyền ghi: {str(e)}")
            print("❗ Người dùng có thể không có quyền ghi trên database này")

        print("\n=== KẾT QUẢ KIỂM TRA ===")
        print("✅ Kết nối MongoDB thành công!")
        print("✅ Xác thực người dùng OK")
        print("✅ Quyền truy cập database OK")

        # Thêm gợi ý cho .env
        print("\n=== THÔNG TIN CHO .ENV ===")
        # Loại bỏ thông tin nhạy cảm khi hiển thị
        masked_uri = uri.replace(uri.split('@')[0], "mongodb+srv://****:****")
        print(f"MONGODB_URI={masked_uri}")
        print(f"MONGODB_DB={db_name}")

        return True

    except Exception as e:
        print(f"\n❌ Lỗi kết nối: {str(e)}")

        if "bad auth" in str(e).lower():
            print("\n=== LỖI XÁC THỰC ===")
            print("1. Kiểm tra username và password trong URI")
            print("2. Đảm bảo người dùng có quyền trên database này")
            print("3. Kiểm tra IP hiện tại đã được whitelist")

        elif "No servers found" in str(e):
            print("\n=== LỖI KẾT NỐI ===")
            print("1. Kiểm tra tên cluster trong URI")
            print("2. Đảm bảo kết nối internet ổn định")
            print("3. Kiểm tra cluster MongoDB Atlas đang hoạt động")

        print("\n=== KIỂM TRA MONGODB ATLAS ===")
        print("1. Đăng nhập vào dashboard MongoDB Atlas")
        print("2. Vào mục 'Database Access' - kiểm tra người dùng")
        print("3. Vào mục 'Network Access' - thêm IP hiện tại")
        print("4. Vào mục 'Databases' - lấy connection string mới")

        return False
    finally:
        if 'client' in locals():
            client.close()


# Chạy chương trình nếu được gọi trực tiếp
if __name__ == "__main__":
    # Cho phép truyền URI từ command line
    uri = sys.argv[1] if len(sys.argv) > 1 else None
    db_name = sys.argv[2] if len(sys.argv) > 2 else None

    asyncio.run(test_mongodb_connection(uri, db_name))