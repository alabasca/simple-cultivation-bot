# check_uri.py
from dotenv import load_dotenv
import os
import time


def check_mongodb_uri():
    print("\n=== Kiểm tra MongoDB URI ===\n")

    # Load .env
    load_dotenv()
    uri = os.getenv('MONGODB_URI')

    if not uri:
        print("❌ Không tìm thấy MONGODB_URI trong file .env")
        return False

    print("URI gốc:")
    print(uri)
    print("\nKiểm tra format URI...")

    # Kiểm tra các phần của URI
    try:
        # Tách các phần của URI
        if not uri.startswith('mongodb+srv://'):
            print("❌ URI phải bắt đầu với 'mongodb+srv://'")
            return False

        # Tách username và password
        auth_part = uri.split('mongodb+srv://')[1].split('@')[0]
        if ':' not in auth_part:
            print("❌ Thiếu username hoặc password")
            return False

        username, password = auth_part.split(':')
        print(f"✓ Username: {username}")
        print(f"✓ Password: {'*' * len(password)}")

        # Tách cluster
        cluster_part = uri.split('@')[1].split('/?')[0]
        print(f"✓ Cluster: {cluster_part}")

        # Kiểm tra parameters
        if '?' in uri:
            params = uri.split('?')[1]
            print(f"✓ Parameters: {params}")

            # Kiểm tra trùng lặp parameters
            if params.count('retryWrites=true') > 1:
                print("❌ Parameters bị trùng lặp!")
                return False

        print("\n✅ URI format hợp lệ!")

        # Tạo URI chuẩn
        standard_uri = f"mongodb+srv://{username}:{password}@{cluster_part}/?retryWrites=true&w=majority"
        print("\nURI chuẩn (copy vào .env):")
        print(standard_uri)

        return True

    except Exception as e:
        print(f"\n❌ Lỗi khi parse URI: {str(e)}")
        return False


if __name__ == "__main__":
    check_mongodb_uri()
    print("\nĐóng sau 30 giây...")
    time.sleep(30)
