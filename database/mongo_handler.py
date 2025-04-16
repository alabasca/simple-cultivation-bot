# database/mongo_handler.py
import motor.motor_asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
import asyncio
from bson import ObjectId
from modules.utils import mongo_utils
import certifi
import os
import logging
import sys
from dotenv import load_dotenv


class MongoDB:
    def __init__(self):
        # Load environment variables
        load_dotenv()

        # Get MongoDB credentials
        self.uri = os.getenv('MONGODB_URI')
        if not self.uri:
            raise ValueError("MONGODB_URI không tìm thấy trong .env")

        self.db_name = os.getenv('MONGODB_DB', 'tutien_bot')
        self._client = None
        self._db = None
        self.is_connected = False
        self.locks = {}
        self.connection_retries = 3
        self.retry_delay = 5

        # Thiết lập logging
        self.setup_logging()

    async def connect(self) -> bool:
        """Kết nối đến MongoDB với cơ chế retry"""
        # Kiểm tra URI trước khi kết nối
        if not self.uri:
            print("\n❌ Lỗi: MongoDB URI không được cung cấp")
            print("Kiểm tra biến MONGODB_URI trong tệp .env của bạn")
            raise ValueError("MongoDB URI không tìm thấy")

        if '@' not in self.uri:
            print("\n❌ Lỗi: MongoDB URI không hợp lệ")
            print("URI phải có định dạng: mongodb+srv://username:password@cluster.mongodb.net/")
            print("Kiểm tra biến MONGODB_URI trong tệp .env của bạn")
            raise ValueError("MongoDB URI không hợp lệ")

        for attempt in range(self.connection_retries):
            try:
                print(f"\n=== Test Kết Nối MongoDB ===")
                print(f"Đang kết nối MongoDB (Lần {attempt + 1}/{self.connection_retries})...")
                print(f"Database: {self.db_name}")

                # Kết nối với SSL và timeout
                self._client = motor.motor_asyncio.AsyncIOMotorClient(
                    self.uri,
                    tlsCAFile=certifi.where(),
                    serverSelectionTimeoutMS=5000,
                    retryWrites=True,
                    connectTimeoutMS=5000
                )

                # Kiểm tra kết nối
                await self._client.admin.command('ping')

                # Khởi tạo database và collections
                self._db = self._client[self.db_name]
                self.players = self._db.players
                self.combat_history = self._db.combat_history

                self.is_connected = True
                print("✓ Kết nối MongoDB thành công!")
                return True

            except Exception as e:
                print(f"\n❌ Lỗi kết nối MongoDB (Lần {attempt + 1}/{self.connection_retries})")
                print(f"Chi tiết lỗi: {str(e)}")

                if "bad auth" in str(e).lower():
                    print("\nLỗi xác thực! Kiểm tra:")
                    print("1. Username và password trong MongoDB URI là chính xác")
                    print("2. Database user có quyền read/write")
                    print("3. IP của bạn đã được whitelist")

                    # Hiển thị gợi ý cụ thể
                    print("\n❌ Lỗi: " + str(e))
                    print("Kiểm tra:")
                    print("1. Ký tự đặc biệt trong password - cần mã hóa URL (@ -> %40, etc.)")
                    print("2. Đối chiếu lại username/password trong MongoDB Atlas")
                    print("3. IP hiện tại của bạn cần được whitelist trong MongoDB Atlas")
                    print("4. Quyền hạn của người dùng trên database cụ thể")

                    # Không thử lại khi lỗi xác thực
                    raise ValueError("Lỗi xác thực MongoDB - Kiểm tra thông tin đăng nhập")

                if attempt < self.connection_retries - 1:
                    print(f"\nĐang thử lại sau {self.retry_delay} giây...")
                    await asyncio.sleep(self.retry_delay)
                else:
                    error_msg = "\nKhông thể kết nối sau nhiều lần thử. Kiểm tra:"
                    error_msg += "\n1. MongoDB URI trong .env là chính xác"
                    error_msg += "\n2. MongoDB Atlas cluster đang hoạt động"
                    error_msg += "\n3. Network connection ổn định"
                    error_msg += "\n4. IP đã được whitelist trong MongoDB Atlas"
                    print(error_msg)

                    # Log lỗi cho việc gỡ lỗi sau này
                    logging.error(f"Không thể kết nối MongoDB sau {self.connection_retries} lần thử: {str(e)}")
                    raise ConnectionError(error_msg)

    async def get_lock(self, user_id: int) -> asyncio.Lock:
        """Lấy lock cho người chơi để tránh race condition"""
        if user_id not in self.locks:
            self.locks[user_id] = asyncio.Lock()
        return self.locks[user_id]

    async def setup(self):
        """Khởi tạo kết nối và setup database"""
        if not self.is_connected:
            await self.connect()
        await self.setup_indexes()

    async def setup_indexes(self):
        """Thiết lập các index cần thiết cho hiệu suất truy vấn"""
        if not self.is_connected:
            await self.connect()

        try:
            # Index cho players collection
            await self.players.create_index("user_id", unique=True)
            await self.players.create_index([("exp", -1)])  # Descending for top players
            await self.players.create_index([
                ("sect", 1),
                ("exp", -1)
            ])  # Compound index for sect rankings

            # Index cho combat_history
            await self.combat_history.create_index([
                ("timestamp", -1),
                ("attacker_id", 1),
                ("defender_id", 1)
            ])

            # Thêm TTL index cho combat_history (tự động xóa sau 30 ngày)
            await self.combat_history.create_index(
                "timestamp",
                expireAfterSeconds=30 * 24 * 60 * 60
            )

            print("✓ Đã tạo indexes thành công!")

        except Exception as e:
            print(f"❌ Lỗi khi tạo indexes: {e}")
            raise

    async def get_player(self, user_id: int) -> Optional[Dict]:
        """Lấy thông tin người chơi từ database"""
        if not self.is_connected:
            await self.connect()

        try:
            player = await self.players.find_one({"user_id": user_id})
            if player:
                return await mongo_utils.prepare_from_mongo(player)
            return None
        except Exception as e:
            print(f"❌ Lỗi khi lấy thông tin người chơi {user_id}: {e}")
            return None

    async def create_player(self, user_id: int, sect: str) -> bool:
        """Tạo người chơi mới với dữ liệu ban đầu"""
        if not self.is_connected:
            await self.connect()

        try:
            current_time = datetime.now()
            player_data = {
                "user_id": user_id,
                "level": "Phàm Nhân",
                "exp": 0,
                "sect": sect,
                "hp": 100,
                "attack": 10,
                "defense": 5,
                "last_train": current_time,
                "last_monster": current_time,
                "last_boss": current_time,
                "last_daily": current_time,
                "daily_streak": 0,
                "created_at": current_time,
                "updated_at": current_time,
                "stats": {
                    "monsters_killed": 0,
                    "bosses_killed": 0,
                    "pvp_wins": 0,
                    "pvp_losses": 0,
                    "total_exp_gained": 0
                }
            }

            await self.players.insert_one(
                await mongo_utils.prepare_for_mongo(player_data)
            )
            return True
        except Exception as e:
            print(f"❌ Lỗi khi tạo người chơi {user_id}: {e}")
            return False

    async def update_player(self, user_id: int, **kwargs) -> bool:
        """Cập nhật thông tin người chơi với khóa để tránh xung đột"""
        if not self.is_connected:
            await self.connect()

        try:
            async with await self.get_lock(user_id):
                update_data = await mongo_utils.prepare_for_mongo(kwargs)
                update_data['updated_at'] = datetime.now()

                result = await self.players.update_one(
                    {"user_id": user_id},
                    {"$set": update_data}
                )
                return result.modified_count > 0
        except Exception as e:
            print(f"❌ Lỗi khi cập nhật người chơi {user_id}: {e}")
            return False

    async def increment_player_stats(self, user_id: int, **stats) -> bool:
        """Tăng các chỉ số thống kê của người chơi"""
        if not self.is_connected:
            await self.connect()

        try:
            async with await self.get_lock(user_id):
                update_data = {f"stats.{k}": v for k, v in stats.items()}
                result = await self.players.update_one(
                    {"user_id": user_id},
                    {"$inc": update_data}
                )
                return result.modified_count > 0
        except Exception as e:
            print(f"❌ Lỗi khi tăng chỉ số người chơi {user_id}: {e}")
            return False

    async def get_player_ranking(self, limit: int = 10) -> List[Dict]:
        """Lấy xếp hạng người chơi dựa trên exp"""
        if not self.is_connected:
            await self.connect()

        try:
            cursor = self.players.find().sort("exp", -1).limit(limit)
            players = await cursor.to_list(length=limit)
            return [await mongo_utils.prepare_from_mongo(player) for player in players]
        except Exception as e:
            print(f"❌ Lỗi khi lấy xếp hạng người chơi: {e}")
            return []

    async def get_sect_ranking(self, sect: str, limit: int = 10) -> List[Dict]:
        """Lấy xếp hạng người chơi trong môn phái"""
        if not self.is_connected:
            await self.connect()

        try:
            cursor = self.players.find({"sect": sect}).sort("exp", -1).limit(limit)
            players = await cursor.to_list(length=limit)
            return [await mongo_utils.prepare_from_mongo(player) for player in players]
        except Exception as e:
            print(f"❌ Lỗi khi lấy xếp hạng môn phái {sect}: {e}")
            return []

    async def add_combat_history(self, attacker_id: int, defender_id: int,
                                 result: str, exp_gained: int = 0) -> bool:
        """Thêm lịch sử đánh nhau giữa người chơi"""
        if not self.is_connected:
            await self.connect()

        try:
            combat_data = {
                "attacker_id": attacker_id,
                "defender_id": defender_id,
                "result": result,
                "exp_gained": exp_gained,
                "timestamp": datetime.now()
            }

            await self.combat_history.insert_one(
                await mongo_utils.prepare_for_mongo(combat_data)
            )
            return True
        except Exception as e:
            print(f"❌ Lỗi khi thêm lịch sử đánh nhau: {e}")
            return False

    async def get_combat_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Lấy lịch sử đánh nhau của người chơi"""
        if not self.is_connected:
            await self.connect()

        try:
            # Tìm các trận đấu mà người chơi tham gia như là người tấn công hoặc phòng thủ
            query = {"$or": [
                {"attacker_id": user_id},
                {"defender_id": user_id}
            ]}

            cursor = self.combat_history.find(query).sort("timestamp", -1).limit(limit)
            history = await cursor.to_list(length=limit)
            return [await mongo_utils.prepare_from_mongo(item) for item in history]
        except Exception as e:
            print(f"❌ Lỗi khi lấy lịch sử đánh nhau của người chơi {user_id}: {e}")
            return []

    def setup_logging(self):
        """Thiết lập logging cho MongoDB handler"""
        try:
            # Tạo thư mục logs nếu chưa tồn tại
            log_dir = "logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)

            # Thiết lập logging
            log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            logging.basicConfig(
                level=logging.INFO,
                format=log_format,
                handlers=[
                    logging.FileHandler(f"{log_dir}/mongodb.log"),
                    logging.StreamHandler(sys.stdout)
                ]
            )
        except Exception as e:
            print(f"❌ Lỗi thiết lập logging: {e}")

    async def test_connection(self) -> Dict[str, Any]:
        """Kiểm tra kết nối và trả về thông tin chi tiết"""
        if not self.is_connected:
            try:
                await self.connect()
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "details": "Không thể kết nối đến MongoDB"
                }

        try:
            # Kiểm tra ping
            start_time = datetime.now()
            await self._client.admin.command('ping')
            ping_time = (datetime.now() - start_time).total_seconds() * 1000

            # Lấy thông tin server
            server_info = await self._client.admin.command('serverStatus')

            return {
                "success": True,
                "database": self.db_name,
                "ping_ms": round(ping_time, 2),
                "server_version": server_info.get("version", "Unknown"),
                "connection_count": server_info.get("connections", {}).get("current", 0)
            }
        except Exception as e:
            logging.error(f"Lỗi khi kiểm tra kết nối: {e}")
            return {
                "success": False,
                "error": str(e),
                "details": "Kết nối không ổn định"
            }

    async def close(self):
        """Đóng kết nối database an toàn"""
        if self._client:
            self._client.close()
            self.is_connected = False
            logging.info("Đã đóng kết nối MongoDB an toàn")
            print("✓ Đã đóng kết nối MongoDB an toàn")