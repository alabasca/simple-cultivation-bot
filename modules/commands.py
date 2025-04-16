# modules/commands.py
import discord
from discord.ext import commands
from datetime import datetime, timedelta
import random
import asyncio
from typing import Dict, Any, List, Optional
from modules.shared_commands import handle_daily_command
from config import SECTS, SECT_EMOJIS, SECT_COLORS


class Commands(commands.Cog):
    """Các lệnh tiện ích trong hệ thống Tu Tiên"""

    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.command_cooldowns = {}  # Cache cho cooldown

    @commands.command(name="dailycmd", aliases=["nhanqua"], usage="")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def daily_cmd(self, ctx):  # Đổi tên hàm để phù hợp với tên lệnh
        """Điểm danh hàng ngày để nhận thưởng (alias của !daily)"""
        await handle_daily_command(ctx, self.db)  # Gọi hàm xử lý chung

    @commands.Cog.listener()
    async def on_ready(self):
        """Thông báo khi module đã sẵn sàng"""
        print("✓ Module Commands đã sẵn sàng!")

    @commands.command(name="server_info", aliases=["thongtin", "server"], usage="")
    @commands.guild_only()
    async def server_info(self, ctx):
        """Xem thông tin server tu tiên"""
        try:
            # Hiển thị thông báo đang tải
            loading_msg = await ctx.send("⏳ Đang tải thông tin server...")

            guild = ctx.guild

            # Đếm số người trong từng môn phái
            sect_counts = {}
            active_players = 0
            total_exp = 0

            # Lấy danh sách người chơi từ database
            all_players = await self.db.get_all_players()
            for player in all_players:
                if player.get('sect'):
                    sect_name = player.get('sect')
                    sect_counts[sect_name] = sect_counts.get(sect_name, 0) + 1
                    total_exp += player.get('exp', 0)
                    active_players += 1

            embed = discord.Embed(
                title=f"📊 Thông Tin {guild.name}",
                description="Thông tin chi tiết về tông môn",
                color=0x2ecc71,
                timestamp=datetime.now()
            )

            # Thông tin cơ bản
            embed.add_field(
                name="👥 Tổng Thành Viên",
                value=f"{guild.member_count:,}",
                inline=True
            )
            embed.add_field(
                name="🔰 Tu Sĩ Hoạt Động",
                value=f"{active_players:,}",
                inline=True
            )
            embed.add_field(
                name="📈 Tổng Tu Vi",
                value=f"{total_exp:,} EXP",
                inline=True
            )

            # Thêm thông tin về thời gian
            embed.add_field(
                name="📅 Ngày Thành Lập",
                value=guild.created_at.strftime("%d/%m/%Y"),
                inline=True
            )
            embed.add_field(
                name="⏱️ Tuổi Server",
                value=self.format_time_difference(guild.created_at),
                inline=True
            )
            embed.add_field(
                name="🔄 Hoạt Động",
                value=f"{active_players / guild.member_count * 100:.1f}% thành viên",
                inline=True
            )

            # Thông tin môn phái
            if sect_counts:
                # Sắp xếp các môn phái theo số lượng thành viên
                sorted_sects = sorted(sect_counts.items(), key=lambda x: x[1], reverse=True)

                # Thêm emoji vào tên môn phái nếu có
                sect_info = []
                for name, count in sorted_sects:
                    emoji = SECT_EMOJIS.get(name, "🏯") if 'SECT_EMOJIS' in globals() else "🏯"
                    sect_info.append(f"{emoji} {name}: {count} tu sĩ")

                sect_text = "\n".join(sect_info)
            else:
                sect_text = "Chưa có tu sĩ nào"

            embed.add_field(
                name="🏯 Phân Bố Môn Phái",
                value=f"```\n{sect_text}\n```",
                inline=False
            )

            # Thêm icon server
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)

            # Thêm footer
            channel_count = len(guild.text_channels) + len(guild.voice_channels)
            embed.set_footer(text=f"Server ID: {guild.id} • {channel_count} kênh • {len(guild.roles)} roles")

            # Gửi embed và xóa thông báo đang tải
            await ctx.send(embed=embed)
            await loading_msg.delete()

        except Exception as e:
            print(f"Lỗi khi xem thông tin server: {e}")
            await ctx.send("❌ Có lỗi xảy ra khi lấy thông tin server!")

    @commands.command(name="top", aliases=["bangxephang", "bxh", "xephang"], usage="[all/sect/pvp] [số_lượng]")
    @commands.guild_only()
    async def leaderboard(self, ctx, type_str="all", limit: int = 10):
        """Xem bảng xếp hạng tu sĩ"""
        try:
            # Hiển thị thông báo đang tải
            loading_msg = await ctx.send("⏳ Đang tải bảng xếp hạng...")

            # Giới hạn số lượng hiển thị
            limit = min(max(1, limit), 20)

            # Chuyển loại xếp hạng về chữ thường
            type_str = type_str.lower()

            if type_str in ["sect", "môn phái", "monphai", "môn", "phái"]:
                # Bảng xếp hạng theo môn phái
                embed = await self.create_sect_leaderboard(limit)

            elif type_str in ["pvp", "combat", "pk", "đấu"]:
                # Bảng xếp hạng theo chiến thắng PvP
                embed = await self.create_pvp_leaderboard(ctx, limit)

            else:
                # Bảng xếp hạng cá nhân theo tu vi
                embed = await self.create_player_leaderboard(ctx, limit)

            # Thêm thời gian cập nhật
            embed.set_footer(text=f"Cập nhật: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}")

            # Gửi embed và xóa thông báo đang tải
            await ctx.send(embed=embed)
            await loading_msg.delete()

        except Exception as e:
            print(f"Lỗi khi xem bảng xếp hạng: {e}")
            await ctx.send("❌ Có lỗi xảy ra khi lấy bảng xếp hạng!")

    async def create_sect_leaderboard(self, limit: int) -> discord.Embed:
        """Tạo bảng xếp hạng môn phái"""
        all_players = await self.db.get_all_players()
        sect_stats = {}

        # Tính tổng exp và số lượng thành viên theo môn phái
        for player in all_players:
            sect = player.get('sect')
            if sect:
                if sect not in sect_stats:
                    sect_stats[sect] = {
                        "exp": 0,
                        "members": 0,
                        "avg_exp": 0
                    }

                sect_stats[sect]["exp"] += player.get('exp', 0)
                sect_stats[sect]["members"] += 1

        # Tính trung bình exp
        for sect in sect_stats:
            if sect_stats[sect]["members"] > 0:
                sect_stats[sect]["avg_exp"] = sect_stats[sect]["exp"] // sect_stats[sect]["members"]

        # Sắp xếp các môn phái theo tổng exp
        sorted_sects = sorted(sect_stats.items(), key=lambda x: x[1]["exp"], reverse=True)

        embed = discord.Embed(
            title="🏯 Bảng Xếp Hạng Môn Phái",
            description="Tổng tu vi của các môn phái",
            color=0xf1c40f
        )

        for i, (sect, stats) in enumerate(sorted_sects[:limit], 1):
            medal = self.get_rank_medal(i)

            # Chọn màu tương ứng cho môn phái nếu có
            color_hex = SECT_COLORS.get(sect, "🔵") if 'SECT_COLORS' in globals() else "🔵"
            emoji = SECT_EMOJIS.get(sect, "🏯") if 'SECT_EMOJIS' in globals() else "🏯"

            embed.add_field(
                name=f"{medal} {emoji} {sect}",
                value=(
                    f"```\n"
                    f"Tổng Tu Vi: {stats['exp']:,} EXP\n"
                    f"Thành viên: {stats['members']} tu sĩ\n"
                    f"Trung bình: {stats['avg_exp']:,} EXP/người\n"
                    f"Xếp Hạng: #{i}\n"
                    f"```"
                ),
                inline=False
            )

        return embed

    async def create_pvp_leaderboard(self, ctx, limit: int) -> discord.Embed:
        """Tạo bảng xếp hạng dựa trên thành tích PvP"""
        all_players = await self.db.get_all_players()

        # Lọc người chơi có thông tin PvP
        pvp_players = []
        for player in all_players:
            stats = player.get('stats', {})
            wins = stats.get('pvp_wins', 0)
            losses = stats.get('pvp_losses', 0)

            if wins > 0 or losses > 0:
                # Tính tỷ lệ thắng
                total_matches = wins + losses
                win_rate = wins / total_matches if total_matches > 0 else 0

                pvp_players.append({
                    "user_id": player.get('user_id'),
                    "wins": wins,
                    "losses": losses,
                    "total": total_matches,
                    "win_rate": win_rate,
                    "level": player.get('level', 'Phàm Nhân'),
                    "sect": player.get('sect', 'Không có')
                })

        # Sắp xếp theo số trận thắng, sau đó theo tỷ lệ thắng
        sorted_players = sorted(
            pvp_players,
            key=lambda x: (x['wins'], x['win_rate']),
            reverse=True
        )

        embed = discord.Embed(
            title="⚔️ Bảng Xếp Hạng PvP",
            description="Những cao thủ chiến đấu hàng đầu",
            color=0xe74c3c
        )

        for i, player_data in enumerate(sorted_players[:limit], 1):
            member = ctx.guild.get_member(player_data['user_id'])
            if member:
                medal = self.get_rank_medal(i)
                win_rate_percent = player_data['win_rate'] * 100

                embed.add_field(
                    name=f"{medal} {member.display_name}",
                    value=(
                        f"```\n"
                        f"Thắng: {player_data['wins']} | Thua: {player_data['losses']}\n"
                        f"Tỷ lệ thắng: {win_rate_percent:.1f}%\n"
                        f"Cảnh Giới: {player_data['level']}\n"
                        f"Môn Phái: {player_data['sect']}\n"
                        f"```"
                    ),
                    inline=False
                )

        return embed

    async def create_player_leaderboard(self, ctx, limit: int) -> discord.Embed:
        """Tạo bảng xếp hạng tu sĩ theo exp"""
        top_players = await self.db.get_top_players(limit)

        embed = discord.Embed(
            title="👑 Bảng Xếp Hạng Tu Sĩ",
            description="Những tu sĩ có tu vi cao nhất",
            color=0xf1c40f
        )

        for i, player in enumerate(top_players, 1):
            member = ctx.guild.get_member(player.get('user_id'))
            if member:
                medal = self.get_rank_medal(i)
                sect = player.get('sect', 'Không có môn phái')
                emoji = SECT_EMOJIS.get(sect, "🏯") if 'SECT_EMOJIS' in globals() else "🏯"

                embed.add_field(
                    name=f"{medal} {member.display_name}",
                    value=(
                        f"```\n"
                        f"Cảnh Giới: {player.get('level', 'Phàm Nhân')}\n"
                        f"Tu Vi: {player.get('exp', 0):,} EXP\n"
                        f"Môn Phái: {emoji} {sect}\n"
                        f"```"
                    ),
                    inline=False
                )

        return embed

    def get_rank_medal(self, rank):
        """Lấy huy hiệu theo thứ hạng"""
        if rank == 1:
            return "🥇"
        elif rank == 2:
            return "🥈"
        elif rank == 3:
            return "🥉"
        return f"#{rank}"

    @commands.command(name="stats", aliases=["thongke", "stat", "tk"], usage="")
    @commands.guild_only()
    async def stats(self, ctx):
        """Xem thống kê chi tiết server"""
        try:
            # Hiển thị thông báo đang tải
            loading_msg = await ctx.send("⏳ Đang tải thống kê...")

            # Lấy tất cả người chơi
            all_players = await self.db.get_all_players()

            # Khởi tạo biến thống kê
            level_stats = {}
            sect_stats = {}
            total_exp = 0
            active_players = len(all_players)
            highest_level = {"player": None, "level": "Phàm Nhân"}
            highest_exp = {"player": None, "exp": 0}

            # Thống kê PvP
            total_pvp_matches = 0
            total_monsters_killed = 0
            total_bosses_killed = 0

            # Phân tích dữ liệu
            for player in all_players:
                # Thống kê cảnh giới
                level = player.get('level', 'Phàm Nhân')
                level_stats[level] = level_stats.get(level, 0) + 1

                # Thống kê môn phái
                sect = player.get('sect', 'Không có')
                sect_stats[sect] = sect_stats.get(sect, 0) + 1

                # Tổng exp
                player_exp = player.get('exp', 0)
                total_exp += player_exp

                # Tìm người chơi cao cấp nhất
                member = ctx.guild.get_member(player.get('user_id'))
                if member:
                    if self.compare_levels(level, highest_level["level"]) > 0:
                        highest_level = {"player": member, "level": level}
                    if player_exp > highest_exp["exp"]:
                        highest_exp = {"player": member, "exp": player_exp}

                # Thống kê PvP và các hoạt động khác
                stats = player.get('stats', {})
                total_pvp_matches += stats.get('pvp_wins', 0) + stats.get('pvp_losses', 0)
                total_monsters_killed += stats.get('monsters_killed', 0)
                total_bosses_killed += stats.get('bosses_killed', 0)

            # Tạo embed thống kê
            embed = discord.Embed(
                title="📊 Thống Kê Chi Tiết Tông Môn",
                description=f"Thông tin chi tiết về {ctx.guild.name}",
                color=0x3498db,
                timestamp=datetime.now()
            )

            # Thống kê cơ bản
            embed.add_field(
                name="👥 Tổng Số Tu Sĩ",
                value=f"{active_players:,}",
                inline=True
            )
            embed.add_field(
                name="📈 Tổng Tu Vi",
                value=f"{total_exp:,} EXP",
                inline=True
            )
            embed.add_field(
                name="⚡ Trung Bình Tu Vi",
                value=f"{int(total_exp / active_players):,} EXP" if active_players > 0 else "0",
                inline=True
            )

            # Thêm thống kê hoạt động
            embed.add_field(
                name="⚔️ Hoạt Động",
                value=(
                    f"PvP: {total_pvp_matches:,} trận\n"
                    f"Quái vật: {total_monsters_killed:,} con\n"
                    f"Boss: {total_bosses_killed:,} con"
                ),
                inline=True
            )

            # Thông tin người chơi cao cấp
            if highest_level["player"]:
                embed.add_field(
                    name="👑 Cao Thủ Cảnh Giới",
                    value=(
                        f"Đạo Hữu: {highest_level['player'].mention}\n"
                        f"Cảnh Giới: {highest_level['level']}"
                    ),
                    inline=True
                )

            if highest_exp["player"] and highest_exp["player"] != highest_level["player"]:
                embed.add_field(
                    name="💎 Cao Thủ Tu Vi",
                    value=(
                        f"Đạo Hữu: {highest_exp['player'].mention}\n"
                        f"Tu Vi: {highest_exp['exp']:,} EXP"
                    ),
                    inline=True
                )

            # Phân bố cảnh giới
            if level_stats:
                level_info = "\n".join([
                    f"{level}: {count} tu sĩ"
                    for level, count in sorted(
                        level_stats.items(),
                        key=lambda x: self.get_level_index(x[0])
                    )
                ])
            else:
                level_info = "Chưa có dữ liệu"

            embed.add_field(
                name="🌟 Phân Bố Cảnh Giới",
                value=f"```\n{level_info}\n```",
                inline=False
            )

            # Phân bố môn phái
            if sect_stats:
                # Thêm emoji cho từng tông môn
                sect_info_list = []
                for sect, count in sorted(sect_stats.items(), key=lambda x: x[1], reverse=True):
                    emoji = SECT_EMOJIS.get(sect, "🏯") if 'SECT_EMOJIS' in globals() else "🏯"
                    sect_info_list.append(f"{emoji} {sect}: {count} đệ tử")

                sect_info = "\n".join(sect_info_list)
            else:
                sect_info = "Chưa có dữ liệu"

            embed.add_field(
                name="🏯 Phân Bố Môn Phái",
                value=f"```\n{sect_info}\n```",
                inline=False
            )

            # Thêm icon server
            if ctx.guild.icon:
                embed.set_thumbnail(url=ctx.guild.icon.url)

            # Thêm ghi chú
            embed.set_footer(text="Sử dụng !top để xem bảng xếp hạng chi tiết")

            # Gửi embed và xóa thông báo đang tải
            await ctx.send(embed=embed)
            await loading_msg.delete()

        except Exception as e:
            print(f"Lỗi khi xem thống kê: {e}")
            await ctx.send("❌ Có lỗi xảy ra khi lấy thống kê!")

    def get_level_index(self, level):
        """Lấy thứ tự của cảnh giới để sắp xếp"""
        try:
            cultivation_cog = self.bot.get_cog('Cultivation')
            if cultivation_cog and hasattr(cultivation_cog, 'CULTIVATION_RANKS'):
                return cultivation_cog.CULTIVATION_RANKS.index(level)

            # Dự phòng: thử lấy từ config nếu không có cog
            if hasattr(self.bot, 'config') and hasattr(self.bot.config, 'CULTIVATION_LEVELS'):
                levels = list(self.bot.config.CULTIVATION_LEVELS.keys())
                return levels.index(level) if level in levels else -1

            return -1
        except (ValueError, AttributeError, IndexError):
            return -1

    def compare_levels(self, level1, level2):
        """So sánh hai cảnh giới
        Returns: 1 nếu level1 > level2, -1 nếu level1 < level2, 0 nếu bằng nhau"""
        idx1 = self.get_level_index(level1)
        idx2 = self.get_level_index(level2)
        return (idx1 > idx2) - (idx1 < idx2)

    @commands.command(name="roll", aliases=["random", "r", "xúc xắc", "xucxac"], usage="[số_lớn_nhất]")
    async def roll(self, ctx, max_num: int = 100):
        """Random một số ngẫu nhiên"""
        try:
            # Kiểm tra giới hạn
            max_num = max(1, min(max_num, 1000000))
            number = random.randint(1, max_num)

            # Tạo hiệu ứng xúc xắc
            message = await ctx.send("🎲 Đang tung xúc xắc...")

            # Hiệu ứng ngẫu nhiên
            for i in range(3):
                await asyncio.sleep(0.7)
                await message.edit(content=f"🎲 Đang tung xúc xắc... {random.randint(1, max_num)}")

            # Hiển thị kết quả
            embed = discord.Embed(
                title="🎲 Thiên Cơ Hiện",
                description=(
                    f"{ctx.author.mention} đã tung xúc xắc!\n"
                    f"Con số định mệnh là: **{number:,}**\n"
                    f"*(Trong khoảng 1 - {max_num:,})*"
                ),
                color=0x9b59b6,
                timestamp=datetime.now()
            )

            # Thêm ghi chú nếu là số đặc biệt
            if number == 1:
                embed.add_field(
                    name="👑 Số Một",
                    value="Độc Tôn Thiên Hạ! Một ngày đẹp trời sắp đến.",
                    inline=False
                )
            elif number == max_num:
                embed.add_field(
                    name="🎯 Số Tối Đa",
                    value="Đã Đạt Đến Đỉnh Cao! Vạn sự hanh thông.",
                    inline=False
                )
            elif number == 69:
                embed.add_field(
                    name="😏 Số May Mắn",
                    value="Số này thật... thú vị!",
                    inline=False
                )
            elif number == 88:
                embed.add_field(
                    name="🍀 Số Phát Tài",
                    value="Cát tường như ý! Vạn sự hanh thông.",
                    inline=False
                )
            elif number == 666:
                embed.add_field(
                    name="😈 Con Số Quỷ Dữ",
                    value="Hắc ám lực lượng hiện hữu!",
                    inline=False
                )

            # Xóa tin nhắn tạm thời và gửi kết quả
            await message.delete()
            await ctx.send(embed=embed)

        except ValueError:
            await ctx.send("❌ Vui lòng nhập một số hợp lệ!")
        except Exception as e:
            print(f"Lỗi khi roll số: {e}")
            await ctx.send("❌ Có lỗi xảy ra!")

    @commands.command(name="ping", aliases=["latency", "zing"], usage="")
    async def ping(self, ctx):
        """Kiểm tra độ trễ của bot"""
        try:
            # Đo độ trễ
            start_time = datetime.now()
            message = await ctx.send("🏓 Đang kiểm tra...")
            end_time = datetime.now()

            # Tính toán các loại độ trễ
            api_latency = round(self.bot.latency * 1000)
            bot_latency = round((end_time - start_time).total_seconds() * 1000)

            # Hiệu ứng đo độ trễ
            for i in range(3):
                dots = "." * (i + 1)
                await message.edit(content=f"🏓 Đang kiểm tra{dots}")
                await asyncio.sleep(0.3)

            embed = discord.Embed(
                title="🏓 Tốc Độ Kết Nối",
                description=f"Kiểm tra độ trễ của {self.bot.user.name}",
                color=self.get_ping_color(api_latency),
                timestamp=datetime.now()
            )

            embed.add_field(
                name="⚡ Discord API",
                value=f"{api_latency}ms",
                inline=True
            )
            embed.add_field(
                name="🤖 Bot Latency",
                value=f"{bot_latency}ms",
                inline=True
            )

            # Thêm thông tin về thời gian hoạt động nếu có
            uptime = datetime.now() - getattr(self.bot, 'start_time', datetime.now())
            embed.add_field(
                name="⏱️ Uptime",
                value=self.format_time_difference(datetime.now() - uptime),
                inline=True
            )

            # Thêm đánh giá tốc độ
            status = self.get_ping_status(api_latency)
            embed.add_field(
                name="📊 Trạng Thái",
                value=status,
                inline=False
            )

            # Thêm icon bot
            if self.bot.user.avatar:
                embed.set_thumbnail(url=self.bot.user.avatar.url)

            await message.edit(content=None, embed=embed)

        except Exception as e:
            print(f"Lỗi khi kiểm tra ping: {e}")
            await ctx.send("❌ Có lỗi xảy ra khi kiểm tra kết nối!")

    def get_ping_color(self, latency):
        """Lấy màu dựa trên độ trễ"""
        if latency < 100:
            return 0x2ecc71  # Xanh lá
        elif latency < 200:
            return 0xf1c40f  # Vàng
        else:
            return 0xe74c3c  # Đỏ

    def get_ping_status(self, latency):
        """Lấy đánh giá dựa trên độ trễ"""
        if latency < 100:
            return "🟢 Kết nối cực kỳ ổn định"
        elif latency < 200:
            return "🟡 Kết nối tạm ổn"
        elif latency < 300:
            return "🟠 Kết nối hơi chậm"
        else:
            return "🔴 Kết nối không ổn định"

    def format_time_difference(self, time_diff):
        """Format thời gian theo dạng dễ đọc"""
        if isinstance(time_diff, datetime):
            time_diff = datetime.now() - time_diff

        days = time_diff.days
        hours, remainder = divmod(time_diff.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        parts = []
        if days > 0:
            parts.append(f"{days} ngày")
        if hours > 0:
            parts.append(f"{hours} giờ")
        if minutes > 0:
            parts.append(f"{minutes} phút")
        if seconds > 0 and not parts:  # Chỉ hiện giây nếu chưa có phần tử nào
            parts.append(f"{seconds} giây")

        return ", ".join(parts)

    @commands.command(name="daily", aliases=["diemdanh", "điểm danh", "nhandiemdanh"], usage="")
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def daily(self, ctx):
        """Điểm danh hàng ngày để nhận thưởng"""
        user_id = ctx.author.id

        try:
            # Kiểm tra người chơi
            player = await self.db.get_player(user_id)
            if not player:
                await ctx.send(
                    f"{ctx.author.mention}, bạn chưa bắt đầu tu luyện! Hãy sử dụng lệnh `!tongmon` để chọn môn phái.")
                return

            # Kiểm tra thời gian điểm danh lần trước
            now = datetime.now()
            last_daily = player.get('last_daily')
            if isinstance(last_daily, str):
                try:
                    last_daily = datetime.strptime(last_daily, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    last_daily = datetime.min

            # Tính thời gian trôi qua từ lần điểm danh trước
            time_since_last = now - last_daily if last_daily else timedelta(days=2)

            # Kiểm tra streak
            streak = player.get('daily_streak', 0)
            if time_since_last.days > 2:  # Reset streak nếu quá 2 ngày
                streak = 0

            # Tính phần thưởng
            base_reward = 100  # EXP cơ bản
            streak_bonus = min(streak * 0.1, 1.0)  # Tối đa 100% bonus

            reward = int(base_reward * (1 + streak_bonus))
            new_streak = streak + 1

            # Xử lý phần thưởng đặc biệt mỗi 7 ngày
            special_reward = False
            special_reward_text = ""
            if new_streak % 7 == 0:
                special_reward = True
                bonus_exp = int(reward * 0.5)  # Thêm 50% exp
                reward += bonus_exp
                special_reward_text = f"🎁 **Phần thưởng đặc biệt 7 ngày**: +{bonus_exp} EXP"

            # Cập nhật người chơi
            new_exp = player.get('exp', 0) + reward
            await self.db.update_player(
                user_id,
                exp=new_exp,
                last_daily=now,
                daily_streak=new_streak
            )

            # Tạo embed thông báo
            embed = discord.Embed(
                title="📝 Điểm Danh Thành Công",
                description=f"{ctx.author.mention} đã điểm danh ngày hôm nay!",
                color=0x2ecc71,
                timestamp=now
            )

            # Thông tin phần thưởng
            embed.add_field(
                name="🏮 Phần Thưởng",
                value=(
                    f"EXP cơ bản: +{base_reward}\n"
                    f"Streak bonus: +{int(streak_bonus * 100)}%\n"
                    f"**Tổng cộng**: +{reward} EXP"
                ),
                inline=True
            )

            # Thông tin streak
            embed.add_field(
                name="🔥 Streak",
                value=(
                    f"Streak hiện tại: {new_streak} ngày\n"
                    f"Streak bonus: +{min(new_streak * 10, 100)}%\n"
                    f"Ngày tiếp theo: {(new_streak + 1) % 7}/7"
                ),
                inline=True
            )

            # Thêm thông tin phần thưởng đặc biệt nếu có
            if special_reward:
                embed.add_field(
                    name="🎁 Phần Thưởng Đặc Biệt",
                    value=(
                        f"Chúc mừng! Bạn đã đạt streak {new_streak} ngày!\n"
                        f"{special_reward_text}"
                    ),
                    inline=False
                )

            # Thêm thông tin tu vi
            embed.add_field(
                name="📊 Tu Vi",
                value=(
                    f"Cảnh giới: {player.get('level', 'Phàm Nhân')}\n"
                    f"Tu vi trước: {player.get('exp', 0):,} EXP\n"
                    f"Tu vi hiện tại: {new_exp:,} EXP"
                ),
                inline=False
            )

            # Thêm avatar người chơi
            if ctx.author.avatar:
                embed.set_thumbnail(url=ctx.author.avatar.url)

            # Thêm footer
            embed.set_footer(text="Hãy điểm danh mỗi ngày để nhận nhiều phần thưởng hơn!")

            await ctx.send(embed=embed)

            # Kiểm tra thăng cấp
            cultivation_cog = self.bot.get_cog('Cultivation')
            if cultivation_cog:
                await cultivation_cog.check_level_up(ctx, player.get('level', 'Phàm Nhân'), new_exp)

        except Exception as e:
            print(f"Lỗi khi điểm danh: {e}")
            await ctx.send("❌ Có lỗi xảy ra khi điểm danh!")
            self.daily.reset_cooldown(ctx)

    @daily.error
    async def daily_error(self, ctx, error):
        """Xử lý lỗi lệnh daily"""
        if isinstance(error, commands.CommandOnCooldown):
            # Tính thời gian còn lại
            retry_after = int(error.retry_after)
            hours, remainder = divmod(retry_after, 3600)
            minutes, seconds = divmod(remainder, 60)

            # Tính thời gian có thể điểm danh tiếp theo
            next_daily = datetime.now() + timedelta(seconds=retry_after)
            next_time = next_daily.strftime('%H:%M:%S')

            embed = discord.Embed(
                title="⏳ Điểm Danh Đã Thực Hiện",
                description=f"{ctx.author.mention}, bạn đã điểm danh hôm nay rồi!",
                color=0xf1c40f
            )

            embed.add_field(
                name="⏰ Thời Gian Còn Lại",
                value=f"{hours} giờ, {minutes} phút, {seconds} giây",
                inline=True
            )

            embed.add_field(
                name="📅 Lần Tiếp Theo",
                value=f"Quay lại vào lúc {next_time} để điểm danh tiếp!",
                inline=True
            )

            await ctx.send(embed=embed)
        else:
            print(f"Lỗi không xử lý được trong daily: {error}")
            await ctx.send("❌ Có lỗi xảy ra khi thực hiện lệnh điểm danh!")

    @commands.command(name="help", aliases=["h", "commands", "cmd"], usage="[lệnh]")
    async def help_command(self, ctx, command_name: str = None):
        """Hiển thị danh sách lệnh và hướng dẫn"""
        if command_name:
            # Hiển thị thông tin chi tiết về một lệnh cụ thể
            await self.show_command_help(ctx, command_name)
        else:
            # Hiển thị danh sách tất cả lệnh
            await self.show_all_commands(ctx)

    async def show_command_help(self, ctx, command_name: str):
        """Hiển thị thông tin chi tiết về một lệnh cụ thể"""
        # Tìm lệnh
        command = self.bot.get_command(command_name)
        if not command:
            # Thử tìm kiếm theo alias
            for cmd in self.bot.commands:
                if command_name in cmd.aliases:
                    command = cmd
                    break

        if not command:
            await ctx.send(f"❌ Không tìm thấy lệnh `{command_name}`!")
            return

        # Tạo embed hiển thị thông tin lệnh
        embed = discord.Embed(
            title=f"📖 Lệnh: {ctx.prefix}{command.name}",
            description=command.help or "Không có mô tả chi tiết.",
            color=0x3498db,
            timestamp=datetime.now()
        )

        # Cách sử dụng
        usage = command.usage or ""
        embed.add_field(
            name="🔍 Cú Pháp",
            value=f"`{ctx.prefix}{command.name} {usage}`",
            inline=False
        )

        # Các tên thay thế
        if command.aliases:
            aliases = ", ".join([f"`{ctx.prefix}{alias}`" for alias in command.aliases])
            embed.add_field(
                name="🔄 Tên Thay Thế",
                value=aliases,
                inline=False
            )

        # Cooldown nếu có
        if command._buckets and command._buckets._cooldown:
            cooldown = command._buckets._cooldown
            embed.add_field(
                name="⏱️ Cooldown",
                value=f"{cooldown.rate} lần mỗi {cooldown.per} giây",
                inline=True
            )

        # Phân loại người dùng
        if command.cog:
            embed.add_field(
                name="📚 Nhóm",
                value=command.cog.qualified_name,
                inline=True
            )

        # Thêm ví dụ sử dụng
        example = f"{ctx.prefix}{command.name}"
        if usage:
            if "[" in usage:  # Có tham số tùy chọn
                example += " " + usage.replace("[", "").replace("]", "")
            else:
                example += " " + usage

        embed.add_field(
            name="💡 Ví Dụ",
            value=f"`{example}`",
            inline=False
        )

        await ctx.send(embed=embed)

    async def show_all_commands(self, ctx):
        """Hiển thị danh sách tất cả lệnh theo nhóm"""
        embed = discord.Embed(
            title="📚 Danh Sách Lệnh Tu Tiên Bot",
            description=(
                f"Sử dụng `{ctx.prefix}help [lệnh]` để xem chi tiết về một lệnh cụ thể.\n"
                f"Ví dụ: `{ctx.prefix}help daily`"
            ),
            color=0x2ecc71,
            timestamp=datetime.now()
        )

        # Nhóm lệnh theo cog
        cog_commands = {}
        for command in self.bot.commands:
            if command.hidden:
                continue

            cog_name = command.cog.qualified_name if command.cog else "Khác"
            if cog_name not in cog_commands:
                cog_commands[cog_name] = []

            cog_commands[cog_name].append(command)

        # Thêm các nhóm lệnh vào embed
        for cog_name, commands in sorted(cog_commands.items()):
            # Tạo danh sách lệnh
            command_list = []
            for cmd in sorted(commands, key=lambda x: x.name):
                brief = cmd.help.split('\n')[0] if cmd.help else "Không có mô tả"
                command_list.append(f"`{ctx.prefix}{cmd.name}` - {brief[:40]}")

            embed.add_field(
                name=f"🔹 {cog_name}",
                value="\n".join(command_list) if command_list else "Không có lệnh",
                inline=False
            )

        # Thêm thông tin bổ sung
        embed.set_footer(text=f"Tổng số lệnh: {sum(len(cmds) for cmds in cog_commands.values())}")

        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)

        await ctx.send(embed=embed)

    @commands.command(name="profile", aliases=["thongtin", "me", "info"], usage="[@người_chơi]")
    async def profile(self, ctx, member: discord.Member = None):
        """Xem thông tin cá nhân của người chơi"""
        # Nếu không cung cấp member, lấy thông tin người gọi lệnh
        target = member or ctx.author

        try:
            # Lấy thông tin người chơi
            player = await self.db.get_player(target.id)
            if not player:
                if target == ctx.author:
                    await ctx.send(
                        f"{ctx.author.mention}, bạn chưa bắt đầu tu luyện! Hãy sử dụng lệnh `!tongmon` để chọn môn phái.")
                else:
                    await ctx.send(f"{target.mention} chưa bắt đầu tu luyện!")
                return

            # Tạo embed thông tin người chơi
            sect = player.get('sect', 'Không có môn phái')
            sect_emoji = SECT_EMOJIS.get(sect, "🏯") if 'SECT_EMOJIS' in globals() else "🏯"

            embed = discord.Embed(
                title=f"📊 Thông Tin Tu Sĩ: {target.display_name}",
                description=f"Đệ tử {sect_emoji} **{sect}**",
                color=SECT_COLORS.get(sect, 0x3498db) if 'SECT_COLORS' in globals() else 0x3498db,
                timestamp=datetime.now()
            )

            # Thông tin cơ bản
            embed.add_field(
                name="🌟 Cảnh Giới",
                value=player.get('level', 'Phàm Nhân'),
                inline=True
            )

            embed.add_field(
                name="📈 Tu Vi",
                value=f"{player.get('exp', 0):,} EXP",
                inline=True
            )

            # Thêm thông tin về ngày tham gia
            joined_at = player.get('created_at')
            if joined_at:
                if isinstance(joined_at, str):
                    try:
                        joined_at = datetime.strptime(joined_at, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        joined_at = None

                if joined_at:
                    time_diff = datetime.now() - joined_at
                    days = time_diff.days

                    embed.add_field(
                        name="⏱️ Thời Gian Tu Luyện",
                        value=f"{days} ngày",
                        inline=True
                    )

            # Thông tin chiến đấu
            stats = player.get('stats', {})

            # Chỉ số chiến đấu
            embed.add_field(
                name="⚔️ Sức Mạnh",
                value=(
                    f"Công Kích: {player.get('attack', 0)}\n"
                    f"Phòng Thủ: {player.get('defense', 0)}\n"
                    f"HP: {player.get('hp', 100)}/100"
                ),
                inline=True
            )

            # Thống kê chiến đấu
            pvp_wins = stats.get('pvp_wins', 0)
            pvp_losses = stats.get('pvp_losses', 0)
            total_pvp = pvp_wins + pvp_losses
            win_rate = (pvp_wins / total_pvp * 100) if total_pvp > 0 else 0

            embed.add_field(
                name="📊 Thành Tích PvP",
                value=(
                    f"Thắng: {pvp_wins} | Thua: {pvp_losses}\n"
                    f"Tỷ lệ thắng: {win_rate:.1f}%\n"
                    f"Tổng trận: {total_pvp}"
                ),
                inline=True
            )

            # Thành tích săn quái
            monsters_killed = stats.get('monsters_killed', 0)
            bosses_killed = stats.get('bosses_killed', 0)

            embed.add_field(
                name="🐉 Thành Tích Săn Quái",
                value=(
                    f"Quái thường: {monsters_killed}\n"
                    f"Boss: {bosses_killed}\n"
                    f"Tổng: {monsters_killed + bosses_killed}"
                ),
                inline=True
            )

            # Thông tin streak
            daily_streak = player.get('daily_streak', 0)
            last_daily = player.get('last_daily')
            if isinstance(last_daily, str):
                try:
                    last_daily = datetime.strptime(last_daily, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    last_daily = datetime.min

            embed.add_field(
                name="🔥 Điểm Danh",
                value=(
                    f"Streak: {daily_streak} ngày\n"
                    f"Bonus: +{min(daily_streak * 10, 100)}%\n"
                    f"Đặc biệt: {daily_streak % 7}/7 ngày"
                ),
                inline=True
            )

            # Thêm avatar người chơi
            if target.avatar:
                embed.set_thumbnail(url=target.avatar.url)

            # Thêm footer
            embed.set_footer(text=f"ID: {target.id} • Thành viên từ: {target.created_at.strftime('%d/%m/%Y')}")

            await ctx.send(embed=embed)

        except Exception as e:
            print(f"Lỗi khi xem thông tin người chơi: {e}")
            await ctx.send("❌ Có lỗi xảy ra khi lấy thông tin người chơi!")


async def setup(bot):
    await bot.add_cog(Commands(bot, bot.db))