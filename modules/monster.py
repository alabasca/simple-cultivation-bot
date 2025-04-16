import discord
from discord.ext import commands
from datetime import datetime, timedelta
import random
import asyncio
import math
from typing import Dict, List, Tuple, Optional, Union, Any
from modules.utils import format_time
from config import (
    MONSTER_COOLDOWN, BOSS_COOLDOWN,
    MONSTER_HP_MULTIPLIER, MONSTER_ATK_MULTIPLIER,
    BOSS_HP_MULTIPLIER, BOSS_ATK_MULTIPLIER,
    MONSTER_EXP, BOSS_EXP
)


class Monster(commands.Cog):
    """Hệ thống săn quái vật và boss"""

    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.combat_locks = {}  # Lock cho mỗi người chơi
        self.monster_types = self.load_monster_types()
        self.boss_battles = {}  # Lưu thông tin các trận đánh boss nhóm
        self.item_drops = self.load_item_drops()
        self.combat_messages = self.load_combat_messages()

        # Tạo task định kỳ để dọn dẹp các trận đánh boss cũ
        self.bot.loop.create_task(self.cleanup_boss_battles())

    def load_monster_types(self) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """Load các loại quái vật và boss với thông tin chi tiết hơn"""
        return {
            "monster": {
                "normal": [
                    {"name": "Yêu Lang", "type": "Thú", "element": "Mộc",
                     "description": "Sói yêu có sức mạnh trung bình"},
                    {"name": "Hắc Hổ", "type": "Thú", "element": "Kim", "description": "Hổ đen với móng vuốt sắc bén"},
                    {"name": "Độc Xà", "type": "Thú", "element": "Thủy", "description": "Rắn độc có thể phun nọc độc"},
                    {"name": "Huyết Điểu", "type": "Thú", "element": "Hỏa",
                     "description": "Chim máu với đôi cánh sắc như dao"},
                    {"name": "Thực Hồn Thảo", "type": "Thực Vật", "element": "Mộc",
                     "description": "Cỏ ăn hồn hút sinh lực của tu sĩ"},
                    {"name": "Hắc Ưng", "type": "Thú", "element": "Kim",
                     "description": "Đại bàng đen với tốc độ kinh người"},
                    {"name": "Ma Hầu", "type": "Thú", "element": "Thổ",
                     "description": "Khỉ ma tinh quái và nhanh nhẹn"},
                    {"name": "Thi Quỷ", "type": "Quỷ", "element": "Âm",
                     "description": "Quỷ xác chết với móng vuốt sắc nhọn"}
                ],
                "elite": [
                    {"name": "Tam Đầu Yêu Lang", "type": "Thú", "element": "Mộc",
                     "description": "Sói ba đầu với sức mạnh kinh người"},
                    {"name": "Ngũ Vĩ Hắc Hổ", "type": "Thú", "element": "Kim",
                     "description": "Hổ đen năm đuôi với sức mạnh phi thường"},
                    {"name": "Cửu Đầu Xà", "type": "Thú", "element": "Thủy",
                     "description": "Rắn chín đầu với nọc độc chết người"},
                    {"name": "Huyết Phượng", "type": "Thú", "element": "Hỏa",
                     "description": "Phượng hoàng máu với lửa thiêu đốt linh hồn"},
                    {"name": "Thực Hồn Vương Thảo", "type": "Thực Vật", "element": "Mộc",
                     "description": "Vua của các loài cỏ ăn hồn"}
                ],
                "boss": [
                    {"name": "Yêu Lang Vương", "type": "Thú", "element": "Mộc", "description": "Vua của loài sói yêu"},
                    {"name": "Hắc Hổ Vương", "type": "Thú", "element": "Kim", "description": "Vua của loài hổ đen"},
                    {"name": "Xà Đế", "type": "Thú", "element": "Thủy", "description": "Hoàng đế của loài rắn"},
                    {"name": "Huyết Điểu Vương", "type": "Thú", "element": "Hỏa",
                     "description": "Vua của loài chim máu"}
                ]
            },
            "boss": {
                "normal": [
                    {"name": "Yêu Vương", "type": "Thú", "element": "Mộc", "description": "Vua của các loài yêu thú",
                     "skills": ["Yêu Khí Phệ Thiên", "Thú Vương Nộ"]},
                    {"name": "Hắc Hổ Vương", "type": "Thú", "element": "Kim", "description": "Vua của loài hổ đen",
                     "skills": ["Hắc Hổ Trảo", "Vương Giả Nộ Khiếu"]},
                    {"name": "Xà Đế", "type": "Thú", "element": "Thủy", "description": "Hoàng đế của loài rắn",
                     "skills": ["Vạn Độc Phệ Tâm", "Xà Đế Thôn Thiên"]},
                    {"name": "Huyết Điểu Vương", "type": "Thú", "element": "Hỏa",
                     "description": "Vua của loài chim máu", "skills": ["Huyết Vũ Thiên Hạ", "Phần Thiên Dẫn Lôi"]},
                    {"name": "Thực Hồn Đại Đế", "type": "Thực Vật", "element": "Mộc",
                     "description": "Đế vương của các loài cỏ ăn hồn",
                     "skills": ["Thôn Hồn Thuật", "Vạn Mộc Phệ Tinh"]},
                    {"name": "Hắc Ưng Vương", "type": "Thú", "element": "Kim",
                     "description": "Vua của loài đại bàng đen", "skills": ["Thiên Không Liệt", "Ưng Vương Trảo"]},
                    {"name": "Ma Hầu Vương", "type": "Thú", "element": "Thổ", "description": "Vua của loài khỉ ma",
                     "skills": ["Địa Sát Quyền", "Hầu Vương Nộ"]}
                ],
                "elite": [
                    {"name": "Cửu Thiên Yêu Vương", "type": "Thú", "element": "Hỗn Độn",
                     "description": "Yêu vương cửu thiên với sức mạnh hủy diệt",
                     "skills": ["Cửu Thiên Phá", "Yêu Vương Quyết", "Thiên Địa Vô Cực"]},
                    {"name": "Bách Thú Vương", "type": "Thú", "element": "Ngũ Hành",
                     "description": "Vua của trăm loài thú",
                     "skills": ["Bách Thú Triều Bái", "Vạn Thú Phục Tùng", "Thú Vương Oai"]},
                    {"name": "Vạn Xà Đại Đế", "type": "Thú", "element": "Thủy",
                     "description": "Đại đế của vạn loài rắn",
                     "skills": ["Vạn Xà Triều Bái", "Đại Đế Uy", "Vạn Độc Thiên Hạ"]},
                    {"name": "Huyết Phượng Hoàng", "type": "Thú", "element": "Hỏa",
                     "description": "Phượng hoàng máu với sức mạnh hủy diệt",
                     "skills": ["Phượng Hoàng Vũ", "Huyết Hỏa Thiêu Thiên", "Niết Bàn Trùng Sinh"]}
                ]
            }
        }

    def load_item_drops(self) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """Load danh sách vật phẩm có thể rơi ra"""
        return {
            "monster": {
                "normal": [
                    {"name": "Yêu Lang Nha", "type": "Nguyên Liệu", "rarity": "Phổ Thông", "value": 10, "chance": 0.3},
                    {"name": "Hắc Hổ Trảo", "type": "Nguyên Liệu", "rarity": "Phổ Thông", "value": 15, "chance": 0.25},
                    {"name": "Xà Đảm", "type": "Nguyên Liệu", "rarity": "Phổ Thông", "value": 12, "chance": 0.3},
                    {"name": "Huyết Điểu Vũ", "type": "Nguyên Liệu", "rarity": "Phổ Thông", "value": 8, "chance": 0.35},
                    {"name": "Linh Thảo", "type": "Dược Liệu", "rarity": "Phổ Thông", "value": 20, "chance": 0.2},
                    {"name": "Tiểu Hồi Khí Đan", "type": "Đan Dược", "rarity": "Phổ Thông", "value": 30, "chance": 0.1}
                ],
                "elite": [
                    {"name": "Tam Đầu Lang Nha", "type": "Nguyên Liệu", "rarity": "Hiếm", "value": 50, "chance": 0.4},
                    {"name": "Ngũ Vĩ Hổ Trảo", "type": "Nguyên Liệu", "rarity": "Hiếm", "value": 60, "chance": 0.35},
                    {"name": "Cửu Đầu Xà Đảm", "type": "Nguyên Liệu", "rarity": "Hiếm", "value": 55, "chance": 0.4},
                    {"name": "Huyết Phượng Vũ", "type": "Nguyên Liệu", "rarity": "Hiếm", "value": 70, "chance": 0.3},
                    {"name": "Trung Phẩm Linh Thạch", "type": "Tài Nguyên", "rarity": "Hiếm", "value": 100,
                     "chance": 0.2},
                    {"name": "Hồi Khí Đan", "type": "Đan Dược", "rarity": "Hiếm", "value": 80, "chance": 0.25}
                ]
            },
            "boss": {
                "normal": [
                    {"name": "Yêu Vương Tinh", "type": "Nguyên Liệu", "rarity": "Quý", "value": 200, "chance": 0.5},
                    {"name": "Hắc Hổ Vương Tâm", "type": "Nguyên Liệu", "rarity": "Quý", "value": 250, "chance": 0.45},
                    {"name": "Xà Đế Đảm", "type": "Nguyên Liệu", "rarity": "Quý", "value": 220, "chance": 0.5},
                    {"name": "Huyết Điểu Vương Lông", "type": "Nguyên Liệu", "rarity": "Quý", "value": 180,
                     "chance": 0.55},
                    {"name": "Thượng Phẩm Linh Thạch", "type": "Tài Nguyên", "rarity": "Quý", "value": 300,
                     "chance": 0.3},
                    {"name": "Đại Hồi Khí Đan", "type": "Đan Dược", "rarity": "Quý", "value": 250, "chance": 0.35},
                    {"name": "Tăng Lực Đan", "type": "Đan Dược", "rarity": "Quý", "value": 280, "chance": 0.25}
                ],
                "elite": [
                    {"name": "Cửu Thiên Yêu Vương Tinh", "type": "Nguyên Liệu", "rarity": "Cực Phẩm", "value": 1000,
                     "chance": 0.6},
                    {"name": "Bách Thú Vương Tâm", "type": "Nguyên Liệu", "rarity": "Cực Phẩm", "value": 1200,
                     "chance": 0.55},
                    {"name": "Vạn Xà Đại Đế Đảm", "type": "Nguyên Liệu", "rarity": "Cực Phẩm", "value": 1100,
                     "chance": 0.6},
                    {"name": "Huyết Phượng Hoàng Vũ", "type": "Nguyên Liệu", "rarity": "Cực Phẩm", "value": 1300,
                     "chance": 0.5},
                    {"name": "Cực Phẩm Linh Thạch", "type": "Tài Nguyên", "rarity": "Cực Phẩm", "value": 1500,
                     "chance": 0.4},
                    {"name": "Tẩy Tủy Đan", "type": "Đan Dược", "rarity": "Cực Phẩm", "value": 2000, "chance": 0.2},
                    {"name": "Bí Tịch Tàn Quyển", "type": "Bí Kíp", "rarity": "Cực Phẩm", "value": 5000, "chance": 0.1}
                ]
            }
        }

    def load_combat_messages(self) -> Dict[str, List[str]]:
        """Load các thông báo chiến đấu đa dạng"""
        return {
            "player_attack": [
                "🗡️ {player} tung một chiêu {skill}, gây {damage} sát thương!",
                "⚔️ {player} vận công phóng ra một đạo kiếm khí, gây {damage} sát thương!",
                "👊 {player} thi triển {skill}, đánh trúng {target}, gây {damage} sát thương!",
                "💥 {player} bất ngờ tấn công, {target} không kịp phòng bị, nhận {damage} sát thương!",
                "🔥 {player} vận dụng hỏa thuật, thiêu đốt {target}, gây {damage} sát thương!"
            ],
            "player_crit": [
                "⚡ {player} thi triển tuyệt kỹ {skill}, đánh trúng điểm yếu của {target}, gây {damage} sát thương chí mạng!",
                "💯 Một đòn trí mạng! {player} gây ra {damage} sát thương kinh hoàng!",
                "🌟 {player} tìm ra điểm yếu của {target}, tung đòn quyết định, gây {damage} sát thương chí mạng!",
                "⭐ Tuyệt chiêu! {player} gây ra {damage} sát thương chí mạng với {skill}!",
                "🔴 Đòn đánh trí mạng! {player} khiến {target} trọng thương với {damage} sát thương!"
            ],
            "monster_attack": [
                "👿 {monster} gầm lên đầy giận dữ, tấn công {player}, gây {damage} sát thương!",
                "🐺 {monster} nhe nanh múa vuốt, gây {damage} sát thương cho {player}!",
                "🦂 {monster} phun nọc độc vào {player}, gây {damage} sát thương!",
                "🐍 {monster} quấn lấy {player}, siết chặt và gây {damage} sát thương!",
                "🦇 {monster} lao vào {player} với tốc độ kinh người, gây {damage} sát thương!"
            ],
            "boss_attack": [
                "👑 {boss} thi triển {skill}, đại địa rung chuyển, gây {damage} sát thương cho {player}!",
                "🔱 {boss} gầm lên một tiếng, không gian vỡ vụn, {player} nhận {damage} sát thương!",
                "🌋 {boss} thi triển tuyệt kỹ {skill}, {player} không kịp né tránh, nhận {damage} sát thương!",
                "⚡ {boss} vận dụng thiên địa chi lực, đánh trúng {player}, gây {damage} sát thương!",
                "🌀 {boss} tạo ra một cơn lốc năng lượng, cuốn lấy {player}, gây {damage} sát thương!"
            ],
            "boss_crit": [
                "💥 {boss} thi triển tuyệt kỹ bí truyền {skill}, đánh trúng điểm yếu của {player}, gây {damage} sát thương chí mạng!",
                "☄️ Đòn tấn công hủy diệt! {boss} gây ra {damage} sát thương kinh hoàng cho {player}!",
                "🌠 {boss} tập trung toàn bộ sức mạnh, tung đòn quyết định, gây {damage} sát thương chí mạng cho {player}!",
                "🔥 Thiên địa biến sắc! {boss} gây ra {damage} sát thương chí mạng với {skill}!",
                "⚠️ Đòn đánh hủy diệt! {boss} khiến {player} trọng thương với {damage} sát thương!"
            ],
            "player_dodge": [
                "🌀 {player} thi triển thân pháp, né tránh đòn tấn công của {enemy}!",
                "💨 {player} lướt nhanh như gió, tránh được đòn tấn công!",
                "✨ {player} thi triển tuyệt kỹ, khiến {enemy} đánh trượt!",
                "🌪️ {player} xoay người trong không trung, tránh được đòn tấn công của {enemy}!",
                "🏃 {player} di chuyển nhanh như chớp, khiến {enemy} không thể chạm tới!"
            ],
            "enemy_dodge": [
                "💨 {enemy} di chuyển nhanh như chớp, tránh được đòn tấn công của {player}!",
                "🌀 {enemy} lướt đi như một cơn gió, khiến {player} đánh trượt!",
                "🏃 {enemy} né tránh đòn tấn công một cách tinh tế!",
                "✨ {enemy} thi triển kỹ năng phòng thủ, khiến đòn tấn công của {player} vô hiệu!",
                "🌪️ {enemy} biến mất trong làn khói, tránh được đòn tấn công!"
            ],
            "victory": [
                "🎉 {player} đã đánh bại {enemy}! Nhận được {exp} exp và {items}!",
                "🏆 Chiến thắng! {player} đã hạ gục {enemy} và nhận được {exp} exp cùng {items}!",
                "💯 {player} đã tiêu diệt {enemy}! Thu hoạch {exp} exp và {items}!",
                "🌟 Thắng lợi! {player} đã đánh bại {enemy}, nhận {exp} exp và {items}!",
                "🔥 {player} đã chiến thắng {enemy}! Phần thưởng: {exp} exp và {items}!"
            ],
            "defeat": [
                "💀 {player} đã bị đánh bại bởi {enemy}! Không nhận được phần thưởng.",
                "☠️ Thất bại! {player} đã ngã xuống trước {enemy}.",
                "😵 {player} không địch lại sức mạnh của {enemy} và bị đánh bại.",
                "💔 {player} đã kiệt sức và thua cuộc trước {enemy}.",
                "🏳️ {player} buộc phải rút lui trước sức mạnh của {enemy}."
            ]
        }

    async def get_combat_lock(self, user_id: int) -> asyncio.Lock:
        """Lấy hoặc tạo lock cho người chơi"""
        if user_id not in self.combat_locks:
            self.combat_locks[user_id] = asyncio.Lock()
        return self.combat_locks[user_id]

    async def cleanup_boss_battles(self):
        """Dọn dẹp các trận đánh boss cũ định kỳ"""
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                current_time = datetime.now()
                to_remove = []

                for battle_id, battle_info in self.boss_battles.items():
                    # Xóa các trận đánh đã kết thúc hoặc quá 30 phút
                    if battle_info['ended'] or (current_time - battle_info['start_time']).total_seconds() > 1800:
                        to_remove.append(battle_id)

                for battle_id in to_remove:
                    del self.boss_battles[battle_id]

            except Exception as e:
                print(f"Lỗi khi dọn dẹp trận đánh boss: {e}")

            await asyncio.sleep(300)  # Kiểm tra mỗi 5 phút

    async def check_combat_conditions(self, ctx, action_type: str) -> Tuple[Optional[Dict], Optional[datetime]]:
        """Kiểm tra điều kiện trước khi chiến đấu"""
        player = await self.db.get_player(ctx.author.id)
        if not player:
            await ctx.send("Ngươi chưa gia nhập môn phái nào! Hãy vào kênh tông-môn-chi-lộ để chọn môn phái.")
            return None, None

        # Kiểm tra cooldown
        last_action = player.get(f'last_{action_type}')
        cooldown = MONSTER_COOLDOWN if action_type == 'monster' else BOSS_COOLDOWN

        if last_action:
            time_passed = datetime.now() - last_action
            if time_passed.total_seconds() < cooldown:
                remaining = cooldown - time_passed.total_seconds()

                # Tạo thông báo cooldown thân thiện
                if action_type == 'monster':
                    messages = [
                        f"⏳ Ngươi vẫn đang hồi phục sau trận chiến trước. Còn {format_time(int(remaining))} nữa mới có thể đánh quái!",
                        f"🔄 Khí hải chưa hồi phục hoàn toàn. Hãy đợi thêm {format_time(int(remaining))} nữa!",
                        f"⌛ Cần thêm {format_time(int(remaining))} để khôi phục linh lực trước khi đánh quái tiếp!"
                    ]
                else:
                    messages = [
                        f"⏳ Ngươi vẫn đang hồi phục sau trận chiến với boss. Còn {format_time(int(remaining))} nữa!",
                        f"🔄 Đánh boss tiêu hao quá nhiều linh lực. Hãy đợi thêm {format_time(int(remaining))} nữa!",
                        f"⌛ Cần thêm {format_time(int(remaining))} để khôi phục đủ sức mạnh đánh boss!"
                    ]

                await ctx.send(random.choice(messages))
                return None, None

        return player, last_action

    async def simulate_combat(self, player_stats: Dict, enemy_stats: Dict, max_rounds: int = 10) -> Tuple[
        int, int, List[str]]:
        """Mô phỏng trận chiến với nhiều yếu tố ngẫu nhiên và kỹ năng"""
        player_hp = player_stats['hp']
        enemy_hp = enemy_stats['hp']
        battle_log = []
        rounds = 0

        # Danh sách kỹ năng người chơi dựa trên cảnh giới
        player_skills = self.get_player_skills(player_stats.get('level', 'Phàm Nhân'))

        # Danh sách kỹ năng của quái/boss
        enemy_skills = enemy_stats.get('skills', ['Tấn Công Thường'])

        while enemy_hp > 0 and player_hp > 0 and rounds < max_rounds:
            # Player attacks
            # Xác định có né tránh không
            if random.random() < 0.1:  # 10% cơ hội né tránh
                dodge_msg = random.choice(self.combat_messages['enemy_dodge'])
                battle_log.append(dodge_msg.format(
                    enemy=enemy_stats['name'],
                    player=player_stats.get('name', 'Tu sĩ')
                ))
            else:
                # Xác định có chí mạng không
                is_crit = random.random() < 0.15  # 15% cơ hội chí mạng

                # Chọn kỹ năng ngẫu nhiên
                skill = random.choice(player_skills)

                # Tính sát thương
                damage_multiplier = 1.5 if is_crit else (0.8 + random.random() * 0.4)
                damage = int(player_stats['attack'] * damage_multiplier)
                enemy_hp -= damage

                # Thêm log chiến đấu
                if is_crit:
                    msg = random.choice(self.combat_messages['player_crit'])
                else:
                    msg = random.choice(self.combat_messages['player_attack'])

                battle_log.append(msg.format(
                    player=player_stats.get('name', 'Tu sĩ'),
                    target=enemy_stats['name'],
                    damage=damage,
                    skill=skill
                ))

            # Enemy counterattack if still alive
            if enemy_hp > 0:
                # Xác định có né tránh không
                if random.random() < 0.08:  # 8% cơ hội né tránh
                    dodge_msg = random.choice(self.combat_messages['player_dodge'])
                    battle_log.append(dodge_msg.format(
                        player=player_stats.get('name', 'Tu sĩ'),
                        enemy=enemy_stats['name']
                    ))
                else:
                    # Xác định có chí mạng không
                    is_crit = random.random() < 0.12  # 12% cơ hội chí mạng

                    # Chọn kỹ năng ngẫu nhiên
                    skill = random.choice(enemy_skills)

                    # Tính sát thương
                    damage_multiplier = 1.5 if is_crit else (0.8 + random.random() * 0.4)
                    enemy_damage = int(enemy_stats['attack'] * damage_multiplier)
                    player_hp -= enemy_damage

                    # Thêm log chiến đấu
                    if 'boss' in enemy_stats:
                        if is_crit:
                            msg = random.choice(self.combat_messages['boss_crit'])
                        else:
                            msg = random.choice(self.combat_messages['boss_attack'])

                        battle_log.append(msg.format(
                            boss=enemy_stats['name'],
                            player=player_stats.get('name', 'Tu sĩ'),
                            damage=enemy_damage,
                            skill=skill
                        ))
                    else:
                        msg = random.choice(self.combat_messages['monster_attack'])
                        battle_log.append(msg.format(
                            monster=enemy_stats['name'],
                            player=player_stats.get('name', 'Tu sĩ'),
                            damage=enemy_damage
                        ))

            rounds += 1
            # Thêm delay nhỏ để tạo cảm giác thực tế
            await asyncio.sleep(0.1)

        return player_hp, enemy_hp, battle_log

    def get_player_skills(self, level: str) -> List[str]:
        """Lấy danh sách kỹ năng người chơi dựa trên cảnh giới"""
        # Kỹ năng cơ bản
        basic_skills = ["Quyền Cước", "Kiếm Pháp Cơ Bản", "Chưởng Pháp"]

        # Kỹ năng theo cảnh giới
        if "Luyện Khí" in level:
            return basic_skills + ["Linh Khí Quyền", "Ngưng Khí Thuật"]
        elif "Trúc Cơ" in level:
            return basic_skills + ["Linh Khí Quyền", "Ngưng Khí Thuật", "Trúc Cơ Kiếm Pháp", "Linh Khí Phá"]
        elif "Nguyên Anh" in level:
            return basic_skills + ["Trúc Cơ Kiếm Pháp", "Linh Khí Phá", "Nguyên Anh Chưởng", "Thiên Địa Hợp Nhất"]
        elif "Kim Đan" in level or higher_level(level):
            return ["Linh Khí Phá", "Nguyên Anh Chưởng", "Thiên Địa Hợp Nhất", "Kiếm Khí Trảm", "Đại Đạo Vô Hình",
                    "Tiên Thiên Công"]
        else:
            return basic_skills

    def higher_level(self, level: str) -> bool:
        """Kiểm tra xem cảnh giới có cao hơn Kim Đan không"""
        high_levels = ["Hóa Thần", "Luyện Hư", "Đại Thừa", "Diễn Chủ"]
        return any(high in level for high in high_levels)

    async def roll_for_items(self, enemy_type: str, is_elite: bool) -> List[Dict[str, Any]]:
        """Quay ngẫu nhiên vật phẩm rơi ra"""
        category = "boss" if enemy_type == "boss" else "monster"
        rarity = "elite" if is_elite else "normal"

        possible_items = self.item_drops[category][rarity]
        dropped_items = []

        # Số lượng vật phẩm có thể rơi ra
        max_items = 2 if enemy_type == "monster" else 3
        if is_elite:
            max_items += 1

        # Xác định số lượng vật phẩm thực tế
        num_items = random.randint(1, max_items)

        # Quay ngẫu nhiên vật phẩm
        for _ in range(num_items):
            for item in possible_items:
                if random.random() < item["chance"]:
                    # Thêm số lượng ngẫu nhiên
                    quantity = 1
                    if item["type"] == "Nguyên Liệu":
                        quantity = random.randint(1, 3)
                    elif item["type"] == "Tài Nguyên":
                        quantity = random.randint(1, 2)

                    dropped_items.append({
                        "name": item["name"],
                        "type": item["type"],
                        "rarity": item["rarity"],
                        "value": item["value"],
                        "quantity": quantity
                    })
                    break

        return dropped_items

    async def create_combat_embed(
            self,
            ctx,
            enemy_type: str,
            player_stats: Dict,
            enemy_stats: Dict,
            battle_log: List,
            is_victory: bool,
            exp_gained: int = 0,
            items_gained: List = None
    ) -> discord.Embed:
        """Tạo embed hiển thị kết quả trận đấu"""
        color = 0x00ff00 if is_victory else 0xff0000
        title_emoji = "🗡️" if enemy_type == "monster" else "👑"

        # Xác định tiêu đề dựa trên loại kẻ địch
        if enemy_type == "monster":
            if enemy_stats.get('is_elite', False):
                title = f"{title_emoji} Đánh Quái Vật Tinh Anh"
            else:
                title = f"{title_emoji} Đánh Quái Vật"
        else:
            if enemy_stats.get('is_elite', False):
                title = f"{title_emoji} Đánh Boss Tinh Anh"
            else:
                title = f"{title_emoji} Đánh Boss"

        embed = discord.Embed(
            title=title,
            description=f"{ctx.author.mention} đang chiến đấu với {enemy_stats['name']}...",
            color=color,
            timestamp=datetime.now()
        )

        # Thông tin HP
        embed.add_field(
            name=f"❤️ Máu {enemy_stats['name']}",
            value=f"{max(0, enemy_stats['current_hp']):,}/{enemy_stats['hp']:,}",
            inline=True
        )
        embed.add_field(
            name="❤️ Máu Tu Sĩ",
            value=f"{max(0, player_stats['current_hp']):,}/{player_stats['hp']:,}",
            inline=True
        )

        # Thông tin kẻ địch
        enemy_info = f"**Loại:** {enemy_stats.get('type', 'Không rõ')}\n"
        enemy_info += f"**Nguyên tố:** {enemy_stats.get('element', 'Không rõ')}\n"

        if enemy_stats.get('description'):
            enemy_info += f"**Mô tả:** {enemy_stats['description']}\n"

        if enemy_stats.get('skills') and len(enemy_stats['skills']) > 0:
            enemy_info += f"**Kỹ năng:** {', '.join(enemy_stats['skills'])}"

        embed.add_field(
            name=f"📋 Thông Tin {enemy_stats['name']}",
            value=enemy_info,
            inline=False
        )

        # Log chiến đấu
        if battle_log:
            log_text = "\n".join(battle_log[-5:])  # Chỉ hiện 5 dòng cuối
            embed.add_field(
                name="⚔️ Diễn Biến Chiến Đấu",
                value=f"```\n{log_text}\n```",
                inline=False
            )

        # Kết quả
        if is_victory:
            # Hiển thị vật phẩm nhận được
            items_text = ""
            if items_gained and len(items_gained) > 0:
                items_list = []
                for item in items_gained:
                    rarity_emoji = "⚪" if item["rarity"] == "Phổ Thông" else "🔵" if item["rarity"] == "Hiếm" else "🟣" if \
                    item["rarity"] == "Quý" else "🟠"
                    items_list.append(f"{rarity_emoji} {item['name']} x{item['quantity']}")
                items_text = ", ".join(items_list)
            else:
                items_text = "Không có vật phẩm"

            embed.add_field(
                name="🎉 Kết Quả",
                value=(
                    f"Chiến thắng! Nhận được {exp_gained:,} exp\n"
                    f"Tỷ lệ HP còn lại: {(player_stats['current_hp'] / player_stats['hp'] * 100):.1f}%"
                ),
                inline=False
            )

            embed.add_field(
                name="💎 Vật Phẩm Nhận Được",
                value=items_text,
                inline=False
            )
        else:
            embed.add_field(
                name="💀 Kết Quả",
                value="Thất bại! Không nhận được phần thưởng",
                inline=False
            )

            # Thêm gợi ý khi thua
            embed.add_field(
                name="💡 Gợi Ý",
                value=(
                    "• Tăng cảnh giới để có sức mạnh lớn hơn\n"
                    "• Sử dụng đan dược để tăng sức mạnh tạm thời\n"
                    "• Nâng cấp trang bị để tăng chỉ số chiến đấu\n"
                    "• Thử đánh quái thường trước khi đánh boss"
                ),
                inline=False
            )

        # Thêm hình ảnh minh họa nếu có
        monster_images = {
            "Yêu Lang": "https://example.com/yeulang.jpg",
            "Hắc Hổ": "https://example.com/hacho.jpg",
            # Thêm các hình ảnh khác
        }

        image_url = monster_images.get(enemy_stats['name'])
        if image_url:
            embed.set_thumbnail(url=image_url)

        return embed

    @commands.command(aliases=["danh_quai", "danhquai", "danh_monster", "hunt"])
    @commands.cooldown(1, MONSTER_COOLDOWN, commands.BucketType.user)
    async def danhquai(self, ctx):
        """Đánh quái thường để nhận kinh nghiệm và vật phẩm"""
        async with await self.get_combat_lock(ctx.author.id):
            try:
                # Hiển thị thông báo đang tìm quái
                loading_msg = await ctx.send("🔍 Đang tìm kiếm quái vật...")

                # Tạo hiệu ứng tìm kiếm
                await asyncio.sleep(1.5)

                # Kiểm tra điều kiện
                player, last_action = await self.check_combat_conditions(ctx, 'monster')
                if not player:
                    await loading_msg.delete()
                    return

                # Chọn quái vật
                is_elite = random.random() < 0.2  # 20% cơ hội gặp quái elite
                monster_list = self.monster_types['monster']['elite' if is_elite else 'normal']
                monster_data = random.choice(monster_list)

                # Cập nhật thông báo
                await loading_msg.edit(content=f"⚔️ Đã phát hiện {monster_data['name']}! Đang chuẩn bị chiến đấu...")
                await asyncio.sleep(1)

                # Tính chỉ số quái
                player_stats = {
                    'name': ctx.author.display_name,
                    'hp': player['hp'],
                    'attack': player['attack'],
                    'defense': player['defense'],
                    'level': player['level'],
                    'current_hp': player['hp']
                }

                monster_stats = {
                    'name': monster_data['name'],
                    'hp': int(player['hp'] * MONSTER_HP_MULTIPLIER * (1.5 if is_elite else 1)),
                    'attack': int(player['attack'] * MONSTER_ATK_MULTIPLIER * (1.5 if is_elite else 1)),
                    'is_elite': is_elite,
                    'current_hp': int(player['hp'] * MONSTER_HP_MULTIPLIER * (1.5 if is_elite else 1)),
                    'type': monster_data['type'],
                    'element': monster_data['element'],
                    'description': monster_data['description']
                }

                # Mô phỏng chiến đấu
                player_stats['current_hp'], monster_stats['current_hp'], battle_log = \
                    await self.simulate_combat(player_stats, monster_stats)

                # Xác định kết quả
                is_victory = monster_stats['current_hp'] <= 0
                exp_gained = 0
                items_gained = []

                if is_victory:
                    # Tính exp thưởng
                    exp_gained = MONSTER_EXP * (2 if is_elite else 1)

                    # Thêm bonus exp dựa trên % HP còn lại
                    hp_percent = player_stats['current_hp'] / player_stats['hp']
                    if hp_percent > 0.8:
                        exp_gained = int(exp_gained * 1.2)  # +20% nếu còn >80% HP

                    new_exp = player['exp'] + exp_gained

                    # Quay vật phẩm
                    items_gained = await self.roll_for_items("monster", is_elite)

                    # Thêm vật phẩm vào kho đồ người chơi
                    if items_gained:
                        inventory_cog = self.bot.get_cog('Inventory')
                        if inventory_cog:
                            for item in items_gained:
                                await inventory_cog.add_item_to_player(
                                    ctx.author.id,
                                    item['name'],
                                    item['type'],
                                    item['rarity'],
                                    item['quantity']
                                )

                    # Cập nhật thống kê
                    stats = player.get('stats', {})
                    monsters_killed = stats.get('monsters_killed', 0) + 1
                    elite_monsters_killed = stats.get('elite_monsters_killed', 0) + (1 if is_elite else 0)

                    # Cập nhật người chơi
                    await self.db.update_player(
                        ctx.author.id,
                        exp=new_exp,
                        last_monster=datetime.now(),
                        stats__monsters_killed=monsters_killed,
                        stats__elite_monsters_killed=elite_monsters_killed
                    )

                    # Kiểm tra level up
                    cultivation_cog = self.bot.get_cog('Cultivation')
                    if cultivation_cog:
                        await cultivation_cog.check_level_up(ctx, player['level'], new_exp)

                # Tạo và gửi embed
                embed = await self.create_combat_embed(
                    ctx, "monster", player_stats, monster_stats,
                    battle_log, is_victory, exp_gained, items_gained
                )

                # Xóa thông báo đang tải và gửi kết quả
                await loading_msg.delete()
                await ctx.send(embed=embed)

            except Exception as e:
                print(f"Lỗi khi đánh quái: {e}")
                await ctx.send("Có lỗi xảy ra trong quá trình chiến đấu!")

    @commands.command(aliases=["danh_boss", "danhboss", "boss"])
    @commands.cooldown(1, BOSS_COOLDOWN, commands.BucketType.user)
    async def danhboss(self, ctx, *members: discord.Member):
        """Đánh boss (có thể rủ thêm người)"""
        async with await self.get_combat_lock(ctx.author.id):
            try:
                # Hiển thị thông báo đang tìm boss
                loading_msg = await ctx.send("🔍 Đang tìm kiếm boss...")

                # Tạo hiệu ứng tìm kiếm
                await asyncio.sleep(2)

                # Kiểm tra điều kiện
                player, last_action = await self.check_combat_conditions(ctx, 'boss')
                if not player:
                    await loading_msg.delete()
                    return

                # Kiểm tra người chơi được tag
                team_members = [ctx.author]
                team_stats = [player]

                if members:
                    await loading_msg.edit(content="⏳ Đang mời các đạo hữu tham gia...")

                    for member in members:
                        if member.bot or member == ctx.author:
                            continue

                        member_data = await self.db.get_player(member.id)
                        if not member_data:
                            continue

                        # Kiểm tra xem người chơi có đang trong trận đấu khác không
                        if member.id in self.combat_locks and self.combat_locks[member.id].locked():
                            continue

                        team_members.append(member)
                        team_stats.append(member_data)

                        if len(team_members) >= 3:  # Giới hạn tối đa 3 người
                            break

                # Tạo ID trận đấu
                battle_id = f"boss_{ctx.author.id}_{datetime.now().timestamp()}"

                # Chọn boss
                is_elite = random.random() < 0.1  # 10% cơ hội gặp boss elite
                boss_list = self.monster_types['boss']['elite' if is_elite else 'normal']
                boss_data = random.choice(boss_list)

                # Cập nhật thông báo
                await loading_msg.edit(content=f"⚔️ Đã phát hiện {boss_data['name']}! Đang chuẩn bị chiến đấu...")
                await asyncio.sleep(1.5)

                # Tính chỉ số boss dựa trên số lượng người chơi
                team_size = len(team_members)
                team_hp_total = sum(p['hp'] for p in team_stats)
                team_atk_total = sum(p['attack'] for p in team_stats)

                # Tính chỉ số boss tăng theo số người
                boss_hp_multiplier = BOSS_HP_MULTIPLIER * (1 + (team_size - 1) * 0.5)
                boss_atk_multiplier = BOSS_ATK_MULTIPLIER * (1 + (team_size - 1) * 0.3)

                boss_stats = {
                    'name': boss_data['name'],
                    'hp': int(team_hp_total * boss_hp_multiplier * (2 if is_elite else 1)),
                    'attack': int(team_atk_total * boss_atk_multiplier * (2 if is_elite else 1) / team_size),
                    'is_elite': is_elite,
                    'current_hp': int(team_hp_total * boss_hp_multiplier * (2 if is_elite else 1)),
                    'type': boss_data['type'],
                    'element': boss_data['element'],
                    'description': boss_data['description'],
                    'skills': boss_data.get('skills', []),
                    'boss': True  # Đánh dấu đây là boss
                }

                # Tạo thông tin trận đấu
                team_player_stats = []
                for i, (member, stats) in enumerate(zip(team_members, team_stats)):
                    player_combat_stats = {
                        'name': member.display_name,
                        'hp': stats['hp'],
                        'attack': stats['attack'],
                        'defense': stats['defense'],
                        'level': stats['level'],
                        'current_hp': stats['hp'],
                        'user_id': member.id
                    }
                    team_player_stats.append(player_combat_stats)

                # Lưu thông tin trận đấu
                self.boss_battles[battle_id] = {
                    'boss': boss_stats,
                    'team': team_player_stats,
                    'start_time': datetime.now(),
                    'ended': False,
                    'battle_log': [],
                    'channel_id': ctx.channel.id
                }

                # Tạo embed thông báo bắt đầu trận đấu
                embed = discord.Embed(
                    title=f"👑 Trận Chiến Boss: {boss_data['name']}",
                    description=f"Một trận chiến khốc liệt sắp diễn ra!",
                    color=0xff9900
                )

                # Thông tin boss
                embed.add_field(
                    name=f"👑 {boss_data['name']}",
                    value=(
                        f"**HP:** {boss_stats['hp']:,}\n"
                        f"**Công Kích:** {boss_stats['attack']:,}\n"
                        f"**Loại:** {boss_data['type']}\n"
                        f"**Nguyên Tố:** {boss_data['element']}"
                    ),
                    inline=False
                )

                # Thông tin đội
                team_info = []
                for i, (member, stats) in enumerate(zip(team_members, team_player_stats)):
                    team_info.append(f"• {member.mention} - {stats['level']} - HP: {stats['hp']:,}")

                embed.add_field(
                    name=f"👥 Đội Tham Gia ({len(team_members)} người)",
                    value="\n".join(team_info),
                    inline=False
                )

                # Thêm thông tin về phần thưởng
                embed.add_field(
                    name="💰 Phần Thưởng Tiềm Năng",
                    value=(
                        f"• EXP: {BOSS_EXP * (3 if is_elite else 1):,} (chia đều)\n"
                        f"• Vật phẩm quý hiếm\n"
                        f"• Có cơ hội nhận được bí kíp"
                    ),
                    inline=False
                )

                # Thêm hướng dẫn
                embed.add_field(
                    name="⚔️ Bắt Đầu Chiến Đấu",
                    value="Trận chiến sẽ bắt đầu trong 5 giây...",
                    inline=False
                )

                # Xóa thông báo đang tải và gửi thông báo mới
                await loading_msg.delete()
                battle_msg = await ctx.send(embed=embed)

                # Đếm ngược
                for i in range(5, 0, -1):
                    await battle_msg.edit(embed=discord.Embed(
                        title=f"👑 Trận Chiến Boss: {boss_data['name']}",
                        description=f"Trận chiến sẽ bắt đầu trong {i} giây...",
                        color=0xff9900
                    ))
                    await asyncio.sleep(1)

                # Bắt đầu trận đấu
                await self.simulate_boss_battle(ctx, battle_id, battle_msg)

            except Exception as e:
                print(f"Lỗi khi đánh boss: {e}")
                await ctx.send("Có lỗi xảy ra trong quá trình chiến đấu!")

    async def simulate_boss_battle(self, ctx, battle_id: str, battle_msg):
        """Mô phỏng trận đấu với boss"""
        try:
            battle = self.boss_battles[battle_id]
            boss = battle['boss']
            team = battle['team']
            battle_log = []

            # Số vòng tối đa
            max_rounds = 20
            current_round = 0

            # Danh sách người chơi còn sống
            alive_players = team.copy()

            while boss['current_hp'] > 0 and any(
                    p['current_hp'] > 0 for p in alive_players) and current_round < max_rounds:
                current_round += 1

                # Hiển thị thông tin vòng đấu
                round_embed = discord.Embed(
                    title=f"👑 Trận Chiến Boss: {boss['name']} - Vòng {current_round}",
                    description=f"Trận chiến đang diễn ra khốc liệt!",
                    color=0xff9900
                )

                # Thông tin HP boss
                hp_percent = boss['current_hp'] / boss['hp'] * 100
                hp_bar = self.create_hp_bar(hp_percent)

                round_embed.add_field(
                    name=f"👑 {boss['name']}",
                    value=f"HP: {boss['current_hp']:,}/{boss['hp']:,}\n{hp_bar}",
                    inline=False
                )

                # Lượt của từng người chơi
                for player in alive_players:
                    if player['current_hp'] <= 0:
                        continue

                    # Player attacks
                    # Xác định có né tránh không
                    if random.random() < 0.1:  # 10% cơ hội né tránh
                        dodge_msg = random.choice(self.combat_messages['enemy_dodge'])
                        log_entry = dodge_msg.format(
                            enemy=boss['name'],
                            player=player['name']
                        )
                        battle_log.append(log_entry)
                    else:
                        # Xác định có chí mạng không
                        is_crit = random.random() < 0.15  # 15% cơ hội chí mạng

                        # Chọn kỹ năng ngẫu nhiên
                        player_skills = self.get_player_skills(player['level'])
                        skill = random.choice(player_skills)

                        # Tính sát thương
                        damage_multiplier = 1.5 if is_crit else (0.8 + random.random() * 0.4)
                        damage = int(player['attack'] * damage_multiplier)
                        boss['current_hp'] -= damage

                        # Thêm log chiến đấu
                        if is_crit:
                            msg = random.choice(self.combat_messages['player_crit'])
                        else:
                            msg = random.choice(self.combat_messages['player_attack'])

                        log_entry = msg.format(
                            player=player['name'],
                            target=boss['name'],
                            damage=damage,
                            skill=skill
                        )
                        battle_log.append(log_entry)

                    # Cập nhật thông tin trận đấu
                    battle['battle_log'] = battle_log

                    # Kiểm tra boss đã bị đánh bại chưa
                    if boss['current_hp'] <= 0:
                        break

                # Lượt của boss nếu còn sống
                if boss['current_hp'] > 0:
                    # Boss tấn công ngẫu nhiên một người chơi còn sống
                    alive_targets = [p for p in alive_players if p['current_hp'] > 0]
                    if alive_targets:
                        target = random.choice(alive_targets)

                        # Xác định có né tránh không
                        if random.random() < 0.08:  # 8% cơ hội né tránh
                            dodge_msg = random.choice(self.combat_messages['player_dodge'])
                            log_entry = dodge_msg.format(
                                player=target['name'],
                                enemy=boss['name']
                            )
                            battle_log.append(log_entry)
                        else:
                            # Xác định có chí mạng không
                            is_crit = random.random() < 0.12  # 12% cơ hội chí mạng

                            # Chọn kỹ năng ngẫu nhiên
                            skill = random.choice(boss.get('skills', ['Tấn Công Thường']))

                            # Tính sát thương
                            damage_multiplier = 1.5 if is_crit else (0.8 + random.random() * 0.4)
                            damage = int(boss['attack'] * damage_multiplier)
                            target['current_hp'] -= damage

                            # Thêm log chiến đấu
                            if is_crit:
                                msg = random.choice(self.combat_messages['boss_crit'])
                            else:
                                msg = random.choice(self.combat_messages['boss_attack'])

                            log_entry = msg.format(
                                boss=boss['name'],
                                player=target['name'],
                                damage=damage,
                                skill=skill
                            )
                            battle_log.append(log_entry)

                # Hiển thị thông tin người chơi
                for player in alive_players:
                    hp_percent = max(0, player['current_hp']) / player['hp'] * 100
                    hp_bar = self.create_hp_bar(hp_percent)
                    status = "🟢 Sống" if player['current_hp'] > 0 else "🔴 Gục"

                    round_embed.add_field(
                        name=f"{player['name']}",
                        value=f"HP: {max(0, player['current_hp']):,}/{player['hp']:,}\n{hp_bar}\nTrạng thái: {status}",
                        inline=True
                    )

                # Hiển thị log chiến đấu
                if battle_log:
                    recent_log = battle_log[-min(5, len(battle_log)):]  # Lấy 5 dòng gần nhất
                    round_embed.add_field(
                        name="⚔️ Diễn Biến Chiến Đấu",
                        value="\n".join(recent_log),
                        inline=False
                    )

                # Cập nhật thông báo
                await battle_msg.edit(embed=round_embed)

                # Đợi một chút để người chơi theo dõi
                await asyncio.sleep(2)

                # Cập nhật danh sách người chơi còn sống
                alive_players = [p for p in team if p['current_hp'] > 0]

            # Kết thúc trận đấu
            battle['ended'] = True

            # Xác định kết quả
            is_victory = boss['current_hp'] <= 0

            # Tạo embed kết quả
            result_embed = discord.Embed(
                title=f"👑 Kết Thúc Trận Chiến: {boss['name']}",
                description="Trận chiến đã kết thúc!",
                color=0x00ff00 if is_victory else 0xff0000,
                timestamp=datetime.now()
            )

            if is_victory:
                # Tính exp và phần thưởng
                base_exp = BOSS_EXP * (3 if boss['is_elite'] else 1)
                alive_count = len([p for p in team if p['current_hp'] > 0])

                # Quay vật phẩm
                items_gained = await self.roll_for_items("boss", boss['is_elite'])

                # Phân phối phần thưởng
                result_embed.add_field(
                    name="🎉 Chiến Thắng!",
                    value=f"Đội đã đánh bại {boss['name']}!",
                    inline=False
                )

                # Hiển thị phần thưởng cho từng người chơi
                for player in team:
                    member = ctx.guild.get_member(player['user_id'])
                    if not member:
                        continue

                    # Tính exp cho người chơi này
                    player_exp = base_exp // len(team)
                    if player['current_hp'] <= 0:
                        player_exp = player_exp // 2  # Người chơi bị gục nhận một nửa exp

                    # Cập nhật exp và thống kê
                    player_data = await self.db.get_player(player['user_id'])
                    if player_data:
                        new_exp = player_data['exp'] + player_exp

                        stats = player_data.get('stats', {})
                        bosses_killed = stats.get('bosses_killed', 0) + 1
                        elite_bosses_killed = stats.get('elite_bosses_killed', 0) + (1 if boss['is_elite'] else 0)

                        # Cập nhật người chơi
                        await self.db.update_player(
                            player['user_id'],
                            exp=new_exp,
                            last_boss=datetime.now(),
                            stats__bosses_killed=bosses_killed,
                            stats__elite_bosses_killed=elite_bosses_killed
                        )

                        # Kiểm tra level up
                        cultivation_cog = self.bot.get_cog('Cultivation')
                        if cultivation_cog:
                            await cultivation_cog.check_level_up(member, player_data['level'], new_exp)

                    # Thêm vật phẩm vào kho đồ người chơi
                    if items_gained and player['current_hp'] > 0:  # Chỉ người còn sống nhận vật phẩm
                        inventory_cog = self.bot.get_cog('Inventory')
                        if inventory_cog:
                            # Mỗi người nhận ngẫu nhiên 1-2 vật phẩm
                            player_items = random.sample(items_gained, min(2, len(items_gained)))
                            for item in player_items:
                                await inventory_cog.add_item_to_player(
                                    player['user_id'],
                                    item['name'],
                                    item['type'],
                                    item['rarity'],
                                    item['quantity']
                                )

                    # Hiển thị phần thưởng
                    status = "🟢 Sống" if player['current_hp'] > 0 else "🔴 Gục"
                    result_embed.add_field(
                        name=f"{player['name']} ({status})",
                        value=f"• EXP: +{player_exp:,}\n• HP còn lại: {max(0, player['current_hp']):,}/{player['hp']:,}",
                        inline=True
                    )

                # Hiển thị vật phẩm nhận được
                if items_gained:
                    items_text = []
                    for item in items_gained:
                        rarity_emoji = "⚪" if item["rarity"] == "Phổ Thông" else "🔵" if item[
                                                                                            "rarity"] == "Hiếm" else "🟣" if \
                        item["rarity"] == "Quý" else "🟠"
                        items_text.append(f"{rarity_emoji} {item['name']} x{item['quantity']}")

                    result_embed.add_field(
                        name="💎 Vật Phẩm Nhận Được",
                        value="\n".join(items_text),
                        inline=False
                    )
            else:
                # Thất bại
                result_embed.add_field(
                    name="💀 Thất Bại!",
                    value=f"Đội đã thất bại trước {boss['name']}!",
                    inline=False
                )

                # Hiển thị thông tin người chơi
                for player in team:
                    status = "🟢 Sống" if player['current_hp'] > 0 else "🔴 Gục"
                    result_embed.add_field(
                        name=f"{player['name']} ({status})",
                        value=f"• HP còn lại: {max(0, player['current_hp']):,}/{player['hp']:,}",
                        inline=True
                    )

                # Thêm gợi ý
                result_embed.add_field(
                    name="💡 Gợi Ý",
                    value=(
                        "• Tăng cảnh giới để có sức mạnh lớn hơn\n"
                        "• Sử dụng đan dược để tăng sức mạnh tạm thời\n"
                        "• Nâng cấp trang bị để tăng chỉ số chiến đấu\n"
                        "• Rủ thêm đồng đội mạnh hơn"
                    ),
                    inline=False
                )

            # Cập nhật thông báo kết quả
            await battle_msg.edit(embed=result_embed)

        except Exception as e:
            print(f"Lỗi khi mô phỏng trận đấu boss: {e}")
            await ctx.send("Có lỗi xảy ra trong quá trình chiến đấu với boss!")

    def create_hp_bar(self, percent: float, length: int = 10) -> str:
        """Tạo thanh HP trực quan"""
        filled = int(length * percent / 100)
        empty = length - filled

        if percent > 70:
            color = "🟩"  # Xanh lá
        elif percent > 30:
            color = "🟨"  # Vàng
        else:
            color = "🟥"  # Đỏ

        bar = color * filled + "⬜" * empty
        return f"{bar} {percent:.1f}%"

    @commands.command(aliases=["monster_info", "quai", "quaivat"])
    async def monster_info(self, ctx, *, monster_name: str = None):
        """Xem thông tin về quái vật và boss"""
        try:
            # Nếu không có tên quái, hiển thị danh sách
            if not monster_name:
                await self.show_monster_list(ctx)
                return

            # Tìm kiếm quái vật hoặc boss
            monster_data = None
            monster_type = None
            monster_rarity = None

            # Tìm trong danh sách quái thường
            for rarity in ['normal', 'elite']:
                for monster in self.monster_types['monster'][rarity]:
                    if monster['name'].lower() == monster_name.lower():
                        monster_data = monster
                        monster_type = 'monster'
                        monster_rarity = rarity
                        break

            # Tìm trong danh sách boss
            if not monster_data:
                for rarity in ['normal', 'elite']:
                    for boss in self.monster_types['boss'][rarity]:
                        if boss['name'].lower() == monster_name.lower():
                            monster_data = boss
                            monster_type = 'boss'
                            monster_rarity = rarity
                            break

            # Nếu không tìm thấy, thử tìm gần đúng
            if not monster_data:
                all_monsters = []
                for rarity in ['normal', 'elite']:
                    all_monsters.extend([(m, 'monster', rarity) for m in self.monster_types['monster'][rarity]])
                    all_monsters.extend([(m, 'boss', rarity) for m in self.monster_types['boss'][rarity]])

                # Tìm quái vật có tên gần giống nhất
                best_match = None
                best_score = 0

                for m, m_type, m_rarity in all_monsters:
                    score = self.string_similarity(m['name'].lower(), monster_name.lower())
                    if score > best_score and score > 0.6:  # Ngưỡng tương đồng
                        best_score = score
                        best_match = (m, m_type, m_rarity)

                if best_match:
                    monster_data, monster_type, monster_rarity = best_match
                    await ctx.send(
                        f"Không tìm thấy '{monster_name}'. Hiển thị kết quả gần nhất: '{monster_data['name']}'")
                else:
                    await ctx.send(f"Không tìm thấy quái vật hoặc boss nào có tên '{monster_name}'.")
                    return

            # Hiển thị thông tin quái vật
            embed = discord.Embed(
                title=f"{'👑' if monster_type == 'boss' else '👿'} {monster_data['name']}",
                description=monster_data.get('description', 'Không có mô tả'),
                color=0xff9900 if monster_type == 'boss' else 0x7289da
            )

            # Thêm thông tin cơ bản
            embed.add_field(
                name="📋 Thông Tin Cơ Bản",
                value=(
                    f"**Loại:** {monster_data.get('type', 'Không rõ')}\n"
                    f"**Nguyên tố:** {monster_data.get('element', 'Không rõ')}\n"
                    f"**Độ hiếm:** {'Tinh Anh' if monster_rarity == 'elite' else 'Thường'}\n"
                    f"**Phân loại:** {'Boss' if monster_type == 'boss' else 'Quái Vật'}"
                ),
                inline=False
            )

            # Thêm thông tin kỹ năng nếu có
            if monster_data.get('skills'):
                embed.add_field(
                    name="⚔️ Kỹ Năng",
                    value="\n".join([f"• {skill}" for skill in monster_data['skills']]),
                    inline=False
                )

            # Thêm thông tin vật phẩm rơi ra
            drop_category = monster_type
            drop_rarity = monster_rarity
            possible_drops = self.item_drops[drop_category][drop_rarity]

            if possible_drops:
                drops_text = []
                for item in possible_drops:
                    rarity_emoji = "⚪" if item["rarity"] == "Phổ Thông" else "🔵" if item["rarity"] == "Hiếm" else "🟣" if \
                    item["rarity"] == "Quý" else "🟠"
                    chance_percent = item["chance"] * 100
                    drops_text.append(f"{rarity_emoji} {item['name']} ({chance_percent:.1f}%)")

                embed.add_field(
                    name="💎 Vật Phẩm Có Thể Rơi Ra",
                    value="\n".join(drops_text),
                    inline=False
                )

            # Thêm thông tin exp
            if monster_type == 'monster':
                exp_value = MONSTER_EXP * (2 if monster_rarity == 'elite' else 1)
            else:
                exp_value = BOSS_EXP * (3 if monster_rarity == 'elite' else 1)

            embed.add_field(
                name="📈 Kinh Nghiệm",
                value=f"{exp_value:,} EXP",
                inline=True
            )

            # Thêm thông tin cooldown
            cooldown = BOSS_COOLDOWN if monster_type == 'boss' else MONSTER_COOLDOWN
            embed.add_field(
                name="⏱️ Cooldown",
                value=f"{cooldown // 60} phút",
                inline=True
            )

            # Thêm lệnh liên quan
            embed.add_field(
                name="🎮 Lệnh Liên Quan",
                value=f"`!{'danhboss' if monster_type == 'boss' else 'danhquai'}`",
                inline=True
            )

            await ctx.send(embed=embed)

        except Exception as e:
            print(f"Lỗi khi hiển thị thông tin quái vật: {e}")
            await ctx.send("Có lỗi xảy ra khi hiển thị thông tin quái vật!")

    async def show_monster_list(self, ctx):
        """Hiển thị danh sách quái vật và boss"""
        embed = discord.Embed(
            title="📋 Danh Sách Quái Vật & Boss",
            description="Dưới đây là danh sách các loại quái vật và boss trong thế giới tu tiên:",
            color=0x7289da
        )

        # Danh sách quái thường
        normal_monsters = [m['name'] for m in self.monster_types['monster']['normal']]
        embed.add_field(
            name="👿 Quái Vật Thường",
            value="\n".join([f"• {name}" for name in normal_monsters]),
            inline=True
        )

        # Danh sách quái tinh anh
        elite_monsters = [m['name'] for m in self.monster_types['monster']['elite']]
        embed.add_field(
            name="💪 Quái Vật Tinh Anh",
            value="\n".join([f"• {name}" for name in elite_monsters]),
            inline=True
        )

        # Danh sách boss thường
        normal_bosses = [b['name'] for b in self.monster_types['boss']['normal']]
        embed.add_field(
            name="👑 Boss Thường",
            value="\n".join([f"• {name}" for name in normal_bosses]),
            inline=True
        )

        # Danh sách boss tinh anh
        elite_bosses = [b['name'] for b in self.monster_types['boss']['elite']]
        embed.add_field(
            name="🔱 Boss Tinh Anh",
            value="\n".join([f"• {name}" for name in elite_bosses]),
            inline=True
        )

        # Thêm hướng dẫn
        embed.add_field(
            name="🔍 Xem Chi Tiết",
            value="Sử dụng lệnh `!monster_info [tên_quái]` để xem thông tin chi tiết về một loại quái vật hoặc boss.",
            inline=False
        )

        await ctx.send(embed=embed)

    def string_similarity(self, s1: str, s2: str) -> float:
        """Tính độ tương đồng giữa hai chuỗi (Levenshtein distance)"""
        if len(s1) < len(s2):
            s1, s2 = s2, s1

        if len(s2) == 0:
            return 0.0

        distances = range(len(s1) + 1)
        for i2, c2 in enumerate(s2):
            distances_ = [i2 + 1]
            for i1, c1 in enumerate(s1):
                if c1 == c2:
                    distances_.append(distances[i1])
                else:
                    distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
            distances = distances_

        return 1 - distances[-1] / max(len(s1), len(s2))

    @commands.command(aliases=["boss_list", "bosses", "danhsachboss"])
    async def boss_list(self, ctx):
        """Xem danh sách boss đã đánh bại"""
        try:
            player = await self.db.get_player(ctx.author.id)
            if not player:
                await ctx.send("Ngươi chưa gia nhập môn phái nào! Hãy vào kênh tông-môn-chi-lộ để chọn môn phái.")
                return

            stats = player.get('stats', {})
            bosses_killed = stats.get('bosses_killed', 0)
            elite_bosses_killed = stats.get('elite_bosses_killed', 0)

            embed = discord.Embed(
                title="📊 Thống Kê Săn Boss",
                description=f"Thành tích săn boss của {ctx.author.display_name}:",
                color=0xff9900
            )

            # Thêm thông tin tổng quan
            embed.add_field(
                name="🏆 Tổng Số Boss Đã Đánh Bại",
                value=f"**{bosses_killed:,}** boss",
                inline=True
            )

            embed.add_field(
                name="👑 Boss Tinh Anh Đã Đánh Bại",
                value=f"**{elite_bosses_killed:,}** boss tinh anh",
                inline=True
            )

            # Tính tỷ lệ boss tinh anh
            if bosses_killed > 0:
                elite_ratio = (elite_bosses_killed / bosses_killed) * 100
                embed.add_field(
                    name="📈 Tỷ Lệ Boss Tinh Anh",
                    value=f"**{elite_ratio:.1f}%**",
                    inline=True
                )

            # Thêm thông tin về boss đã đánh bại (nếu có lưu trong database)
            boss_records = stats.get('boss_records', {})
            if boss_records:
                boss_list = []
                for boss_name, count in boss_records.items():
                    boss_list.append(f"• {boss_name}: {count} lần")

                embed.add_field(
                    name="📋 Boss Đã Đánh Bại",
                    value="\n".join(boss_list) if boss_list else "Chưa có thông tin chi tiết",
                    inline=False
                )

            # Thêm thông tin về phần thưởng đã nhận
            embed.add_field(
                name="💰 Phần Thưởng Đã Nhận",
                value=(
                    f"• EXP: ~{bosses_killed * BOSS_EXP:,}\n"
                    f"• Vật phẩm quý hiếm: ~{bosses_killed * 2} món\n"
                    f"• Cơ hội nhận bí kíp: {elite_bosses_killed} lần"
                ),
                inline=False
            )

            # Thêm gợi ý
            embed.add_field(
                name="💡 Gợi Ý",
                value=(
                    "• Sử dụng `!danhboss` để đánh boss\n"
                    "• Rủ thêm đồng đội để tăng cơ hội chiến thắng\n"
                    "• Boss tinh anh có tỷ lệ xuất hiện 10%\n"
                    "• Cooldown đánh boss: 30 phút"
                ),
                inline=False
            )

            await ctx.send(embed=embed)

        except Exception as e:
            print(f"Lỗi khi hiển thị danh sách boss: {e}")
            await ctx.send("Có lỗi xảy ra khi hiển thị danh sách boss!")

    @commands.command(aliases=["monster_list", "monsters", "danhsachquai"])
    async def monster_list(self, ctx):
        """Xem danh sách quái vật đã đánh bại"""
        try:
            player = await self.db.get_player(ctx.author.id)
            if not player:
                await ctx.send("Ngươi chưa gia nhập môn phái nào! Hãy vào kênh tông-môn-chi-lộ để chọn môn phái.")
                return

            stats = player.get('stats', {})
            monsters_killed = stats.get('monsters_killed', 0)
            elite_monsters_killed = stats.get('elite_monsters_killed', 0)

            embed = discord.Embed(
                title="📊 Thống Kê Săn Quái",
                description=f"Thành tích săn quái của {ctx.author.display_name}:",
                color=0x7289da
            )

            # Thêm thông tin tổng quan
            embed.add_field(
                name="🏆 Tổng Số Quái Đã Đánh Bại",
                value=f"**{monsters_killed:,}** quái",
                inline=True
            )

            embed.add_field(
                name="💪 Quái Tinh Anh Đã Đánh Bại",
                value=f"**{elite_monsters_killed:,}** quái tinh anh",
                inline=True
            )

            # Tính tỷ lệ quái tinh anh
            if monsters_killed > 0:
                elite_ratio = (elite_monsters_killed / monsters_killed) * 100
                embed.add_field(
                    name="📈 Tỷ Lệ Quái Tinh Anh",
                    value=f"**{elite_ratio:.1f}%**",
                    inline=True
                )

            # Thêm thông tin về quái đã đánh bại (nếu có lưu trong database)
            monster_records = stats.get('monster_records', {})
            if monster_records:
                monster_list = []
                for monster_name, count in monster_records.items():
                    monster_list.append(f"• {monster_name}: {count} lần")

                embed.add_field(
                    name="📋 Quái Đã Đánh Bại",
                    value="\n".join(monster_list) if monster_list else "Chưa có thông tin chi tiết",
                    inline=False
                )

            # Thêm thông tin về phần thưởng đã nhận
            embed.add_field(
                name="💰 Phần Thưởng Đã Nhận",
                value=(
                    f"• EXP: ~{monsters_killed * MONSTER_EXP:,}\n"
                    f"• Vật phẩm thường: ~{monsters_killed} món\n"
                    f"• Vật phẩm hiếm: ~{elite_monsters_killed * 2} món"
                ),
                inline=False
            )

            # Thêm gợi ý
            embed.add_field(
                name="💡 Gợi Ý",
                value=(
                    "• Sử dụng `!danhquai` để đánh quái\n"
                    "• Quái tinh anh có tỷ lệ xuất hiện 20%\n"
                    "• Cooldown đánh quái: 10 phút\n"
                    "• Đánh quái là cách hiệu quả để kiếm nguyên liệu"
                ),
                inline=False
            )

            await ctx.send(embed=embed)

        except Exception as e:
            print(f"Lỗi khi hiển thị danh sách quái: {e}")
            await ctx.send("Có lỗi xảy ra khi hiển thị danh sách quái!")


async def setup(bot):
    await bot.add_cog(Monster(bot, bot.db))