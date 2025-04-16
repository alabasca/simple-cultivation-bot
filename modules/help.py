import discord
from discord.ext import commands
from config import CULTIVATION_LEVELS, CHAT_EXP, VOICE_EXP, MONSTER_EXP, BOSS_EXP, SECTS, SECT_EMOJIS
import asyncio
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import random


class Help(commands.Cog):
    """Hệ thống hướng dẫn và trợ giúp"""

    def __init__(self, bot):
        self.bot = bot
        self.help_cache = {}
        self.cache_lock = asyncio.Lock()
        self.cache_lifetime = 300  # 5 phút
        self.interactive_sessions = {}  # Lưu trữ phiên tương tác

        # Danh sách các emoji cho nút điều hướng
        self.nav_emojis = {
            "first": "⏮️",
            "prev": "◀️",
            "next": "▶️",
            "last": "⏭️",
            "close": "❌"
        }

        # Danh sách các emoji cho các chủ đề
        self.topic_emojis = {
            "main": "📚",
            "commands": "🎮",
            "exp": "💫",
            "levels": "🌟",
            "sects": "🏯",
            "combat": "⚔️",
            "items": "🎒",
            "events": "🎉"
        }

        # Danh sách các chủ đề và tiêu đề
        self.topics = {
            "main": "Giới Thiệu Hệ Thống Tu Tiên",
            "commands": "Các Lệnh Cơ Bản",
            "exp": "Hệ Thống Tu Luyện & Phần Thưởng",
            "levels": "Hệ Thống Cảnh Giới",
            "sects": "Hệ Thống Môn Phái",
            "combat": "Hệ Thống Chiến Đấu",
            "items": "Vật Phẩm & Trang Bị",
            "events": "Sự Kiện & Hoạt Động"
        }

    async def get_cached_help(self, section: str) -> discord.Embed:
        """Lấy help embed từ cache hoặc tạo mới"""
        async with self.cache_lock:
            if section in self.help_cache:
                embed, timestamp = self.help_cache[section]
                if (datetime.now() - timestamp).seconds < self.cache_lifetime:
                    return embed

            # Tạo embed mới nếu không có trong cache hoặc đã hết hạn
            embed = await self.create_help_section(section)
            self.help_cache[section] = (embed, datetime.now())
            return embed

    async def create_help_section(self, section: str) -> discord.Embed:
        """Tạo các section help riêng biệt"""
        if section == "main":
            return await self.create_main_embed()
        elif section == "commands":
            return await self.create_commands_embed()
        elif section == "exp":
            return await self.create_exp_embed()
        elif section == "levels":
            return await self.create_levels_embed()
        elif section == "sects":
            return await self.create_sects_embed()
        elif section == "combat":
            return await self.create_combat_embed()
        elif section == "items":
            return await self.create_items_embed()
        elif section == "events":
            return await self.create_events_embed()
        return None

    async def create_main_embed(self) -> discord.Embed:
        """Tạo embed giới thiệu chính"""
        embed = discord.Embed(
            title=f"{self.topic_emojis['main']} Hệ Thống Tu Tiên",
            description=(
                "Chào mừng đến với thế giới tu tiên. Dưới đây là những thông tin cơ bản "
                "giúp người mới bắt đầu.\n\n"
                "**Bắt Đầu Tu Luyện:**\n"
                "• Chọn môn phái trong kênh 🏯┃tông-môn-chi-lộ\n"
                "• Điểm danh hàng ngày để nhận thưởng\n"
                "• Tu luyện thông qua chat, voice và chiến đấu\n\n"
                "**Lệnh Cơ Bản:**\n"
                "• `!tutien` - Xem hướng dẫn này\n"
                "• `!tuvi` - Xem thông tin tu vi\n"
                "• `!daily` - Điểm danh nhận thưởng"
            ),
            color=0xf1c40f
        )

        # Thêm thông tin về cách sử dụng hướng dẫn tương tác
        embed.add_field(
            name="🔍 Hướng Dẫn Tương Tác",
            value=(
                "Sử dụng `!help [chủ_đề]` để xem chi tiết về một chủ đề cụ thể:\n"
                "• `!help commands` - Danh sách lệnh\n"
                "• `!help exp` - Hệ thống kinh nghiệm\n"
                "• `!help levels` - Cảnh giới tu luyện\n"
                "• `!help sects` - Thông tin môn phái\n"
                "• `!help combat` - Hệ thống chiến đấu\n"
                "• `!help items` - Vật phẩm và trang bị\n"
                "• `!help events` - Sự kiện và hoạt động"
            ),
            inline=False
        )

        # Thêm thông tin về cách sử dụng lệnh help cho từng lệnh cụ thể
        embed.add_field(
            name="❓ Trợ Giúp Lệnh Cụ Thể",
            value=(
                "Sử dụng `!help [tên_lệnh]` để xem chi tiết về một lệnh cụ thể:\n"
                "Ví dụ: `!help tuvi`, `!help danhquai`, `!help tongmon`"
            ),
            inline=False
        )

        embed.set_thumbnail(url="https://i.imgur.com/3MUxw2G.png")

        # Thêm footer với thông tin phiên bản
        embed.set_footer(text="Tu Tiên Bot v1.0 • Sử dụng !tutien để xem lại hướng dẫn")

        return embed

    async def create_commands_embed(self) -> discord.Embed:
        """Tạo embed danh sách lệnh"""
        embed = discord.Embed(
            title=f"{self.topic_emojis['commands']} Các Lệnh Cơ Bản",
            description="Dưới đây là danh sách các lệnh chính trong hệ thống tu tiên:",
            color=0x3498db
        )

        # Thông tin & Điểm danh
        embed.add_field(
            name="📝 Thông Tin & Điểm Danh",
            value=(
                "`!tuvi [@người_chơi]` - Xem thông tin tu vi\n"
                "`!tutien` - Xem hướng dẫn tổng quan\n"
                "`!help [lệnh/chủ_đề]` - Xem hướng dẫn chi tiết\n"
                "`!daily` hoặc `!diemdanh` - Điểm danh nhận thưởng\n"
                "`!exp [@người_chơi]` - Xem chi tiết kinh nghiệm\n"
                "`!rank [@người_chơi]` - Xem chi tiết cảnh giới"
            ),
            inline=False
        )

        # Tu luyện & Chiến đấu
        embed.add_field(
            name="⚔️ Tu Luyện & Chiến Đấu",
            value=(
                "`!danhquai` - Đánh quái vật (10 phút/lần)\n"
                "`!danhboss` - Đánh boss (30 phút/lần)\n"
                "`!combat @người_chơi` - PvP với người chơi khác (30 phút/lần)\n"
                "`!tudo @người_chơi` - Thách đấu tự do (không ảnh hưởng EXP)\n"
                "`!luyendan` - Luyện đan dược (1 giờ/lần)"
            ),
            inline=False
        )

        # Vật phẩm & Trang bị
        embed.add_field(
            name="🎒 Vật Phẩm & Trang bị",
            value=(
                "`!kho` - Xem kho đồ cá nhân\n"
                "`!trangbi` - Xem và quản lý trang bị\n"
                "`!shop` - Mở cửa hàng đạo cụ\n"
                "`!sudung [vật_phẩm]` - Sử dụng vật phẩm\n"
                "`!tangthu` - Xem tàng thư môn phái"
            ),
            inline=False
        )

        # Thống kê & Tiện ích
        embed.add_field(
            name="📊 Thống Kê & Tiện Ích",
            value=(
                "`!server_info` - Xem thông tin server\n"
                "`!top [all/sect] [số_lượng]` - Xem bảng xếp hạng\n"
                "`!stats` - Xem thống kê chi tiết\n"
                "`!ping` - Kiểm tra độ trễ\n"
                "`!roll [số]` - Random số ngẫu nhiên"
            ),
            inline=False
        )

        # Thêm ghi chú
        embed.add_field(
            name="📝 Ghi Chú",
            value=(
                "• Sử dụng `!help [tên_lệnh]` để xem chi tiết về một lệnh cụ thể\n"
                "• Các lệnh có thể có cooldown riêng\n"
                "• Một số lệnh yêu cầu cảnh giới nhất định\n"
                "• Một số lệnh chỉ có thể sử dụng trong kênh chỉ định"
            ),
            inline=False
        )

        return embed

    async def create_exp_embed(self) -> discord.Embed:
        """Tạo embed thông tin kinh nghiệm"""
        embed = discord.Embed(
            title=f"{self.topic_emojis['exp']} Hệ Thống Tu Luyện & Phần Thưởng",
            description="Có nhiều cách để tăng công lực và tu vi:",
            color=0x2ecc71
        )

        # Điểm danh
        embed.add_field(
            name="🌟 Điểm Danh Hàng Ngày",
            value=(
                "• Phần thưởng cơ bản: 100 EXP\n"
                "• Bonus streak: +10% mỗi ngày (tối đa 100%)\n"
                "• Phần thưởng đặc biệt mỗi 7 ngày\n"
                "• Reset streak nếu bỏ lỡ 2 ngày liên tiếp"
            ),
            inline=False
        )

        # Tu luyện thường ngày
        embed.add_field(
            name="📈 Tu Luyện Thường Ngày",
            value=(
                f"• Chat: +{CHAT_EXP} EXP mỗi tin nhắn\n"
                f"• Voice: +{VOICE_EXP} EXP mỗi phút\n"
                f"• Đánh quái: +{MONSTER_EXP} EXP (có thể nhận bonus)\n"
                f"• Đánh boss: +{BOSS_EXP} EXP (có thể nhận bonus)\n"
                "• PvP: Cướp 10% EXP đối thủ (tối đa 500 EXP)"
            ),
            inline=False
        )

        # Nhiệm vụ và sự kiện
        embed.add_field(
            name="🎯 Nhiệm Vụ & Sự Kiện",
            value=(
                "• Nhiệm vụ hàng ngày: 50-200 EXP\n"
                "• Nhiệm vụ hàng tuần: 300-1000 EXP\n"
                "• Sự kiện đặc biệt: Phần thưởng đa dạng\n"
                "• Đại hội tông môn: EXP và vật phẩm quý hiếm"
            ),
            inline=False
        )

        # Luyện đan và chế tạo
        embed.add_field(
            name="🧪 Luyện Đan & Chế Tạo",
            value=(
                "• Luyện đan: 50-300 EXP mỗi lần thành công\n"
                "• Chế tạo vũ khí: 100-500 EXP mỗi lần thành công\n"
                "• Đột phá trang bị: 200-1000 EXP mỗi lần thành công\n"
                "• Tỷ lệ thành công phụ thuộc vào cảnh giới"
            ),
            inline=False
        )

        # Thêm biểu đồ tăng trưởng
        embed.add_field(
            name="📊 Biểu Đồ Tăng Trưởng",
            value=(
                "```\n"
                "Cấp độ      | EXP/ngày (ước tính)\n"
                "------------|-------------------\n"
                "Phàm Nhân   | 300-500 EXP\n"
                "Luyện Khí   | 500-800 EXP\n"
                "Trúc Cơ     | 800-1200 EXP\n"
                "Nguyên Anh  | 1000-1500 EXP\n"
                "Kim Đan     | 1200-2000 EXP\n"
                "```"
            ),
            inline=False
        )

        return embed

    async def create_levels_embed(self) -> discord.Embed:
        """Tạo embed thông tin cảnh giới"""
        embed = discord.Embed(
            title=f"{self.topic_emojis['levels']} Hệ Thống Cảnh Giới",
            description=(
                "Con đường tu tiên gian nan, đầy thử thách. "
                "Mỗi bước tiến là một bước gần hơn đến với đại đạo."
            ),
            color=0xe74c3c
        )

        # Tạo các field cho từng cảnh giới
        realm_info = {
            "👤 Phàm Nhân": {
                "desc": (
                    "```\n"
                    "• Cấp độ khởi đầu\n"
                    "• Chưa có linh căn\n"
                    f"• EXP yêu cầu: {CULTIVATION_LEVELS['Phàm Nhân']['exp_req']:,}\n"
                    "```"
                ),
                "inline": False
            },
            "🌊 Luyện Khí (9 Tầng)": {
                "desc": await self.create_cultivation_stages(
                    "Luyện Khí",
                    [
                        ("Tầng 1", "Linh khí nhập thể"),
                        ("Tầng 2", "Khai thông kinh mạch"),
                        ("Tầng 3", "Linh khí tuần hoàn"),
                        ("Tầng 4", "Kinh mạch củng cố"),
                        ("Tầng 5", "Linh khí thành tụ"),
                        ("Tầng 6", "Linh căn thành hình"),
                        ("Tầng 7", "Linh khí hóa chân"),
                        ("Tầng 8", "Bát mạch thông suốt"),
                        ("Tầng 9", "Cửu khiếu ngưng thần")
                    ]
                ),
                "inline": False
            },
            "💫 Trúc Cơ (3 Tầng)": {
                "desc": await self.create_cultivation_stages(
                    "Trúc Cơ",
                    [
                        ("Sơ Kỳ", "Đặt nền móng"),
                        ("Trung Kỳ", "Củng cố đạo tâm"),
                        ("Đại Viên Mãn", "Trúc cơ thành công")
                    ]
                ),
                "inline": False
            },
            "✨ Nguyên Anh (3 Tầng)": {
                "desc": await self.create_cultivation_stages(
                    "Nguyên Anh",
                    [
                        ("Sơ Kỳ", "Nguyên anh thành hình"),
                        ("Trung Kỳ", "Nguyên anh củng cố"),
                        ("Đại Viên Mãn", "Nguyên anh viên mãn")
                    ]
                ),
                "inline": False
            },
            "🔥 Kim Đan (3 Tầng)": {
                "desc": await self.create_cultivation_stages(
                    "Kim Đan",
                    [
                        ("Sơ Kỳ", "Kim đan thành hình"),
                        ("Trung Kỳ", "Kim đan củng cố"),
                        ("Đại Viên Mãn", "Kim đan viên mãn")
                    ]
                ),
                "inline": False
            }
        }

        # Thêm các field vào embed
        for title, info in realm_info.items():
            embed.add_field(
                name=title,
                value=info["desc"],
                inline=info["inline"]
            )

        # Thêm ghi chú
        embed.add_field(
            name="📝 Ghi Chú",
            value=(
                "```\n"
                "• EXP tăng theo cấp số nhân\n"
                "• Mỗi cấp độ có chỉ số riêng\n"
                "• Có thể vượt cấp chiến đấu\n"
                "• Càng lên cao càng khó khăn\n"
                "• Sử dụng !levels để xem chi tiết hơn\n"
                "```"
            ),
            inline=False
        )

        return embed

    async def create_cultivation_stages(self, realm: str, stages: List[tuple]) -> str:
        """Tạo chuỗi hiển thị các giai đoạn tu luyện"""
        result = ["```"]
        for i, (stage, desc) in enumerate(stages):
            prefix = "├─" if i < len(stages) - 1 else "└─"
            level_key = f"{realm} {stage}"
            exp_req = 0

            # Tìm kiếm key phù hợp trong CULTIVATION_LEVELS
            for key in CULTIVATION_LEVELS:
                if key.startswith(level_key):
                    exp_req = CULTIVATION_LEVELS[key]['exp_req']
                    break

            result.append(f"{prefix} {stage:<12} ─ {desc}")
            result.append(f"   EXP: {exp_req:,}")

        result.append("```")
        return "\n".join(result)

    async def create_sects_embed(self) -> discord.Embed:
        """Tạo embed thông tin môn phái"""
        embed = discord.Embed(
            title=f"{self.topic_emojis['sects']} Hệ Thống Môn Phái",
            description="Mỗi môn phái có những đặc trưng và ưu điểm riêng:",
            color=0x9b59b6
        )

        # Thông tin từng môn phái
        for sect_name, sect_data in SECTS.items():
            emoji = SECT_EMOJIS.get(sect_name, "🏯")

            # Tạo mô tả chi tiết
            description = sect_data.get('description', "Không có mô tả")
            attack_bonus = sect_data.get('attack_bonus', 1.0)
            defense_bonus = sect_data.get('defense_bonus', 1.0)

            # Tạo chuỗi bonus
            bonuses = []
            if attack_bonus != 1.0:
                bonus_percent = int((attack_bonus - 1.0) * 100)
                bonuses.append(f"⚔️ +{bonus_percent}% Công Kích")

            if defense_bonus != 1.0:
                bonus_percent = int((defense_bonus - 1.0) * 100)
                bonuses.append(f"🛡️ +{bonus_percent}% Phòng Thủ")

            # Thêm các bonus đặc biệt khác nếu có
            special_bonus = sect_data.get('special_bonus', None)
            if special_bonus:
                bonuses.append(f"✨ {special_bonus}")

            # Tạo chuỗi hiển thị
            value = f"{description}\n" + "\n".join(bonuses)

            # Thêm thông tin về kỹ năng đặc biệt nếu có
            special_skill = sect_data.get('special_skill', None)
            if special_skill:
                value += f"\n🔮 Kỹ năng: {special_skill}"

            embed.add_field(
                name=f"{emoji} {sect_name}",
                value=value,
                inline=False
            )

        # Thêm thông tin về cách gia nhập môn phái
        embed.add_field(
            name="📝 Gia Nhập Môn Phái",
            value=(
                "• Sử dụng lệnh `!tongmon` để chọn môn phái\n"
                "• Mỗi người chỉ được chọn một môn phái\n"
                "• Có thể đổi môn phái sau 7 ngày với chi phí 1000 EXP\n"
                "• Mỗi môn phái có nhiệm vụ và phần thưởng riêng"
            ),
            inline=False
        )

        return embed

    async def create_combat_embed(self) -> discord.Embed:
        """Tạo embed thông tin hệ thống chiến đấu"""
        embed = discord.Embed(
            title=f"{self.topic_emojis['combat']} Hệ Thống Chiến Đấu",
            description="Hệ thống chiến đấu đa dạng với nhiều cơ chế:",
            color=0xe67e22
        )

        # Thông tin cơ bản về chiến đấu
        embed.add_field(
            name="⚔️ Cơ Chế Chiến Đấu",
            value=(
                "• Chỉ số chiến đấu dựa trên cảnh giới và trang bị\n"
                "• Công thức: Sát thương = (Công kích người tấn công - Phòng thủ người bị tấn công/2) * Hệ số ngẫu nhiên\n"
                "• Hệ số ngẫu nhiên: 0.8 - 1.2\n"
                "• Có cơ hội tấn công chí mạng (x1.5 sát thương)\n"
                "• Có cơ hội né tránh (phụ thuộc vào chênh lệch cảnh giới)"
            ),
            inline=False
        )

        # Thông tin về PvE
        embed.add_field(
            name="🐺 Đánh Quái (PvE)",
            value=(
                f"• Lệnh: `!danhquai` (Cooldown: 10 phút)\n"
                f"• Phần thưởng: {MONSTER_EXP} EXP + vật phẩm ngẫu nhiên\n"
                "• Loại quái: Thường, Tinh Anh, Thủ Lĩnh (tỷ lệ xuất hiện khác nhau)\n"
                "• Cấp độ quái phụ thuộc vào cảnh giới người chơi\n"
                "• Có thể thất bại nếu máu về 0"
            ),
            inline=False
        )

        # Thông tin về Boss
        embed.add_field(
            name="🐉 Đánh Boss",
            value=(
                f"• Lệnh: `!danhboss` (Cooldown: 30 phút)\n"
                f"• Phần thưởng: {BOSS_EXP} EXP + vật phẩm quý hiếm\n"
                "• Boss mạnh hơn quái thường nhiều lần\n"
                "• Có thể thất bại nếu máu về 0\n"
                "• Có thể mời đồng đội cùng đánh boss"
            ),
            inline=False
        )

        # Thông tin về PvP
        embed.add_field(
            name="🥊 PvP Với Người Chơi",
            value=(
                "• Lệnh: `!combat @người_chơi` (Cooldown: 30 phút)\n"
                "• Phần thưởng: Cướp 10% EXP đối thủ (tối đa 500 EXP)\n"
                "• Người thua mất EXP và có thể bị thương\n"
                "• Chỉ có thể PvP với người có cảnh giới chênh lệch ±2 cấp\n"
                "• Có thể từ chối thách đấu\n"
                "• Lệnh `!tudo @người_chơi` để thách đấu không ảnh hưởng EXP"
            ),
            inline=False
        )

        # Thông tin về trang bị và kỹ năng
        embed.add_field(
            name="🛡️ Trang Bị & Kỹ Năng",
            value=(
                "• Trang bị tăng chỉ số chiến đấu\n"
                "• Mỗi môn phái có kỹ năng đặc biệt riêng\n"
                "• Kỹ năng mở khóa theo cảnh giới\n"
                "• Đan dược có thể tăng chỉ số tạm thời\n"
                "• Vũ khí có thể được nâng cấp để tăng sức mạnh"
            ),
            inline=False
        )

        return embed

    async def create_items_embed(self) -> discord.Embed:
        """Tạo embed thông tin vật phẩm và trang bị"""
        embed = discord.Embed(
            title=f"{self.topic_emojis['items']} Vật Phẩm & Trang Bị",
            description="Hệ thống vật phẩm đa dạng với nhiều công dụng:",
            color=0x1abc9c
        )

        # Thông tin về các loại vật phẩm
        embed.add_field(
            name="🧪 Đan Dược",
            value=(
                "• Linh Khí Đan: Hồi phục HP trong chiến đấu\n"
                "• Tăng Lực Đan: Tăng công kích tạm thời\n"
                "• Cường Thể Đan: Tăng phòng thủ tạm thời\n"
                "• Tu Vi Đan: Tăng EXP nhận được\n"
                "• Tẩy Tủy Đan: Reset điểm tiềm năng"
            ),
            inline=False
        )

        # Thông tin về trang bị
        embed.add_field(
            name="⚔️ Vũ Khí & Trang Bị",
            value=(
                "• Vũ khí: Tăng sát thương\n"
                "• Áo giáp: Tăng phòng thủ\n"
                "• Phụ kiện: Tăng các chỉ số khác\n"
                "• Độ hiếm: Phàm, Luyện, Trúc, Nguyên, Kim, Thần\n"
                "• Có thể nâng cấp và đính linh thạch"
            ),
            inline=False
        )

        # Thông tin về nguyên liệu
        embed.add_field(
            name="💎 Nguyên Liệu",
            value=(
                "• Linh thạch: Tiền tệ trong game\n"
                "• Linh thảo: Dùng để luyện đan\n"
                "• Khoáng thạch: Dùng để rèn vũ khí\n"
                "• Thú hạch: Nhận từ quái vật, dùng để đổi vật phẩm\n"
                "• Bí tịch: Mở khóa kỹ năng mới"
            ),
            inline=False
        )

        # Thông tin về hệ thống kho đồ
        embed.add_field(
            name="🎒 Kho Đồ",
            value=(
                "• Lệnh: `!kho` để xem kho đồ\n"
                "• Lệnh: `!sudung [vật_phẩm]` để sử dụng\n"
                "• Lệnh: `!trangbi` để quản lý trang bị\n"
                "• Lệnh: `!ban [vật_phẩm] [số_lượng] [@người_chơi]` để bán/tặng\n"
                "• Dung lượng kho tăng theo cảnh giới"
            ),
            inline=False
        )

        # Thông tin về cửa hàng
        embed.add_field(
            name="🏪 Cửa Hàng",
            value=(
                "• Lệnh: `!shop` để mở cửa hàng\n"
                "• Lệnh: `!mua [mã_vật_phẩm] [số_lượng]` để mua\n"
                "• Cửa hàng làm mới mỗi ngày\n"
                "• Vật phẩm đặc biệt xuất hiện ngẫu nhiên\n"
                "• Có thể bán vật phẩm để lấy linh thạch"
            ),
            inline=False
        )

        return embed

    async def create_events_embed(self) -> discord.Embed:
        """Tạo embed thông tin sự kiện và hoạt động"""
        embed = discord.Embed(
            title=f"{self.topic_emojis['events']} Sự Kiện & Hoạt Động",
            description="Tham gia các sự kiện để nhận phần thưởng đặc biệt:",
            color=0x8e44ad
        )

        # Thông tin về sự kiện hàng ngày
        embed.add_field(
            name="📅 Sự Kiện Hàng Ngày",
            value=(
                "• Nhiệm vụ hàng ngày: Làm mới lúc 0h mỗi ngày\n"
                "• Săn Yêu Thú: Xuất hiện ngẫu nhiên trong ngày\n"
                "• Tầm Bảo: Tìm kho báu ẩn trong server\n"
                "• Luận Đạo: Trả lời câu hỏi về tu tiên"
            ),
            inline=False
        )

        # Thông tin về sự kiện hàng tuần
        embed.add_field(
            name="📆 Sự Kiện Hàng Tuần",
            value=(
                "• Đại Hội Tông Môn: Thi đấu giữa các môn phái\n"
                "• Săn Boss Thế Giới: Boss mạnh xuất hiện ngẫu nhiên\n"
                "• Thí Luyện Tháp: Thử thách nhiều tầng, phần thưởng lớn\n"
                "• Bí Cảnh: Khám phá bí cảnh, nhận vật phẩm quý hiếm"
            ),
            inline=False
        )

        # Thông tin về sự kiện theo mùa
        embed.add_field(
            name="🎭 Sự Kiện Theo Mùa",
            value=(
                "• Tiên Môn Đại Hội: Diễn ra mỗi tháng\n"
                "• Lễ Hội Mùa Xuân/Hạ/Thu/Đông: Theo mùa trong năm\n"
                "• Ngày Thành Lập Server: Kỷ niệm ngày thành lập\n"
                "• Sự Kiện Đặc Biệt: Theo các dịp lễ trong năm"
            ),
            inline=False
        )

        # Thông tin về phần thưởng
        embed.add_field(
            name="🏆 Phần Thưởng",
            value=(
                "• EXP: Tăng kinh nghiệm tu luyện\n"
                "• Linh Thạch: Tiền tệ trong game\n"
                "• Vật Phẩm Quý: Đan dược, trang bị hiếm\n"
                "• Danh Hiệu: Danh hiệu đặc biệt\n"
                "• Kỹ Năng: Mở khóa kỹ năng mới"
            ),
            inline=False
        )

        # Thông tin về cách tham gia
        embed.add_field(
            name="🔍 Cách Tham Gia",
            value=(
                "• Theo dõi thông báo trong kênh #thông-báo\n"
                "• Sử dụng lệnh `!sukien` để xem sự kiện hiện tại\n"
                "• Đăng ký tham gia qua bot hoặc trong kênh sự kiện\n"
                "• Một số sự kiện yêu cầu cảnh giới tối thiểu"
            ),
            inline=False
        )

        return embed

    @commands.command(name='tutien')
    async def tutien(self, ctx):
        """Hiển thị hướng dẫn tu tiên tổng quan"""
        try:
            # Tạo tất cả các embed
            embeds = await asyncio.gather(
                self.get_cached_help("main"),
                self.get_cached_help("commands"),
                self.get_cached_help("exp"),
                self.get_cached_help("levels"),
                self.get_cached_help("sects")
            )

            # Thêm footer cho tất cả embed
            for i, embed in enumerate(embeds, 1):
                if embed:  # Kiểm tra embed không None
                    embed.set_footer(text=f"Trang {i}/{len(embeds)} • Sử dụng !tutien để xem lại")

            # Gửi tất cả embed
            await ctx.send(embeds=[e for e in embeds if e])

        except Exception as e:
            print(f"Lỗi khi hiển thị help: {e}")
            await ctx.send("Có lỗi xảy ra khi hiển thị hướng dẫn. Vui lòng thử lại sau!")

    @commands.command(name='help')
    async def help_command(self, ctx, *, query: str = None):
        """Hiển thị hướng dẫn chi tiết về lệnh hoặc chủ đề"""
        try:
            # Nếu không có query, hiển thị help chính
            if not query:
                main_embed = await self.get_cached_help("main")
                await ctx.send(embed=main_embed)
                return

            # Kiểm tra xem query có phải là chủ đề không
            query = query.lower()
            if query in self.topics:
                embed = await self.get_cached_help(query)
                if embed:
                    await ctx.send(embed=embed)
                    return

            # Kiểm tra xem query có phải là lệnh không
            command = self.bot.get_command(query)
            if command:
                await self.send_command_help(ctx, command)
                return

            # Nếu không tìm thấy, tìm kiếm gần đúng
            await self.send_search_results(ctx, query)

        except Exception as e:
            print(f"Lỗi khi hiển thị help: {e}")
            await ctx.send("Có lỗi xảy ra khi hiển thị hướng dẫn. Vui lòng thử lại sau!")

    async def send_command_help(self, ctx, command):
        """Hiển thị thông tin chi tiết về một lệnh cụ thể"""
        # Tạo embed thông tin lệnh
        embed = discord.Embed(
            title=f"📖 Hướng Dẫn: !{command.name}",
            description=command.help or "Không có mô tả chi tiết.",
            color=0x3498db
        )

        # Thêm cách sử dụng
        usage = command.usage or ""
        embed.add_field(
            name="🔍 Cách Sử Dụng",
            value=f"`!{command.name} {usage}`",
            inline=False
        )

        # Thêm các tên gọi khác
        if command.aliases:
            embed.add_field(
                name="🔄 Tên Gọi Khác",
                value=", ".join([f"`!{alias}`" for alias in command.aliases]),
                inline=False
            )

        # Thêm thông tin cooldown nếu có
        if command._buckets and command._buckets._cooldown:
            cooldown = command._buckets._cooldown
            embed.add_field(
                name="⏱️ Cooldown",
                value=f"{cooldown.rate} lần trong {cooldown.per:.0f} giây",
                inline=True
            )

        # Thêm thông tin quyền hạn nếu có
        if command.checks:
            permissions = []
            for check in command.checks:
                if "has_permissions" in str(check):
                    permissions.append("Yêu cầu quyền quản trị")
                elif "is_owner" in str(check):
                    permissions.append("Chỉ dành cho chủ bot")
                elif "guild_only" in str(check):
                    permissions.append("Chỉ sử dụng trong server")

            if permissions:
                embed.add_field(
                    name="🔒 Yêu Cầu",
                    value="\n".join(permissions),
                    inline=True
                )

        # Thêm ví dụ sử dụng
        examples = self.get_command_examples(command.name)
        if examples:
            embed.add_field(
                name="📝 Ví Dụ",
                value="\n".join(examples),
                inline=False
            )

        await ctx.send(embed=embed)

    def get_command_examples(self, command_name: str) -> List[str]:
        """Lấy các ví dụ sử dụng cho lệnh"""
        examples = {
            "tuvi": [
                "`!tuvi` - Xem tu vi của bản thân",
                "`!tuvi @Nguyễn Văn A` - Xem tu vi của người khác"
            ],
            "daily": [
                "`!daily` - Điểm danh nhận thưởng hàng ngày"
            ],
            "danhquai": [
                "`!danhquai` - Đánh quái vật ngẫu nhiên"
            ],
            "danhboss": [
                "`!danhboss` - Đánh boss một mình",
                "`!danhboss @Nguyễn Văn A @Nguyễn Văn B` - Rủ người khác cùng đánh boss"
            ],
            "combat": [
                "`!combat @Nguyễn Văn A` - Thách đấu PvP với người chơi khác"
            ],
            "top": [
                "`!top` - Xem top 10 người chơi",
                "`!top all 20` - Xem top 20 người chơi",
                "`!top sect` - Xem top theo môn phái"
            ],
            "tongmon": [
                "`!tongmon` - Xem danh sách môn phái",
                "`!tongmon join Thiên Kiếm Tông` - Gia nhập môn phái"
            ]
        }

        return examples.get(command_name, [])

    async def send_search_results(self, ctx, query: str):
        """Tìm kiếm và hiển thị kết quả gần đúng"""
        # Tìm kiếm trong các lệnh
        commands = []
        for command in self.bot.commands:
            if query in command.name or any(query in alias for alias in command.aliases):
                commands.append(command)

        # Tìm kiếm trong các chủ đề
        topics = []
        for topic, title in self.topics.items():
            if query in topic or query in title.lower():
                topics.append((topic, title))

        # Tạo embed kết quả tìm kiếm
        embed = discord.Embed(
            title=f"🔍 Kết Quả Tìm Kiếm: '{query}'",
            description="Dưới đây là các kết quả phù hợp với tìm kiếm của bạn:",
            color=0x3498db
        )

        # Thêm kết quả lệnh
        if commands:
            command_list = []
            for cmd in commands[:5]:  # Giới hạn 5 kết quả
                desc = cmd.help.split('\n')[0] if cmd.help else "Không có mô tả"
                command_list.append(f"• `!{cmd.name}` - {desc[:50]}...")

            embed.add_field(
                name="🎮 Lệnh",
                value="\n".join(command_list) if command_list else "Không tìm thấy lệnh phù hợp",
                inline=False
            )

        # Thêm kết quả chủ đề
        if topics:
            topic_list = []
            for topic_id, title in topics:
                topic_list.append(f"• `!help {topic_id}` - {title}")

            embed.add_field(
                name="📚 Chủ Đề",
                value="\n".join(topic_list) if topic_list else "Không tìm thấy chủ đề phù hợp",
                inline=False
            )

        # Nếu không có kết quả nào
        if not commands and not topics:
            embed.description = f"Không tìm thấy kết quả nào cho '{query}'. Vui lòng thử lại với từ khóa khác."
            embed.add_field(
                name="💡 Gợi Ý",
                value=(
                    "• Sử dụng `!help` để xem danh sách chủ đề\n"
                    "• Sử dụng `!tutien` để xem hướng dẫn tổng quan\n"
                    "• Kiểm tra lại chính tả của từ khóa"
                ),
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.command(name='helpinteractive', aliases=['helpint'])
    async def help_interactive(self, ctx):
        """Hiển thị hướng dẫn tương tác"""
        # Kiểm tra xem người dùng đã có phiên tương tác chưa
        if ctx.author.id in self.interactive_sessions:
            await ctx.send("Bạn đã có một phiên hướng dẫn tương tác đang hoạt động. Vui lòng kết thúc phiên đó trước.")
            return

        # Tạo embed chính
        main_embed = await self.get_cached_help("main")

        # Thêm hướng dẫn sử dụng nút
        main_embed.add_field(
            name="🔄 Hướng Dẫn Tương Tác",
            value=(
                "Sử dụng các nút bên dưới để điều hướng:\n"
                "• ⏮️ - Trang đầu\n"
                "• ◀️ - Trang trước\n"
                "• ▶️ - Trang tiếp\n"
                "• ⏭️ - Trang cuối\n"
                "• ❌ - Đóng hướng dẫn"
            ),
            inline=False
        )

        # Gửi embed và thêm reaction
        message = await ctx.send(embed=main_embed)

        # Thêm các reaction để điều hướng
        for emoji in self.nav_emojis.values():
            await message.add_reaction(emoji)

        # Lưu thông tin phiên tương tác
        self.interactive_sessions[ctx.author.id] = {
            "message_id": message.id,
            "channel_id": ctx.channel.id,
            "current_page": 0,
            "pages": ["main", "commands", "exp", "levels", "sects", "combat", "items", "events"]
        }

        # Tạo task để tự động kết thúc phiên sau 5 phút
        self.bot.loop.create_task(self.end_interactive_session(ctx.author.id, 300))

    async def end_interactive_session(self, user_id: int, delay: int):
        """Kết thúc phiên tương tác sau một khoảng thời gian"""
        await asyncio.sleep(delay)
        if user_id in self.interactive_sessions:
            del self.interactive_sessions[user_id]

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Xử lý phản ứng cho hướng dẫn tương tác"""
        # Bỏ qua phản ứng của bot
        if user.bot:
            return

        # Kiểm tra xem người dùng có phiên tương tác không
        if user.id not in self.interactive_sessions:
            return

        # Lấy thông tin phiên
        session = self.interactive_sessions[user.id]

        # Kiểm tra xem reaction có phải trên tin nhắn của phiên không
        if reaction.message.id != session["message_id"]:
            return

        # Xử lý các loại reaction
        emoji = str(reaction.emoji)
        current_page = session["current_page"]
        pages = session["pages"]

        # Xóa reaction của người dùng
        try:
            await reaction.remove(user)
        except:
            pass  # Bỏ qua nếu không có quyền xóa reaction

        # Xử lý điều hướng
        if emoji == self.nav_emojis["first"]:
            current_page = 0
        elif emoji == self.nav_emojis["prev"]:
            current_page = max(0, current_page - 1)
        elif emoji == self.nav_emojis["next"]:
            current_page = min(len(pages) - 1, current_page + 1)
        elif emoji == self.nav_emojis["last"]:
            current_page = len(pages) - 1
        elif emoji == self.nav_emojis["close"]:
            # Kết thúc phiên
            del self.interactive_sessions[user.id]
            try:
                await reaction.message.clear_reactions()
            except:
                pass
            return

        # Cập nhật trang hiện tại
        session["current_page"] = current_page

        # Lấy embed mới
        new_embed = await self.get_cached_help(pages[current_page])

        # Thêm thông tin trang
        new_embed.set_footer(text=f"Trang {current_page + 1}/{len(pages)} • {self.topics[pages[current_page]]}")

        # Cập nhật tin nhắn
        try:
            channel = self.bot.get_channel(session["channel_id"])
            message = await channel.fetch_message(session["message_id"])
            await message.edit(embed=new_embed)
        except:
            # Nếu có lỗi, kết thúc phiên
            if user.id in self.interactive_sessions:
                del self.interactive_sessions[user.id]

    @commands.command(name='helpupdate')
    @commands.has_permissions(administrator=True)
    async def update_help_cache(self, ctx):
        """Cập nhật cache help (Admin only)"""
        try:
            async with self.cache_lock:
                self.help_cache.clear()
            await ctx.send("✅ Đã cập nhật cache help thành công!")
        except Exception as e:
            print(f"Lỗi khi cập nhật cache help: {e}")
            await ctx.send("❌ Có lỗi xảy ra khi cập nhật cache!")

    @commands.command(name='helpadmin')
    @commands.has_permissions(administrator=True)
    async def help_admin(self, ctx):
        """Hiển thị các lệnh quản trị (Admin only)"""
        embed = discord.Embed(
            title="👑 Lệnh Quản Trị",
            description="Các lệnh dành cho quản trị viên:",
            color=0xe74c3c
        )

        # Quản lý người chơi
        embed.add_field(
            name="👥 Quản Lý Người Chơi",
            value=(
                "`!setexp @user [số_exp]` - Đặt EXP cho người chơi\n"
                "`!addexp @user [số_exp]` - Thêm EXP cho người chơi\n"
                "`!setlevel @user [cảnh_giới]` - Đặt cảnh giới cho người chơi\n"
                "`!resetplayer @user` - Reset dữ liệu người chơi"
            ),
            inline=False
        )

        # Quản lý hệ thống
        embed.add_field(
            name="⚙️ Quản Lý Hệ Thống",
            value=(
                "`!reload [module]` - Tải lại module\n"
                "`!helpupdate` - Cập nhật cache help\n"
                "`!announce [nội_dung]` - Gửi thông báo toàn server\n"
                "`!setcooldown [lệnh] [giây]` - Đặt cooldown cho lệnh"
            ),
            inline=False
        )

        # Quản lý sự kiện
        embed.add_field(
            name="🎉 Quản Lý Sự Kiện",
            value=(
                "`!createevent [tên] [mô_tả]` - Tạo sự kiện mới\n"
                "`!endevent [id]` - Kết thúc sự kiện\n"
                "`!addboss [tên] [HP] [ATK] [DEF]` - Thêm boss mới\n"
                "`!additem [tên] [loại] [hiếm]` - Thêm vật phẩm mới"
            ),
            inline=False
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Help(bot))