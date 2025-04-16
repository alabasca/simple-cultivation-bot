import discord
from discord.ext import commands
from datetime import datetime, timedelta
import traceback
import sys
import logging
import asyncio
import re
from typing import Optional, List, Dict, Any, Union, Tuple
import json
import os

# Thiết lập logging nâng cao
log_directory = 'logs'
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# Tạo tên file log với timestamp
current_time = datetime.now().strftime("%Y-%m-%d")
log_file = f"{log_directory}/errors_{current_time}.log"

# Cấu hình logging
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stderr)
    ]
)

# Tạo logger riêng cho bot
bot_logger = logging.getLogger('tu_tien_bot')
bot_logger.setLevel(logging.ERROR)


class ErrorHandler(commands.Cog):
    """Xử lý lỗi và ngoại lệ cho bot"""

    def __init__(self, bot):
        self.bot = bot
        self.error_cooldowns = {}  # Lưu cooldown cho mỗi user
        self.error_counts = {}  # Đếm số lỗi cho mỗi loại
        self.logger = bot_logger
        self.error_lock = asyncio.Lock()

        # Tạo file thống kê lỗi nếu chưa tồn tại
        self.error_stats_file = f"{log_directory}/error_stats.json"
        if not os.path.exists(self.error_stats_file):
            with open(self.error_stats_file, 'w', encoding='utf-8') as f:
                json.dump({}, f)

        # Tải thống kê lỗi từ file
        self.load_error_stats()

        # Khởi tạo task định kỳ lưu thống kê lỗi
        self.bot.loop.create_task(self.periodic_save_stats())

    async def periodic_save_stats(self):
        """Task định kỳ lưu thống kê lỗi"""
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await asyncio.sleep(300)  # Lưu mỗi 5 phút
            self.save_error_stats()

    def load_error_stats(self):
        """Tải thống kê lỗi từ file"""
        try:
            with open(self.error_stats_file, 'r', encoding='utf-8') as f:
                self.error_counts = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            self.error_counts = {}

    def save_error_stats(self):
        """Lưu thống kê lỗi vào file"""
        try:
            with open(self.error_stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.error_counts, f, indent=2)
        except Exception as e:
            print(f"Lỗi khi lưu thống kê lỗi: {e}")

    def update_error_stats(self, error_type: str):
        """Cập nhật thống kê lỗi"""
        if error_type not in self.error_counts:
            self.error_counts[error_type] = 0
        self.error_counts[error_type] += 1

    async def create_error_embed(self,
                                 title: str,
                                 description: str,
                                 color: int = 0xff0000,
                                 footer: bool = True,
                                 fields: List[Dict[str, Any]] = None) -> discord.Embed:
        """Tạo embed thông báo lỗi bất đồng bộ với nhiều tùy chọn hơn"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.now()
        )

        # Thêm các trường tùy chọn
        if fields:
            for field in fields:
                embed.add_field(
                    name=field.get('name', 'Thông tin'),
                    value=field.get('value', 'Không có dữ liệu'),
                    inline=field.get('inline', False)
                )

        if footer:
            embed.set_footer(text="Sử dụng !tutien để xem hướng dẫn chi tiết")

        return embed

    async def log_error(self, ctx: commands.Context, error: Exception, error_type: str = "Unknown") -> None:
        """Log lỗi với thông tin chi tiết và cập nhật thống kê"""
        async with self.error_lock:
            try:
                # Tạo ID lỗi duy nhất để dễ theo dõi
                error_id = f"ERR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(str(error)) % 10000:04d}"

                # Tạo thông tin lỗi chi tiết
                error_msg = (
                    f"\nError ID: {error_id}\n"
                    f"Time: {datetime.now()}\n"
                    f"Error Type: {error_type}\n"
                    f"Command: {ctx.command}\n"
                    f"Author: {ctx.author} (ID: {ctx.author.id})\n"
                    f"Guild: {ctx.guild.name if ctx.guild else 'DM'} "
                    f"(ID: {ctx.guild.id if ctx.guild else 'N/A'})\n"
                    f"Channel: {ctx.channel.name} (ID: {ctx.channel.id})\n"
                    f"Message: {ctx.message.content}\n"
                    f"Error: {str(error)}\n"
                    f"Traceback:\n{''.join(traceback.format_tb(error.__traceback__))}\n"
                    f"{'-' * 50}"
                )

                # Log lỗi
                self.logger.error(error_msg)

                # Cập nhật thống kê
                self.update_error_stats(error_type)

                # Thông báo cho owner bot nếu là lỗi nghiêm trọng
                if isinstance(error, (commands.CommandInvokeError, commands.ExtensionError)):
                    # Lấy owner từ ID hoặc từ application info
                    owner = None
                    if hasattr(self.bot, 'owner_id'):
                        owner = self.bot.get_user(self.bot.owner_id)

                    if not owner and hasattr(self.bot, 'application_info'):
                        app_info = await self.bot.application_info()
                        owner = app_info.owner

                    if owner:
                        error_embed = await self.create_error_embed(
                            f"🚨 Lỗi Nghiêm Trọng (ID: {error_id})",
                            f"```py\n{str(error)[:1500]}```",
                            0xff0000,
                            False,
                            [
                                {
                                    "name": "Command",
                                    "value": f"`{ctx.message.content[:100]}`",
                                    "inline": True
                                },
                                {
                                    "name": "User",
                                    "value": f"{ctx.author} (ID: {ctx.author.id})",
                                    "inline": True
                                },
                                {
                                    "name": "Server",
                                    "value": f"{ctx.guild.name if ctx.guild else 'DM'}",
                                    "inline": True
                                }
                            ]
                        )

                        try:
                            await owner.send(embed=error_embed)
                        except discord.HTTPException:
                            pass

            except Exception as e:
                print(f"Error in logging: {e}")

    async def check_error_cooldown(self, user_id: int, error_type: str = "generic") -> bool:
        """Kiểm tra cooldown của error handling với nhiều loại lỗi khác nhau"""
        current_time = datetime.now()
        cooldown_key = f"{user_id}_{error_type}"

        if cooldown_key in self.error_cooldowns:
            last_error = self.error_cooldowns[cooldown_key]
            # Cooldown khác nhau cho từng loại lỗi
            cooldown_seconds = 5  # Mặc định

            if error_type == "cooldown":
                cooldown_seconds = 3
            elif error_type == "permission":
                cooldown_seconds = 10
            elif error_type == "not_found":
                cooldown_seconds = 2

            if (current_time - last_error).total_seconds() < cooldown_seconds:
                return False

        self.error_cooldowns[cooldown_key] = current_time
        return True

    async def handle_cooldown_error(self, ctx: commands.Context, error: commands.CommandOnCooldown) -> discord.Embed:
        """Xử lý lỗi cooldown với thông báo thân thiện hơn"""
        remaining = timedelta(seconds=error.retry_after)
        days = remaining.days
        hours, remainder = divmod(remaining.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        time_formats = []
        if days > 0:
            time_formats.append(f"{days} ngày")
        if hours > 0:
            time_formats.append(f"{hours} giờ")
        if minutes > 0:
            time_formats.append(f"{minutes} phút")
        if seconds > 0 or not time_formats:
            time_formats.append(f"{seconds} giây")

        time_str = " ".join(time_formats)

        # Tùy chỉnh thông báo dựa trên thời gian chờ
        if error.retry_after > 3600:
            message = f"Đạo hữu cần nghỉ ngơi thêm {time_str} nữa.\nTu luyện cần thời gian, không thể vội vàng!"
        elif error.retry_after > 60:
            message = f"Hãy chờ thêm {time_str} nữa.\nTu đạo cần phải từ từ, dục tốc bất đạt!"
        else:
            message = f"Xin chờ {time_str} nữa.\nKhí hải chưa hồi phục, cần thêm thời gian!"

        embed = await self.create_error_embed(
            "⏳ Kỹ Năng Chưa Hồi",
            message,
            0xff9900
        )

        # Thêm gợi ý tùy chỉnh nếu có
        if hasattr(ctx.command, 'cooldown_message'):
            embed.add_field(
                name="💡 Gợi Ý",
                value=ctx.command.cooldown_message,
                inline=False
            )
        else:
            # Thêm gợi ý mặc định dựa trên loại lệnh
            command_category = getattr(ctx.command.cog, 'qualified_name', 'Unknown')

            if command_category == "Cultivation":
                embed.add_field(
                    name="💡 Gợi Ý",
                    value="Trong lúc chờ đợi, hãy thử tu luyện bằng cách tham gia voice chat hoặc trò chuyện với đạo hữu khác.",
                    inline=False
                )
            elif command_category == "Combat":
                embed.add_field(
                    name="💡 Gợi Ý",
                    value="Sau mỗi trận chiến, cơ thể cần thời gian hồi phục. Hãy thử luyện công hoặc tương tác với các đạo hữu khác.",
                    inline=False
                )

        return embed

    async def find_similar_commands(self, cmd: str) -> List[Tuple[str, float]]:
        """Tìm các lệnh tương tự với độ tương đồng"""
        all_commands = [c.name for c in self.bot.commands]
        similar_commands = []

        for command in all_commands:
            similarity = await self.calculate_similarity(cmd, command)
            if similarity > 0.6:  # Giảm ngưỡng để có nhiều gợi ý hơn
                similar_commands.append((command, similarity))

        # Sắp xếp theo độ tương đồng giảm dần
        similar_commands.sort(key=lambda x: x[1], reverse=True)
        return similar_commands[:3]  # Trả về tối đa 3 gợi ý

    async def calculate_similarity(self, s1: str, s2: str) -> float:
        """Tính độ tương đồng giữa hai chuỗi bất đồng bộ (Levenshtein distance)"""
        if len(s1) < len(s2):
            s1, s2 = s2, s1

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

    async def get_command_help(self, command_name: str) -> Optional[str]:
        """Lấy hướng dẫn sử dụng cho lệnh"""
        command = self.bot.get_command(command_name)
        if not command:
            return None

        help_text = command.help or "Không có mô tả chi tiết."
        usage = command.usage or ""

        return f"**Cách dùng:** `!{command_name} {usage}`\n{help_text}"

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """Xử lý các lỗi command chính với nhiều loại lỗi hơn"""
        # Bỏ qua nếu command có error handler riêng
        if hasattr(ctx.command, 'on_error'):
            return

        # Lấy lỗi gốc
        original_error = error
        error = getattr(error, 'original', error)

        # Bỏ qua một số loại lỗi đặc biệt
        if isinstance(error, (commands.CommandNotFound, commands.DisabledCommand)):
            pass  # Xử lý sau

        # Kiểm tra cooldown error handling dựa trên loại lỗi
        error_type = "generic"
        if isinstance(error, commands.CommandOnCooldown):
            error_type = "cooldown"
        elif isinstance(error, commands.MissingPermissions):
            error_type = "permission"
        elif isinstance(error, commands.CommandNotFound):
            error_type = "not_found"

        if not await self.check_error_cooldown(ctx.author.id, error_type):
            return

        try:
            embed = None

            if isinstance(error, commands.CommandOnCooldown):
                embed = await self.handle_cooldown_error(ctx, error)

            elif isinstance(error, commands.MissingPermissions):
                missing_perms = [perm.replace('_', ' ').title() for perm in error.missing_permissions]
                missing_perms_str = ', '.join(missing_perms)
                embed = await self.create_error_embed(
                    "🚫 Không Đủ Quyền Hạn",
                    f"Ngươi cần có các quyền sau: `{missing_perms_str}`\n"
                    "Hãy tu luyện thêm hoặc xin phép Tông Chủ.",
                    0xf1c40f
                )

            elif isinstance(error, commands.BotMissingPermissions):
                missing_perms = [perm.replace('_', ' ').title() for perm in error.missing_permissions]
                missing_perms_str = ', '.join(missing_perms)
                embed = await self.create_error_embed(
                    "⚠️ Bot Thiếu Quyền",
                    f"Bot cần có các quyền sau để thực hiện lệnh này: `{missing_perms_str}`\n"
                    "Vui lòng liên hệ quản trị viên để cấp quyền cho bot.",
                    0xe74c3c
                )

            elif isinstance(error, commands.MissingRequiredArgument):
                usage = ctx.command.usage if ctx.command.usage else "không có hướng dẫn"
                help_text = await self.get_command_help(ctx.command.name)

                fields = [
                    {
                        "name": "📝 Cách Dùng Đúng",
                        "value": f"`!{ctx.command.name} {usage}`",
                        "inline": False
                    }
                ]

                if help_text:
                    fields.append({
                        "name": "💡 Mô Tả",
                        "value": help_text[:1024],  # Discord giới hạn 1024 ký tự cho field
                        "inline": False
                    })

                embed = await self.create_error_embed(
                    "❌ Thiếu Thông Tin",
                    f"Thiếu thông tin bắt buộc: `{error.param.name}`",
                    0xff9900,
                    True,
                    fields
                )

            elif isinstance(error, commands.BadArgument):
                embed = await self.create_error_embed(
                    "❌ Thông Tin Không Hợp Lệ",
                    f"Thông tin bạn cung cấp không hợp lệ: {str(error)}",
                    0xff9900
                )

                # Thêm gợi ý cho một số lỗi phổ biến
                if "Member" in str(error) and "not found" in str(error):
                    embed.add_field(
                        name="💡 Gợi Ý",
                        value="Hãy đảm bảo bạn đã tag người dùng đúng cách: @tên_người_dùng",
                        inline=False
                    )

            elif isinstance(error, commands.CommandNotFound):
                cmd = ctx.message.content.split()[0][1:]  # Bỏ prefix
                similar_cmds = await self.find_similar_commands(cmd)

                desc = f"Thuật `{cmd}` không tồn tại trong các môn phái!"

                if similar_cmds:
                    suggestions = []
                    for cmd_name, similarity in similar_cmds:
                        cmd_help = await self.get_command_help(cmd_name)
                        cmd_desc = cmd_help.split('\n')[0] if cmd_help else "Không có mô tả"
                        suggestions.append(f"• `!{cmd_name}` - {cmd_desc[:50]}...")

                    desc += f"\n\nCó phải ý ngươi là:\n" + "\n".join(suggestions)

                embed = await self.create_error_embed(
                    "📜 Thuật Không Tồn Tại",
                    desc,
                    0xff9900
                )

            elif isinstance(error, commands.NoPrivateMessage):
                embed = await self.create_error_embed(
                    "🏯 Không Thể Sử Dụng",
                    "Thuật này chỉ có thể sử dụng trong tông môn, không thể dùng trong tin nhắn riêng!",
                    0xe74c3c
                )

            elif isinstance(error, commands.PrivateMessageOnly):
                embed = await self.create_error_embed(
                    "🔒 Chỉ Dùng Trong Tin Nhắn Riêng",
                    "Thuật này chỉ có thể sử dụng trong tin nhắn riêng với bot!",
                    0xe74c3c
                )

            elif isinstance(error, commands.NotOwner):
                embed = await self.create_error_embed(
                    "👑 Chỉ Dành Cho Tông Chủ",
                    "Chỉ có Tông Chủ mới có thể sử dụng thuật này!",
                    0xe74c3c
                )

            elif isinstance(error, commands.DisabledCommand):
                embed = await self.create_error_embed(
                    "🚫 Thuật Đã Bị Phong Ấn",
                    "Thuật này hiện đã bị phong ấn và không thể sử dụng.",
                    0xe74c3c
                )

            elif isinstance(error, commands.MaxConcurrencyReached):
                embed = await self.create_error_embed(
                    "⏳ Đang Thực Hiện",
                    f"Thuật này đang được thực hiện. Vui lòng đợi hoàn thành.",
                    0xff9900
                )

            elif isinstance(error, discord.Forbidden):
                embed = await self.create_error_embed(
                    "🔒 Không Đủ Quyền",
                    "Bot không có đủ quyền để thực hiện hành động này.",
                    0xe74c3c
                )

            else:
                # Log lỗi không xác định
                error_type = type(error).__name__
                await self.log_error(ctx, error, error_type)

                # Tạo ID lỗi để dễ theo dõi
                error_id = f"ERR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(str(error)) % 10000:04d}"

                embed = await self.create_error_embed(
                    "⚠️ Có Lỗi Xảy Ra",
                    f"Có lỗi xảy ra khi thực hiện lệnh này. (ID: {error_id})\n"
                    "Hãy thử lại sau hoặc liên hệ Tông Chủ nếu lỗi vẫn tiếp tục.",
                    0xe74c3c
                )

            if embed:
                try:
                    await ctx.send(embed=embed)
                except discord.HTTPException:
                    # Fallback nếu không gửi được embed
                    await ctx.send(f"Có lỗi khi thực hiện lệnh: {str(error)[:1500]}")

        except Exception as e:
            print(f"Error in error handler: {e}")
            traceback.print_exc()

    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        """Xử lý các lỗi không phải từ command"""
        error_type = sys.exc_info()[0].__name__
        error = sys.exc_info()[1]

        # Log lỗi
        error_msg = (
            f"\nTime: {datetime.now()}\n"
            f"Event: {event}\n"
            f"Error Type: {error_type}\n"
            f"Error: {str(error)}\n"
            f"Traceback:\n{''.join(traceback.format_tb(sys.exc_info()[2]))}\n"
            f"{'-' * 50}"
        )

        self.logger.error(error_msg)

        # Cập nhật thống kê
        self.update_error_stats(f"event_{event}_{error_type}")

    @commands.command(name="error_stats", aliases=["errors", "loi"])
    @commands.is_owner()
    async def error_stats(self, ctx):
        """Xem thống kê lỗi (chỉ dành cho chủ bot)"""
        if not self.error_counts:
            await ctx.send("Chưa có lỗi nào được ghi nhận.")
            return

        # Sắp xếp lỗi theo số lượng giảm dần
        sorted_errors = sorted(self.error_counts.items(), key=lambda x: x[1], reverse=True)

        embed = discord.Embed(
            title="📊 Thống Kê Lỗi",
            description=f"Tổng số loại lỗi: {len(sorted_errors)}",
            color=0x3498db,
            timestamp=datetime.now()
        )

        # Hiển thị top 15 lỗi phổ biến nhất
        for i, (error_type, count) in enumerate(sorted_errors[:15], 1):
            embed.add_field(
                name=f"{i}. {error_type}",
                value=f"Số lần: {count}",
                inline=True
            )

        # Thêm tổng số lỗi
        total_errors = sum(self.error_counts.values())
        embed.set_footer(text=f"Tổng số lỗi: {total_errors}")

        await ctx.send(embed=embed)

    @commands.command(name="clear_errors")
    @commands.is_owner()
    async def clear_errors(self, ctx):
        """Xóa thống kê lỗi (chỉ dành cho chủ bot)"""
        self.error_counts = {}
        self.save_error_stats()
        await ctx.send("✅ Đã xóa thống kê lỗi.")


async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))