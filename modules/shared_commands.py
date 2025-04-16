# modules/shared_commands.py
import discord
from discord.ext import commands
from datetime import datetime, timedelta
import random
from typing import Dict, Any, Optional


# Hàm xử lý lệnh daily chung
async def handle_daily_command(ctx, db):
    """Xử lý lệnh điểm danh hàng ngày"""
    try:
        # Lấy thông tin người chơi
        player = await db.get_player(ctx.author.id)
        if not player:
            await ctx.send(
                f"{ctx.author.mention}, bạn chưa gia nhập môn phái! Hãy sử dụng lệnh `!tongmon` để chọn môn phái.")
            return

        # Lấy thời gian điểm danh cuối cùng
        last_daily = player.get('last_daily')
        now = datetime.now()

        # Chuyển đổi từ string sang datetime nếu cần
        if isinstance(last_daily, str):
            try:
                last_daily = datetime.strptime(last_daily, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                last_daily = None

        # Kiểm tra xem đã điểm danh hôm nay chưa
        if last_daily and (now - last_daily).total_seconds() < 86400:  # 24 giờ = 86400 giây
            # Tính thời gian còn lại
            next_daily = last_daily + timedelta(days=1)
            time_left = next_daily - now
            hours, remainder = divmod(time_left.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            await ctx.send(
                f"⏳ **{ctx.author.display_name}**, bạn đã điểm danh rồi! "
                f"Hãy quay lại sau {hours} giờ {minutes} phút {seconds} giây."
            )
            return

        # Tính toán phần thưởng
        base_exp = 100  # EXP cơ bản
        streak = player.get('daily_streak', 0)

        # Kiểm tra xem có bị reset streak không
        if last_daily and (now - last_daily).total_seconds() > 172800:  # 48 giờ = 172800 giây
            streak = 0

        # Tăng streak
        streak += 1

        # Tính bonus từ streak
        streak_bonus = min(1.0, streak * 0.1)  # 10% mỗi ngày, tối đa 100%
        bonus_exp = int(base_exp * streak_bonus)
        total_exp = base_exp + bonus_exp

        # Cập nhật thông tin người chơi
        new_exp = player.get('exp', 0) + total_exp
        await db.update_player(
            ctx.author.id,
            exp=new_exp,
            last_daily=now,
            daily_streak=streak
        )

        # Tạo embed thông báo
        embed = discord.Embed(
            title="🌟 Điểm Danh Thành Công!",
            description=f"{ctx.author.mention} đã điểm danh thành công!",
            color=0x2ecc71,
            timestamp=now
        )

        embed.add_field(
            name="📊 Phần Thưởng",
            value=(
                f"🔹 EXP Cơ Bản: +{base_exp}\n"
                f"🔹 Bonus Streak ({streak} ngày): +{bonus_exp}\n"
                f"🔹 Tổng Cộng: +{total_exp} EXP"
            ),
            inline=False
        )

        # Thêm thông tin về streak
        embed.add_field(
            name="🔥 Streak Hiện Tại",
            value=f"{streak} ngày liên tiếp",
            inline=True
        )

        # Thêm thông tin về phần thưởng đặc biệt nếu đạt mốc 7 ngày
        if streak % 7 == 0:
            special_reward = "🎁 Phần thưởng đặc biệt: +1 Linh Thạch"
            embed.add_field(
                name="🎁 Phần Thưởng Đặc Biệt",
                value=special_reward,
                inline=True
            )

            # Thêm vật phẩm vào inventory (nếu có module inventory)
            try:
                inventory_cog = ctx.bot.get_cog('Inventory')
                if inventory_cog:
                    await inventory_cog.add_item_to_player(
                        ctx.author.id,
                        "Linh Thạch",
                        "Tài Nguyên",
                        "Phổ Thông",
                        1
                    )
            except Exception as e:
                print(f"Lỗi khi thêm vật phẩm: {e}")

        # Thêm gợi ý
        embed.add_field(
            name="💡 Gợi Ý",
            value=(
                "• Điểm danh mỗi ngày để nhận thưởng\n"
                "• Streak tăng 10% exp mỗi ngày (tối đa 100%)\n"
                "• Bỏ lỡ 2 ngày sẽ reset streak\n"
                "• Mỗi 7 ngày nhận phần thưởng đặc biệt"
            ),
            inline=False
        )

        # Thêm avatar người chơi
        if ctx.author.avatar:
            embed.set_thumbnail(url=ctx.author.avatar.url)

        # Thêm footer
        embed.set_footer(text="Tu Tiên Bot • Điểm danh hàng ngày")

        await ctx.send(embed=embed)

        # Kiểm tra thăng cấp
        cultivation_cog = ctx.bot.get_cog('Cultivation')
        if cultivation_cog:
            await cultivation_cog.check_level_up(ctx, player.get('level', 'Phàm Nhân'), new_exp)

    except Exception as e:
        print(f"Lỗi khi xử lý lệnh daily: {e}")
        await ctx.send("❌ Có lỗi xảy ra khi điểm danh! Xin hãy thử lại sau.")
