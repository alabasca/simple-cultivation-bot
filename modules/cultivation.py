import discord
from discord.ext import commands
from datetime import datetime, timedelta
import random
import asyncio
from typing import Dict, Any, List, Tuple, Optional, Union
from config import (
    CULTIVATION_LEVELS, CHAT_EXP, VOICE_EXP,
    SECTS, SECT_EMOJIS, SECT_COLORS
)


class Cultivation(commands.Cog):
    """Hệ thống tu luyện và kinh nghiệm"""

    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.voice_states = {}  # Để lưu trạng thái voice chat
        self.exp_lock = asyncio.Lock()  # Lock để tránh race condition khi update exp
        self.breakthrough_locks = {}  # Lock cho từng người chơi khi thăng cấp

        # Cache để tránh truy vấn database quá nhiều
        self.player_cache = {}
        self.cache_timeout = 60  # seconds

    # Danh sách các cảnh giới
    CULTIVATION_RANKS = [
        "Phàm Nhân",
        "Luyện Khí Tầng 1", "Luyện Khí Tầng 2", "Luyện Khí Tầng 3",
        "Luyện Khí Tầng 4", "Luyện Khí Tầng 5", "Luyện Khí Tầng 6",
        "Luyện Khí Tầng 7", "Luyện Khí Tầng 8", "Luyện Khí Tầng 9",
        "Trúc Cơ Sơ Kỳ", "Trúc Cơ Trung Kỳ", "Trúc Cơ Đại Viên Mãn",
        "Nguyên Anh Sơ Kỳ", "Nguyên Anh Trung Kỳ", "Nguyên Anh Đại Viên Mãn",
        "Kim Đan Sơ Kỳ", "Kim Đan Trung Kỳ", "Kim Đan Đại Viên Mãn",
        "Hóa Thần Sơ Kỳ", "Hóa Thần Trung Kỳ", "Hóa Thần Đại Viên Mãn",
        "Luyện Hư Sơ Kỳ", "Luyện Hư Trung Kỳ", "Luyện Hư Đại Viên Mãn",
        "Đại Thừa Sơ Kỳ", "Đại Thừa Trung Kỳ", "Đại Thừa Đại Viên Mãn",
        "Diễn Chủ Vạn Giới"
    ]

    # Thông báo đột phá cho từng cảnh giới
    BREAKTHROUGH_MESSAGES = {
        "Luyện Khí": [
            "Linh khí quanh người ngày càng dày đặc! Kinh mạch mở rộng, sức mạnh tăng vọt!",
            "Kinh mạch rộng mở, linh khí lưu thông! Một cảm giác mát lạnh lan tỏa khắp cơ thể!",
            "Từng bước vững chắc trên con đường tu tiên! Thiên địa linh khí quay cuồng quanh thân!",
            "Linh căn được củng cố, tiến thêm một bước! Cảm nhận được sự hòa hợp với thiên đạo!"
        ],
        "Trúc Cơ": [
            "Linh khí hóa thành chân khí, đan điền rung động! Cả người như được tái sinh!",
            "Kinh mạch được rèn luyện, sức mạnh tăng vọt! Ánh sáng huyền bí bao phủ quanh thân!",
            "Căn cơ vững chắc, đạo tâm kiên định! Thiên địa như gần hơn, vạn vật rõ ràng hơn!"
        ],
        "Nguyên Anh": [
            "Nguyên anh thành hình, thiên địa biến sắc! Một bóng người trong suốt xuất hiện trong đan điền!",
            "Linh hồn thăng hoa, uy năng tăng mạnh! Nguyên anh phát sáng, thân thể như được rèn luyện bằng thiên lôi!",
            "Đạo pháp tự nhiên, khí运 bao phủ! Lôi vân tụ tập, vạn thú cúi đầu!"
        ],
        "Kim Đan": [
            "Kim đan ngưng tụ, phát ra ánh sáng rực rỡ! Vạn đạo giao hòa, thiên địa cuối đầu!",
            "Thiên địa giao hòa, đan thành một thể! Mỗi động tác đều mang theo uy năng bất diệt!",
            "Đan hỏa thiêu đốt, thoát thai hoán cốt! Cơ thể trở nên tinh thuần, sức mạnh như thác đổ!"
        ],
        "Hóa Thần": [
            "Thần hồn thoát xác, khí thế ngút trời! Mây đen tụ tập, sấm sét vang dội!",
            "Pháp tắc thiên địa, tùy tâm nắm giữ! Vạn vật như trở nên rõ ràng, mọi bí ẩn đều hiển lộ!",
            "Thần thông quảng đại, pháp lực vô biên! Một ý niệm có thể khiến sông núi dời chỗ!"
        ],
        "Luyện Hư": [
            "Hư không sinh diệt, đạo pháp tự nhiên! Không gian quanh người như bị bẻ cong!",
            "Không trung hiển hiện dị tượng, thiên địa chấn động! Vạn vật như đứng yên lặng trước đạo hạnh của ngươi!",
            "Hư không lay động, vạn vật thần phục! Một tâm niệm có thể khiến không gian vỡ vụn!"
        ],
        "Đại Thừa": [
            "Đại đạo sinh thành, vạn pháp quy tông! Thiên địa như rung chuyển trước đạo hạnh của ngươi!",
            "Thiên địa biến sắc, vạn vật cúi đầu! Ngay cả ánh sáng cũng phải tuân theo ý chí của ngươi!",
            "Một bước một dấu ấn, đạo pháp tự nhiên! Mỗi hơi thở đều khiến vạn vật rung động!"
        ],
        "Diễn Chủ": [
            "Vạn giới thần phục, đạo pháp viên mãn! Ngươi đã vượt qua giới hạn của tự nhiên!",
            "Thiên địa bái phục, vạn đạo quy tông! Ngay cả thời gian cũng phải tuân theo ý chí của ngươi!",
            "Một tiếng kiếm ngân vang, vạn giới chấn động! Ngươi đã đạt tới đỉnh cao của đạo pháp!"
        ]
    }

    # Phản hồi khi nhận exp từ chat và voice
    CHAT_EXP_MESSAGES = [
        "Ngươi cảm thấy linh khí dâng lên!",
        "Đạo tâm kiên định, tu vi tinh tiến!",
        "Từng chút tu luyện, tích góp thành công!",
        "Mỗi lời nói đều là một bước tiến trên con đường tu tiên!"
    ]

    VOICE_EXP_MESSAGES = [
        "Khí tức điều hòa, tu vi tăng tiến!",
        "Tọa đàm luận đạo, tâm đắc vô cùng!",
        "Ngộ đạo trường ngâm, linh khí tràn đầy!",
        "Âm thanh hòa vào thiên địa, tu vi tăng mạnh!"
    ]

    @commands.Cog.listener()
    async def on_ready(self):
        """Khởi tạo khi bot khởi động"""
        print("✓ Module Cultivation đã sẵn sàng!")

        # Khởi tạo nhiệm vụ kiểm tra voice chat định kỳ
        self.bot.loop.create_task(self.voice_exp_task())

    async def voice_exp_task(self):
        """Nhiệm vụ định kỳ cấp exp cho voice chat"""
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            try:
                # Kiểm tra và cấp exp cho người trong voice
                current_time = datetime.now()
                for guild in self.bot.guilds:
                    for voice_channel in guild.voice_channels:
                        for member in voice_channel.members:
                            if not member.bot and not member.voice.afk and not member.voice.self_deaf:
                                # Kiểm tra xem đã có trong voice_states chưa
                                if member.id not in self.voice_states:
                                    self.voice_states[member.id] = current_time
                                    continue

                                # Tính thời gian và cấp exp
                                last_time = self.voice_states[member.id]
                                time_diff = (current_time - last_time).total_seconds() / 60

                                if time_diff >= 1:  # Mỗi phút cấp exp một lần
                                    exp_gained = int(time_diff * VOICE_EXP)
                                    self.voice_states[member.id] = current_time

                                    if exp_gained > 0:
                                        # Cập nhật exp
                                        await self.update_exp(member.id, exp_gained, source="voice")

            except Exception as e:
                print(f"Lỗi trong voice_exp_task: {e}")

            # Chờ 1 phút trước khi kiểm tra lại
            await asyncio.sleep(60)

    @commands.command(name="tuvi", aliases=["tu", "info", "profile"], usage="[@người_chơi]")
    async def tuvi(self, ctx, member: discord.Member = None):
        """Xem thông tin tu vi của bản thân hoặc người khác"""
        try:
            # Hiển thị thông báo đang tải
            loading_msg = await ctx.send("⏳ Đang tải thông tin tu vi...")

            # Xác định người chơi cần xem
            target = member or ctx.author

            # Lấy thông tin người chơi từ database
            player = await self.get_player(target.id)
            if not player:
                if target == ctx.author:
                    embed = discord.Embed(
                        title="❌ Chưa Gia Nhập Môn Phái",
                        description="Ngươi chưa gia nhập môn phái nào! Hãy sử dụng lệnh `!tongmon` để chọn môn phái.",
                        color=0xff0000
                    )
                else:
                    embed = discord.Embed(
                        title="❌ Không Tìm Thấy",
                        description=f"{target.display_name} chưa bắt đầu tu luyện!",
                        color=0xff0000
                    )

                await loading_msg.delete()
                await ctx.send(embed=embed)
                return

            # Tạo embed hiển thị thông tin tu vi
            embed = await self.create_player_profile(ctx, target, player)

            # Gửi embed và xóa thông báo đang tải
            await ctx.send(embed=embed)
            await loading_msg.delete()

        except Exception as e:
            print(f"Lỗi khi xem tu vi: {e}")
            await ctx.send("❌ Có lỗi xảy ra khi xem tu vi! Xin hãy thử lại sau.")

    async def create_player_profile(self, ctx, target: discord.Member, player: Dict[str, Any]) -> discord.Embed:
        """Tạo embed thông tin tu vi chi tiết"""
        # Lấy thông tin môn phái
        sect = player.get('sect', 'Không có')
        sect_emoji = SECT_EMOJIS.get(sect, "🏯") if 'SECT_EMOJIS' in globals() else "🏯"
        sect_color = SECT_COLORS.get(sect, 0x2ecc71) if 'SECT_COLORS' in globals() else 0x2ecc71

        embed = discord.Embed(
            title=f"📊 Tu Vi của {target.display_name}",
            description=f"{sect_emoji} Đệ tử **{sect}**",
            color=sect_color,
            timestamp=datetime.now()
        )

        # Thông tin cơ bản
        embed.add_field(
            name="⭐ Cảnh Giới",
            value=player.get('level', 'Phàm Nhân'),
            inline=True
        )

        embed.add_field(
            name="📈 Tu Vi",
            value=f"{player.get('exp', 0):,} EXP",
            inline=True
        )

        # Thêm thông tin về thời gian tu luyện
        joined_at = player.get('created_at')
        if joined_at:
            if isinstance(joined_at, str):
                try:
                    joined_at = datetime.strptime(joined_at, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    joined_at = None

            if joined_at:
                time_diff = datetime.now() - joined_at
                embed.add_field(
                    name="⏱️ Thời Gian Tu Luyện",
                    value=f"{time_diff.days} ngày",
                    inline=True
                )

        # Tính toán và hiển thị tiến trình tu luyện
        next_level_info = await self.get_next_level_info(player.get('level', 'Phàm Nhân'), player.get('exp', 0))
        if next_level_info:
            next_level, exp_needed = next_level_info
            current_exp = player.get('exp', 0)
            exp_remaining = max(0, exp_needed - current_exp)
            progress = min(100, (current_exp / exp_needed) * 100)
            progress_bar = self.create_progress_bar(progress)

            exp_info = (
                f"```\n{progress_bar}\n"
                f"Kinh Nghiệm: {current_exp:,}/{exp_needed:,}\n"
                f"Còn Thiếu: {exp_remaining:,} EXP\n"
                f"Tiến Độ: {progress:.1f}%\n"
                f"Cảnh Giới Tiếp Theo: {next_level}```"
            )
        else:
            exp_info = "```\nĐã đạt đến đỉnh cao nhất của con đường tu tiên!\n```"

        embed.add_field(
            name="📊 Tiến Trình Tu Luyện",
            value=exp_info,
            inline=False
        )

        # Thông tin chiến đấu
        attack, defense = self.calculate_combat_stats(player)

        combat_stats = (
            f"```\n"
            f"❤️ Sinh Lực:  {player.get('hp', 100):,}\n"
            f"⚔️ Công Kích: {attack:,} ({player.get('attack', 10):,} + bonus)\n"
            f"🛡️ Phòng Thủ: {defense:,} ({player.get('defense', 5):,} + bonus)\n"
            f"```"
        )
        embed.add_field(
            name="💪 Thông Số Chiến Đấu",
            value=combat_stats,
            inline=False
        )

        # Thống kê PvP và săn quái
        stats = player.get('stats', {})
        pvp_wins = stats.get('pvp_wins', 0)
        pvp_losses = stats.get('pvp_losses', 0)
        monsters_killed = stats.get('monsters_killed', 0)
        bosses_killed = stats.get('bosses_killed', 0)

        if pvp_wins > 0 or pvp_losses > 0 or monsters_killed > 0 or bosses_killed > 0:
            stats_info = []

            if pvp_wins > 0 or pvp_losses > 0:
                total_pvp = pvp_wins + pvp_losses
                win_rate = f"{(pvp_wins / total_pvp * 100):.1f}%" if total_pvp > 0 else "0%"
                stats_info.append(f"⚔️ PvP: {pvp_wins}W/{pvp_losses}L ({win_rate})")

            if monsters_killed > 0:
                stats_info.append(f"👹 Quái: {monsters_killed}")

            if bosses_killed > 0:
                stats_info.append(f"🐉 Boss: {bosses_killed}")

            embed.add_field(
                name="📊 Thành Tích",
                value="\n".join(stats_info),
                inline=True
            )

        # Thêm thông tin điểm danh
        daily_streak = player.get('daily_streak', 0)
        if daily_streak > 0:
            embed.add_field(
                name="🔥 Điểm Danh",
                value=f"Streak: {daily_streak} ngày",
                inline=True
            )

        # Thêm avatar người chơi
        if target.avatar:
            embed.set_thumbnail(url=target.avatar.url)

        # Thêm thời gian xem và footer
        embed.set_footer(text=f"ID: {target.id} • Tu luyện từ: {target.created_at.strftime('%d/%m/%Y')}")

        return embed

    def calculate_combat_stats(self, player: Dict[str, Any]) -> Tuple[int, int]:
        """Tính toán sức công kích và phòng thủ có áp dụng bonus từ môn phái"""
        # Lấy chỉ số cơ bản
        attack = player.get('attack', 10)
        defense = player.get('defense', 5)

        # Lấy tông môn và áp dụng bonus
        sect = player.get('sect')
        if sect and sect in SECTS:
            attack_bonus = SECTS[sect].get('attack_bonus', 1.0)
            defense_bonus = SECTS[sect].get('defense_bonus', 1.0)

            attack = int(attack * attack_bonus)
            defense = int(defense * defense_bonus)

        return attack, defense

    def create_progress_bar(self, percent, length=20):
        """Tạo thanh tiến trình trực quan"""
        filled = int(length * percent / 100)
        empty = length - filled
        bar = '█' * filled + '░' * empty
        return f"[{bar}] {percent:.1f}%"

    async def get_next_level_info(self, current_level, current_exp):
        """
        Lấy thông tin về cấp độ tiếp theo
        Returns: tuple (next_level, exp_needed) hoặc None nếu đã max level
        """
        try:
            current_index = self.CULTIVATION_RANKS.index(current_level)
            if current_index < len(self.CULTIVATION_RANKS) - 1:
                next_level = self.CULTIVATION_RANKS[current_index + 1]
                exp_needed = CULTIVATION_LEVELS[next_level]["exp_req"]
                return (next_level, exp_needed)
            return None
        except (ValueError, KeyError, IndexError) as e:
            print(f"Lỗi khi lấy thông tin cấp độ tiếp theo: {e}")
            return None

    async def get_player(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Lấy thông tin người chơi (với cache)"""
        # Kiểm tra cache
        if user_id in self.player_cache:
            player, timestamp = self.player_cache[user_id]
            if (datetime.now() - timestamp).seconds < self.cache_timeout:
                return player

        # Lấy từ database
        player = await self.db.get_player(user_id)
        if player:
            self.player_cache[user_id] = (player, datetime.now())
        return player

    async def update_exp(self, user_id: int, exp_gained: int, source: str = "unknown") -> Tuple[
        Optional[int], Optional[str]]:
        """Cập nhật exp và kiểm tra thăng cấp an toàn với lock"""
        if exp_gained <= 0:
            return None, None

        async with self.exp_lock:
            try:
                player = await self.get_player(user_id)
                if player:
                    # Cập nhật exp
                    new_exp = player.get('exp', 0) + exp_gained

                    # Cập nhật tổng exp đã nhận
                    stats = player.get('stats', {})
                    total_exp = stats.get('total_exp_gained', 0) + exp_gained

                    # Cập nhật vào database
                    update_data = {
                        'exp': new_exp,
                        'stats__total_exp_gained': total_exp
                    }

                    await self.db.update_player(user_id, **update_data)

                    # Xóa cache
                    if user_id in self.player_cache:
                        del self.player_cache[user_id]

                    # Trả về exp mới và level hiện tại
                    return new_exp, player.get('level', 'Phàm Nhân')
                return None, None
            except Exception as e:
                print(f"Lỗi khi cập nhật exp: {e}")
                return None, None

    async def create_breakthrough_embed(self, user: discord.Member, old_level: str, new_level: str,
                                        new_stats: Dict[str, Any]) -> discord.Embed:
        """Tạo embed thông báo đột phá"""
        # Xác định realm và chọn thông báo
        realm = new_level.split()[0]
        specific_message = "Đột phá thành công! Thiên địa chấn động!"
        for key, messages in self.BREAKTHROUGH_MESSAGES.items():
            if key in new_level:
                specific_message = random.choice(messages)
                break

        embed = discord.Embed(
            title="☯️ Tu Vi Tăng Mạnh, Thiên Địa Chấn Động!",
            description=(
                f"📢 Tiếng kiếm ngân vang, linh khí hội tụ, "
                f"toàn server chấn kinh trước một bước tiến của {user.mention}!\n\n"
                f"{specific_message}"
            ),
            color=0xffd700,
            timestamp=datetime.now()
        )

        # Thông tin đột phá
        embed.add_field(
            name="🔮 Đột Phá Cảnh Giới",
            value=f"```{old_level} ➜ {new_level}```",
            inline=False
        )

        # Hiển thị chỉ số mới
        embed.add_field(
            name="📊 Chỉ Số Mới",
            value=(
                f"```\n"
                f"❤️ Sinh Lực:  {new_stats.get('hp', 100):,}\n"
                f"⚔️ Công Kích: {new_stats.get('attack', 10):,}\n"
                f"🛡️ Phòng Thủ: {new_stats.get('defense', 5):,}\n"
                f"```"
            ),
            inline=False
        )

        # Thêm ghi chú đặc biệt
        if "Đại Viên Mãn" in new_level:
            embed.add_field(
                name="🌟 Ghi Chú",
                value="Đã đạt tới đỉnh cao của cảnh giới này! Chuẩn bị đột phá lên cảnh giới mới!",
                inline=False
            )
        elif new_level == "Diễn Chủ Vạn Giới":
            embed.add_field(
                name="👑 Chúc Mừng",
                value="Đã đạt tới đỉnh cao của con đường tu tiên! Từ nay vạn giới đều nằm dưới chân ngươi!",
                inline=False
            )

        if user.avatar:
            embed.set_thumbnail(url=user.avatar.url)

        return embed

    async def check_level_up(self, ctx, current_level: str, new_exp: int) -> bool:
        """Kiểm tra và xử lý thăng cấp cho người chơi"""
        if isinstance(ctx, discord.Member):
            user = ctx
        else:
            user = ctx.author

        # Lấy hoặc tạo lock cho người chơi
        if user.id not in self.breakthrough_locks:
            self.breakthrough_locks[user.id] = asyncio.Lock()

        async with self.breakthrough_locks[user.id]:
            try:
                current_index = self.CULTIVATION_RANKS.index(current_level)

                # Kiểm tra các cấp độ tiếp theo
                level_ups = []
                final_level = current_level

                for next_index in range(current_index + 1, len(self.CULTIVATION_RANKS)):
                    next_level = self.CULTIVATION_RANKS[next_index]
                    exp_required = CULTIVATION_LEVELS[next_level]["exp_req"]

                    # Nếu đủ exp để lên cấp
                    if new_exp >= exp_required:
                        level_ups.append((next_level, CULTIVATION_LEVELS[next_level]))
                        final_level = next_level
                    else:
                        break

                # Nếu có thăng cấp
                if level_ups:
                    # Lấy thông số cuối cùng
                    final_stats = level_ups[-1][1]

                    # Cập nhật người chơi
                    await self.db.update_player(
                        user.id,
                        level=final_level,
                        hp=final_stats.get("hp", 100),
                        attack=final_stats.get("attack", 10),
                        defense=final_stats.get("defense", 5)
                    )

                    # Xóa cache
                    if user.id in self.player_cache:
                        del self.player_cache[user.id]

                    # Tạo và gửi thông báo đột phá
                    embed = await self.create_breakthrough_embed(
                        user,
                        current_level,
                        final_level,
                        final_stats
                    )

                    # Gửi thông báo
                    if isinstance(ctx, discord.Member):
                        # Tìm kênh thích hợp để gửi
                        for guild in self.bot.guilds:
                            if user in guild.members:
                                # Thử gửi vào kênh hệ thống hoặc kênh chung
                                channel = guild.system_channel
                                if not channel:
                                    for ch_name in ['general', 'chat', 'thông-báo', 'chung']:
                                        channel = discord.utils.get(guild.text_channels, name=ch_name)
                                        if channel:
                                            break

                                if channel and channel.permissions_for(guild.me).send_messages:
                                    await channel.send(embed=embed)
                                    break
                    else:
                        # Nếu là context bình thường, gửi vào kênh hiện tại
                        await ctx.send(embed=embed)

                    return True

                return False

            except Exception as e:
                print(f"Lỗi khi xử lý thăng cấp: {e}")
                return False

    @commands.Cog.listener()
    async def on_message(self, message):
        """Xử lý nhận exp khi chat"""
        if message.author.bot:
            return

        # Chỉ xử lý tin nhắn trong kênh text của server
        if not isinstance(message.channel, discord.TextChannel):
            return

        try:
            # Kiểm tra người chơi có trong hệ thống không
            player = await self.get_player(message.author.id)
            if not player:
                return

            # Cập nhật exp với xác suất thông báo thấp (10%)
            new_exp, current_level = await self.update_exp(message.author.id, CHAT_EXP, source="chat")

            # Thông báo ngẫu nhiên với xác suất 10% để không spam
            if new_exp is not None and random.random() < 0.1:
                # Gửi thông báo riêng tư về việc nhận exp
                try:
                    msg = random.choice(self.CHAT_EXP_MESSAGES)
                    await message.author.send(f"💬 **Chat EXP**: +{CHAT_EXP} EXP! {msg}")
                except discord.Forbidden:
                    # Không thể gửi DM, bỏ qua
                    pass

            # Kiểm tra thăng cấp
            if new_exp is not None and current_level is not None:
                await self.check_level_up(message, current_level, new_exp)

        except Exception as e:
            print(f"Lỗi khi xử lý exp chat: {e}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Xử lý nhận exp khi voice chat"""
        if member.bot:
            return

        try:
            # Kiểm tra người chơi có trong hệ thống không
            player = await self.get_player(member.id)
            if not player:
                return

            # Vào voice chat
            if before.channel is None and after.channel is not None and not after.afk and not after.self_deaf:
                self.voice_states[member.id] = datetime.now()
                # Gửi thông báo bắt đầu tu luyện
                try:
                    await member.send(
                        f"🎙️ **Voice Tu Luyện**: Bắt đầu tu luyện trong voice chat. +{VOICE_EXP} EXP mỗi phút!")
                except discord.Forbidden:
                    # Không thể gửi DM, bỏ qua
                    pass

            # Rời voice chat
            elif before.channel is not None and (after.channel is None or after.afk or after.self_deaf):
                join_time = self.voice_states.pop(member.id, None)
                if join_time:
                    # Tính thời gian và exp
                    time_in_voice = (datetime.now() - join_time).total_seconds() / 60
                    exp_gained = int(time_in_voice * VOICE_EXP)
                    if exp_gained > 0:
                        # Cập nhật exp
                        new_exp, current_level = await self.update_exp(member.id, exp_gained, source="voice")
                        # Gửi thông báo kết thúc tu luyện
                        try:
                            minutes = int(time_in_voice)
                            seconds = int((time_in_voice - minutes) * 60)
                            time_str = f"{minutes} phút" if seconds == 0 else f"{minutes} phút {seconds} giây"
                            msg = random.choice(self.VOICE_EXP_MESSAGES)
                            await member.send(
                                f"🎙️ **Voice Tu Luyện**: Kết thúc sau {time_str}.\n"
                                f"Nhận được: +{exp_gained} EXP! {msg}"
                            )
                        except discord.Forbidden:
                            # Không thể gửi DM, bỏ qua
                            pass

                        # Kiểm tra thăng cấp
                        if new_exp is not None and current_level is not None:
                            await self.check_level_up(member, current_level, new_exp)

        except Exception as e:
            print(f"Lỗi khi xử lý exp voice: {e}")

    @commands.command(name="exp", aliases=["exp_info", "kinh_nghiem", "kinhnghiem"], usage="[@người_chơi]")
    async def check_exp(self, ctx, member: discord.Member = None):
        """Kiểm tra exp chi tiết và cách tăng tu vi"""
        target = member or ctx.author
        player = await self.get_player(target.id)

        if not player:
            if target == ctx.author:
                await ctx.send(
                    f"{ctx.author.mention}, bạn chưa bắt đầu tu luyện! Hãy sử dụng lệnh `!tongmon` để chọn môn phái.")
            else:
                await ctx.send(f"{target.display_name} chưa bắt đầu tu luyện!")
            return

        embed = discord.Embed(
            title=f"📊 Chi Tiết EXP của {target.display_name}",
            description=f"Thông tin chi tiết về tu vi và cách tăng kinh nghiệm",
            color=0x3498db,
            timestamp=datetime.now()
        )

        # Thông tin exp hiện tại
        embed.add_field(
            name="🔮 Cảnh Giới",
            value=player.get('level', 'Phàm Nhân'),
            inline=True
        )

        embed.add_field(
            name="📈 EXP Hiện Tại",
            value=f"{player.get('exp', 0):,}",
            inline=True
        )

        # Thống kê tổng exp đã nhận
        stats = player.get('stats', {})
        total_exp_gained = stats.get('total_exp_gained', 0)
        embed.add_field(
            name="💯 Tổng EXP Đã Nhận",
            value=f"{total_exp_gained:,}",
            inline=True
        )

        # Thông tin cấp tiếp theo
        next_level_info = await self.get_next_level_info(player.get('level', 'Phàm Nhân'), player.get('exp', 0))
        if next_level_info:
            next_level, exp_needed = next_level_info
            exp_remaining = exp_needed - player.get('exp', 0)
            progress = (player.get('exp', 0) / exp_needed) * 100
            # Tính thời gian dự kiến để đạt level tiếp theo
            exp_per_day_estimate = 500  # Ước tính mỗi ngày nhận được 500 exp
            days_estimate = exp_remaining / exp_per_day_estimate

            embed.add_field(
                name="⭐ Cấp Tiếp Theo",
                value=f"{next_level}",
                inline=True
            )

            embed.add_field(
                name="📊 EXP Còn Thiếu",
                value=f"{exp_remaining:,}",
                inline=True
            )

            embed.add_field(
                name="⏱️ Thời Gian Dự Kiến",
                value=f"~{days_estimate:.1f} ngày",
                inline=True
            )

            # Tạo thanh tiến độ
            progress_bar = self.create_progress_bar(progress)
            embed.add_field(
                name="📈 Tiến Độ",
                value=f"```\n{progress_bar}\n```",
                inline=False
            )

        # Thông tin cách tăng exp
        embed.add_field(
            name="💬 Chat",
            value=f"Mỗi tin nhắn: +{CHAT_EXP} EXP",
            inline=True
        )

        embed.add_field(
            name="🎙️ Voice",
            value=f"Mỗi phút voice: +{VOICE_EXP} EXP",
            inline=True
        )

        embed.add_field(
            name="📝 Điểm Danh",
            value="Mỗi ngày: +100 EXP (+ bonus)",
            inline=True
        )

        # Thêm thông tin combat
        combat_info = (
            "⚔️ **Combat**:\n"
            "• Đánh quái: +10-30 EXP\n"
            "• Đánh boss: +50-150 EXP\n"
            "• PvP: Cướp 10% EXP đối thủ"
        )

        embed.add_field(
            name="⚔️ Chiến Đấu",
            value=combat_info,
            inline=False
        )

        # Thêm hình ảnh người chơi
        if target.avatar:
            embed.set_thumbnail(url=target.avatar.url)

        embed.set_footer(text="Tu luyện chăm chỉ để tăng cảnh giới!")

        await ctx.send(embed=embed)

    @commands.command(name="levels", aliases=["canhgioi", "cảnhgiới", "xephang"], usage="")
    async def cultivation_levels(self, ctx):
        """Xem danh sách các cảnh giới tu luyện"""
        try:
            # Tạo embed thông tin cảnh giới
            embed = discord.Embed(
                title="🌟 Hệ Thống Cảnh Giới Tu Luyện",
                description=(
                    "Đạo tu tiên gian nan, đầy thử thách. "
                    "Mỗi bước tiến là một bước gần hơn đến với đại đạo."
                ),
                color=0xe74c3c,
                timestamp=datetime.now()
            )

            # Nhóm các cảnh giới theo realm
            realms = {
                "Phàm Nhân": ["Phàm Nhân"],
                "Luyện Khí": [level for level in self.CULTIVATION_RANKS if level.startswith("Luyện Khí")],
                "Trúc Cơ": [level for level in self.CULTIVATION_RANKS if level.startswith("Trúc Cơ")],
                "Nguyên Anh": [level for level in self.CULTIVATION_RANKS if level.startswith("Nguyên Anh")],
                "Kim Đan": [level for level in self.CULTIVATION_RANKS if level.startswith("Kim Đan")],
                "Hóa Thần": [level for level in self.CULTIVATION_RANKS if level.startswith("Hóa Thần")],
                "Luyện Hư": [level for level in self.CULTIVATION_RANKS if level.startswith("Luyện Hư")],
                "Đại Thừa": [level for level in self.CULTIVATION_RANKS if level.startswith("Đại Thừa")],
                "Diễn Chủ": [level for level in self.CULTIVATION_RANKS if level.startswith("Diễn Chủ")]
            }

            # Thêm các realm vào embed
            for realm, levels in realms.items():
                # Tạo thông tin chi tiết về các cấp độ trong realm
                level_details = []
                for level in levels:
                    if level in CULTIVATION_LEVELS:
                        exp_req = CULTIVATION_LEVELS[level]["exp_req"]
                        stats = CULTIVATION_LEVELS[level]
                        level_details.append(
                            f"• {level}: {exp_req:,} EXP"
                        )

                # Thêm thông tin realm vào embed
                if level_details:
                    embed.add_field(
                        name=f"✨ {realm}",
                        value="\n".join(level_details),
                        inline=False
                    )

            # Thêm ghi chú
            embed.add_field(
                name="📝 Ghi Chú",
                value=(
                    "• EXP tăng theo cấp số nhân\n"
                    "• Mỗi cấp độ có chỉ số riêng\n"
                    "• Tu luyện nhiều để tăng cảnh giới\n"
                    "• Càng lên cao càng khó khăn"
                ),
                inline=False
            )

            # Thêm footer
            embed.set_footer(text="Sử dụng !tuvi để xem tu vi hiện tại")

            await ctx.send(embed=embed)

        except Exception as e:
            print(f"Lỗi khi hiển thị cảnh giới: {e}")
            await ctx.send("❌ Có lỗi xảy ra khi hiển thị thông tin cảnh giới!")

    @commands.command(name="rank", aliases=["rank_info", "xephang", "cultivation"], usage="[@người_chơi]")
    async def rank_info(self, ctx, member: discord.Member = None):
        """Xem chi tiết về cảnh giới của người chơi"""
        target = member or ctx.author
        player = await self.get_player(target.id)

        if not player:
            if target == ctx.author:
                await ctx.send(
                    f"{ctx.author.mention}, bạn chưa bắt đầu tu luyện! Hãy sử dụng lệnh `!tongmon` để chọn môn phái.")
            else:
                await ctx.send(f"{target.display_name} chưa bắt đầu tu luyện!")
            return

        try:
            # Lấy thông tin cảnh giới hiện tại
            current_level = player.get('level', 'Phàm Nhân')
            current_exp = player.get('exp', 0)
            current_index = self.CULTIVATION_RANKS.index(current_level)

            # Tạo embed thông tin cảnh giới
            sect = player.get('sect', 'Không có môn phái')
            sect_emoji = SECT_EMOJIS.get(sect, "🏯") if 'SECT_EMOJIS' in globals() else "🏯"
            sect_color = SECT_COLORS.get(sect, 0xe74c3c) if 'SECT_COLORS' in globals() else 0xe74c3c

            embed = discord.Embed(
                title=f"📊 Cảnh Giới của {target.display_name}",
                description=f"{sect_emoji} Đệ tử **{sect}** | Cảnh giới: **{current_level}**",
                color=sect_color,
                timestamp=datetime.now()
            )

            # Thông tin cảnh giới hiện tại
            if current_level in CULTIVATION_LEVELS:
                current_stats = CULTIVATION_LEVELS[current_level]
                # Thêm thông tin chỉ số cơ bản
                embed.add_field(
                    name="📊 Chỉ Số Cơ Bản",
                    value=(
                        f"❤️ Sinh Lực: {current_stats.get('hp', 100)}\n"
                        f"⚔️ Công Kích: {current_stats.get('attack', 10)}\n"
                        f"🛡️ Phòng Thủ: {current_stats.get('defense', 5)}"
                    ),
                    inline=True
                )

            # Thông tin cảnh giới tiếp theo
            next_level_info = await self.get_next_level_info(current_level, current_exp)
            if next_level_info:
                next_level, exp_needed = next_level_info
                exp_remaining = exp_needed - current_exp
                progress = (current_exp / exp_needed) * 100

                # Lấy thông tin cảnh giới tiếp theo
                if next_level in CULTIVATION_LEVELS:
                    next_stats = CULTIVATION_LEVELS[next_level]
                    # Tính toán sự tăng trưởng
                    hp_growth = next_stats.get('hp', 100) - CULTIVATION_LEVELS[current_level].get('hp', 100)
                    atk_growth = next_stats.get('attack', 10) - CULTIVATION_LEVELS[current_level].get('attack', 10)
                    def_growth = next_stats.get('defense', 5) - CULTIVATION_LEVELS[current_level].get('defense', 5)

                    # Thêm thông tin cảnh giới tiếp theo
                    embed.add_field(
                        name=f"⬆️ Cảnh Giới Tiếp Theo: {next_level}",
                        value=(
                            f"❤️ Sinh Lực: {next_stats.get('hp', 100)} (+{hp_growth})\n"
                            f"⚔️ Công Kích: {next_stats.get('attack', 10)} (+{atk_growth})\n"
                            f"🛡️ Phòng Thủ: {next_stats.get('defense', 5)} (+{def_growth})"
                        ),
                        inline=True
                    )

                # Thêm thông tin tiến độ
                progress_bar = self.create_progress_bar(progress)
                embed.add_field(
                    name="📈 Tiến Độ Đột Phá",
                    value=(
                        f"```\n{progress_bar}\n```\n"
                        f"EXP hiện tại: {current_exp:,}\n"
                        f"EXP cần thiết: {exp_needed:,}\n"
                        f"Còn thiếu: {exp_remaining:,} EXP"
                    ),
                    inline=False
                )
            else:
                # Đã đạt đến cảnh giới cao nhất
                embed.add_field(
                    name="👑 Cảnh Giới Tối Thượng",
                    value="Bạn đã đạt đến đỉnh cao của con đường tu tiên!",
                    inline=False
                )

            # Thêm thông tin ranking
            all_players = await self.db.get_all_players()
            if all_players:
                sorted_players = sorted(all_players, key=lambda x: x.get('exp', 0), reverse=True)
                player_rank = next((i + 1 for i, p in enumerate(sorted_players) if p.get('user_id') == target.id), None)

                if player_rank:
                    rank_emoji = "🥇" if player_rank == 1 else "🥈" if player_rank == 2 else "🥉" if player_rank == 3 else f"#{player_rank}"
                    same_level_count = sum(1 for p in all_players if p.get('level', 'Phàm Nhân') == current_level)

                    embed.add_field(
                        name="🏆 Xếp Hạng",
                        value=(
                            f"Xếp hạng toàn server: {rank_emoji}\n"
                            f"Người cùng cảnh giới: {same_level_count} tu sĩ\n"
                            f"Tổng số tu sĩ: {len(all_players)}"
                        ),
                        inline=False
                    )

            # Thêm avatar người chơi
            if target.avatar:
                embed.set_thumbnail(url=target.avatar.url)

            # Thêm footer
            embed.set_footer(text="Tu luyện chăm chỉ để đột phá cảnh giới!")

            await ctx.send(embed=embed)

        except Exception as e:
            print(f"Lỗi khi hiển thị thông tin cảnh giới: {e}")
            await ctx.send("❌ Có lỗi xảy ra khi hiển thị thông tin cảnh giới!")


async def setup(bot):
    await bot.add_cog(Cultivation(bot, bot.db))