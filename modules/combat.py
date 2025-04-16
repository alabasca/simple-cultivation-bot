import discord
from discord.ext import commands
from datetime import datetime, timedelta
import random
import asyncio
from typing import Dict, Any, Optional, Tuple, List, Union
from modules.utils import format_time
from config import (
    COMBAT_COOLDOWN, SECTS, EXP_STEAL_PERCENT, DAMAGE_VARIATION,
    SECT_EMOJIS, SECT_COLORS, MAX_EXP_STEAL
)


class Combat(commands.Cog):
    """Hệ thống chiến đấu PvP giữa các tu sĩ"""

    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.combat_locks = {}  # Khóa để tránh race condition
        self.active_duels = {}  # Lưu trữ các lời mời đấu tự do đang chờ

        # Giá trị mặc định
        self.default_exp_steal = 0.1  # 10%
        self.default_damage_variation = 0.2  # ±20%
        self.default_max_exp_steal = 500  # Giới hạn exp cướp được

        # Danh sách các thông báo chiến đấu
        self.attack_messages = [
            "{attacker} thi triển {skill}, gây {damage} sát thương cho {defender}!",
            "{attacker} vận công phóng ra một đạo kiếm khí, gây {damage} sát thương cho {defender}!",
            "{attacker} tung một chiêu {skill}, đánh trúng {defender}, gây {damage} sát thương!",
            "{attacker} bất ngờ tấn công, {defender} không kịp phòng bị, nhận {damage} sát thương!",
            "{attacker} vận dụng {skill}, gây {damage} sát thương cho {defender}!"
        ]

        self.critical_messages = [
            "⚡ {attacker} thi triển tuyệt kỹ {skill}, đánh trúng điểm yếu của {defender}, gây {damage} sát thương chí mạng!",
            "💯 Một đòn trí mạng! {attacker} gây ra {damage} sát thương kinh hoàng cho {defender}!",
            "🌟 {attacker} tìm ra điểm yếu của {defender}, tung đòn quyết định, gây {damage} sát thương chí mạng!",
            "⭐ Tuyệt chiêu! {attacker} gây ra {damage} sát thương chí mạng với {skill}!",
            "🔴 Đòn đánh trí mạng! {attacker} khiến {defender} trọng thương với {damage} sát thương!"
        ]

        self.dodge_messages = [
            "🌀 {defender} thi triển thân pháp, né tránh đòn tấn công của {attacker}!",
            "💨 {defender} lướt nhanh như gió, tránh được đòn tấn công!",
            "✨ {defender} thi triển tuyệt kỹ, khiến {attacker} đánh trượt!",
            "🌪️ {defender} xoay người trong không trung, tránh được đòn tấn công của {attacker}!",
            "🏃 {defender} di chuyển nhanh như chớp, khiến {attacker} không thể chạm tới!"
        ]

        self.victory_messages = [
            "🏆 {winner} đã chiến thắng {loser} và cướp được {exp} exp!",
            "👑 {winner} đã đánh bại {loser}! Thu hoạch {exp} exp!",
            "🌟 Thắng lợi! {winner} đã hạ gục {loser}, nhận {exp} exp!",
            "🔥 {winner} đã chiến thắng {loser}! Phần thưởng: {exp} exp!",
            "💪 {winner} đã chứng minh sức mạnh vượt trội so với {loser}, cướp được {exp} exp!"
        ]

    async def get_lock(self, user_id: int) -> asyncio.Lock:
        """Lấy hoặc tạo lock cho người chơi"""
        if user_id not in self.combat_locks:
            self.combat_locks[user_id] = asyncio.Lock()
        return self.combat_locks[user_id]

    @commands.command(name="combat", aliases=["pk", "pvp", "đấu"], usage="@người_chơi")
    @commands.guild_only()
    @commands.cooldown(1, COMBAT_COOLDOWN, commands.BucketType.user)
    async def combat(self, ctx, target: discord.Member = None):
        """PvP với người chơi khác để cướp exp"""
        if not target:
            await ctx.send("Sử dụng: !combat @người_chơi")
            return

        # Kiểm tra self-combat
        if target.id == ctx.author.id:
            await ctx.send("Không thể tự đánh chính mình!")
            return

        # Kiểm tra đánh bot
        if target.bot:
            await ctx.send("Không thể đánh bot! Chọn một người chơi thật.")
            return

        # Lấy khóa của người tấn công
        async with await self.get_lock(ctx.author.id):
            try:
                # Hiển thị thông báo đang tải
                loading_msg = await ctx.send("⏳ Đang kiểm tra điều kiện chiến đấu...")

                # Lấy thông tin người chơi
                attacker = await self.db.get_player(ctx.author.id)
                defender = await self.db.get_player(target.id)

                if not attacker:
                    await loading_msg.delete()
                    await ctx.send(
                        f"{ctx.author.mention}, bạn chưa bắt đầu tu luyện! Hãy sử dụng lệnh `!tongmon` để chọn môn phái.")
                    return

                if not defender:
                    await loading_msg.delete()
                    await ctx.send(f"{target.mention} chưa bắt đầu tu luyện!")
                    return

                # Kiểm tra cooldown
                now = datetime.now()
                last_combat = attacker.get('last_combat', datetime.min)
                if isinstance(last_combat, str):
                    try:
                        last_combat = datetime.strptime(last_combat, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        last_combat = datetime.min

                cooldown_time = timedelta(seconds=COMBAT_COOLDOWN)
                if now - last_combat < cooldown_time:
                    remaining = cooldown_time - (now - last_combat)
                    await loading_msg.delete()
                    await ctx.send(
                        f"⏳ **{ctx.author.display_name}**, còn {format_time(remaining.seconds)} nữa mới có thể chiến đấu!")
                    ctx.command.reset_cooldown(ctx)
                    return

                # Kiểm tra HP (nếu có hệ thống HP)
                if attacker.get('hp', 100) <= 0:
                    await loading_msg.delete()
                    await ctx.send(
                        f"{ctx.author.mention}, bạn đang bị thương nặng, không thể chiến đấu! Hãy hồi phục trước.")
                    ctx.command.reset_cooldown(ctx)
                    return

                if defender.get('hp', 100) <= 0:
                    await loading_msg.delete()
                    await ctx.send(f"{target.mention} đang bị thương nặng, không thể chiến đấu!")
                    ctx.command.reset_cooldown(ctx)
                    return

                # Kiểm tra chênh lệch cảnh giới
                attacker_level_index = self.get_level_index(attacker.get('level', 'Phàm Nhân'))
                defender_level_index = self.get_level_index(defender.get('level', 'Phàm Nhân'))

                level_diff = abs(attacker_level_index - defender_level_index)
                if level_diff > 5:  # Chênh lệch quá 5 cảnh giới
                    await loading_msg.delete()
                    if attacker_level_index > defender_level_index:
                        await ctx.send(
                            f"❌ Cảnh giới của bạn quá cao so với {target.display_name}. Không thể khiêu chiến!")
                    else:
                        await ctx.send(
                            f"❌ Cảnh giới của bạn quá thấp so với {target.display_name}. Không thể khiêu chiến!")
                    ctx.command.reset_cooldown(ctx)
                    return

                # Xóa thông báo đang tải
                await loading_msg.delete()

                # Thông báo bắt đầu chiến đấu
                battle_msg = await ctx.send(
                    f"⚔️ **{ctx.author.display_name}** đang khiêu chiến **{target.display_name}**!\n"
                    f"Trận đấu sẽ bắt đầu sau 3 giây..."
                )

                # Hiệu ứng đếm ngược
                for i in range(3, 0, -1):
                    await asyncio.sleep(1)
                    await battle_msg.edit(
                        content=f"⚔️ **{ctx.author.display_name}** đang khiêu chiến **{target.display_name}**!\n"
                                f"Trận đấu sẽ bắt đầu sau {i} giây...")

                # Bắt đầu xử lý combat
                await battle_msg.edit(
                    content=f"⚔️ **{ctx.author.display_name}** đang chiến đấu với **{target.display_name}**!")

                # Tạo trận đấu turn-based
                winner, loser, exp_gained, combat_log = await self.process_combat(ctx.author, target, attacker,
                                                                                  defender)

                # Tạo embed kết quả
                embed = await self.create_combat_result_embed(
                    ctx.author, target, attacker, defender,
                    winner, loser, exp_gained, combat_log
                )

                await ctx.send(embed=embed)

                # Cập nhật thời gian cooldown
                await self.db.update_player(
                    ctx.author.id,
                    last_combat=now
                )

                # Log lại trận đấu
                await self.log_combat(ctx.author.id, target.id, winner.id == ctx.author.id, exp_gained)

                # Kiểm tra thăng cấp
                if winner.id == ctx.author.id and exp_gained > 0:
                    cultivation_cog = self.bot.get_cog('Cultivation')
                    if cultivation_cog:
                        await cultivation_cog.check_level_up(ctx, attacker['level'], attacker['exp'] + exp_gained)

            except Exception as e:
                print(f"Lỗi trong combat: {e}")
                await ctx.send("Có lỗi xảy ra trong quá trình chiến đấu!")
                ctx.command.reset_cooldown(ctx)

    @commands.command(name="tudo", aliases=["friendly", "duel", "thachdau"], usage="@người_chơi")
    @commands.guild_only()
    async def friendly_duel(self, ctx, target: discord.Member = None):
        """Thách đấu tự do với người chơi khác (không cướp exp)"""
        if not target:
            await ctx.send("Sử dụng: !tudo @người_chơi")
            return

        # Kiểm tra self-duel
        if target.id == ctx.author.id:
            await ctx.send("Không thể tự thách đấu chính mình!")
            return

        # Kiểm tra đánh bot
        if target.bot:
            await ctx.send("Không thể thách đấu bot! Chọn một người chơi thật.")
            return

        # Kiểm tra xem đã có lời mời thách đấu chưa
        duel_key = f"{ctx.author.id}_{target.id}"
        if duel_key in self.active_duels:
            await ctx.send(f"Bạn đã gửi lời thách đấu cho {target.display_name} rồi! Vui lòng đợi phản hồi.")
            return

        # Lấy thông tin người chơi
        attacker = await self.db.get_player(ctx.author.id)
        defender = await self.db.get_player(target.id)

        if not attacker:
            await ctx.send(
                f"{ctx.author.mention}, bạn chưa bắt đầu tu luyện! Hãy sử dụng lệnh `!tongmon` để chọn môn phái.")
            return

        if not defender:
            await ctx.send(f"{target.mention} chưa bắt đầu tu luyện!")
            return

        # Kiểm tra HP (nếu có hệ thống HP)
        if attacker.get('hp', 100) <= 0:
            await ctx.send(
                f"{ctx.author.mention}, bạn đang bị thương nặng, không thể chiến đấu! Hãy hồi phục trước.")
            return

        if defender.get('hp', 100) <= 0:
            await ctx.send(f"{target.mention} đang bị thương nặng, không thể chiến đấu!")
            return

        # Tạo embed lời mời thách đấu
        embed = discord.Embed(
            title="🤺 Lời Thách Đấu",
            description=f"{ctx.author.mention} đã thách đấu {target.mention} một trận đấu tự do!",
            color=0x3498db
        )

        embed.add_field(
            name="📝 Thông Tin",
            value=(
                "• Đây là trận đấu tự do, không ảnh hưởng đến EXP\n"
                "• Không có cooldown sau khi đấu\n"
                "• Kết quả chỉ mang tính chất giao lưu"
            ),
            inline=False
        )

        # Tạo view với các nút chấp nhận/từ chối
        class DuelView(discord.ui.View):
            def __init__(self, cog):
                super().__init__(timeout=60)  # Timeout sau 60 giây
                self.cog = cog
                self.value = None

            @discord.ui.button(label="Chấp Nhận", style=discord.ButtonStyle.green)
            async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != target.id:
                    await interaction.response.send_message("Bạn không phải người được thách đấu!", ephemeral=True)
                    return

                await interaction.response.defer()
                self.value = True
                self.stop()

            @discord.ui.button(label="Từ Chối", style=discord.ButtonStyle.red)
            async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != target.id:
                    await interaction.response.send_message("Bạn không phải người được thách đấu!", ephemeral=True)
                    return

                await interaction.response.defer()
                self.value = False
                self.stop()

        # Gửi lời mời và đợi phản hồi
        view = DuelView(self)
        message = await ctx.send(embed=embed, view=view)

        # Lưu lời mời vào active_duels
        self.active_duels[duel_key] = {
            "message_id": message.id,
            "channel_id": ctx.channel.id,
            "timestamp": datetime.now()
        }

        # Đợi phản hồi
        await view.wait()

        # Xóa lời mời khỏi active_duels
        if duel_key in self.active_duels:
            del self.active_duels[duel_key]

        # Xử lý kết quả
        if view.value is None:
            await message.edit(content="⏱️ Lời thách đấu đã hết hạn!", embed=None, view=None)
            return
        elif view.value is False:
            await message.edit(content=f"❌ {target.display_name} đã từ chối lời thách đấu!", embed=None, view=None)
            return

        # Bắt đầu trận đấu tự do
        await message.edit(content=f"⚔️ {target.display_name} đã chấp nhận lời thách đấu!", embed=None, view=None)

        # Thông báo bắt đầu chiến đấu
        battle_msg = await ctx.send(
            f"⚔️ **{ctx.author.display_name}** đang chiến đấu với **{target.display_name}**!\n"
            f"Trận đấu sẽ bắt đầu sau 3 giây..."
        )

        # Hiệu ứng đếm ngược
        for i in range(3, 0, -1):
            await asyncio.sleep(1)
            await battle_msg.edit(
                content=f"⚔️ **{ctx.author.display_name}** đang chiến đấu với **{target.display_name}**!\n"
                        f"Trận đấu sẽ bắt đầu sau {i} giây...")

        # Bắt đầu xử lý combat
        await battle_msg.edit(
            content=f"⚔️ **{ctx.author.display_name}** đang chiến đấu với **{target.display_name}**!")

        # Tạo trận đấu turn-based (không cướp exp)
        winner, loser, _, combat_log = await self.process_friendly_combat(ctx.author, target, attacker, defender)

        # Tạo embed kết quả
        embed = await self.create_friendly_combat_result_embed(
            ctx.author, target, attacker, defender,
            winner, loser, combat_log
        )

        await ctx.send(embed=embed)

        # Log lại trận đấu tự do
        await self.log_combat(ctx.author.id, target.id, winner.id == ctx.author.id, 0, friendly=True)

    async def process_combat(
            self,
            attacker_user: discord.Member,
            defender_user: discord.Member,
            attacker_data: Dict[str, Any],
            defender_data: Dict[str, Any]
    ) -> Tuple[discord.Member, discord.Member, int, List[str]]:
        """Xử lý quá trình chiến đấu và trả về kết quả"""
        # Khởi tạo thông số chiến đấu
        attacker_hp = attacker_data.get('hp', 100)
        defender_hp = defender_data.get('hp', 100)

        # Tính toán sức mạnh có áp dụng bonus từ môn phái
        attacker_atk, attacker_def = self.calculate_combat_stats(attacker_data)
        defender_atk, defender_def = self.calculate_combat_stats(defender_data)

        # Lấy giá trị từ config hoặc mặc định
        exp_steal_percent = EXP_STEAL_PERCENT if 'EXP_STEAL_PERCENT' in globals() else self.default_exp_steal
        damage_variation = DAMAGE_VARIATION if 'DAMAGE_VARIATION' in globals() else self.default_damage_variation
        max_exp_steal = MAX_EXP_STEAL if 'MAX_EXP_STEAL' in globals() else self.default_max_exp_steal

        # Ghi lại log chiến đấu
        combat_log = []

        # Lấy kỹ năng của người chơi dựa trên cảnh giới
        attacker_skills = self.get_skills_by_level(attacker_data.get('level', 'Phàm Nhân'))
        defender_skills = self.get_skills_by_level(defender_data.get('level', 'Phàm Nhân'))

        # Vòng lặp chiến đấu
        turn = 0
        max_turns = 10  # Giới hạn số turn để tránh vòng lặp vô hạn

        while attacker_hp > 0 and defender_hp > 0 and turn < max_turns:
            turn += 1

            # Người tấn công đánh trước
            # Kiểm tra né tránh
            if random.random() < 0.1:  # 10% cơ hội né tránh
                dodge_msg = random.choice(self.dodge_messages)
                combat_log.append(dodge_msg.format(
                    attacker=attacker_user.display_name,
                    defender=defender_user.display_name
                ))
            else:
                # Kiểm tra đòn chí mạng
                is_crit = random.random() < 0.15  # 15% cơ hội chí mạng

                # Chọn kỹ năng ngẫu nhiên
                skill = random.choice(attacker_skills)

                # Tính sát thương
                damage_multiplier = 1.5 if is_crit else 1.0 + random.uniform(-damage_variation, damage_variation)
                damage = int(self.calculate_damage(attacker_atk, defender_def) * damage_multiplier)
                defender_hp -= damage

                # Thêm log chiến đấu
                if is_crit:
                    msg = random.choice(self.critical_messages)
                else:
                    msg = random.choice(self.attack_messages)

                combat_log.append(msg.format(
                    attacker=attacker_user.display_name,
                    defender=defender_user.display_name,
                    damage=damage,
                    skill=skill
                ))

            # Kiểm tra HP
            if defender_hp <= 0:
                # Tính exp cướp được
                exp_gained = int(defender_data['exp'] * exp_steal_percent)
                exp_gained = min(exp_gained, max_exp_steal)  # Giới hạn exp cướp được

                # Thông báo chiến thắng
                victory_msg = random.choice(self.victory_messages)
                combat_log.append(victory_msg.format(
                    winner=attacker_user.display_name,
                    loser=defender_user.display_name,
                    exp=exp_gained
                ))

                # Cập nhật exp cho người thắng và người thua
                await self.db.update_player(
                    attacker_user.id,
                    exp=attacker_data['exp'] + exp_gained,
                    stats__pvp_wins=(attacker_data.get('stats', {}).get('pvp_wins', 0) + 1)
                )

                await self.db.update_player(
                    defender_user.id,
                    exp=max(0, defender_data['exp'] - exp_gained),
                    stats__pvp_losses=(defender_data.get('stats', {}).get('pvp_losses', 0) + 1)
                )

                return attacker_user, defender_user, exp_gained, combat_log

            # Người phòng thủ đánh lại
            # Kiểm tra né tránh
            if random.random() < 0.1:  # 10% cơ hội né tránh
                dodge_msg = random.choice(self.dodge_messages)
                combat_log.append(dodge_msg.format(
                    attacker=defender_user.display_name,
                    defender=attacker_user.display_name
                ))
            else:
                # Kiểm tra đòn chí mạng
                is_crit = random.random() < 0.15  # 15% cơ hội chí mạng

                # Chọn kỹ năng ngẫu nhiên
                skill = random.choice(defender_skills)

                # Tính sát thương
                damage_multiplier = 1.5 if is_crit else 1.0 + random.uniform(-damage_variation, damage_variation)
                damage = int(self.calculate_damage(defender_atk, attacker_def) * damage_multiplier)
                attacker_hp -= damage

                # Thêm log chiến đấu
                if is_crit:
                    msg = random.choice(self.critical_messages)
                else:
                    msg = random.choice(self.attack_messages)

                combat_log.append(msg.format(
                    attacker=defender_user.display_name,
                    defender=attacker_user.display_name,
                    damage=damage,
                    skill=skill
                ))

            # Kiểm tra HP
            if attacker_hp <= 0:
                # Người phòng thủ thắng - không cướp exp
                combat_log.append(f"🛡️ {defender_user.display_name} đã thành công phòng thủ!")

                # Cập nhật thống kê
                await self.db.update_player(
                    attacker_user.id,
                    stats__pvp_losses=(attacker_data.get('stats', {}).get('pvp_losses', 0) + 1)
                )

                await self.db.update_player(
                    defender_user.id,
                    stats__pvp_wins=(defender_data.get('stats', {}).get('pvp_wins', 0) + 1)
                )

                return defender_user, attacker_user, 0, combat_log

        # Nếu đạt max turn mà chưa có kết quả, người có HP cao hơn thắng
        if attacker_hp > defender_hp:
            exp_gained = int(defender_data[
                                 'exp'] * exp_steal_percent * 0.5)  # Chỉ cướp 50% bình thường vì không chiến thắng hoàn toàn
            exp_gained = min(exp_gained, max_exp_steal)  # Giới hạn exp cướp được
            combat_log.append(f"🏆 {attacker_user.display_name} thắng với HP cao hơn!")

            await self.db.update_player(
                attacker_user.id,
                exp=attacker_data['exp'] + exp_gained,
                stats__pvp_wins=(attacker_data.get('stats', {}).get('pvp_wins', 0) + 1)
            )

            await self.db.update_player(
                defender_user.id,
                exp=max(0, defender_data['exp'] - exp_gained),
                stats__pvp_losses=(defender_data.get('stats', {}).get('pvp_losses', 0) + 1)
            )

            return attacker_user, defender_user, exp_gained, combat_log
        else:
            combat_log.append(f"🛡️ {defender_user.display_name} thắng với HP cao hơn!")

            await self.db.update_player(
                attacker_user.id,
                stats__pvp_losses=(attacker_data.get('stats', {}).get('pvp_losses', 0) + 1)
            )

            await self.db.update_player(
                defender_user.id,
                stats__pvp_wins=(defender_data.get('stats', {}).get('pvp_wins', 0) + 1)
            )

            return defender_user, attacker_user, 0, combat_log

    async def process_friendly_combat(
            self,
            attacker_user: discord.Member,
            defender_user: discord.Member,
            attacker_data: Dict[str, Any],
            defender_data: Dict[str, Any]
    ) -> Tuple[discord.Member, discord.Member, int, List[str]]:
        """Xử lý quá trình chiến đấu tự do (không cướp exp)"""
        # Khởi tạo thông số chiến đấu
        attacker_hp = attacker_data.get('hp', 100)
        defender_hp = defender_data.get('hp', 100)

        # Tính toán sức mạnh có áp dụng bonus từ môn phái
        attacker_atk, attacker_def = self.calculate_combat_stats(attacker_data)
        defender_atk, defender_def = self.calculate_combat_stats(defender_data)

        # Lấy giá trị từ config hoặc mặc định
        damage_variation = DAMAGE_VARIATION if 'DAMAGE_VARIATION' in globals() else self.default_damage_variation

        # Ghi lại log chiến đấu
        combat_log = []

        # Lấy kỹ năng của người chơi dựa trên cảnh giới
        attacker_skills = self.get_skills_by_level(attacker_data.get('level', 'Phàm Nhân'))
        defender_skills = self.get_skills_by_level(defender_data.get('level', 'Phàm Nhân'))

        # Vòng lặp chiến đấu
        turn = 0
        max_turns = 15  # Tăng số turn cho trận đấu tự do

        while attacker_hp > 0 and defender_hp > 0 and turn < max_turns:
            turn += 1

            # Người tấn công đánh trước
            # Kiểm tra né tránh
            if random.random() < 0.1:  # 10% cơ hội né tránh
                dodge_msg = random.choice(self.dodge_messages)
                combat_log.append(dodge_msg.format(
                    attacker=attacker_user.display_name,
                    defender=defender_user.display_name
                ))
            else:
                # Kiểm tra đòn chí mạng
                is_crit = random.random() < 0.15  # 15% cơ hội chí mạng

                # Chọn kỹ năng ngẫu nhiên
                skill = random.choice(attacker_skills)

                # Tính sát thương
                damage_multiplier = 1.5 if is_crit else 1.0 + random.uniform(-damage_variation, damage_variation)
                damage = int(self.calculate_damage(attacker_atk, defender_def) * damage_multiplier)
                defender_hp -= damage

                # Thêm log chiến đấu
                if is_crit:
                    msg = random.choice(self.critical_messages)
                else:
                    msg = random.choice(self.attack_messages)

                combat_log.append(msg.format(
                    attacker=attacker_user.display_name,
                    defender=defender_user.display_name,
                    damage=damage,
                    skill=skill
                ))

            # Kiểm tra HP
            if defender_hp <= 0:
                combat_log.append(f"🏆 {attacker_user.display_name} đã chiến thắng trong trận đấu tự do!")

                # Không cập nhật exp, chỉ cập nhật thống kê
                await self.db.update_player(
                    attacker_user.id,
                    stats__friendly_wins=(attacker_data.get('stats', {}).get('friendly_wins', 0) + 1)
                )

                await self.db.update_player(
                    defender_user.id,
                    stats__friendly_losses=(defender_data.get('stats', {}).get('friendly_losses', 0) + 1)
                )

                return attacker_user, defender_user, 0, combat_log

            # Người phòng thủ đánh lại
            # Kiểm tra né tránh
            if random.random() < 0.1:  # 10% cơ hội né tránh
                dodge_msg = random.choice(self.dodge_messages)
                combat_log.append(dodge_msg.format(
                    attacker=defender_user.display_name,
                    defender=attacker_user.display_name
                ))
            else:
                # Kiểm tra đòn chí mạng
                is_crit = random.random() < 0.15  # 15% cơ hội chí mạng

                # Chọn kỹ năng ngẫu nhiên
                skill = random.choice(defender_skills)

                # Tính sát thương
                damage_multiplier = 1.5 if is_crit else 1.0 + random.uniform(-damage_variation, damage_variation)
                damage = int(self.calculate_damage(defender_atk, attacker_def) * damage_multiplier)
                attacker_hp -= damage

                # Thêm log chiến đấu
                if is_crit:
                    msg = random.choice(self.critical_messages)
                else:
                    msg = random.choice(self.attack_messages)

                combat_log.append(msg.format(
                    attacker=defender_user.display_name,
                    defender=attacker_user.display_name,
                    damage=damage,
                    skill=skill
                ))

            # Kiểm tra HP
            if attacker_hp <= 0:
                combat_log.append(f"🏆 {defender_user.display_name} đã chiến thắng trong trận đấu tự do!")

                # Không cập nhật exp, chỉ cập nhật thống kê
                await self.db.update_player(
                    attacker_user.id,
                    stats__friendly_losses=(attacker_data.get('stats', {}).get('friendly_losses', 0) + 1)
                )

                await self.db.update_player(
                    defender_user.id,
                    stats__friendly_wins=(defender_data.get('stats', {}).get('friendly_wins', 0) + 1)
                )

                return defender_user, attacker_user, 0, combat_log

        # Nếu đạt max turn mà chưa có kết quả, người có HP cao hơn thắng
        if attacker_hp > defender_hp:
            combat_log.append(f"🏆 {attacker_user.display_name} thắng với HP cao hơn trong trận đấu tự do!")

            # Không cập nhật exp, chỉ cập nhật thống kê
            await self.db.update_player(
                attacker_user.id,
                stats__friendly_wins=(attacker_data.get('stats', {}).get('friendly_wins', 0) + 1)
            )

            await self.db.update_player(
                defender_user.id,
                stats__friendly_losses=(defender_data.get('stats', {}).get('friendly_losses', 0) + 1)
            )

            return attacker_user, defender_user, 0, combat_log
        else:
            combat_log.append(f"🏆 {defender_user.display_name} thắng với HP cao hơn trong trận đấu tự do!")

            # Không cập nhật exp, chỉ cập nhật thống kê
            await self.db.update_player(
                attacker_user.id,
                stats__friendly_losses=(attacker_data.get('stats', {}).get('friendly_losses', 0) + 1)
            )

            await self.db.update_player(
                defender_user.id,
                stats__friendly_wins=(defender_data.get('stats', {}).get('friendly_wins', 0) + 1)
            )

            return defender_user, attacker_user, 0, combat_log

    def calculate_combat_stats(self, player_data: Dict[str, Any]) -> Tuple[int, int]:
        """Tính toán sức công kích và phòng thủ có áp dụng bonus từ môn phái"""
        # Lấy chỉ số cơ bản
        attack = player_data.get('attack', 10)
        defense = player_data.get('defense', 5)

        # Lấy tông môn và áp dụng bonus
        sect = player_data.get('sect')
        if sect and sect in SECTS:
            attack_bonus = SECTS[sect].get('attack_bonus', 1.0)
            defense_bonus = SECTS[sect].get('defense_bonus', 1.0)

            attack = int(attack * attack_bonus)
            defense = int(defense * defense_bonus)

        return attack, defense

    def calculate_damage(self, attack: int, defense: int, variation: float = 0.2) -> int:
        """Tính toán sát thương với yếu tố ngẫu nhiên"""
        # Công thức cơ bản: damage = attack - defense/2
        base_damage = max(1, attack - defense // 2)

        # Thêm yếu tố ngẫu nhiên (mặc định ±20%)
        variation_multiplier = 1.0 + random.uniform(-variation, variation)
        damage = max(1, int(base_damage * variation_multiplier))

        return damage

    def get_skills_by_level(self, level: str) -> List[str]:
        """Lấy danh sách kỹ năng dựa trên cảnh giới"""
        # Kỹ năng cơ bản
        basic_skills = ["Quyền Cước", "Kiếm Pháp Cơ Bản", "Chưởng Pháp"]

        # Kỹ năng theo cảnh giới
        if "Luyện Khí" in level:
            return basic_skills + ["Linh Khí Quyền", "Ngưng Khí Thuật"]
        elif "Trúc Cơ" in level:
            return basic_skills + ["Linh Khí Quyền", "Ngưng Khí Thuật", "Trúc Cơ Kiếm Pháp", "Linh Khí Phá"]
        elif "Nguyên Anh" in level:
            return basic_skills + ["Trúc Cơ Kiếm Pháp", "Linh Khí Phá", "Nguyên Anh Chưởng", "Thiên Địa Hợp Nhất"]
        elif "Kim Đan" in level or self.higher_level(level):
            return ["Linh Khí Phá", "Nguyên Anh Chưởng", "Thiên Địa Hợp Nhất", "Kiếm Khí Trảm", "Đại Đạo Vô Hình",
                    "Tiên Thiên Công"]
        else:
            return basic_skills

    def higher_level(self, level: str) -> bool:
        """Kiểm tra xem cảnh giới có cao hơn Kim Đan không"""
        high_levels = ["Hóa Thần", "Luyện Hư", "Đại Thừa", "Diễn Chủ"]
        return any(high in level for high in high_levels)

    def get_level_index(self, level: str) -> int:
        """Lấy chỉ số của cảnh giới trong danh sách cảnh giới"""
        cultivation_cog = self.bot.get_cog('Cultivation')
        if cultivation_cog and hasattr(cultivation_cog, 'CULTIVATION_RANKS'):
            try:
                return cultivation_cog.CULTIVATION_RANKS.index(level)
            except ValueError:
                return 0

        # Fallback nếu không tìm thấy Cultivation cog
        levels = [
            "Phàm Nhân",
            "Luyện Khí Tầng 1", "Luyện Khí Tầng 2", "Luyện Khí Tầng 3",
            "Luyện Khí Tầng 4", "Luyện Khí Tầng 5", "Luyện Khí Tầng 6",
            "Luyện Khí Tầng 7", "Luyện Khí Tầng 8", "Luyện Khí Tầng 9",
            "Trúc Cơ Sơ Kỳ", "Trúc Cơ Trung Kỳ", "Trúc Cơ Đại Viên Mãn",
            "Nguyên Anh Sơ Kỳ", "Nguyên Anh Trung Kỳ", "Nguyên Anh Đại Viên Mãn",
            "Kim Đan Sơ Kỳ", "Kim Đan Trung Kỳ", "Kim Đan Đại Viên Mãn"
        ]
        try:
            return levels.index(level)
        except ValueError:
            return 0

    async def create_combat_result_embed(
            self,
            attacker_user: discord.Member,
            defender_user: discord.Member,
            attacker_data: Dict[str, Any],
            defender_data: Dict[str, Any],
            winner: discord.Member,
            loser: discord.Member,
            exp_gained: int,
            combat_log: list
    ) -> discord.Embed:
        """Tạo embed hiển thị kết quả trận đấu"""
        # Màu sắc dựa trên kết quả
        if winner.id == attacker_user.id:
            color = 0x3498db  # Xanh dương - người tấn công thắng
        else:
            color = 0xe74c3c  # Đỏ - người phòng thủ thắng

        # Tạo embed kết quả
        embed = discord.Embed(
            title="⚔️ Kết Quả Chiến Đấu Tu Tiên",
            description=f"Trận đấu giữa {attacker_user.mention} và {defender_user.mention} đã kết thúc!",
            color=color,
            timestamp=datetime.now()
        )

        # Thông tin người tấn công
        attacker_atk, attacker_def = self.calculate_combat_stats(attacker_data)
        attacker_sect = attacker_data.get('sect', 'Không có môn phái')
        attacker_emoji = SECT_EMOJIS.get(attacker_sect, "🏯") if 'SECT_EMOJIS' in globals() else "🏯"

        embed.add_field(
            name=f"{attacker_emoji} {attacker_user.display_name}",
            value=(
                f"Cảnh Giới: {attacker_data['level']}\n"
                f"Môn Phái: {attacker_sect}\n"
                f"Công Kích: {attacker_atk} ({attacker_data['attack']} + bonus)\n"
                f"Phòng Thủ: {attacker_def} ({attacker_data['defense']} + bonus)"
            ),
            inline=True
        )

        # Thông tin người phòng thủ
        defender_atk, defender_def = self.calculate_combat_stats(defender_data)
        defender_sect = defender_data.get('sect', 'Không có môn phái')
        defender_emoji = SECT_EMOJIS.get(defender_sect, "🏯") if 'SECT_EMOJIS' in globals() else "🏯"

        embed.add_field(
            name=f"{defender_emoji} {defender_user.display_name}",
            value=(
                f"Cảnh Giới: {defender_data['level']}\n"
                f"Môn Phái: {defender_sect}\n"
                f"Công Kích: {defender_atk} ({defender_data['attack']} + bonus)\n"
                f"Phòng Thủ: {defender_def} ({defender_data['defense']} + bonus)"
            ),
            inline=True
        )

        # Kết quả trận đấu
        winner_symbol = "🏆" if winner.id == attacker_user.id else "🛡️"

        if exp_gained > 0:
            result_text = (
                f"{winner_symbol} **{winner.display_name}** đã chiến thắng!\n"
                f"Cướp được {exp_gained:,} exp ({int(EXP_STEAL_PERCENT * 100)}% exp của đối thủ)"
            )
        else:
            result_text = f"{winner_symbol} **{winner.display_name}** đã chiến thắng!"

        embed.add_field(
            name="📊 Kết Quả",
            value=result_text,
            inline=False
        )

        # Tóm tắt chiến đấu
        if len(combat_log) > 5:
            # Chỉ hiển thị 5 dòng log quan trọng nhất nếu quá dài
            summary_log = "\n".join(combat_log[:2] + ["..."] + combat_log[-2:])
        else:
            summary_log = "\n".join(combat_log)

        embed.add_field(
            name="🗒️ Diễn Biến Chiến Đấu",
            value=f"```\n{summary_log}\n```",
            inline=False
        )

        # Thêm thông tin bổ sung
        embed.set_footer(text=f"Tu Tiên PvP • Cooldown: {format_time(COMBAT_COOLDOWN)}")

        # Thêm ảnh đại diện người thắng
        if winner.avatar:
            embed.set_thumbnail(url=winner.avatar.url)

        return embed

    async def create_friendly_combat_result_embed(
            self,
            attacker_user: discord.Member,
            defender_user: discord.Member,
            attacker_data: Dict[str, Any],
            defender_data: Dict[str, Any],
            winner: discord.Member,
            loser: discord.Member,
            combat_log: list
    ) -> discord.Embed:
        """Tạo embed hiển thị kết quả trận đấu tự do"""
        # Màu sắc dựa trên kết quả
        if winner.id == attacker_user.id:
            color = 0x3498db  # Xanh dương - người tấn công thắng
        else:
            color = 0xe74c3c  # Đỏ - người phòng thủ thắng

        # Tạo embed kết quả
        embed = discord.Embed(
            title="🤺 Kết Quả Đấu Tự Do",
            description=f"Trận đấu tự do giữa {attacker_user.mention} và {defender_user.mention} đã kết thúc!",
            color=color,
            timestamp=datetime.now()
        )

        # Thông tin người tấn công
        attacker_atk, attacker_def = self.calculate_combat_stats(attacker_data)
        attacker_sect = attacker_data.get('sect', 'Không có môn phái')
        attacker_emoji = SECT_EMOJIS.get(attacker_sect, "🏯") if 'SECT_EMOJIS' in globals() else "🏯"

        embed.add_field(
            name=f"{attacker_emoji} {attacker_user.display_name}",
            value=(
                f"Cảnh Giới: {attacker_data['level']}\n"
                f"Môn Phái: {attacker_sect}\n"
                f"Công Kích: {attacker_atk} ({attacker_data['attack']} + bonus)\n"
                f"Phòng Thủ: {attacker_def} ({attacker_data['defense']} + bonus)"
            ),
            inline=True
        )

        # Thông tin người phòng thủ
        defender_atk, defender_def = self.calculate_combat_stats(defender_data)
        defender_sect = defender_data.get('sect', 'Không có môn phái')
        defender_emoji = SECT_EMOJIS.get(defender_sect, "🏯") if 'SECT_EMOJIS' in globals() else "🏯"

        embed.add_field(
            name=f"{defender_emoji} {defender_user.display_name}",
            value=(
                f"Cảnh Giới: {defender_data['level']}\n"
                f"Môn Phái: {defender_sect}\n"
                f"Công Kích: {defender_atk} ({defender_data['attack']} + bonus)\n"
                f"Phòng Thủ: {defender_def} ({defender_data['defense']} + bonus)"
            ),
            inline=True
        )

        # Kết quả trận đấu
        winner_symbol = "🏆" if winner.id == attacker_user.id else "🛡️"
        result_text = f"{winner_symbol} **{winner.display_name}** đã chiến thắng trong trận đấu tự do!"

        embed.add_field(
            name="📊 Kết Quả",
            value=result_text,
            inline=False
        )

        # Tóm tắt chiến đấu
        if len(combat_log) > 5:
            # Chỉ hiển thị 5 dòng log quan trọng nhất nếu quá dài
            summary_log = "\n".join(combat_log[:2] + ["..."] + combat_log[-2:])
        else:
            summary_log = "\n".join(combat_log)

        embed.add_field(
            name="🗒️ Diễn Biến Chiến Đấu",
            value=f"```\n{summary_log}\n```",
            inline=False
        )

        # Thêm thông tin bổ sung
        embed.add_field(
            name="📝 Ghi Chú",
            value="Đây là trận đấu tự do, không ảnh hưởng đến EXP và không có cooldown.",
            inline=False
        )

        embed.set_footer(text="Tu Tiên Đấu Tự Do • Sử dụng !tudo @người_chơi để thách đấu")

        # Thêm ảnh đại diện người thắng
        if winner.avatar:
            embed.set_thumbnail(url=winner.avatar.url)

        return embed

    async def log_combat(self, attacker_id: int, defender_id: int, attacker_won: bool, exp_gained: int,
                         friendly: bool = False):
        """Ghi lại lịch sử trận đấu vào database"""
        try:
            # Tạo dữ liệu trận đấu
            combat_data = {
                "attacker_id": attacker_id,
                "defender_id": defender_id,
                "result": "win" if attacker_won else "lose",
                "exp_gained": exp_gained,
                "friendly": friendly,
                "timestamp": datetime.now()
            }

            # Lưu vào database
            await self.db.add_combat_history(
                attacker_id=attacker_id,
                defender_id=defender_id,
                result="win" if attacker_won else "lose",
                exp_gained=exp_gained,
                friendly=friendly
            )

        except Exception as e:
            print(f"Lỗi khi log trận đấu: {e}")

    @commands.command(name="combatinfo", aliases=["pvpinfo", "chiendau"], usage="")
    async def combat_info(self, ctx):
        """Xem thông tin hệ thống chiến đấu PvP"""
        embed = discord.Embed(
            title="🗡️ Hệ Thống Chiến Đấu Tu Tiên",
            description="Thông tin về hệ thống PvP giữa các tu sĩ",
            color=0x9b59b6
        )

        # Quy tắc cơ bản
        embed.add_field(
            name="📜 Quy Tắc Cơ Bản",
            value=(
                "• Sử dụng lệnh `!combat @người_chơi` để khiêu chiến\n"
                f"• Mỗi lần combat cần chờ {format_time(COMBAT_COOLDOWN)}\n"
                f"• Người thắng sẽ cướp được {int(EXP_STEAL_PERCENT * 100)}% exp của người thua (tối đa {MAX_EXP_STEAL:,} exp)\n"
                "• Công thức sát thương: Công kích - (Phòng thủ/2)\n"
                "• Sát thương có yếu tố ngẫu nhiên ±20%"
            ),
            inline=False
        )

        # Bonus môn phái
        embed.add_field(
            name="🏯 Bonus Môn Phái",
            value=(
                    "Mỗi môn phái có bonus riêng trong chiến đấu:\n" +
                    "\n".join([
                        f"• {name}: Công +{int((info.get('attack_bonus', 1.0) - 1) * 100)}%, " +
                        f"Thủ +{int((info.get('defense_bonus', 1.0) - 1) * 100)}%"
                        for name, info in SECTS.items()
                    ])
            ),
            inline=False
        )

        # Các loại trận đấu
        embed.add_field(
            name="⚔️ Các Loại Trận Đấu",
            value=(
                "• **PvP Thường**: `!combat @người_chơi` - Cướp exp, có cooldown\n"
                "• **Đấu Tự Do**: `!tudo @người_chơi` - Không cướp exp, không có cooldown\n"
                "• **Chênh lệch cảnh giới**: Không thể đánh người chơi chênh lệch quá 5 cảnh giới"
            ),
            inline=False
        )

        # Mẹo chiến đấu
        embed.add_field(
            name="💡 Mẹo Chiến Đấu",
            value=(
                "• Nâng cao cảnh giới để tăng chỉ số cơ bản\n"
                "• Chọn môn phái phù hợp với phong cách chiến đấu\n"
                "• Tu luyện thường xuyên để tăng exp và sức mạnh\n"
                "• Chiến đấu với đối thủ có exp cao để cướp nhiều exp hơn\n"
                "• Có 15% cơ hội gây sát thương chí mạng (x1.5)\n"
                "• Có 10% cơ hội né tránh đòn tấn công"
            ),
            inline=False
        )

        await ctx.send(embed=embed)

    @commands.command(name="pvpstats", aliases=["combatstat", "chiendaustats"], usage="[@người_chơi]")
    async def pvp_stats(self, ctx, member: discord.Member = None):
        """Xem thống kê chiến đấu PvP của bản thân hoặc người khác"""
        target = member or ctx.author

        # Lấy thông tin người chơi
        player = await self.db.get_player(target.id)
        if not player:
            if target == ctx.author:
                await ctx.send(
                    f"{ctx.author.mention}, bạn chưa bắt đầu tu luyện! Hãy sử dụng lệnh `!tongmon` để chọn môn phái.")
            else:
                await ctx.send(f"{target.display_name} chưa bắt đầu tu luyện!")
            return

        # Lấy thống kê chiến đấu
        stats = player.get('stats', {})
        pvp_wins = stats.get('pvp_wins', 0)
        pvp_losses = stats.get('pvp_losses', 0)
        friendly_wins = stats.get('friendly_wins', 0)
        friendly_losses = stats.get('friendly_losses', 0)

        # Tính tỷ lệ thắng
        total_pvp = pvp_wins + pvp_losses
        win_rate = (pvp_wins / total_pvp * 100) if total_pvp > 0 else 0

        total_friendly = friendly_wins + friendly_losses
        friendly_win_rate = (friendly_wins / total_friendly * 100) if total_friendly > 0 else 0

        # Tạo embed
        embed = discord.Embed(
            title=f"⚔️ Thống Kê Chiến Đấu của {target.display_name}",
            description=f"Thông tin chi tiết về thành tích PvP của {target.mention}",
            color=SECT_COLORS.get(player.get('sect', 'Không có'), 0x9b59b6),
            timestamp=datetime.now()
        )

        # Thông tin cơ bản
        embed.add_field(
            name="📊 PvP Thường",
            value=(
                f"🏆 Thắng: {pvp_wins}\n"
                f"💔 Thua: {pvp_losses}\n"
                f"🔄 Tổng số trận: {total_pvp}\n"
                f"📈 Tỷ lệ thắng: {win_rate:.1f}%"
            ),
            inline=True
        )

        embed.add_field(
            name="🤺 Đấu Tự Do",
            value=(
                f"🏆 Thắng: {friendly_wins}\n"
                f"💔 Thua: {friendly_losses}\n"
                f"🔄 Tổng số trận: {total_friendly}\n"
                f"📈 Tỷ lệ thắng: {friendly_win_rate:.1f}%"
            ),
            inline=True
        )

        # Thêm thông tin tổng hợp
        total_wins = pvp_wins + friendly_wins
        total_losses = pvp_losses + friendly_losses
        total_matches = total_pvp + total_friendly
        total_win_rate = (total_wins / total_matches * 100) if total_matches > 0 else 0

        embed.add_field(
            name="📈 Tổng Hợp",
            value=(
                f"🏆 Tổng thắng: {total_wins}\n"
                f"💔 Tổng thua: {total_losses}\n"
                f"🔄 Tổng số trận: {total_matches}\n"
                f"📈 Tỷ lệ thắng tổng: {total_win_rate:.1f}%"
            ),
            inline=False
        )

        # Thêm thông tin về exp đã cướp được
        exp_stolen = stats.get('exp_stolen', 0)
        exp_lost = stats.get('exp_lost', 0)

        if exp_stolen > 0 or exp_lost > 0:
            embed.add_field(
                name="💰 EXP PvP",
                value=(
                    f"📈 EXP đã cướp: {exp_stolen:,}\n"
                    f"📉 EXP đã mất: {exp_lost:,}\n"
                    f"📊 Cân bằng: {(exp_stolen - exp_lost):+,}"
                ),
                inline=False
            )

        # Thêm thông tin về đối thủ thường gặp
        recent_opponents = await self.db.get_recent_opponents(target.id, limit=3)
        if recent_opponents:
            opponents_text = []
            for opponent_id, count in recent_opponents:
                opponent = self.bot.get_user(opponent_id)
                name = opponent.display_name if opponent else f"ID: {opponent_id}"
                opponents_text.append(f"• {name}: {count} trận")

            embed.add_field(
                name="👥 Đối Thủ Thường Gặp",
                value="\n".join(opponents_text) if opponents_text else "Không có dữ liệu",
                inline=False
            )

        # Thêm avatar người chơi
        if target.avatar:
            embed.set_thumbnail(url=target.avatar.url)

        # Thêm footer
        embed.set_footer(text="Tu Tiên PvP • Sử dụng !combat @người_chơi để khiêu chiến")

        await ctx.send(embed=embed)

    @commands.command(name="pvphistory", aliases=["lichsu", "history"], usage="[số_lượng]")
    async def pvp_history(self, ctx, limit: int = 5):
        """Xem lịch sử chiến đấu PvP gần đây"""
        # Giới hạn số lượng trận đấu hiển thị
        limit = min(max(1, limit), 10)  # Giới hạn từ 1-10

        # Lấy lịch sử chiến đấu
        history = await self.db.get_combat_history(ctx.author.id, limit=limit)

        if not history:
            await ctx.send("Bạn chưa có trận đấu nào!")
            return

        # Tạo embed
        embed = discord.Embed(
            title=f"📜 Lịch Sử Chiến Đấu của {ctx.author.display_name}",
            description=f"{len(history)} trận đấu gần đây nhất",
            color=0x3498db,
            timestamp=datetime.now()
        )

        # Thêm thông tin từng trận đấu
        for i, match in enumerate(history, 1):
            # Lấy thông tin người chơi
            opponent_id = match['defender_id'] if match['attacker_id'] == ctx.author.id else match['attacker_id']
            opponent = self.bot.get_user(opponent_id)
            opponent_name = opponent.display_name if opponent else f"ID: {opponent_id}"

            # Xác định kết quả
            is_attacker = match['attacker_id'] == ctx.author.id
            is_win = (is_attacker and match['result'] == 'win') or (not is_attacker and match['result'] == 'lose')

            # Định dạng thời gian
            match_time = match.get('timestamp', datetime.now())
            if isinstance(match_time, str):
                try:
                    match_time = datetime.strptime(match_time, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    match_time = datetime.now()

            time_ago = self.format_time_ago(match_time)

            # Tạo nội dung
            result_emoji = "🏆" if is_win else "💔"
            match_type = "Đấu Tự Do" if match.get('friendly', False) else "PvP"
            exp_text = f" (+{match['exp_gained']:,} EXP)" if match['exp_gained'] > 0 and is_win else ""

            match_text = (
                f"{result_emoji} **{match_type}** vs {opponent_name}\n"
                f"{'Thắng' if is_win else 'Thua'}{exp_text} • {time_ago}"
            )

            embed.add_field(
                name=f"Trận #{i}",
                value=match_text,
                inline=True
            )

        # Thêm footer
        embed.set_footer(text=f"Sử dụng !pvphistory [số_lượng] để xem thêm • Tối đa 10 trận")

        await ctx.send(embed=embed)

    def format_time_ago(self, past_time: datetime) -> str:
        """Định dạng thời gian đã trôi qua (ví dụ: '5 phút trước')"""
        now = datetime.now()
        diff = (now - past_time).total_seconds()

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
            return past_time.strftime("%d/%m/%Y")

    @combat.error
    async def combat_error(self, ctx, error):
        """Xử lý lỗi lệnh combat"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Sử dụng: !combat @người_chơi")
            ctx.command.reset_cooldown(ctx)
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Không tìm thấy người chơi! Hãy đảm bảo bạn đã tag đúng người.")
            ctx.command.reset_cooldown(ctx)
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                f"⏳ **{ctx.author.display_name}**, còn {format_time(int(error.retry_after))} nữa mới có thể chiến đấu!")
        else:
            print(f"Lỗi không xử lý được trong combat: {error}")
            await ctx.send("Có lỗi xảy ra khi thực hiện lệnh combat!")
            ctx.command.reset_cooldown(ctx)

    @friendly_duel.error
    async def friendly_duel_error(self, ctx, error):
        """Xử lý lỗi lệnh tudo"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Sử dụng: !tudo @người_chơi")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Không tìm thấy người chơi! Hãy đảm bảo bạn đã tag đúng người.")
        else:
            print(f"Lỗi không xử lý được trong tudo: {error}")
            await ctx.send("Có lỗi xảy ra khi thực hiện lệnh tudo!")


async def setup(bot):
    await bot.add_cog(Combat(bot, bot.db))