from datetime import datetime, timedelta
import asyncio
from typing import Union, Optional, Dict, Any, List, Tuple, Callable
import re
import math
import random
from bson import ObjectId
import json
import unicodedata
import string


class TimeFormatter:
    """Các phương thức xử lý và định dạng thời gian"""

    @staticmethod
    def format_time(seconds: int) -> str:
        """Chuyển đổi số giây thành định dạng phút:giây"""
        if seconds < 0:
            return "0 giây"

        days = seconds // 86400
        seconds %= 86400
        hours = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60

        parts = []
        if days > 0:
            parts.append(f"{days} ngày")
        if hours > 0:
            parts.append(f"{hours} giờ")
        if minutes > 0:
            parts.append(f"{minutes} phút")
        if seconds > 0 or not parts:
            parts.append(f"{seconds} giây")

        return " ".join(parts)

    @staticmethod
    async def format_time_async(seconds: int) -> str:
        """Phiên bản bất đồng bộ của format_time"""
        return TimeFormatter.format_time(seconds)

    @staticmethod
    def format_duration(duration: timedelta) -> str:
        """Định dạng timedelta thành chuỗi dễ đọc"""
        return TimeFormatter.format_time(int(duration.total_seconds()))

    @staticmethod
    async def format_duration_async(duration: timedelta) -> str:
        """Phiên bản bất đồng bộ của format_duration"""
        return TimeFormatter.format_duration(duration)

    @staticmethod
    def get_time_from_db(time_str: Optional[str]) -> datetime:
        """Chuyển đổi chuỗi thời gian từ database thành đối tượng datetime"""
        if not time_str:
            return datetime.now()

        try:
            return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                return datetime.fromisoformat(time_str)
            except ValueError:
                return datetime.now()

    @staticmethod
    async def get_time_from_db_async(time_str: Optional[str]) -> datetime:
        """Phiên bản bất đồng bộ của get_time_from_db"""
        return TimeFormatter.get_time_from_db(time_str)

    @staticmethod
    def time_until(target_time: datetime) -> timedelta:
        """Tính thời gian còn lại đến một thời điểm cụ thể"""
        now = datetime.now()
        if target_time <= now:
            return timedelta(0)
        return target_time - now

    @staticmethod
    def time_since(past_time: datetime) -> timedelta:
        """Tính thời gian đã trôi qua từ một thời điểm trong quá khứ"""
        now = datetime.now()
        if past_time >= now:
            return timedelta(0)
        return now - past_time

    @staticmethod
    def format_relative_time(dt: datetime) -> str:
        """Định dạng thời gian tương đối (ví dụ: '5 phút trước', '2 giờ nữa')"""
        now = datetime.now()
        diff = (now - dt).total_seconds() if dt < now else (dt - now).total_seconds()

        if dt < now:
            if diff < 60:
                return "vừa xong"
            elif diff < 3600:
                minutes = int(diff // 60)
                return f"{minutes} phút trước"
            elif diff < 86400:
                hours = int(diff // 3600)
                return f"{hours} giờ trước"
            elif diff < 604800:  # 7 days
                days = int(diff // 86400)
                return f"{days} ngày trước"
            else:
                return dt.strftime("%d/%m/%Y")
        else:
            if diff < 60:
                return "sắp tới"
            elif diff < 3600:
                minutes = int(diff // 60)
                return f"{minutes} phút nữa"
            elif diff < 86400:
                hours = int(diff // 3600)
                return f"{hours} giờ nữa"
            elif diff < 604800:  # 7 days
                days = int(diff // 86400)
                return f"{days} ngày nữa"
            else:
                return dt.strftime("%d/%m/%Y")


class ExpFormatter:
    """Các phương thức xử lý và định dạng kinh nghiệm"""

    @staticmethod
    def format_exp(exp: int) -> str:
        """Định dạng số exp để dễ đọc"""
        if exp >= 1000000000:
            return f"{exp / 1000000000:.1f}B"
        elif exp >= 1000000:
            return f"{exp / 1000000:.1f}M"
        elif exp >= 1000:
            return f"{exp / 1000:.1f}K"
        return f"{exp}"

    @staticmethod
    async def format_exp_async(exp: int) -> str:
        """Phiên bản bất đồng bộ của format_exp"""
        return ExpFormatter.format_exp(exp)

    @staticmethod
    def parse_exp_string(exp_str: str) -> int:
        """Chuyển đổi chuỗi exp (như '1.5K', '2M') thành số nguyên"""
        exp_str = exp_str.upper().strip()
        multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000}

        match = re.match(r'^(\d+\.?\d*)([KMB])?$', exp_str)
        if not match:
            raise ValueError(f"Định dạng exp không hợp lệ: {exp_str}")

        number = float(match.group(1))
        multiplier = multipliers.get(match.group(2), 1)
        return int(number * multiplier)

    @staticmethod
    async def parse_exp_string_async(exp_str: str) -> int:
        """Phiên bản bất đồng bộ của parse_exp_string"""
        return ExpFormatter.parse_exp_string(exp_str)

    @staticmethod
    def calculate_exp_needed(current_level: int, target_level: int, base_exp: int = 100,
                             multiplier: float = 1.5) -> int:
        """Tính toán lượng exp cần thiết để đạt từ level hiện tại đến level mục tiêu"""
        if target_level <= current_level:
            return 0

        total_exp = 0
        for level in range(current_level, target_level):
            level_exp = int(base_exp * (multiplier ** level))
            total_exp += level_exp

        return total_exp

    @staticmethod
    def calculate_level_from_exp(exp: int, base_exp: int = 100, multiplier: float = 1.5) -> Tuple[int, int]:
        """Tính toán level dựa trên tổng exp, trả về (level, exp_còn_lại)"""
        if exp < base_exp:
            return 1, exp

        level = 1
        exp_needed = base_exp

        while exp >= exp_needed:
            exp -= exp_needed
            level += 1
            exp_needed = int(base_exp * (multiplier ** (level - 1)))

        return level, exp


class MongoUtils:
    """Các phương thức tiện ích cho MongoDB"""

    @staticmethod
    def convert_id(id_: Union[str, ObjectId]) -> ObjectId:
        """Chuyển đổi ID dạng chuỗi thành ObjectId"""
        if isinstance(id_, str):
            return ObjectId(id_)
        return id_

    @staticmethod
    def prepare_for_mongo(data: Dict[str, Any]) -> Dict[str, Any]:
        """Chuẩn bị dữ liệu để lưu vào MongoDB"""
        cleaned = {}
        for key, value in data.items():
            if isinstance(value, datetime):
                cleaned[key] = value.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(value, ObjectId):
                cleaned[key] = str(value)
            elif isinstance(value, dict):
                cleaned[key] = MongoUtils.prepare_for_mongo(value)
            elif isinstance(value, list):
                cleaned[key] = [
                    MongoUtils.prepare_for_mongo(item)
                    if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                cleaned[key] = value
        return cleaned

    @staticmethod
    async def prepare_for_mongo_async(data: Dict[str, Any]) -> Dict[str, Any]:
        """Phiên bản bất đồng bộ của prepare_for_mongo"""
        return MongoUtils.prepare_for_mongo(data)

    @staticmethod
    def prepare_from_mongo(data: Dict[str, Any]) -> Dict[str, Any]:
        """Chuyển đổi dữ liệu từ MongoDB thành dạng Python thích hợp"""
        converted = {}
        for key, value in data.items():
            if isinstance(value, str) and re.match(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', value):
                try:
                    converted[key] = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                    continue
                except ValueError:
                    pass
            if isinstance(value, dict):
                converted[key] = MongoUtils.prepare_from_mongo(value)
            elif isinstance(value, list):
                converted[key] = [
                    MongoUtils.prepare_from_mongo(item)
                    if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                converted[key] = value
        return converted

    @staticmethod
    async def prepare_from_mongo_async(data: Dict[str, Any]) -> Dict[str, Any]:
        """Phiên bản bất đồng bộ của prepare_from_mongo"""
        return MongoUtils.prepare_from_mongo(data)

    @staticmethod
    def update_nested_dict(original: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Cập nhật từ điển lồng nhau, hỗ trợ ký hiệu dấu chấm (ví dụ: 'stats.hp')"""
        result = original.copy()

        for key, value in updates.items():
            if "__" in key:  # Ký hiệu đặc biệt cho các trường lồng nhau
                parts = key.split("__")
                current = result
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    elif not isinstance(current[part], dict):
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value
            else:
                result[key] = value

        return result


class TextUtils:
    """Các phương thức xử lý và định dạng văn bản"""

    @staticmethod
    def create_progress_bar(current: float, maximum: float, length: int = 20, filled_char: str = '█',
                            empty_char: str = '░') -> str:
        """Tạo thanh tiến trình trực quan"""
        if maximum <= 0:
            percent = 0
        else:
            percent = min(1.0, current / maximum)

        filled_length = int(length * percent)
        bar = filled_char * filled_length + empty_char * (length - filled_length)
        return f"[{bar}] {percent:.1%}"

    @staticmethod
    async def create_progress_bar_async(current: float, maximum: float, length: int = 20, filled_char: str = '█',
                                        empty_char: str = '░') -> str:
        """Phiên bản bất đồng bộ của create_progress_bar"""
        return TextUtils.create_progress_bar(current, maximum, length, filled_char, empty_char)

    @staticmethod
    def create_hp_bar(current: float, maximum: float, length: int = 10) -> str:
        """Tạo thanh HP với màu sắc dựa trên phần trăm"""
        percent = current / maximum if maximum > 0 else 0

        if percent > 0.7:  # >70% HP: xanh lá
            filled_char = '🟩'
        elif percent > 0.3:  # 30-70% HP: vàng
            filled_char = '🟨'
        else:  # <30% HP: đỏ
            filled_char = '🟥'

        empty_char = '⬜'
        filled_length = int(length * percent)
        bar = filled_char * filled_length + empty_char * (length - filled_length)

        return f"{bar} {percent:.1%}"

    @staticmethod
    def truncate_string(text: str, max_length: int = 100, ellipsis: str = "...") -> str:
        """Cắt ngắn chuỗi và thêm dấu chấm lửng nếu cần"""
        if not text:
            return ""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(ellipsis)] + ellipsis

    @staticmethod
    async def truncate_string_async(text: str, max_length: int = 100, ellipsis: str = "...") -> str:
        """Phiên bản bất đồng bộ của truncate_string"""
        return TextUtils.truncate_string(text, max_length, ellipsis)

    @staticmethod
    def format_number(number: Union[int, float], decimal_places: int = 0) -> str:
        """Định dạng số với dấu phân cách hàng nghìn"""
        if decimal_places > 0:
            return f"{number:,.{decimal_places}f}"
        return f"{number:,}"

    @staticmethod
    async def format_number_async(number: Union[int, float], decimal_places: int = 0) -> str:
        """Phiên bản bất đồng bộ của format_number"""
        return TextUtils.format_number(number, decimal_places)

    @staticmethod
    def normalize_text(text: str) -> str:
        """Chuẩn hóa văn bản (loại bỏ dấu, chuyển thành chữ thường)"""
        # Chuyển về Unicode NFD để tách dấu
        text = unicodedata.normalize('NFD', text)
        # Loại bỏ các ký tự dấu
        text = ''.join(c for c in text if not unicodedata.combining(c))
        # Chuyển về chữ thường
        text = text.lower()
        return text

    @staticmethod
    def calculate_similarity(s1: str, s2: str) -> float:
        """Tính độ tương đồng giữa hai chuỗi (Levenshtein distance)"""
        # Chuẩn hóa chuỗi
        s1 = TextUtils.normalize_text(s1)
        s2 = TextUtils.normalize_text(s2)

        # Đảm bảo s1 là chuỗi dài hơn
        if len(s1) < len(s2):
            s1, s2 = s2, s1

        # Nếu một trong hai chuỗi rỗng
        if len(s2) == 0:
            return 0.0 if len(s1) > 0 else 1.0

        # Tính khoảng cách Levenshtein
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        # Tính độ tương đồng (0-1)
        distance = previous_row[-1]
        max_len = max(len(s1), len(s2))
        return 1 - (distance / max_len)


class RandomUtils:
    """Các phương thức ngẫu nhiên hữu ích"""

    @staticmethod
    def weighted_choice(choices: List[Any], weights: List[float]) -> Any:
        """Chọn một phần tử ngẫu nhiên dựa trên trọng số"""
        if len(choices) != len(weights):
            raise ValueError("Số lượng lựa chọn và trọng số phải bằng nhau")

        total = sum(weights)
        r = random.uniform(0, total)
        upto = 0

        for i, w in enumerate(weights):
            upto += w
            if upto >= r:
                return choices[i]

        # Fallback nếu có lỗi làm tròn
        return choices[-1]

    @staticmethod
    async def weighted_choice_async(choices: List[Any], weights: List[float]) -> Any:
        """Phiên bản bất đồng bộ của weighted_choice"""
        return RandomUtils.weighted_choice(choices, weights)

    @staticmethod
    def chance(probability: float) -> bool:
        """Kiểm tra xem một sự kiện có xảy ra không dựa trên xác suất (0-1)"""
        return random.random() < probability

    @staticmethod
    def random_range(min_val: float, max_val: float) -> float:
        """Tạo số ngẫu nhiên trong khoảng [min_val, max_val]"""
        return min_val + random.random() * (max_val - min_val)

    @staticmethod
    def random_int_range(min_val: int, max_val: int) -> int:
        """Tạo số nguyên ngẫu nhiên trong khoảng [min_val, max_val]"""
        return random.randint(min_val, max_val)

    @staticmethod
    def random_element(elements: List[Any]) -> Any:
        """Chọn một phần tử ngẫu nhiên từ danh sách"""
        if not elements:
            return None
        return random.choice(elements)

    @staticmethod
    def random_elements(elements: List[Any], count: int, unique: bool = True) -> List[Any]:
        """Chọn nhiều phần tử ngẫu nhiên từ danh sách"""
        if not elements:
            return []

        if unique:
            # Đảm bảo không chọn trùng
            count = min(count, len(elements))
            return random.sample(elements, count)
        else:
            # Cho phép chọn trùng
            return [random.choice(elements) for _ in range(count)]


class CombatUtils:
    """Các phương thức hỗ trợ tính toán chiến đấu"""

    @staticmethod
    def calculate_damage(attack: int, defense: int, variance: float = 0.2) -> int:
        """Tính toán sát thương dựa trên công và thủ"""
        base_damage = max(1, attack - defense // 2)
        variance_factor = 1.0 + random.uniform(-variance, variance)
        return max(1, int(base_damage * variance_factor))

    @staticmethod
    async def calculate_damage_async(attack: int, defense: int, variance: float = 0.2) -> int:
        """Phiên bản bất đồng bộ của calculate_damage"""
        return CombatUtils.calculate_damage(attack, defense, variance)

    @staticmethod
    def is_critical_hit(crit_chance: float = 0.15) -> bool:
        """Kiểm tra xem đòn đánh có phải chí mạng không"""
        return random.random() < crit_chance

    @staticmethod
    def is_dodge(dodge_chance: float = 0.1) -> bool:
        """Kiểm tra xem có né tránh thành công không"""
        return random.random() < dodge_chance

    @staticmethod
    def calculate_hit_chance(attacker_level: int, defender_level: int, base_chance: float = 0.9) -> float:
        """Tính toán tỷ lệ đánh trúng dựa trên chênh lệch cấp độ"""
        level_diff = attacker_level - defender_level
        modifier = min(0.3, max(-0.3, level_diff * 0.05))  # Giới hạn trong khoảng [-0.3, 0.3]
        return min(0.99, max(0.5, base_chance + modifier))  # Giới hạn trong khoảng [0.5, 0.99]

    @staticmethod
    def calculate_exp_reward(player_level: int, enemy_level: int, base_exp: int) -> int:
        """Tính toán phần thưởng exp dựa trên chênh lệch cấp độ"""
        level_diff = enemy_level - player_level
        if level_diff <= -5:
            # Đánh quái cấp thấp hơn nhiều
            return max(1, int(base_exp * 0.1))
        elif level_diff <= -2:
            # Đánh quái cấp thấp hơn
            return int(base_exp * 0.5)
        elif level_diff <= 2:
            # Đánh quái cùng cấp
            return base_exp
        elif level_diff <= 5:
            # Đánh quái cấp cao hơn
            return int(base_exp * 1.5)
        else:
            # Đánh quái cấp cao hơn nhiều
            return int(base_exp * 2)


class ValidationUtils:
    """Các phương thức kiểm tra và xác thực dữ liệu"""

    @staticmethod
    def is_valid_username(username: str) -> bool:
        """Kiểm tra tên người dùng có hợp lệ không"""
        if not username or len(username) < 3 or len(username) > 20:
            return False

        # Chỉ cho phép chữ cái, số, gạch dưới và gạch ngang
        pattern = r'^[a-zA-Z0-9_-]+$'
        return bool(re.match(pattern, username))

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Kiểm tra email có hợp lệ không"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def sanitize_input(text: str) -> str:
        """Làm sạch dữ liệu đầu vào để tránh injection"""
        if not text:
            return ""

        # Loại bỏ các ký tự đặc biệt và HTML tags
        text = re.sub(r'<[^>]*>', '', text)

        # Thay thế các ký tự không mong muốn
        chars_to_replace = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;',
            '/': '&#x2F;',
            '\\': '&#x5C;',
            '`': '&#x60;'
        }

        for char, replacement in chars_to_replace.items():
            text = text.replace(char, replacement)

        return text

    @staticmethod
    def is_safe_url(url: str) -> bool:
        """Kiểm tra URL có an toàn không"""
        # Kiểm tra URL có bắt đầu bằng http:// hoặc https://
        if not url.startswith(('http://', 'https://')):
            return False

        # Kiểm tra URL không chứa ký tự nguy hiểm
        unsafe_chars = [';', '&', '|', '>', '<', '`', '$', '(', ')', '{', '}']
        return not any(char in url for char in unsafe_chars)


class FileUtils:
    """Các phương thức xử lý file"""

    @staticmethod
    def read_json(file_path: str) -> Dict[str, Any]:
        """Đọc dữ liệu từ file JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error reading JSON file: {e}")
            return {}

    @staticmethod
    async def read_json_async(file_path: str) -> Dict[str, Any]:
        """Phiên bản bất đồng bộ của read_json"""
        return FileUtils.read_json(file_path)

    @staticmethod
    def write_json(file_path: str, data: Dict[str, Any]) -> bool:
        """Ghi dữ liệu vào file JSON"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error writing JSON file: {e}")
            return False

    @staticmethod
    async def write_json_async(file_path: str, data: Dict[str, Any]) -> bool:
        """Phiên bản bất đồng bộ của write_json"""
        return FileUtils.write_json(file_path, data)

    @staticmethod
    def ensure_directory(directory_path: str) -> bool:
        """Đảm bảo thư mục tồn tại, tạo mới nếu cần"""
        import os
        try:
            if not os.path.exists(directory_path):
                os.makedirs(directory_path)
            return True
        except Exception as e:
            print(f"Error creating directory: {e}")
            return False


# Tạo instances của các class tiện ích
time_utils = TimeFormatter()
exp_utils = ExpFormatter()
mongo_utils = MongoUtils()
text_utils = TextUtils()
random_utils = RandomUtils()
combat_utils = CombatUtils()
validation_utils = ValidationUtils()
file_utils = FileUtils()


# Các hàm tiện ích cũ giữ nguyên để tương thích ngược
def format_time(seconds):
    """Chuyển đổi số giây thành định dạng phút:giây"""
    return TimeFormatter.format_time(seconds)


def get_time_from_db(time_str):
    """Convert database time string to datetime object"""
    return TimeFormatter.get_time_from_db(time_str)


def format_exp(exp):
    """Format số exp để dễ đọc"""
    return ExpFormatter.format_exp(exp)


# Export các hàm và instances
__all__ = [
    # Các hàm cũ
    'format_time',
    'get_time_from_db',
    'format_exp',

    # Các instance mới
    'time_utils',
    'exp_utils',
    'mongo_utils',
    'text_utils',
    'random_utils',
    'combat_utils',
    'validation_utils',
    'file_utils'
]
