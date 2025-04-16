# modules/daily.py
import discord
from discord.ext import commands
from datetime import datetime, timedelta
import random
import asyncio
from typing import Dict, Any, List, Tuple, Optional
from modules.shared_commands import handle_daily_command
import calendar
from config import SECT_EMOJIS, SECT_COLORS


class Daily(commands.Cog):
    """Hệ thống điểm danh hàng ngày"""

    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.reward_lock = asyncio.Lock()  # Lock để tránh race condition
        self.player_cache = {}  # Cache để giảm số lần truy vấn database
        self.cache_timeout = 60  # seconds

    @commands.command(name="daily", aliases=["diemdanh"], usage="")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def daily(self, ctx):
        """Điểm danh hàng ngày để nhận thưởng"""
        await handle_daily_command(ctx, self.db)  # Gọi hàm xử lý chung

    # Danh sách thông điệp điểm danh
    DAILY_MESSAGES = [
        "Siêng năng tu luyện, ắt có ngày thành đạo!",
        "Một ngày không tu luyện, đạo tâm lui một bước.",
        "Tu đạo cần bền bỉ, mỗi ngày một bước tiến.",
        "Kiên trì là chìa khóa của thành công!",
        "Đường tu tiên không dễ, nhưng ngươi đã tiến bộ rồi!",
        "Tích tiểu thành đại, từng bước vững chắc!",
        "Đạo tâm kiên định, ắt thành chánh quả!",
        "Lửa thử vàng, gian nan thử đạo tâm!",
        "Ngày mới tu vi tăng, đạo tâm kiên cố!",
        "Thiên đạo vô tư, cần cù bù thông minh!"
    ]

    # Danh sách emoji ngày
    DAY_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣"]

    # Phần thưởng đặc biệt theo mốc
    MILESTONE_REWARDS = {
        7: {"bonus": 100, "message": "Một tuần kiên trì!", "emoji": "🌟"},
        14: {"bonus": 200, "message": "Hai tuần bền bỉ!", "emoji": "✨"},
        30: {"bonus": 500, "message": "Một tháng kiên định!", "emoji": "🌙"},
        50: {"bonus": 1000, "message": "Ngũ thập nhật thành đạo!", "emoji": "☀️"},
        100: {"bonus": 2000, "message": "Bách nhật bất đoạn!", "emoji": "🔥"},
        200: {"bonus": 5000, "message": "Song bách nhật đại viên mãn!", "emoji": "💫"},
        365: {"bonus": 10000, "message": "Nhất niên tinh tiến!", "emoji": "👑"}
    }

    # Hiệu ứng đặc biệt thứ trong tuần
    WEEKDAY_BONUSES = {
        0: {"bonus": 0.1, "name": "Ngày Đầu Tuần", "message": "Khởi đầu tuần mới đầy năng lượng!"},
        1: {"bonus": 0.05, "name": "Ngày Trí Tuệ", "message": "Tâm trí minh mẫn, tu vi tăng tiến!"},
        2: {"bonus": 0.05, "name": "Ngày Giữa Tuần", "message": "Nửa chặng đường, kiên trì bất biến!"},
        3: {"bonus": 0.05, "name": "Ngày Nghị Lực", "message": "Ý chí kiên cường, vượt mọi chông gai!"},
        4: {"bonus": 0.05, "name": "Ngày Cuối Tuần", "message": "Kết thúc tuần đầy thành tựu!"},
        5: {"bonus": 0.15, "name": "Ngày Thứ Bảy", "message": "Thời gian nghỉ ngơi, tu vi tăng vọt!"},
        6: {"bonus": 0.2, "name": "Ngày Chủ Nhật", "message": "Ngày linh thiêng, đạo hạnh tăng cao!"}
    }

    @commands.Cog.listener()
    async def on_ready(self):
        """Khởi tạo khi bot khởi động"""
        print("✓ Module Daily đã sẵn sàng!")

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

    async def format_next_daily_time(self, last_daily: datetime) -> str:
        """Format thời gian điểm danh tiếp theo"""
        next_daily = last_daily + timedelta(days=1)
        now = datetime.now()

        if next_daily < now:
            return "Có thể điểm danh ngay bây giờ!"

        time_left = next_daily - now
        hours = int(time_left.seconds / 3600)
        minutes = int((time_left.seconds % 3600) / 60)
        seconds = time_left.seconds % 60

        if hours > 0:
            return f"{hours} giờ {minutes} phút {seconds} giây"
        elif minutes > 0:
            return f"{minutes} phút {seconds} giây"
        else:
            return f"{seconds} giây"

    @commands.command(name="daily", aliases=["diemdanh", "điểmdanh", "nhandiemdanh"], usage="")
    @commands.cooldown(1, 30, commands.BucketType.user)  # Cooldown 30 giây giữa các lần thử
    async def daily(self, ctx):
        """Điểm danh nhận thưởng hàng ngày"""
        # Hiển thị thông báo đang xử lý
        loading_msg = await ctx.send("⏳ Đang xử lý điểm danh...")

        async with self.reward_lock:
            try:
                # Kiểm tra người chơi
                player = await self.get_player(ctx.author.id)
                if not player:
                    await loading_msg.delete()
                    await ctx.send(
                        f"{ctx.author.mention}, bạn chưa gia nhập môn phái nào! Hãy sử dụng lệnh `!tongmon` để chọn môn phái.")
                    return

                current_time = datetime.now()

                # Lấy thông tin điểm danh từ player
                last_daily = player.get('last_daily')
                streak = player.get('daily_streak', 0)

                # Chuyển đổi từ string sang datetime nếu cần
                if isinstance(last_daily, str):
                    try:
                        last_daily = datetime.strptime(last_daily, '%Y-%m-%d %H:%M:%S')
                    except (ValueError, TypeError):
                        last_daily = datetime.min

                # Nếu chưa đến giờ điểm danh
                if last_daily and current_time - last_daily < timedelta(days=1):
                    next_daily = last_daily + timedelta(days=1)
                    time_left = next_daily - current_time
                    hours = int(time_left.seconds / 3600)
                    minutes = int((time_left.seconds % 3600) / 60)
                    seconds = time_left.seconds % 60

                    # Tạo hiệu ứng hoạt ảnh đếm ngược
                    for i in range(3):
                        await loading_msg.edit(content=f"⏳ Đang kiểm tra thời gian điểm danh{'.' * (i + 1)}")
                        await asyncio.sleep(0.5)

                    embed = discord.Embed(
                        title="⏰ Chưa Đến Giờ Điểm Danh",
                        description=(
                            f"{ctx.author.mention}, bạn cần đợi thêm:\n"
                            f"```{hours} giờ {minutes} phút {seconds} giây```"
                        ),
                        color=0xff9900,
                        timestamp=current_time
                    )

                    # Thêm thông tin điểm danh tiếp theo
                    next_time = next_daily.strftime('%H:%M:%S ngày %d/%m/%Y')
                    embed.add_field(
                        name="⌚ Thời Gian Điểm Danh Tiếp Theo",
                        value=f"```{next_time}```",
                        inline=False
                    )

                    # Thêm thông tin streak hiện tại
                    if streak > 0:
                        embed.add_field(
                            name="🔥 Chuỗi Ngày Hiện Tại",
                            value=f"```{streak} ngày liên tiếp```",
                            inline=True
                        )

                        # Tính toán mốc tiếp theo
                        next_milestone = None
                        for days in sorted(self.MILESTONE_REWARDS.keys()):
                            if streak < days:
                                next_milestone = days
                                break

                        if next_milestone:
                            embed.add_field(
                                name="🎯 Mốc Tiếp Theo",
                                value=f"```Còn {next_milestone - streak} ngày nữa đến mốc {next_milestone} ngày!```",
                                inline=True
                            )

                    if ctx.author.avatar:
                        embed.set_thumbnail(url=ctx.author.avatar.url)

                    embed.set_footer(text="Tu đạo cần kiên nhẫn!")

                    await loading_msg.delete()
                    await ctx.send(embed=embed)
                    return

                # Kiểm tra chuỗi điểm danh
                old_streak = streak
                if last_daily and current_time - last_daily < timedelta(days=2):
                    streak += 1
                else:
                    streak = 1
                    # Thông báo mất chuỗi nếu trước đó có streak > 1
                    if old_streak > 1:
                        await loading_msg.edit(content=f"😢 Tiếc quá! Bạn đã mất chuỗi điểm danh {old_streak} ngày!")
                        await asyncio.sleep(1.5)

                # Hiệu ứng hoạt ảnh nhận quà
                for i in range(3):
                    await loading_msg.edit(content=f"🎁 Đang nhận phần thưởng{'.' * (i + 1)}")
                    await asyncio.sleep(0.5)

                # Tính phần thưởng
                base_exp = 100
                streak_bonus = min(streak * 0.1, 1.0)  # Tối đa 100% bonus từ streak

                # Tính bonus theo thứ trong tuần
                weekday = current_time.weekday()
                weekday_data = self.WEEKDAY_BONUSES.get(weekday, {"bonus": 0, "name": "Ngày Thường", "message": ""})
                weekday_bonus = weekday_data["bonus"]

                # Tính tổng exp thường
                exp_reward = int(base_exp * (1 + streak_bonus + weekday_bonus))

                # Tạo embed thông báo
                # Lấy màu và emoji dựa theo môn phái
                sect = player.get('sect', 'Không có')
                sect_emoji = SECT_EMOJIS.get(sect, "🏯") if 'SECT_EMOJIS' in globals() else "🏯"
                sect_color = SECT_COLORS.get(sect, 0xffd700) if 'SECT_COLORS' in globals() else 0xffd700

                embed = discord.Embed(
                    title=f"🌟 Điểm Danh Thành Công!",
                    description=f"{sect_emoji} {random.choice(self.DAILY_MESSAGES)}",
                    color=sect_color,
                    timestamp=current_time
                )

                # Thông tin phần thưởng
                reward_info = [
                    f"+{base_exp} EXP (Cơ bản)",
                ]

                if streak_bonus > 0:
                    streak_bonus_exp = int(base_exp * streak_bonus)
                    reward_info.append(f"+{streak_bonus_exp} EXP (Chuỗi ngày +{int(streak_bonus * 100)}%)")

                if weekday_bonus > 0:
                    weekday_bonus_exp = int(base_exp * weekday_bonus)
                    reward_info.append(
                        f"+{weekday_bonus_exp} EXP ({weekday_data['name']} +{int(weekday_bonus * 100)}%)")

                total_exp = exp_reward

                # Kiểm tra phần thưởng đặc biệt cho mốc
                milestone_bonus = 0
                milestone_message = ""
                for days, reward in self.MILESTONE_REWARDS.items():
                    if streak == days:
                        milestone_bonus = reward["bonus"]
                        milestone_message = reward["message"]
                        milestone_emoji = reward["emoji"]
                        total_exp += milestone_bonus
                        embed.add_field(
                            name=f"{milestone_emoji} {milestone_message}",
                            value=f"```+{milestone_bonus:,} EXP```",
                            inline=False
                        )
                        reward_info.append(f"+{milestone_bonus:,} EXP (Mốc {days} ngày)")
                        break

                # Cập nhật exp và thông tin điểm danh
                new_exp = player.get('exp', 0) + total_exp
                await self.db.update_player(
                    ctx.author.id,
                    exp=new_exp,
                    last_daily=current_time,
                    daily_streak=streak
                )

                # Xóa cache
                if ctx.author.id in self.player_cache:
                    del self.player_cache[ctx.author.id]

                # Thông tin tu vi
                embed.add_field(
                    name="📊 Thông Tin Tu Vi",
                    value=(
                        f"Cảnh Giới: {player.get('level', 'Phàm Nhân')}\n"
                        f"Tu Vi Trước: {player.get('exp', 0):,} EXP\n"
                        f"Tu Vi Hiện Tại: {new_exp:,} EXP\n"
                        f"Tăng: +{total_exp:,} EXP"
                    ),
                    inline=False
                )

                # Thêm thông tin phần thưởng
                embed.add_field(
                    name="🎁 Chi Tiết Phần Thưởng",
                    value="```\n" + "\n".join(reward_info) + "\n```",
                    inline=False
                )

                # Tạo hiển thị chuỗi ngày bằng emoji
                days_in_week = min(7, streak)
                day_icons = []

                # Hiển thị tuần hiện tại
                for i in range(days_in_week):
                    if i == days_in_week - 1:  # Ngày hiện tại
                        day_icons.append("🔥")
                    else:
                        day_icons.append("✅")

                # Điền các ngày còn lại trong tuần
                for i in range(7 - days_in_week):
                    day_icons.append("⬜")

                # Tạo chuỗi hiển thị
                weekday_names = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
                week_display = " ".join([f"{name}:{icon}" for name, icon in zip(weekday_names, day_icons)])

                embed.add_field(
                    name=f"🔥 Chuỗi Ngày: {streak} ngày liên tiếp",
                    value=(
                        f"```\n{week_display}\n```"
                        f"Bonus hiện tại: +{min(streak * 10, 100)}%"
                    ),
                    inline=False
                )

                # Thêm thông tin về mốc tiếp theo
                if streak > 0:
                    next_milestone = None
                    for days in sorted(self.MILESTONE_REWARDS.keys()):
                        if streak < days:
                            next_milestone = days
                            break

                    if next_milestone:
                        days_left = next_milestone - streak
                        embed.add_field(
                            name="🎯 Mốc Tiếp Theo",
                            value=(
                                f"Mốc {next_milestone} ngày: Còn {days_left} ngày nữa\n"
                                f"Phần thưởng: +{self.MILESTONE_REWARDS[next_milestone]['bonus']:,} EXP"
                            ),
                            inline=True
                        )

                # Thêm thông tin về ngày đặc biệt
                if weekday_bonus > 0:
                    embed.add_field(
                        name=f"📅 {weekday_data['name']}",
                        value=weekday_data['message'],
                        inline=True
                    )

                # Thêm thông tin điểm danh tiếp theo
                next_daily = current_time + timedelta(days=1)
                next_time = next_daily.strftime('%H:%M:%S ngày %d/%m/%Y')
                embed.add_field(
                    name="⏰ Điểm Danh Tiếp Theo",
                    value=f"{next_time}",
                    inline=False
                )

                # Thêm avatar người chơi
                if ctx.author.avatar:
                    embed.set_thumbnail(url=ctx.author.avatar.url)

                # Thêm footer
                embed.set_footer(
                    text=f"Tháng {current_time.month}/{current_time.year} | Hãy điểm danh mỗi ngày để nhận nhiều phần thưởng!")

                # Xóa tin nhắn loading và gửi kết quả
                await loading_msg.delete()
                result_msg = await ctx.send(embed=embed)

                # Thêm emoji reaction
                await result_msg.add_reaction("🎁")

                # Kiểm tra level up
                cultivation_cog = self.bot.get_cog('Cultivation')
                if cultivation_cog:
                    await cultivation_cog.check_level_up(ctx, player.get('level', 'Phàm Nhân'), new_exp)

            except Exception as e:
                print(f"Lỗi khi điểm danh: {e}")
                await loading_msg.delete()
                await ctx.send("❌ Có lỗi xảy ra khi điểm danh! Xin hãy thử lại sau.")

    @daily.error
    async def daily_error(self, ctx, error):
        """Xử lý lỗi lệnh daily"""
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏳ Xin đợi {int(error.retry_after)} giây nữa rồi thử lại!")
        else:
            print(f"Lỗi không xử lý được trong daily: {error}")

    @commands.command(name="streak", aliases=["chuoingay", "chuỗingày", "xemchuoi"], usage="[@người_chơi]")
    async def check_streak(self, ctx, member: discord.Member = None):
        """Xem thông tin chuỗi điểm danh"""
        target = member or ctx.author

        try:
            # Lấy thông tin người chơi
            player = await self.get_player(target.id)
            if not player:
                if target == ctx.author:
                    await ctx.send(
                        f"{ctx.author.mention}, bạn chưa bắt đầu tu luyện! Hãy sử dụng lệnh `!tongmon` để chọn môn phái.")
                else:
                    await ctx.send(f"{target.display_name} chưa bắt đầu tu luyện!")
                return

            # Lấy thông tin streak
            streak = player.get('daily_streak', 0)
            last_daily = player.get('last_daily')

            # Chuyển đổi từ string sang datetime nếu cần
            if isinstance(last_daily, str):
                try:
                    last_daily = datetime.strptime(last_daily, '%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError):
                    last_daily = datetime.min

            # Kiểm tra xem streak có còn hiệu lực không
            current_time = datetime.now()
            streak_valid = True
            if last_daily and current_time - last_daily > timedelta(days=2):
                streak_valid = False

            # Tạo embed thông tin
            sect = player.get('sect', 'Không có')
            sect_emoji = SECT_EMOJIS.get(sect, "🏯") if 'SECT_EMOJIS' in globals() else "🏯"
            sect_color = SECT_COLORS.get(sect, 0xffd700) if 'SECT_COLORS' in globals() else 0xffd700

            embed = discord.Embed(
                title=f"🔥 Chuỗi Điểm Danh của {target.display_name}",
                description=f"{sect_emoji} Đệ tử **{sect}**",
                color=sect_color,
                timestamp=current_time
            )

            # Tạo hiển thị chuỗi ngày bằng emoji
            calendar_display = []

            # Tạo lịch tháng
            cal = calendar.monthcalendar(current_time.year, current_time.month)
            month_name = current_time.strftime("%B %Y")

            # Tính toán ngày điểm danh gần nhất
            last_daily_day = last_daily.day if last_daily else None

            # Tên các ngày trong tuần
            day_header = "  ".join(["T2", "T3", "T4", "T5", "T6", "T7", "CN"])
            calendar_display.append(day_header)

            # Thêm các ngày trong tháng
            for week in cal:
                week_line = []
                for day in week:
                    if day == 0:
                        week_line.append("  ")
                    elif day == current_time.day:
                        week_line.append("🔵")
                    elif last_daily and day == last_daily_day:
                        week_line.append("✅")
                    else:
                        week_line.append(f"{day:2d}")
                calendar_display.append("  ".join(week_line))

            # Thông tin streak
            if streak > 0:
                streak_status = "🟢 Đang hoạt động" if streak_valid else "🔴 Đã mất (quá 2 ngày không điểm danh)"
                embed.add_field(
                    name=f"📊 Thông Tin Chuỗi Ngày",
                    value=(
                        f"Chuỗi Hiện Tại: **{streak}** ngày liên tiếp\n"
                        f"Trạng Thái: {streak_status}\n"
                        f"Bonus EXP: +{min(streak * 10, 100)}%"
                    ),
                    inline=False
                )

                # Tìm mốc tiếp theo
                next_milestone = None
                for days in sorted(self.MILESTONE_REWARDS.keys()):
                    if streak < days:
                        next_milestone = days
                        break

                if next_milestone:
                    days_left = next_milestone - streak
                    reward = self.MILESTONE_REWARDS[next_milestone]
                    embed.add_field(
                        name=f"🎯 Mốc Tiếp Theo: {next_milestone} ngày",
                        value=(
                            f"Còn {days_left} ngày nữa\n"
                            f"Phần thưởng: +{reward['bonus']:,} EXP\n"
                            f"Thông điệp: {reward['emoji']} {reward['message']}"
                        ),
                        inline=False
                    )
            else:
                embed.add_field(
                    name="📊 Thông Tin Chuỗi Ngày",
                    value="Chưa có chuỗi điểm danh nào. Hãy bắt đầu điểm danh ngay!",
                    inline=False
                )

            # Hiển thị lịch tháng
            embed.add_field(
                name=f"📅 Lịch Tháng: {month_name}",
                value=f"```\n" + "\n".join(calendar_display) + "\n```",
                inline=False
            )

            # Thông tin thời gian
            if last_daily:
                last_daily_str = last_daily.strftime("%H:%M:%S ngày %d/%m/%Y")
                embed.add_field(
                    name="⏰ Lần Điểm Danh Gần Nhất",
                    value=last_daily_str,
                    inline=True
                )

                # Kiểm tra thời gian điểm danh tiếp theo
                if current_time - last_daily < timedelta(days=1):
                    next_daily = last_daily + timedelta(days=1)
                    time_left = await self.format_next_daily_time(last_daily)
                    embed.add_field(
                        name="⏳ Thời Gian Còn Lại",
                        value=time_left,
                        inline=True
                    )
                else:
                    embed.add_field(
                        name="✅ Trạng Thái",
                        value="Có thể điểm danh ngay bây giờ!",
                        inline=True
                    )

            # Thêm avatar người chơi
            if target.avatar:
                embed.set_thumbnail(url=target.avatar.url)

            # Thêm footer
            embed.set_footer(text="Sử dụng !daily để điểm danh hàng ngày")

            await ctx.send(embed=embed)

        except Exception as e:
            print(f"Lỗi khi kiểm tra streak: {e}")
            await ctx.send("❌ Có lỗi xảy ra khi kiểm tra chuỗi điểm danh!")

    @commands.command(name="calendar", aliases=["lich", "lịch"], usage="")
    async def show_calendar(self, ctx):
        """Hiển thị lịch tháng với các sự kiện đặc biệt"""
        try:
            # Lấy thời gian hiện tại
            now = datetime.now()

            # Tạo embed
            embed = discord.Embed(
                title=f"📅 Lịch Tháng {now.month}/{now.year}",
                description="Lịch các sự kiện đặc biệt và ngày điểm danh",
                color=0x3498db,
                timestamp=now
            )

            # Tạo lịch tháng
            cal = calendar.monthcalendar(now.year, now.month)

            # Tên các ngày trong tuần
            days_of_week = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]

            # Tạo hiển thị lịch
            calendar_display = []

            # Thêm header
            header = " | ".join([day[:2] for day in days_of_week])
            calendar_display.append(header)
            calendar_display.append("-" * len(header))

            # Thêm các ngày trong tháng
            for week in cal:
                week_line = []
                for i, day in enumerate(week):
                    if day == 0:
                        week_line.append("  ")
                    elif day == now.day:
                        week_line.append("🔵")
                    elif i >= 5:  # Thứ 7 và Chủ Nhật
                        week_line.append(f"{day:2d}")
                calendar_display.append(" | ".join(week_line))

            # Thêm các lịch vào embed
            embed.add_field(
                name=f"📆 Lịch Tháng {now.strftime('%B %Y')}",
                value=f"```\n" + "\n".join(calendar_display) + "\n```",
                inline=False
            )

            # Thêm thông tin các ngày đặc biệt
            special_days = []
            for weekday, data in self.WEEKDAY_BONUSES.items():
                if data["bonus"] > 0:
                    day_name = days_of_week[weekday]
                    bonus_percent = int(data["bonus"] * 100)
                    special_days.append(f"**{day_name}** ({data['name']}): +{bonus_percent}% EXP")

            if special_days:
                embed.add_field(
                    name="✨ Ngày Đặc Biệt",
                    value="\n".join(special_days),
                    inline=False
                )

            # Thêm thông tin về các mốc điểm danh
            milestone_info = []
            for days, reward in self.MILESTONE_REWARDS.items():
                milestone_info.append(
                    f"{reward['emoji']} **Mốc {days} ngày**: +{reward['bonus']:,} EXP - {reward['message']}"
                )

            embed.add_field(
                name="🎯 Phần Thưởng Mốc",
                value="\n".join(milestone_info),
                inline=False
            )

            # Thêm thông tin giải thích
            embed.add_field(
                name="📝 Chú Thích",
                value=(
                    "• 🔵 - Ngày hiện tại\n"
                    "• * - Ngày cuối tuần (bonus EXP cao hơn)\n"
                    "• Điểm danh mỗi ngày để nhận thưởng\n"
                    "• Streak tối đa: +100% bonus EXP"
                ),
                inline=False
            )

            # Thêm thông tin streak nếu người chơi có
            player = await self.get_player(ctx.author.id)
            if player and player.get('daily_streak', 0) > 0:
                streak = player.get('daily_streak', 0)
                streak_bonus = min(streak * 10, 100)

                embed.add_field(
                    name="🔥 Chuỗi Ngày Của Bạn",
                    value=f"{streak} ngày liên tiếp (+{streak_bonus}% bonus)",
                    inline=True
                )

                # Kiểm tra thời gian điểm danh tiếp theo
                last_daily = player.get('last_daily')
                if isinstance(last_daily, str):
                    try:
                        last_daily = datetime.strptime(last_daily, '%Y-%m-%d %H:%M:%S')
                    except (ValueError, TypeError):
                        last_daily = datetime.min

                if last_daily:
                    if now - last_daily < timedelta(days=1):
                        time_left = await self.format_next_daily_time(last_daily)
                        embed.add_field(
                            name="⏳ Thời Gian Còn Lại",
                            value=time_left,
                            inline=True
                        )
                    else:
                        embed.add_field(
                            name="✅ Trạng Thái",
                            value="Có thể điểm danh ngay bây giờ!",
                            inline=True
                        )

            # Footer
            embed.set_footer(text="Sử dụng !daily để điểm danh và !streak để xem chi tiết chuỗi ngày")

            await ctx.send(embed=embed)

        except Exception as e:
            print(f"Lỗi khi hiển thị lịch: {e}")
            await ctx.send("❌ Có lỗi xảy ra khi hiển thị lịch!")

    @commands.command(name="milestones", aliases=["phanquadiemdanh", "phầnqua", "dailyrewards"], usage="")
    async def show_milestones(self, ctx):
        """Hiển thị các mốc điểm danh và phần thưởng"""
        try:
            # Tạo embed thông tin
            embed = discord.Embed(
                title="🎁 Phần Thưởng Điểm Danh",
                description="Danh sách các mốc điểm danh đặc biệt và phần thưởng",
                color=0xf1c40f,
                timestamp=datetime.now()
            )

            # Thêm thông tin phần thưởng cơ bản
            embed.add_field(
                name="📊 Phần Thưởng Hàng Ngày",
                value=(
                    "• Phần thưởng cơ bản: **+100 EXP**\n"
                    "• Bonus chuỗi ngày: **+10% mỗi ngày** (tối đa 100%)\n"
                    "• Bonus ngày đặc biệt: **+5% đến +20%**"
                ),
                inline=False
            )

            # Thêm thông tin các mốc đặc biệt
            milestone_table = []
            milestone_table.append("|  Mốc  |  Phần Thưởng  |  Thông Điệp  |")
            milestone_table.append("|--------|--------------|--------------|")

            for days, reward in sorted(self.MILESTONE_REWARDS.items()):
                milestone_table.append(
                    f"| {days:^6} | {reward['emoji']} +{reward['bonus']:,} EXP | {reward['message']} |"
                )

            embed.add_field(
                name="🎯 Các Mốc Đặc Biệt",
                value=f"```\n" + "\n".join(milestone_table) + "\n```",
                inline=False
            )

            # Thêm thông tin ngày đặc biệt
            weekday_info = []
            for weekday, data in sorted(self.WEEKDAY_BONUSES.items()):
                day_name = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"][weekday]
                bonus_percent = int(data["bonus"] * 100)
                if bonus_percent > 0:
                    weekday_info.append(f"• **{day_name}** ({data['name']}): +{bonus_percent}% EXP - {data['message']}")

            embed.add_field(
                name="📅 Ngày Đặc Biệt",
                value="\n".join(weekday_info) if weekday_info else "Không có ngày đặc biệt",
                inline=False
            )

            # Thêm mẹo điểm danh
            embed.add_field(
                name="💡 Mẹo Điểm Danh",
                value=(
                    "• Điểm danh mỗi ngày để giữ chuỗi ngày\n"
                    "• Chuỗi ngày sẽ mất nếu bỏ lỡ 2 ngày liên tiếp\n"
                    "• Điểm danh vào Thứ 7 và Chủ Nhật để nhận nhiều EXP hơn\n"
                    "• Đạt các mốc để nhận phần thưởng đặc biệt"
                ),
                inline=False
            )

            # Thêm thông tin người chơi nếu có
            player = await self.get_player(ctx.author.id)
            if player:
                streak = player.get('daily_streak', 0)
                last_daily = player.get('last_daily')

                if isinstance(last_daily, str):
                    try:
                        last_daily = datetime.strptime(last_daily, '%Y-%m-%d %H:%M:%S')
                    except (ValueError, TypeError):
                        last_daily = datetime.min

                # Kiểm tra xem streak có còn hiệu lực không
                current_time = datetime.now()
                streak_valid = True
                if last_daily and current_time - last_daily > timedelta(days=2):
                    streak_valid = False

                # Hiển thị thông tin streak
                if streak > 0:
                    streak_status = "🟢 Đang hoạt động" if streak_valid else "🔴 Đã mất (quá 2 ngày không điểm danh)"

                    embed.add_field(
                        name="🔥 Chuỗi Ngày Của Bạn",
                        value=(
                            f"Chuỗi hiện tại: **{streak}** ngày liên tiếp\n"
                            f"Trạng thái: {streak_status}\n"
                            f"Bonus hiện tại: +{min(streak * 10, 100)}% EXP"
                        ),
                        inline=True
                    )

                    # Tìm mốc tiếp theo
                    next_milestone = None
                    for days in sorted(self.MILESTONE_REWARDS.keys()):
                        if streak < days:
                            next_milestone = days
                            break

                    if next_milestone:
                        days_left = next_milestone - streak
                        embed.add_field(
                            name="🎯 Mốc Tiếp Theo",
                            value=(
                                f"Mốc {next_milestone} ngày: Còn {days_left} ngày nữa\n"
                                f"Phần thưởng: +{self.MILESTONE_REWARDS[next_milestone]['bonus']:,} EXP"
                            ),
                            inline=True
                        )

            # Thêm avatar người chơi nếu có
            if ctx.author.avatar:
                embed.set_thumbnail(url=ctx.author.avatar.url)

            # Thêm footer
            embed.set_footer(text="Tu luyện mỗi ngày, tinh tiến không ngừng!")

            await ctx.send(embed=embed)

        except Exception as e:
            print(f"Lỗi khi hiển thị mốc điểm danh: {e}")
            await ctx.send("❌ Có lỗi xảy ra khi hiển thị thông tin mốc điểm danh!")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Gửi thông báo về hệ thống điểm danh khi thành viên mới tham gia"""
        try:
            # Đợi một chút để người dùng có thời gian vào server
            await asyncio.sleep(60)

            # Kiểm tra xem người dùng còn trong server không
            if member.guild.get_member(member.id) is None:
                return

            # Kiểm tra xem người dùng đã bắt đầu tu luyện chưa
            player = await self.get_player(member.id)
            if player:
                # Gửi thông báo nhắc nhở điểm danh
                try:
                    embed = discord.Embed(
                        title="📝 Hệ Thống Điểm Danh Tu Tiên",
                        description=(
                            f"Chào mừng {member.mention} đến với hệ thống Tu Tiên!\n\n"
                            f"Đừng quên điểm danh hàng ngày để nhận thưởng và tăng tu vi."
                        ),
                        color=0x2ecc71
                    )

                    embed.add_field(
                        name="🎁 Phần Thưởng Cơ Bản",
                        value="Mỗi ngày: +100 EXP",
                        inline=True
                    )

                    embed.add_field(
                        name="🔥 Chuỗi Ngày",
                        value="Mỗi ngày: +10% bonus (tối đa 100%)",
                        inline=True
                    )

                    embed.add_field(
                        name="📊 Các Lệnh Hữu Ích",
                        value=(
                            "• `!daily` - Điểm danh hàng ngày\n"
                            "• `!streak` - Xem chuỗi ngày hiện tại\n"
                            "• `!calendar` - Xem lịch điểm danh\n"
                            "• `!milestones` - Xem các mốc phần thưởng"
                        ),
                        inline=False
                    )

                    await member.send(embed=embed)
                except discord.Forbidden:
                    # Không thể gửi DM, bỏ qua
                    pass
        except Exception as e:
            print(f"Lỗi khi gửi thông báo cho thành viên mới: {e}")

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        """Thực hiện một số tác vụ khi một lệnh hoàn thành"""
        if ctx.command.name in ["daily", "streak", "calendar", "milestones"]:
            return

        # Nếu đã điểm danh hôm nay, không nhắc nhở
        player = await self.get_player(ctx.author.id)
        if not player:
            return

        # Kiểm tra lần điểm danh cuối
        last_daily = player.get('last_daily')
        if isinstance(last_daily, str):
            try:
                last_daily = datetime.strptime(last_daily, '%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError):
                last_daily = datetime.min

        # Nếu chưa điểm danh hôm nay và là sau 9 giờ sáng, nhắc nhở với xác suất 10%
        current_time = datetime.now()
        if (
                not last_daily or current_time.date() > last_daily.date()) and current_time.hour >= 9 and random.random() < 0.1:
            try:
                embed = discord.Embed(
                    title="📝 Nhắc Nhở Điểm Danh",
                    description=(
                        f"{ctx.author.mention}, hôm nay bạn chưa điểm danh!\n"
                        f"Hãy sử dụng lệnh `!daily` để nhận thưởng."
                    ),
                    color=0xf39c12
                )

                # Thêm thông tin streak nếu có
                streak = player.get('daily_streak', 0)
                if streak > 0:
                    # Tìm mốc tiếp theo
                    next_milestone = None
                    for days in sorted(self.MILESTONE_REWARDS.keys()):
                        if streak < days:
                            next_milestone = days
                            break

                    if next_milestone:
                        days_left = next_milestone - streak
                        embed.add_field(
                            name="🔥 Chuỗi Ngày",
                            value=(
                                f"Hiện tại: {streak} ngày\n"
                                f"Mốc tiếp theo: {next_milestone} ngày (còn {days_left} ngày)"
                            ),
                            inline=False
                        )

                await ctx.send(embed=embed)
            except Exception as e:
                print(f"Lỗi khi gửi nhắc nhở điểm danh: {e}")

    @commands.command(name="reset_streak", hidden=True)
    @commands.has_permissions(administrator=True)
    async def reset_streak(self, ctx, member: discord.Member):
        """Reset chuỗi điểm danh của một người chơi (Admin only)"""
        try:
            player = await self.get_player(member.id)
            if not player:
                await ctx.send(f"{member.display_name} chưa bắt đầu tu luyện!")
                return

            # Reset streak
            await self.db.update_player(
                member.id,
                daily_streak=0
            )

            # Xóa cache
            if member.id in self.player_cache:
                del self.player_cache[member.id]

            await ctx.send(f"✅ Đã reset chuỗi điểm danh của {member.display_name}!")

        except Exception as e:
            print(f"Lỗi khi reset streak: {e}")
            await ctx.send("❌ Có lỗi xảy ra khi reset chuỗi điểm danh!")

    @commands.command(name="set_streak", hidden=True)
    @commands.has_permissions(administrator=True)
    async def set_streak(self, ctx, member: discord.Member, streak: int):
        """Đặt chuỗi điểm danh của một người chơi (Admin only)"""
        try:
            player = await self.get_player(member.id)
            if not player:
                await ctx.send(f"{member.display_name} chưa bắt đầu tu luyện!")
                return

            if streak < 0:
                await ctx.send("❌ Chuỗi ngày không thể là số âm!")
                return

            # Đặt streak mới
            await self.db.update_player(
                member.id,
                daily_streak=streak
            )

            # Xóa cache
            if member.id in self.player_cache:
                del self.player_cache[member.id]

            await ctx.send(f"✅ Đã đặt chuỗi điểm danh của {member.display_name} thành {streak} ngày!")

        except Exception as e:
            print(f"Lỗi khi đặt streak: {e}")
            await ctx.send("❌ Có lỗi xảy ra khi đặt chuỗi điểm danh!")


async def setup(bot):
    await bot.add_cog(Daily(bot, bot.db))