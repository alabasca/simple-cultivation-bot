import os
from dotenv import load_dotenv
import urllib.parse
import logging
from typing import Dict, Any

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler("bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('config')

# Load biến môi trường từ file .env
load_dotenv()

# ======== MongoDB Configuration ========
# Hỗ trợ cả format cũ (URI hoàn chỉnh) và format mới (thành phần riêng lẻ)
MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DB = os.getenv('MONGODB_DB')

# Nếu không tìm thấy URI hoàn chỉnh, kiểm tra các thành phần riêng lẻ
if not MONGODB_URI:
    MONGODB_USERNAME = os.getenv('MONGODB_USERNAME')
    MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD')
    MONGODB_CLUSTER = os.getenv('MONGODB_CLUSTER')

    # Kiểm tra đủ thông tin cho cấu hình MongoDB
    if all([MONGODB_USERNAME, MONGODB_PASSWORD, MONGODB_CLUSTER]):
        # Mã hóa thông tin đăng nhập để tránh các vấn đề với ký tự đặc biệt
        encoded_username = urllib.parse.quote_plus(MONGODB_USERNAME)
        encoded_password = urllib.parse.quote_plus(MONGODB_PASSWORD)

        # Tạo MongoDB URI từ các thành phần
        MONGODB_URI = f"mongodb+srv://{encoded_username}:{encoded_password}@{MONGODB_CLUSTER}/?retryWrites=true&w=majority"
    else:
        # Hiển thị thông báo lỗi chi tiết
        error_message = "\n=== LỖI CẤU HÌNH MONGODB ===\n"
        error_message += "Vui lòng cấu hình một trong hai cách sau trong file .env:\n\n"
        error_message += "Cách 1: Sử dụng URI hoàn chỉnh\n"
        error_message += "MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/\n"
        error_message += "MONGODB_DB=tutien_bot\n\n"
        error_message += "Cách 2: Sử dụng các thành phần riêng lẻ\n"
        error_message += "MONGODB_USERNAME=username\n"
        error_message += "MONGODB_PASSWORD=password\n"
        error_message += "MONGODB_CLUSTER=cluster.mongodb.net\n"
        error_message += "MONGODB_DB=tutien_bot\n"
        logger.error(error_message)
        raise ValueError("Missing MongoDB configuration in .env")

# Đảm bảo có tên database
if not MONGODB_DB:
    MONGODB_DB = "tutien_bot"  # Mặc định nếu không được cấu hình

# ======== Bot Configuration ========
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    raise ValueError("DISCORD_TOKEN not found in .env")

PREFIX = os.getenv('COMMAND_PREFIX', '!')
OWNER_ID = int(os.getenv('OWNER_ID', '0'))  # ID của chủ bot
DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
DEBUG_GUILD_ID = int(os.getenv('DEBUG_GUILD_ID', '0'))  # ID của server dùng để test

# ======== Cultivation Levels and Experience Requirements ========
CULTIVATION_LEVELS = {
    "Phàm Nhân": {
        "exp_req": 0,
        "hp": 100,
        "attack": 10,
        "defense": 5
    },
    # Luyện Khí (9 tầng)
    "Luyện Khí Tầng 1": {
        "exp_req": 100,
        "hp": 150,
        "attack": 15,
        "defense": 8
    },
    "Luyện Khí Tầng 2": {
        "exp_req": 200,
        "hp": 200,
        "attack": 20,
        "defense": 10
    },
    "Luyện Khí Tầng 3": {
        "exp_req": 400,
        "hp": 250,
        "attack": 25,
        "defense": 13
    },
    "Luyện Khí Tầng 4": {
        "exp_req": 800,
        "hp": 300,
        "attack": 30,
        "defense": 15
    },
    "Luyện Khí Tầng 5": {
        "exp_req": 1600,
        "hp": 400,
        "attack": 40,
        "defense": 20
    },
    "Luyện Khí Tầng 6": {
        "exp_req": 3200,
        "hp": 500,
        "attack": 50,
        "defense": 25
    },
    "Luyện Khí Tầng 7": {
        "exp_req": 6400,
        "hp": 600,
        "attack": 60,
        "defense": 30
    },
    "Luyện Khí Tầng 8": {
        "exp_req": 12800,
        "hp": 800,
        "attack": 80,
        "defense": 40
    },
    "Luyện Khí Tầng 9": {
        "exp_req": 25600,
        "hp": 1000,
        "attack": 100,
        "defense": 50
    },
    # Trúc Cơ (3 tầng)
    "Trúc Cơ Sơ Kỳ": {
        "exp_req": 51200,
        "hp": 2000,
        "attack": 200,
        "defense": 100
    },
    "Trúc Cơ Trung Kỳ": {
        "exp_req": 102400,
        "hp": 4000,
        "attack": 400,
        "defense": 200
    },
    "Trúc Cơ Đại Viên Mãn": {
        "exp_req": 204800,
        "hp": 8000,
        "attack": 800,
        "defense": 400
    },
    # Nguyên Anh (3 tầng)
    "Nguyên Anh Sơ Kỳ": {
        "exp_req": 409600,
        "hp": 16000,
        "attack": 1600,
        "defense": 800
    },
    "Nguyên Anh Trung Kỳ": {
        "exp_req": 819200,
        "hp": 32000,
        "attack": 3200,
        "defense": 1600
    },
    "Nguyên Anh Đại Viên Mãn": {
        "exp_req": 1638400,
        "hp": 64000,
        "attack": 6400,
        "defense": 3200
    },
    # Kim Đan (3 tầng)
    "Kim Đan Sơ Kỳ": {
        "exp_req": 3276800,
        "hp": 128000,
        "attack": 12800,
        "defense": 6400
    },
    "Kim Đan Trung Kỳ": {
        "exp_req": 6553600,
        "hp": 256000,
        "attack": 25600,
        "defense": 12800
    },
    "Kim Đan Đại Viên Mãn": {
        "exp_req": 13107200,
        "hp": 512000,
        "attack": 51200,
        "defense": 25600
    },
    # Hóa Thần (3 tầng)
    "Hóa Thần Sơ Kỳ": {
        "exp_req": 26214400,
        "hp": 1024000,
        "attack": 102400,
        "defense": 51200
    },
    "Hóa Thần Trung Kỳ": {
        "exp_req": 52428800,
        "hp": 2048000,
        "attack": 204800,
        "defense": 102400
    },
    "Hóa Thần Đại Viên Mãn": {
        "exp_req": 104857600,
        "hp": 4096000,
        "attack": 409600,
        "defense": 204800
    },
    # Luyện Hư (3 tầng)
    "Luyện Hư Sơ Kỳ": {
        "exp_req": 209715200,
        "hp": 8192000,
        "attack": 819200,
        "defense": 409600
    },
    "Luyện Hư Trung Kỳ": {
        "exp_req": 419430400,
        "hp": 16384000,
        "attack": 1638400,
        "defense": 819200
    },
    "Luyện Hư Đại Viên Mãn": {
        "exp_req": 838860800,
        "hp": 32768000,
        "attack": 3276800,
        "defense": 1638400
    },
    # Đại Thừa (3 tầng)
    "Đại Thừa Sơ Kỳ": {
        "exp_req": 1677721600,
        "hp": 65536000,
        "attack": 6553600,
        "defense": 3276800
    },
    "Đại Thừa Trung Kỳ": {
        "exp_req": 3355443200,
        "hp": 131072000,
        "attack": 13107200,
        "defense": 6553600
    },
    "Đại Thừa Đại Viên Mãn": {
        "exp_req": 6710886400,
        "hp": 262144000,
        "attack": 26214400,
        "defense": 13107200
    },
    # Diễn Chủ
    "Diễn Chủ Vạn Giới": {
        "exp_req": 13421772800,
        "hp": 524288000,
        "attack": 52428800,
        "defense": 26214400
    }
}

# ======== Sect Configuration ========
SECTS = {
    "Thiên Kiếm Tông": {
        "description": "Kiếm thuật vô song, trảm yêu trừ ma.",
        "attack_bonus": 1.2,
        "defense_bonus": 1.0
    },
    "Đoạn Tình Cốc": {
        "description": "Cắt đứt hồng trần, truy cầu sức mạnh tuyệt đối.",
        "attack_bonus": 1.1,
        "defense_bonus": 1.1
    },
    "Huyết Ma Giáo": {
        "description": "Tà đạo hùng mạnh, kẻ mạnh mới là chân lý.",
        "attack_bonus": 1.3,
        "defense_bonus": 0.9
    },
    "Tuyết Nguyệt Cung": {
        "description": "❄️ Cung thủ băng hàn, bóng hồng lạnh lẽo, đẹp như trăng nhưng sắc bén như kiếm.",
        "attack_bonus": 1.15,
        "defense_bonus": 1.05
    },
    "Hồng Trần Lữ Khách": {
        "description": "Không thuộc môn phái nào, phiêu bạt nhân gian, tự do tự tại, lấy trải nghiệm hồng trần làm con đường tu luyện.",
        "attack_bonus": 1.1,
        "defense_bonus": 1.1
    }
}

# Màu sắc và emoji cho từng môn phái
SECT_COLORS = {
    "Thiên Kiếm Tông": 0x3498db,  # 🔵 Blue
    "Đoạn Tình Cốc": 0xf1c40f,  # 🟡 Yellow
    "Huyết Ma Giáo": 0xe74c3c,  # 🔴 Red
    "Tuyết Nguyệt Cung": 0x9b59b6,  # 🟣 Purple
    "Hồng Trần Lữ Khách": 0x2ecc71  # 🟢 Green
}

SECT_EMOJIS = {
    "Thiên Kiếm Tông": "🔵",
    "Đoạn Tình Cốc": "🟡",
    "Huyết Ma Giáo": "🔴",
    "Tuyết Nguyệt Cung": "🟣",
    "Hồng Trần Lữ Khách": "🟢"
}

# Thông tin chi tiết về các môn phái
SECT_DETAILS = {
    "Thiên Kiếm Tông": {
        "founder": "Kiếm Thánh Vô Danh",
        "location": "Thiên Kiếm Phong",
        "specialty": "Kiếm thuật, Kiếm khí",
        "famous_skills": ["Thiên Kiếm Quyết", "Vô Tình Kiếm Pháp", "Kiếm Tâm Thông Minh"],
        "history": "Thiên Kiếm Tông được thành lập từ hơn ngàn năm trước bởi Kiếm Thánh Vô Danh, một kiếm khách đã đạt tới cảnh giới Kiếm Đạo Viên Mãn. Tông môn nổi tiếng với kiếm pháp tinh thuần và đạo tâm kiên định.",
        "motto": "Kiếm tâm như nhất, đạo tâm bất động"
    },
    "Đoạn Tình Cốc": {
        "founder": "Đoạn Tình Tiên Tử",
        "location": "Vạn Tình Cốc",
        "specialty": "Độc công, Mê hương",
        "famous_skills": ["Đoạn Tình Chỉ", "Vạn Độc Thiên Hương", "Tuyệt Tình Quyết"],
        "history": "Đoạn Tình Cốc được sáng lập bởi Đoạn Tình Tiên Tử sau khi bà trải qua một mối tình đau khổ. Môn phái chủ trương đoạn tuyệt tình cảm để theo đuổi võ đạo và trường sinh.",
        "motto": "Đoạn tình tuyệt ái, đạo tâm bất diệt"
    },
    "Huyết Ma Giáo": {
        "founder": "Huyết Ma Tổ Sư",
        "location": "Huyết Ma Sơn",
        "specialty": "Huyết công, Ma công",
        "famous_skills": ["Huyết Ma Đại Pháp", "Cửu Chuyển Huyết Công", "Ma Đạo Thôn Thiên"],
        "history": "Huyết Ma Giáo là một trong những tà phái lớn nhất, được thành lập bởi Huyết Ma Tổ Sư, người đã luyện thành Huyết Ma Đại Pháp bằng cách hấp thu máu của vạn vật. Môn phái theo đuổi sức mạnh tuyệt đối không quan tâm thủ đoạn.",
        "motto": "Thiên địa bất nhân, ngã diệc bất nhân"
    },
    "Tuyết Nguyệt Cung": {
        "founder": "Tuyết Nguyệt Tiên Tử",
        "location": "Hàn Băng Cốc",
        "specialty": "Băng công, Cung pháp",
        "famous_skills": ["Tuyết Nguyệt Thần Công", "Băng Tâm Quyết", "Hàn Nguyệt Cung Pháp"],
        "history": "Tuyết Nguyệt Cung được thành lập bởi Tuyết Nguyệt Tiên Tử, một nữ tu tiên có thiên phú về băng thuật. Môn phái chỉ nhận đệ tử nữ, nổi tiếng với sự thanh cao và kỷ luật nghiêm khắc.",
        "motto": "Tâm như băng thanh, ý tự nguyệt minh"
    },
    "Hồng Trần Lữ Khách": {
        "founder": "Phiêu Miễu Đạo Nhân",
        "location": "Khắp thiên hạ",
        "specialty": "Khinh công, Ẩn thân",
        "famous_skills": ["Phiêu Miễu Thân Pháp", "Trần Thế Vô Ảnh Bộ", "Thiên Ngoại Phi Tiên"],
        "history": "Hồng Trần Lữ Khách không phải là một môn phái truyền thống mà là một tập hợp những người tu tiên yêu thích tự do, phiêu bạt giang hồ. Họ không có tổng môn cố định, thường gặp nhau tại các thắng cảnh để luận đạo.",
        "motto": "Tiêu dao thiên địa, tự tại nhân gian"
    }
}

# ======== Combat Configuration ========
COMBAT_COOLDOWN = 1800  # 30 minutes
MONSTER_COOLDOWN = 600  # 10 minutes
BOSS_COOLDOWN = 1800  # 30 minutes (tăng từ 15 phút lên 30 phút)

# Experience Configuration
CHAT_EXP = 1  # EXP per message
VOICE_EXP = 2  # EXP per minute in voice
MONSTER_EXP = 10  # Base EXP for killing monster
BOSS_EXP = 50  # Base EXP for killing boss
DAILY_EXP = 100  # Base EXP for daily check-in

# Combat Multipliers
MONSTER_HP_MULTIPLIER = 0.3  # Monster HP = Player HP * 0.3
MONSTER_ATK_MULTIPLIER = 0.3  # Monster ATK = Player ATK * 0.3
BOSS_HP_MULTIPLIER = 0.5  # Boss HP = Player HP * 0.5
BOSS_ATK_MULTIPLIER = 0.5  # Boss ATK = Player ATK * 0.5
DAMAGE_VARIATION = 0.2  # Damage varies by ±20%

# Level Up Configuration
EXP_STEAL_PERCENT = 0.1  # Steal 10% of opponent's EXP in PvP
MAX_EXP_STEAL = 500  # Maximum EXP that can be stolen in PvP

# ======== Item Configuration ========
ITEM_RARITIES = {
    "Phổ Thông": {
        "color": 0xffffff,  # White
        "emoji": "⚪",
        "drop_chance": 0.7
    },
    "Hiếm": {
        "color": 0x3498db,  # Blue
        "emoji": "🔵",
        "drop_chance": 0.2
    },
    "Quý": {
        "color": 0x9b59b6,  # Purple
        "emoji": "🟣",
        "drop_chance": 0.08
    },
    "Cực Phẩm": {
        "color": 0xf1c40f,  # Gold
        "emoji": "🟡",
        "drop_chance": 0.02
    },
    "Thần Thánh": {
        "color": 0xe74c3c,  # Red
        "emoji": "🔴",
        "drop_chance": 0.005
    }
}

# ======== Daily Check-in Configuration ========
DAILY_STREAK_BONUS = 0.1  # +10% bonus per day in streak
MAX_DAILY_STREAK_BONUS = 1.0  # Maximum +100% bonus
DAILY_STREAK_RESET_DAYS = 2  # Reset streak after missing 2 days

# ======== Misc Configuration ========
VERSION = "1.0.0"
SUPPORT_SERVER = "https://discord.gg/example"
GITHUB_REPO = "https://github.com/example/tutien-bot"

# ======== Logging Configuration ========
LOG_LEVEL = logging.INFO if not DEBUG_MODE else logging.DEBUG
LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
LOG_FILE = "logs/bot.log"

# Kiểm tra và tạo thư mục logs nếu chưa tồn tại
import os
if not os.path.exists('logs'):
    os.makedirs('logs')

# Thông báo cấu hình đã hoàn tất
logger.info(f"Đã tải cấu hình. Chế độ debug: {DEBUG_MODE}")
