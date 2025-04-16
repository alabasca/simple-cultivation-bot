import discord
from discord.ext import commands
from config import SECTS
import asyncio
import random
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union, Tuple
import math

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

# Thông tin bổ sung về các môn phái
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


class SectSelect(discord.ui.Select):
    """Select menu cho việc chọn môn phái"""

    def __init__(self, cog):
        self.cog = cog

        # Tạo options từ config
        options = [
            discord.SelectOption(
                label=sect_name,
                description=SECTS[sect_name]["description"][:100],
                emoji=SECT_EMOJIS[sect_name],
                value=sect_name
            ) for sect_name in SECTS
        ]

        super().__init__(
            placeholder="Chọn môn phái",
            custom_id="sect_select",
            options=options,
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        """Xử lý khi người dùng chọn tông môn"""
        # Trì hoãn phản hồi để tránh lỗi timeout
        try:
            # Sử dụng defer để tránh lỗi "This interaction failed"
            await interaction.response.defer(ephemeral=True, thinking=True)

            user_id = interaction.user.id
            selected_sect = self.values[0]

            # Lấy hoặc tạo lock cho người chơi
            if user_id not in self.cog.sect_locks:
                self.cog.sect_locks[user_id] = asyncio.Lock()

            async with self.cog.sect_locks[user_id]:
                # Kiểm tra người chơi
                existing_player = await self.cog.db.get_player(user_id)

                if existing_player:
                    # Nếu người chơi đã chọn môn phái này rồi
                    if existing_player.get('sect') == selected_sect:
                        await interaction.followup.send(
                            f"Bạn đã là thành viên của {selected_sect} rồi!",
                            ephemeral=True
                        )
                        return

                    # Kiểm tra thời gian đổi môn phái
                    sect_joined_at = existing_player.get('sect_joined_at')
                    if sect_joined_at:
                        # Chuyển đổi từ string sang datetime nếu cần
                        if isinstance(sect_joined_at, str):
                            try:
                                sect_joined_at = datetime.strptime(sect_joined_at, '%Y-%m-%d %H:%M:%S')
                            except ValueError:
                                sect_joined_at = datetime.now() - timedelta(days=8)  # Mặc định nếu không parse được

                        # Kiểm tra thời gian
                        time_since_join = datetime.now() - sect_joined_at
                        if time_since_join.days < 7:
                            days_left = 7 - time_since_join.days
                            await interaction.followup.send(
                                f"Bạn cần đợi thêm {days_left} ngày nữa mới có thể đổi môn phái!",
                                ephemeral=True
                            )
                            return

                        # Kiểm tra và trừ phí đổi môn phái
                        current_exp = existing_player.get('exp', 0)
                        change_fee = 1000  # Phí đổi môn phái

                        if current_exp < change_fee:
                            await interaction.followup.send(
                                f"Bạn cần có ít nhất {change_fee:,} EXP để đổi môn phái! Hiện tại bạn chỉ có {current_exp:,} EXP.",
                                ephemeral=True
                            )
                            return

                        # Trừ phí
                        new_exp = current_exp - change_fee

                    # Cập nhật môn phái
                    old_sect = existing_player.get('sect')
                    if old_sect:
                        old_role = discord.utils.get(interaction.guild.roles, name=old_sect)
                        if old_role and old_role in interaction.user.roles:
                            try:
                                await interaction.user.remove_roles(old_role)
                            except discord.Forbidden:
                                print(f"Không đủ quyền để xóa role {old_role.name}")

                    # Cập nhật dữ liệu người chơi
                    update_data = {
                        'sect': selected_sect,
                        'sect_joined_at': datetime.now()
                    }

                    # Nếu đổi môn phái, trừ phí
                    if 'new_exp' in locals():
                        update_data['exp'] = new_exp

                    await self.cog.db.update_player(user_id, **update_data)
                    action_msg = "chuyển sang"

                    # Thêm thông tin về phí đổi môn phái nếu có
                    fee_info = f" (Phí: -{change_fee:,} EXP)" if 'new_exp' in locals() else ""
                    action_msg += fee_info

                else:
                    # Tạo người chơi mới
                    try:
                        await self.cog.db.create_player(
                            user_id,
                            selected_sect
                        )
                        action_msg = "gia nhập"
                    except Exception as e:
                        await interaction.followup.send(
                            "Có lỗi xảy ra khi tạo nhân vật. Vui lòng thử lại sau!",
                            ephemeral=True
                        )
                        print(f"Error creating player: {e}")
                        return

                # Cập nhật role Discord
                new_role = discord.utils.get(interaction.guild.roles, name=selected_sect)
                if new_role:
                    try:
                        await interaction.user.add_roles(new_role)
                    except discord.Forbidden:
                        print(f"Không đủ quyền để thêm role {new_role.name}")

                # Tạo embed thông báo
                embed = await self.cog.create_sect_join_embed(
                    interaction.user,
                    selected_sect,
                    action_msg
                )

                # Gửi thông báo riêng cho người dùng
                await interaction.followup.send(embed=embed, ephemeral=True)

                # Gửi thông báo công khai
                await self.cog.send_public_announcement(interaction, selected_sect, action_msg)

        except Exception as e:
            print(f"Error in sect selection callback: {e}")
            # Nếu response chưa được gửi, thử gửi thông báo lỗi
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "Có lỗi xảy ra! Vui lòng thử lại sau.",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        "Có lỗi xảy ra! Vui lòng thử lại sau.",
                        ephemeral=True
                    )
            except Exception as send_error:
                print(f"Could not send error message: {send_error}")


class SectInfoButton(discord.ui.Button):
    """Button để xem thông tin chi tiết về môn phái"""

    def __init__(self, cog, sect_name: str):
        self.cog = cog
        self.sect_name = sect_name
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label=f"Chi tiết {sect_name}",
            emoji=SECT_EMOJIS.get(sect_name, "🏯"),
            custom_id=f"sect_info_{sect_name}"
        )

    async def callback(self, interaction: discord.Interaction):
        """Xử lý khi người dùng nhấn button xem thông tin"""
        try:
            await interaction.response.defer(ephemeral=True, thinking=True)

            # Tạo embed thông tin chi tiết
            embed = await self.cog.create_detailed_sect_info(self.sect_name)

            # Gửi thông tin
            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            print(f"Error in sect info button callback: {e}")
            await interaction.followup.send("Có lỗi xảy ra khi hiển thị thông tin môn phái!", ephemeral=True)


class SectView(discord.ui.View):
    """View cho chọn tông môn qua select menu"""

    def __init__(self, cog):
        super().__init__(timeout=None)  # Persistent view không có timeout
        self.cog = cog

        # Thêm select menu vào view
        self.add_item(SectSelect(cog))

        # Thêm các button thông tin cho từng môn phái
        for sect_name in SECTS:
            self.add_item(SectInfoButton(cog, sect_name))


class SectStatsView(discord.ui.View):
    """View cho hiển thị thống kê môn phái"""

    def __init__(self, cog):
        super().__init__(timeout=300)  # Timeout sau 5 phút
        self.cog = cog
        self.current_page = 0
        self.pages = ["overview", "members", "activities", "rankings"]

    @discord.ui.button(label="Tổng Quan", style=discord.ButtonStyle.primary, custom_id="overview")
    async def overview_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Hiển thị trang tổng quan"""
        self.current_page = 0
        await self.update_page(interaction)

    @discord.ui.button(label="Thành Viên", style=discord.ButtonStyle.secondary, custom_id="members")
    async def members_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Hiển thị trang thành viên"""
        self.current_page = 1
        await self.update_page(interaction)

    @discord.ui.button(label="Hoạt Động", style=discord.ButtonStyle.secondary, custom_id="activities")
    async def activities_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Hiển thị trang hoạt động"""
        self.current_page = 2
        await self.update_page(interaction)

    @discord.ui.button(label="Xếp Hạng", style=discord.ButtonStyle.secondary, custom_id="rankings")
    async def rankings_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Hiển thị trang xếp hạng"""
        self.current_page = 3
        await self.update_page(interaction)

    async def update_page(self, interaction: discord.Interaction):
        """Cập nhật trang hiển thị"""
        try:
            await interaction.response.defer()

            # Lấy embed cho trang hiện tại
            page_type = self.pages[self.current_page]

            # Cập nhật style của các button
            for child in self.children:
                if isinstance(child, discord.ui.Button):
                    if child.custom_id == page_type:
                        child.style = discord.ButtonStyle.primary
                    else:
                        child.style = discord.ButtonStyle.secondary

            # Lấy thông tin môn phái
            sect_name = getattr(self, "sect_name", None)
            if not sect_name:
                await interaction.followup.send("Có lỗi xảy ra: Không tìm thấy thông tin môn phái!", ephemeral=True)
                return

            # Lấy embed tương ứng
            if page_type == "overview":
                embed = await self.cog.create_sect_overview_embed(sect_name)
            elif page_type == "members":
                embed = await self.cog.create_sect_members_embed(sect_name)
            elif page_type == "activities":
                embed = await self.cog.create_sect_activities_embed(sect_name)
            elif page_type == "rankings":
                embed = await self.cog.create_sect_rankings_embed(sect_name)
            else:
                embed = discord.Embed(title="Lỗi", description="Không tìm thấy trang yêu cầu")

            # Cập nhật message
            await interaction.edit_original_response(embed=embed, view=self)

        except Exception as e:
            print(f"Error updating sect stats page: {e}")
            await interaction.followup.send("Có lỗi xảy ra khi cập nhật trang!", ephemeral=True)


class Sect(commands.Cog):
    """Hệ thống môn phái và tông môn"""

    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.setup_lock = asyncio.Lock()
        self.sect_locks = {}  # Lock cho mỗi người chơi
        self.sect_stats_cache = {}  # Cache thống kê môn phái
        self.cache_timeout = 300  # 5 phút

        # Đảm bảo view được đăng ký khi cog được load
        bot.add_view(SectView(self))

    @commands.Cog.listener()
    async def on_ready(self):
        """Thông báo khi module đã sẵn sàng"""
        print("✓ Module Tông Môn đã sẵn sàng!")

        # Khởi tạo task định kỳ cập nhật thống kê môn phái
        self.bot.loop.create_task(self.update_sect_stats_periodically())

    async def update_sect_stats_periodically(self):
        """Cập nhật thống kê môn phái định kỳ"""
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                # Cập nhật thống kê cho tất cả môn phái
                all_players = await self.db.get_all_players()

                for sect_name in SECTS:
                    sect_members = [p for p in all_players if p.get('sect') == sect_name]
                    total_exp = sum(member.get('exp', 0) for member in sect_members)

                    # Tính các chỉ số khác
                    avg_exp = total_exp // len(sect_members) if sect_members else 0
                    highest_level_member = max(sect_members, key=lambda x: x.get('exp', 0)) if sect_members else None
                    highest_exp = highest_level_member.get('exp', 0) if highest_level_member else 0

                    # Lưu vào cache
                    self.sect_stats_cache[sect_name] = {
                        "members_count": len(sect_members),
                        "total_exp": total_exp,
                        "avg_exp": avg_exp,
                        "highest_exp": highest_exp,
                        "updated_at": datetime.now()
                    }

            except Exception as e:
                print(f"Error updating sect stats: {e}")

            # Cập nhật mỗi 5 phút
            await asyncio.sleep(300)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setupsects(self, ctx, channel_name: str = None):
        """Thiết lập hệ thống môn phái"""
        async with self.setup_lock:
            try:
                # Hiển thị thông báo đang thiết lập
                setup_msg = await ctx.send("⏳ Đang thiết lập hệ thống môn phái...")

                # Xác định kênh mục tiêu
                target_channel = None
                if channel_name:
                    target_channel = discord.utils.get(ctx.guild.text_channels, name=channel_name)
                else:
                    # Tìm kênh mặc định hoặc tạo mới
                    target_channel = discord.utils.get(ctx.guild.text_channels, name="🏯┃tông-môn-chi-lộ")
                    if not target_channel:
                        # Tìm category Tu Luyện
                        category = discord.utils.get(ctx.guild.categories, name="Tu Luyện")
                        if not category:
                            try:
                                category = await ctx.guild.create_category(
                                    "Tu Luyện",
                                    reason="Tạo category tu luyện"
                                )
                            except discord.Forbidden:
                                await setup_msg.edit(content="❌ Không đủ quyền để tạo category.")
                                return

                        # Tạo kênh mới
                        try:
                            target_channel = await ctx.guild.create_text_channel(
                                "🏯┃tông-môn-chi-lộ",
                                category=category,
                                reason="Tạo kênh chọn môn phái"
                            )
                        except discord.Forbidden:
                            await setup_msg.edit(content="❌ Không đủ quyền để tạo kênh.")
                            return

                if not target_channel:
                    await setup_msg.edit(content=f"❌ Không tìm thấy kênh '{channel_name}' và không thể tạo kênh mới.")
                    return

                # Cập nhật thông báo
                await setup_msg.edit(content="🔄 Đang tạo roles cho các môn phái...")

                # Tạo roles cho môn phái
                created_roles = []
                for sect_name, color in SECT_COLORS.items():
                    role = discord.utils.get(ctx.guild.roles, name=sect_name)
                    if not role:
                        try:
                            role = await ctx.guild.create_role(
                                name=sect_name,
                                color=discord.Color(color),
                                mentionable=True,
                                reason="Tạo role môn phái"
                            )
                            created_roles.append(role.name)
                        except discord.Forbidden:
                            await setup_msg.edit(content=f"❌ Không đủ quyền để tạo role {sect_name}.")
                            return

                # Cập nhật thông báo
                await setup_msg.edit(content="🔄 Đang thiết lập permissions cho kênh...")

                # Thiết lập permissions cho kênh
                try:
                    await self.setup_channel_permissions(target_channel)
                except discord.Forbidden:
                    await setup_msg.edit(content="❌ Không đủ quyền để thiết lập permissions cho kênh.")
                    return

                # Cập nhật thông báo
                await setup_msg.edit(content="🔄 Đang tạo hướng dẫn chọn môn phái...")

                # Tạo embed hướng dẫn
                embed = await self.create_sect_guide_embed()

                # Xóa tin nhắn cũ và gửi embed mới
                try:
                    await target_channel.purge(limit=10)
                except (discord.Forbidden, discord.HTTPException):
                    print("Không thể xóa tin nhắn cũ")

                try:
                    await target_channel.send(embed=embed, view=SectView(self))

                    # Thông báo kết quả
                    result_embed = discord.Embed(
                        title="✅ Thiết Lập Thành Công",
                        description=f"Đã thiết lập menu chọn môn phái trong {target_channel.mention}",
                        color=0x2ecc71,
                        timestamp=datetime.now()
                    )

                    if created_roles:
                        result_embed.add_field(
                            name="🎭 Roles Đã Tạo",
                            value="\n".join(created_roles),
                            inline=False
                        )

                    # Xóa thông báo đang thiết lập và gửi kết quả
                    await setup_msg.delete()
                    await ctx.send(embed=result_embed)

                except discord.Forbidden:
                    await setup_msg.edit(content="❌ Không đủ quyền để gửi tin nhắn trong kênh đã chọn.")

            except Exception as e:
                print(f"Error in setupsects: {e}")
                await ctx.send(f"❌ Có lỗi xảy ra khi thiết lập: {str(e)}")

    async def setup_channel_permissions(self, channel: discord.TextChannel):
        """Thiết lập permissions cho kênh chọn môn phái"""
        # Permissions cho bot
        await channel.set_permissions(
            self.bot.user,
            read_messages=True,
            send_messages=True,
            manage_messages=True,
            embed_links=True,
            attach_files=True,
            read_message_history=True
        )

        # Permissions mặc định cho tất cả
        await channel.set_permissions(
            channel.guild.default_role,
            read_messages=True,
            send_messages=False,
            read_message_history=True
        )

        # Permissions cho từng role môn phái
        for sect_name in SECTS:
            role = discord.utils.get(channel.guild.roles, name=sect_name)
            if role:
                await channel.set_permissions(
                    role,
                    read_messages=True,
                    send_messages=False,
                    read_message_history=True
                )

    async def create_sect_guide_embed(self) -> discord.Embed:
        """Tạo embed hướng dẫn chọn môn phái"""
        embed = discord.Embed(
            title="🏯 Chọn Môn Phái",
            description=(
                "🔮 Vạn vật tuần hoàn, thiên đạo luân hồi. "
                "Thiếu hiệp, con đường tu tiên của ngươi bắt đầu từ đây!\n\n"
                "📜 Hãy chọn một môn phái để theo đuổi đại đạo:"
            ),
            color=0xf1c40f
        )

        # Thêm thông tin từng môn phái
        for sect_name, info in SECTS.items():
            attack_bonus = info.get('attack_bonus', 1.0)
            defense_bonus = info.get('defense_bonus', 1.0)

            embed.add_field(
                name=f"{SECT_EMOJIS.get(sect_name, '🏯')} {sect_name}",
                value=(
                    f"{info.get('description', 'Không có mô tả')}\n"
                    f"⚔️ Công: {(attack_bonus - 1) * 100:+.0f}% "
                    f"🛡️ Thủ: {(defense_bonus - 1) * 100:+.0f}%"
                ),
                inline=False
            )

        # Thêm thông tin về quy định đổi môn phái
        embed.add_field(
            name="📝 Quy Định Đổi Môn Phái",
            value=(
                "• Phải ở môn phái hiện tại ít nhất 7 ngày\n"
                "• Phí đổi môn phái: 1,000 EXP\n"
                "• Mất tất cả chức vụ và đặc quyền ở môn phái cũ\n"
                "• Phải bắt đầu từ đệ tử ngoại môn ở môn phái mới"
            ),
            inline=False
        )

        embed.set_footer(
            text="Sử dụng menu bên dưới để chọn môn phái • Nhấn vào nút để xem chi tiết từng môn phái"
        )

        # Thêm hình ảnh minh họa
        embed.set_image(url="https://i.imgur.com/3MUxw2G.png")

        return embed

    async def create_sect_join_embed(
            self,
            user: discord.Member,
            sect: str,
            action: str
    ) -> discord.Embed:
        """Tạo embed thông báo gia nhập/chuyển môn phái"""
        embed = discord.Embed(
            title=f"🏯 {action.title()} Môn Phái",
            description=(
                f"Chúc mừng {user.mention} đã {action} {SECT_EMOJIS.get(sect, '🏯')} "
                f"**{sect}**!\n\n*{SECTS.get(sect, {}).get('description', 'Không có mô tả')}*"
            ),
            color=SECT_COLORS.get(sect, 0x7289da),
            timestamp=datetime.now()
        )

        # Thêm thông tin bonus
        sect_info = SECTS.get(sect, {})
        attack_bonus = sect_info.get('attack_bonus', 1.0)
        defense_bonus = sect_info.get('defense_bonus', 1.0)

        bonus_info = []
        if attack_bonus != 1.0:
            bonus = int((attack_bonus - 1) * 100)
            bonus_info.append(f"⚔️ Công Kích: {bonus:+d}%")
        if defense_bonus != 1.0:
            bonus = int((defense_bonus - 1) * 100)
            bonus_info.append(f"🛡️ Phòng Thủ: {bonus:+d}%")

        if bonus_info:
            embed.add_field(
                name="📊 Điểm Mạnh",
                value="\n".join(bonus_info),
                inline=False
            )

        # Thêm thông tin về kỹ năng đặc biệt
        sect_details = SECT_DETAILS.get(sect, {})
        if sect_details.get('famous_skills'):
            embed.add_field(
                name="🔮 Kỹ Năng Nổi Tiếng",
                value="\n".join([f"• {skill}" for skill in sect_details.get('famous_skills', [])[:3]]),
                inline=False
            )

        # Thêm hướng dẫn tiếp theo
        embed.add_field(
            name="📝 Tiếp Theo",
            value=(
                "• Sử dụng `!tuvi` để xem thông tin tu vi\n"
                "• Sử dụng `!daily` để điểm danh nhận thưởng\n"
                "• Chat và tham gia voice để tăng tu vi\n"
                "• Sử dụng `!phai` để xem thông tin chi tiết về môn phái"
            ),
            inline=False
        )

        # Thêm câu châm ngôn của môn phái
        if sect_details.get('motto'):
            embed.add_field(
                name="📜 Châm Ngôn",
                value=f"*\"{sect_details.get('motto')}\"*",
                inline=False
            )

        embed.set_footer(text="Tu Tiên Bot • Chúc may mắn trên con đường tu tiên!")
        return embed

    async def send_public_announcement(
            self,
            interaction: discord.Interaction,
            sect: str,
            action: str
    ):
        """Gửi thông báo công khai khi có người gia nhập/chuyển môn phái"""
        try:
            # Tìm kênh thông báo
            announce_channel = None

            # Thử tìm kênh thông báo theo thứ tự ưu tiên
            channel_names = [
                "chào-mừng", "thông-báo", "welcome", "general", "chung"
            ]

            for name in channel_names:
                channel = discord.utils.get(interaction.guild.text_channels, name=name)
                if channel:
                    announce_channel = channel
                    break

            # Nếu không tìm thấy, dùng system channel
            if not announce_channel and interaction.guild.system_channel:
                announce_channel = interaction.guild.system_channel

            # Nếu tìm thấy kênh thích hợp, gửi thông báo
            if announce_channel:
                # Tạo danh sách các thông báo ngẫu nhiên
                welcome_messages = [
                    f"Chào mừng {interaction.user.mention} {action} {SECT_EMOJIS.get(sect, '🏯')} **{sect}**! Chúc đạo hữu tu luyện tinh tấn!",
                    f"Thiên địa rung chuyển! {interaction.user.mention} vừa {action} {SECT_EMOJIS.get(sect, '🏯')} **{sect}**!",
                    f"Một tu sĩ mới đã xuất hiện! {interaction.user.mention} đã {action} {SECT_EMOJIS.get(sect, '🏯')} **{sect}**!",
                    f"Hãy chào đón {interaction.user.mention}, người vừa {action} {SECT_EMOJIS.get(sect, '🏯')} **{sect}**!"
                ]

                # Chọn một thông báo ngẫu nhiên
                welcome_message = random.choice(welcome_messages)

                embed = discord.Embed(
                    title="👋 Tu Sĩ Mới",
                    description=welcome_message,
                    color=SECT_COLORS.get(sect, 0x7289da),
                    timestamp=datetime.now()
                )

                # Thêm hình ảnh người dùng
                if interaction.user.avatar:
                    embed.set_thumbnail(url=interaction.user.avatar.url)

                await announce_channel.send(embed=embed)
        except Exception as e:
            print(f"Error sending public announcement: {e}")

    async def create_detailed_sect_info(self, sect_name: str) -> discord.Embed:
        """Tạo embed thông tin chi tiết về một môn phái"""
        sect_info = SECTS.get(sect_name, {})
        sect_details = SECT_DETAILS.get(sect_name, {})

        embed = discord.Embed(
            title=f"{SECT_EMOJIS.get(sect_name, '🏯')} {sect_name}",
            description=sect_info.get('description', 'Không có mô tả'),
            color=SECT_COLORS.get(sect_name, 0x7289da),
            timestamp=datetime.now()
        )

        # Thông tin cơ bản
        basic_info = []
        if sect_details.get('founder'):
            basic_info.append(f"👑 Tông Chủ Sáng Lập: {sect_details['founder']}")
        if sect_details.get('location'):
            basic_info.append(f"🗺️ Vị Trí: {sect_details['location']}")
        if sect_details.get('specialty'):
            basic_info.append(f"🔮 Sở Trường: {sect_details['specialty']}")

        if basic_info:
            embed.add_field(
                name="📋 Thông Tin Cơ Bản",
                value="\n".join(basic_info),
                inline=False
            )

        # Lịch sử
        if sect_details.get('history'):
            embed.add_field(
                name="📜 Lịch Sử",
                value=sect_details['history'],
                inline=False
            )

        # Kỹ năng nổi tiếng
        if sect_details.get('famous_skills'):
            embed.add_field(
                name="⚔️ Kỹ Năng Nổi Tiếng",
                value="\n".join([f"• {skill}" for skill in sect_details['famous_skills']]),
                inline=False
            )

        # Thông tin bonus
        attack_bonus = sect_info.get('attack_bonus', 1.0)
        defense_bonus = sect_info.get('defense_bonus', 1.0)

        embed.add_field(
            name="💪 Điểm Mạnh",
            value=(
                f"⚔️ Hệ số công kích: x{attack_bonus} ({(attack_bonus - 1) * 100:+.0f}%)\n"
                f"🛡️ Hệ số phòng thủ: x{defense_bonus} ({(defense_bonus - 1) * 100:+.0f}%)"
            ),
            inline=True
        )

        # Châm ngôn
        if sect_details.get('motto'):
            embed.add_field(
                name="📝 Châm Ngôn",
                value=f"*\"{sect_details['motto']}\"*",
                inline=False
            )

        # Thêm footer
        embed.set_footer(text="Sử dụng !phai để xem thống kê chi tiết về môn phái")

        return embed

    @commands.command(name="tongmon", aliases=["phái", "gianhap", "sect"], usage="")
    async def select_sect_command(self, ctx):
        """Hiển thị menu chọn tông môn"""
        try:
            # Tạo embed hướng dẫn
            embed = await self.create_sect_guide_embed()

            # Gửi menu chọn tông môn
            view = SectView(self)
            message = await ctx.send(embed=embed, view=view)

            # Tự động xóa sau 5 phút
            await asyncio.sleep(300)
            try:
                await message.delete()
            except:
                pass

        except Exception as e:
            print(f"Error in tongmon command: {e}")
            await ctx.send("Có lỗi xảy ra khi hiển thị menu chọn tông môn!")

    @commands.command(name="sect_info", aliases=["thongtinphai", "phai"], usage="[tên_môn_phái]")
    async def sect_info(self, ctx, *, sect_name: str = None):
        """Xem thông tin chi tiết về môn phái"""
        try:
            # Hiển thị thông báo đang tải
            loading_msg = await ctx.send("⏳ Đang tải thông tin môn phái...")

            # Nếu không có tên môn phái, kiểm tra môn phái của người dùng
            if not sect_name:
                player = await self.db.get_player(ctx.author.id)
                if player and player.get('sect'):
                    sect_name = player.get('sect')
                else:
                    # Hiển thị tất cả môn phái
                    await loading_msg.delete()
                    await self.show_all_sects_stats(ctx)
                    return

            # Tìm tông môn phù hợp
            target_sect = None
            for name in SECTS:
                if name.lower() == sect_name.lower() or sect_name.lower() in name.lower():
                    target_sect = name
                    break

            if target_sect:
                # Hiển thị thông tin một môn phái cụ thể
                await loading_msg.delete()
                await self.show_specific_sect_info(ctx, target_sect)
            else:
                await loading_msg.delete()
                await ctx.send(f"Không tìm thấy môn phái nào có tên '{sect_name}'!")

        except Exception as e:
            print(f"Error in sect_info: {e}")
            await ctx.send("Có lỗi xảy ra khi lấy thông tin môn phái!")

    async def show_specific_sect_info(self, ctx, sect_name: str):
        """Hiển thị thông tin chi tiết về một môn phái với giao diện tương tác"""
        try:
            # Tạo view với các tab thông tin
            view = SectStatsView(self)
            view.sect_name = sect_name  # Lưu tên môn phái vào view

            # Tạo embed tổng quan
            embed = await self.create_sect_overview_embed(sect_name)

            # Gửi embed với view
            await ctx.send(embed=embed, view=view)

        except Exception as e:
            print(f"Error showing sect info: {e}")
            await ctx.send("Có lỗi xảy ra khi hiển thị thông tin môn phái!")

    async def create_sect_overview_embed(self, sect_name: str) -> discord.Embed:
        """Tạo embed tổng quan về môn phái"""
        # Lấy thống kê môn phái từ cache hoặc tính toán mới
        if sect_name in self.sect_stats_cache and (
                datetime.now() - self.sect_stats_cache[sect_name]["updated_at"]).seconds < self.cache_timeout:
            sect_stats = self.sect_stats_cache[sect_name]
        else:
            # Tính toán thống kê mới
            all_players = await self.db.get_all_players()
            sect_members = [p for p in all_players if p.get('sect') == sect_name]
            total_exp = sum(member.get('exp', 0) for member in sect_members)
            avg_exp = total_exp // len(sect_members) if sect_members else 0
            highest_level_member = max(sect_members, key=lambda x: x.get('exp', 0)) if sect_members else None
            highest_exp = highest_level_member.get('exp', 0) if highest_level_member else 0

            sect_stats = {
                "members_count": len(sect_members),
                "total_exp": total_exp,
                "avg_exp": avg_exp,
                "highest_exp": highest_exp,
                "updated_at": datetime.now()
            }

            # Lưu vào cache
            self.sect_stats_cache[sect_name] = sect_stats

        # Lấy thông tin môn phái
        sect_info = SECTS.get(sect_name, {})
        sect_details = SECT_DETAILS.get(sect_name, {})

        # Tạo embed
        embed = discord.Embed(
            title=f"{SECT_EMOJIS.get(sect_name, '🏯')} {sect_name} - Tổng Quan",
            description=sect_info.get('description', 'Không có mô tả'),
            color=SECT_COLORS.get(sect_name, 0x7289da),
            timestamp=datetime.now()
        )

        # Thông tin cơ bản
        basic_info = []
        if sect_details.get('founder'):
            basic_info.append(f"👑 Tông Chủ Sáng Lập: {sect_details['founder']}")
        if sect_details.get('location'):
            basic_info.append(f"🗺️ Vị Trí: {sect_details['location']}")
        if sect_details.get('specialty'):
            basic_info.append(f"🔮 Sở Trường: {sect_details['specialty']}")

        if basic_info:
            embed.add_field(
                name="📋 Thông Tin Cơ Bản",
                value="\n".join(basic_info),
                inline=False
            )

        # Thống kê
        embed.add_field(
            name="📊 Thống Kê",
            value=(
                f"👥 Số thành viên: {sect_stats['members_count']}\n"
                f"📈 Tổng tu vi: {sect_stats['total_exp']:,} EXP\n"
                f"⚡ Trung bình: {sect_stats['avg_exp']:,} EXP/người\n"
                f"🔝 Tu vi cao nhất: {sect_stats['highest_exp']:,} EXP"
            ),
            inline=False
        )

        # Thông tin bonus
        attack_bonus = sect_info.get('attack_bonus', 1.0)
        defense_bonus = sect_info.get('defense_bonus', 1.0)

        embed.add_field(
            name="💪 Điểm Mạnh",
            value=(
                f"⚔️ Hệ số công kích: x{attack_bonus} ({(attack_bonus - 1) * 100:+.0f}%)\n"
                f"🛡️ Hệ số phòng thủ: x{defense_bonus} ({(defense_bonus - 1) * 100:+.0f}%)"
            ),
            inline=True
        )

        # Kỹ năng nổi tiếng
        if sect_details.get('famous_skills'):
            embed.add_field(
                name="⚔️ Kỹ Năng Nổi Tiếng",
                value="\n".join([f"• {skill}" for skill in sect_details['famous_skills'][:3]]),
                inline=True
            )

        # Châm ngôn
        if sect_details.get('motto'):
            embed.add_field(
                name="📝 Châm Ngôn",
                value=f"*\"{sect_details['motto']}\"*",
                inline=False
            )

        return embed

    async def create_sect_members_embed(self, sect_name: str) -> discord.Embed:
        """Tạo embed thông tin thành viên của môn phái"""
        # Lấy danh sách thành viên
        all_players = await self.db.get_all_players()
        sect_members = [p for p in all_players if p.get('sect') == sect_name]

        # Sắp xếp theo exp
        sorted_members = sorted(sect_members, key=lambda x: x.get('exp', 0), reverse=True)

        # Tạo embed
        embed = discord.Embed(
            title=f"{SECT_EMOJIS.get(sect_name, '🏯')} {sect_name} - Thành Viên",
            description=f"Danh sách {len(sorted_members)} thành viên của {sect_name}",
            color=SECT_COLORS.get(sect_name, 0x7289da),
            timestamp=datetime.now()
        )

        # Thêm thông tin về phân bố cảnh giới
        level_distribution = {}
        for member in sect_members:
            level = member.get('level', 'Phàm Nhân')
            if level not in level_distribution:
                level_distribution[level] = 0
            level_distribution[level] += 1

        # Sắp xếp cảnh giới theo thứ tự
        cultivation_cog = self.bot.get_cog('Cultivation')
        if cultivation_cog and hasattr(cultivation_cog, 'CULTIVATION_RANKS'):
            sorted_levels = sorted(
                level_distribution.items(),
                key=lambda x: cultivation_cog.CULTIVATION_RANKS.index(x[0]) if x[
                                                                                   0] in cultivation_cog.CULTIVATION_RANKS else -1
            )
        else:
            sorted_levels = sorted(level_distribution.items())

        level_info = []
        for level, count in sorted_levels:
            level_info.append(f"• {level}: {count} người")

        if level_info:
            embed.add_field(
                name="🌟 Phân Bố Cảnh Giới",
                value="\n".join(level_info),
                inline=False
            )

        # Thêm danh sách top thành viên
        top_members = sorted_members[:10]  # Lấy top 10

        if top_members:
            top_text = []
            for i, member in enumerate(top_members, 1):
                user_id = member.get('user_id')
                user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
                username = user.display_name if user else f"ID: {user_id}"
                exp = member.get('exp', 0)
                level = member.get('level', 'Phàm Nhân')
                top_text.append(f"{i}. {username} - {level} - {exp:,} EXP")

            embed.add_field(
                name="👑 Top Thành Viên",
                value="```\n" + "\n".join(top_text) + "\n```",
                inline=False
            )

        # Thêm thông tin về thời gian gia nhập
        recent_members = sorted(sect_members, key=lambda x: x.get('sect_joined_at', datetime.min), reverse=True)[:5]

        if recent_members:
            recent_text = []
            for member in recent_members:
                user_id = member.get('user_id')
                user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
                username = user.display_name if user else f"ID: {user_id}"

                joined_at = member.get('sect_joined_at')
                if isinstance(joined_at, str):
                    try:
                        joined_at = datetime.strptime(joined_at, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        joined_at = None

                joined_str = joined_at.strftime('%d/%m/%Y') if joined_at else "Không rõ"
                recent_text.append(f"• {username} - {joined_str}")

            embed.add_field(
                name="🆕 Thành Viên Mới Nhất",
                value="\n".join(recent_text),
                inline=False
            )

        return embed

    async def create_sect_activities_embed(self, sect_name: str) -> discord.Embed:
        """Tạo embed thông tin hoạt động của môn phái"""
        # Lấy danh sách thành viên
        all_players = await self.db.get_all_players()
        sect_members = [p for p in all_players if p.get('sect') == sect_name]

        # Tạo embed
        embed = discord.Embed(
            title=f"{SECT_EMOJIS.get(sect_name, '🏯')} {sect_name} - Hoạt Động",
            description=f"Thống kê hoạt động của {sect_name}",
            color=SECT_COLORS.get(sect_name, 0x7289da),
            timestamp=datetime.now()
        )

        # Thống kê hoạt động săn quái
        total_monsters = sum(member.get('stats', {}).get('monsters_killed', 0) for member in sect_members)
        total_bosses = sum(member.get('stats', {}).get('bosses_killed', 0) for member in sect_members)

        embed.add_field(
            name="⚔️ Săn Quái & Boss",
            value=(
                f"🐺 Quái vật đã tiêu diệt: {total_monsters:,}\n"
                f"👑 Boss đã tiêu diệt: {total_bosses:,}\n"
                f"📊 Tỷ lệ boss/quái: {(total_bosses / total_monsters * 100):.1f}%" if total_monsters > 0 else "0%"
            ),
            inline=False
        )

        # Thống kê PvP
        total_pvp_wins = sum(member.get('stats', {}).get('pvp_wins', 0) for member in sect_members)
        total_pvp_losses = sum(member.get('stats', {}).get('pvp_losses', 0) for member in sect_members)
        total_pvp = total_pvp_wins + total_pvp_losses

        embed.add_field(
            name="🥊 Thành Tích PvP",
            value=(
                f"🏆 Thắng: {total_pvp_wins:,}\n"
                f"💔 Thua: {total_pvp_losses:,}\n"
                f"📊 Tỷ lệ thắng: {(total_pvp_wins / total_pvp * 100):.1f}%" if total_pvp > 0 else "0%"
            ),
            inline=True
        )

        # Thống kê điểm danh
        total_daily_streak = sum(member.get('daily_streak', 0) for member in sect_members)
        avg_daily_streak = total_daily_streak / len(sect_members) if sect_members else 0

        embed.add_field(
            name="📅 Điểm Danh",
            value=(
                f"🔥 Tổng streak: {total_daily_streak:,}\n"
                f"⭐ Trung bình: {avg_daily_streak:.1f} ngày/người"
            ),
            inline=True
        )

        # Thống kê hoạt động gần đây
        recent_activities = []

        # Thêm thông tin về sự kiện sắp tới
        embed.add_field(
            name="🎉 Sự Kiện Sắp Tới",
            value=(
                "• Đại hội tông môn: 3 ngày nữa\n"
                "• Săn boss thế giới: 7 ngày nữa\n"
                "• Thí luyện tháp: 10 ngày nữa"
            ),
            inline=False
        )

        # Thêm thông tin về nhiệm vụ môn phái
        embed.add_field(
            name="📝 Nhiệm Vụ Môn Phái",
            value=(
                "• Tiêu diệt 100 quái vật: 45/100\n"
                "• Đánh bại 5 boss: 3/5\n"
                "• Thu thập 20 linh thạch: 12/20"
            ),
            inline=False
        )

        return embed

    async def create_sect_rankings_embed(self, sect_name: str) -> discord.Embed:
        """Tạo embed thông tin xếp hạng của môn phái"""
        # Lấy thống kê tất cả môn phái
        all_players = await self.db.get_all_players()

        # Tính toán thống kê cho từng môn phái
        sect_stats = {}
        for name in SECTS:
            sect_members = [p for p in all_players if p.get('sect') == name]
            total_exp = sum(member.get('exp', 0) for member in sect_members)
            avg_exp = total_exp // len(sect_members) if sect_members else 0

            # Tính các chỉ số khác
            total_monsters = sum(member.get('stats', {}).get('monsters_killed', 0) for member in sect_members)
            total_bosses = sum(member.get('stats', {}).get('bosses_killed', 0) for member in sect_members)
            total_pvp_wins = sum(member.get('stats', {}).get('pvp_wins', 0) for member in sect_members)

            sect_stats[name] = {
                "members": len(sect_members),
                "total_exp": total_exp,
                "avg_exp": avg_exp,
                "monsters": total_monsters,
                "bosses": total_bosses,
                "pvp_wins": total_pvp_wins
            }

        # Tạo embed
        embed = discord.Embed(
            title=f"{SECT_EMOJIS.get(sect_name, '🏯')} {sect_name} - Xếp Hạng",
            description=f"Thứ hạng của {sect_name} so với các môn phái khác",
            color=SECT_COLORS.get(sect_name, 0x7289da),
            timestamp=datetime.now()
        )

        # Xếp hạng theo tổng tu vi
        sorted_by_exp = sorted(sect_stats.items(), key=lambda x: x[1]["total_exp"], reverse=True)
        exp_rank = next((i + 1 for i, (name, _) in enumerate(sorted_by_exp) if name == sect_name), 0)

        # Xếp hạng theo số thành viên
        sorted_by_members = sorted(sect_stats.items(), key=lambda x: x[1]["members"], reverse=True)
        members_rank = next((i + 1 for i, (name, _) in enumerate(sorted_by_members) if name == sect_name), 0)

        # Xếp hạng theo trung bình tu vi
        sorted_by_avg = sorted(sect_stats.items(), key=lambda x: x[1]["avg_exp"], reverse=True)
        avg_rank = next((i + 1 for i, (name, _) in enumerate(sorted_by_avg) if name == sect_name), 0)

        # Xếp hạng theo săn quái
        sorted_by_monsters = sorted(sect_stats.items(), key=lambda x: x[1]["monsters"], reverse=True)
        monsters_rank = next((i + 1 for i, (name, _) in enumerate(sorted_by_monsters) if name == sect_name), 0)

        # Xếp hạng theo săn boss
        sorted_by_bosses = sorted(sect_stats.items(), key=lambda x: x[1]["bosses"], reverse=True)
        bosses_rank = next((i + 1 for i, (name, _) in enumerate(sorted_by_bosses) if name == sect_name), 0)

        # Xếp hạng theo PvP
        sorted_by_pvp = sorted(sect_stats.items(), key=lambda x: x[1]["pvp_wins"], reverse=True)
        pvp_rank = next((i + 1 for i, (name, _) in enumerate(sorted_by_pvp) if name == sect_name), 0)

        # Tạo hàm hiển thị xếp hạng với emoji
        def format_rank(rank, total):
            if rank == 1:
                return "🥇 Hạng 1"
            elif rank == 2:
                return "🥈 Hạng 2"
            elif rank == 3:
                return "🥉 Hạng 3"
            else:
                return f"#{rank}/{total}"

        # Thêm thông tin xếp hạng tổng hợp
        total_sects = len(SECTS)
        embed.add_field(
            name="🏆 Xếp Hạng Tổng Hợp",
            value=(
                f"📊 Tổng Tu Vi: {format_rank(exp_rank, total_sects)}\n"
                f"👥 Số Thành Viên: {format_rank(members_rank, total_sects)}\n"
                f"⚡ Trung Bình Tu Vi: {format_rank(avg_rank, total_sects)}"
            ),
            inline=False
        )

        # Thêm thông tin xếp hạng hoạt động
        embed.add_field(
            name="⚔️ Xếp Hạng Hoạt Động",
            value=(
                f"🐺 Săn Quái: {format_rank(monsters_rank, total_sects)}\n"
                f"👑 Săn Boss: {format_rank(bosses_rank, total_sects)}\n"
                f"🥊 PvP: {format_rank(pvp_rank, total_sects)}"
            ),
            inline=False
        )

        # Thêm biểu đồ so sánh với các môn phái khác
        comparison = []
        for i, (name, stats) in enumerate(sorted_by_exp):
            if name == sect_name:
                comparison.append(f"➡️ {i + 1}. {SECT_EMOJIS.get(name, '🏯')} {name}: {stats['total_exp']:,} EXP")
            else:
                comparison.append(f"   {i + 1}. {SECT_EMOJIS.get(name, '🏯')} {name}: {stats['total_exp']:,} EXP")

        embed.add_field(
            name="📊 Bảng Xếp Hạng Tu Vi",
            value="```\n" + "\n".join(comparison) + "\n```",
            inline=False
        )

        return embed

    async def show_all_sects_stats(self, ctx):
        """Hiển thị thống kê tất cả môn phái"""
        try:
            # Hiển thị thông báo đang tải
            loading_msg = await ctx.send("⏳ Đang tải thống kê môn phái...")

            embed = discord.Embed(
                title="🏯 Thống Kê Môn Phái",
                description="Tổng hợp thông tin các môn phái trong tông môn",
                color=0xf1c40f,
                timestamp=datetime.now()
            )

            # Lấy tất cả người chơi
            all_players = await self.db.get_all_players()

            # Thống kê theo môn phái
            sect_stats = {}
            for sect_name in SECTS:
                sect_members = [p for p in all_players if p.get('sect') == sect_name]
                total_exp = sum(member.get('exp', 0) for member in sect_members)

                # Tính các chỉ số khác
                highest_level_member = max(sect_members, key=lambda x: x.get('exp', 0)) if sect_members else None
                highest_exp = highest_level_member.get('exp', 0) if highest_level_member else 0

                # Tính phân bố cảnh giới
                level_counts = {}
                for member in sect_members:
                    level = member.get('level', 'Phàm Nhân')
                    if level not in level_counts:
                        level_counts[level] = 0
                    level_counts[level] += 1

                # Tìm cảnh giới cao nhất
                highest_level = None
                if level_counts:
                    # Sắp xếp cảnh giới theo thứ tự
                    cultivation_cog = self.bot.get_cog('Cultivation')
                    if cultivation_cog and hasattr(cultivation_cog, 'CULTIVATION_RANKS'):
                        sorted_levels = sorted(
                            level_counts.items(),
                            key=lambda x: cultivation_cog.CULTIVATION_RANKS.index(x[0]) if x[
                                                                                               0] in cultivation_cog.CULTIVATION_RANKS else -1,
                            reverse=True
                        )
                        highest_level = sorted_levels[0][0] if sorted_levels else None

                sect_stats[sect_name] = {
                    "members": len(sect_members),
                    "total_exp": total_exp,
                    "avg_exp": total_exp // len(sect_members) if sect_members else 0,
                    "highest_exp": highest_exp,
                    "highest_level": highest_level
                }

            # Sắp xếp theo tổng exp
            sorted_sects = sorted(sect_stats.items(), key=lambda x: x[1]["total_exp"], reverse=True)

            # Thêm thông tin vào embed
            for i, (name, stats) in enumerate(sorted_sects, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"

                # Tạo thanh tiến độ so với môn phái cao nhất
                max_exp = sorted_sects[0][1]["total_exp"] if sorted_sects else 1
                progress = (stats["total_exp"] / max_exp) * 100 if max_exp > 0 else 0
                progress_bar = self.create_progress_bar(progress)

                # Tạo thông tin chi tiết
                sect_info = (
                    f"👥 Thành viên: {stats['members']}\n"
                    f"📈 Tổng tu vi: {stats['total_exp']:,} EXP\n"
                    f"⚡ Trung bình: {stats['avg_exp']:,} EXP/người\n"
                    f"🌟 Cảnh giới cao nhất: {stats['highest_level'] or 'Không có'}\n"
                    f"📊 So với top: {progress_bar}"
                )

                embed.add_field(
                    name=f"{medal} {SECT_EMOJIS.get(name, '🏯')} {name}",
                    value=sect_info,
                    inline=False
                )

            # Thêm hướng dẫn
            embed.set_footer(text="Sử dụng !phai [tên_môn_phái] để xem chi tiết một môn phái")

            # Xóa thông báo đang tải và gửi kết quả
            await loading_msg.delete()
            await ctx.send(embed=embed)

        except Exception as e:
            print(f"Error showing all sects stats: {e}")
            await ctx.send("Có lỗi xảy ra khi hiển thị thống kê môn phái!")

    def create_progress_bar(self, percent: float, length: int = 10) -> str:
        """Tạo thanh tiến độ trực quan"""
        filled = int(length * percent / 100)
        empty = length - filled
        bar = '█' * filled + '░' * empty
        return f"[{bar}] {percent:.1f}%"

    @commands.command(name="sectmembers", aliases=["members", "thanhvien"], usage="[tên_môn_phái]")
    async def sect_members(self, ctx, *, sect_name: str = None):
        """Xem danh sách thành viên của môn phái"""
        try:
            # Hiển thị thông báo đang tải
            loading_msg = await ctx.send("⏳ Đang tải danh sách thành viên...")

            # Nếu không có tên môn phái, kiểm tra môn phái của người dùng
            if not sect_name:
                player = await self.db.get_player(ctx.author.id)
                if player and player.get('sect'):
                    sect_name = player.get('sect')
                else:
                    await loading_msg.delete()
                    await ctx.send("Vui lòng chỉ định tên môn phái hoặc gia nhập một môn phái trước!")
                    return

            # Tìm tông môn phù hợp
            target_sect = None
            for name in SECTS:
                if name.lower() == sect_name.lower() or sect_name.lower() in name.lower():
                    target_sect = name
                    break

            if not target_sect:
                await loading_msg.delete()
                await ctx.send(f"Không tìm thấy môn phái nào có tên '{sect_name}'!")
                return

            # Lấy danh sách thành viên
            all_players = await self.db.get_all_players()
            sect_members = [p for p in all_players if p.get('sect') == target_sect]

            # Sắp xếp theo exp
            sorted_members = sorted(sect_members, key=lambda x: x.get('exp', 0), reverse=True)

            # Tạo embed
            embed = discord.Embed(
                title=f"{SECT_EMOJIS.get(target_sect, '🏯')} Thành Viên {target_sect}",
                description=f"Danh sách {len(sorted_members)} thành viên của {target_sect}",
                color=SECT_COLORS.get(target_sect, 0x7289da),
                timestamp=datetime.now()
            )

            # Chia thành các trang nếu có quá nhiều thành viên
            members_per_page = 10
            total_pages = math.ceil(len(sorted_members) / members_per_page)

            # Hiển thị trang đầu tiên
            page = 1
            start_idx = (page - 1) * members_per_page
            end_idx = min(start_idx + members_per_page, len(sorted_members))

            # Hiển thị danh sách thành viên
            members_list = []
            for i, member in enumerate(sorted_members[start_idx:end_idx], start_idx + 1):
                user_id = member.get('user_id')
                user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
                username = user.display_name if user else f"ID: {user_id}"
                exp = member.get('exp', 0)
                level = member.get('level', 'Phàm Nhân')
                members_list.append(f"{i}. {username} - {level} - {exp:,} EXP")

            embed.add_field(
                name=f"📋 Danh Sách Thành Viên (Trang {page}/{total_pages})",
                value="```\n" + "\n".join(members_list) + "\n```",
                inline=False
            )

            # Thêm thông tin về phân bố cảnh giới
            level_distribution = {}
            for member in sect_members:
                level = member.get('level', 'Phàm Nhân')
                if level not in level_distribution:
                    level_distribution[level] = 0
                level_distribution[level] += 1

            # Sắp xếp cảnh giới theo thứ tự
            cultivation_cog = self.bot.get_cog('Cultivation')
            if cultivation_cog and hasattr(cultivation_cog, 'CULTIVATION_RANKS'):
                sorted_levels = sorted(
                    level_distribution.items(),
                    key=lambda x: cultivation_cog.CULTIVATION_RANKS.index(x[0]) if x[
                                                                                       0] in cultivation_cog.CULTIVATION_RANKS else -1
                )
            else:
                sorted_levels = sorted(level_distribution.items())

            level_info = []
            for level, count in sorted_levels:
                level_info.append(f"• {level}: {count} người")

            if level_info:
                embed.add_field(
                    name="🌟 Phân Bố Cảnh Giới",
                    value="\n".join(level_info),
                    inline=False
                )

            # Thêm footer
            embed.set_footer(text=f"Sử dụng !phai {target_sect} để xem thông tin chi tiết về môn phái")

            # Xóa thông báo đang tải và gửi kết quả
            await loading_msg.delete()
            await ctx.send(embed=embed)

        except Exception as e:
            print(f"Error showing sect members: {e}")
            await ctx.send("Có lỗi xảy ra khi hiển thị danh sách thành viên!")

    @commands.command(name="sectrank", aliases=["sectranking", "xephangphai"], usage="")
    async def sect_ranking(self, ctx):
        """Xem bảng xếp hạng các môn phái"""
        try:
            # Hiển thị thông báo đang tải
            loading_msg = await ctx.send("⏳ Đang tải bảng xếp hạng môn phái...")

            # Lấy tất cả người chơi
            all_players = await self.db.get_all_players()

            # Tính toán thống kê cho từng môn phái
            sect_stats = {}
            for sect_name in SECTS:
                sect_members = [p for p in all_players if p.get('sect') == sect_name]
                total_exp = sum(member.get('exp', 0) for member in sect_members)
                avg_exp = total_exp // len(sect_members) if sect_members else 0

                # Tính các chỉ số khác
                total_monsters = sum(member.get('stats', {}).get('monsters_killed', 0) for member in sect_members)
                total_bosses = sum(member.get('stats', {}).get('bosses_killed', 0) for member in sect_members)
                total_pvp_wins = sum(member.get('stats', {}).get('pvp_wins', 0) for member in sect_members)

                sect_stats[sect_name] = {
                    "members": len(sect_members),
                    "total_exp": total_exp,
                    "avg_exp": avg_exp,
                    "monsters": total_monsters,
                    "bosses": total_bosses,
                    "pvp_wins": total_pvp_wins
                }

            # Tạo embed
            embed = discord.Embed(
                title="🏆 Bảng Xếp Hạng Môn Phái",
                description="So sánh thành tích giữa các môn phái",
                color=0xf1c40f,
                timestamp=datetime.now()
            )

            # Xếp hạng theo tổng tu vi
            sorted_by_exp = sorted(sect_stats.items(), key=lambda x: x[1]["total_exp"], reverse=True)
            exp_ranking = []
            for i, (name, stats) in enumerate(sorted_by_exp, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                exp_ranking.append(f"{medal} {SECT_EMOJIS.get(name, '🏯')} {name}: {stats['total_exp']:,} EXP")

            embed.add_field(
                name="📊 Xếp Hạng Theo Tổng Tu Vi",
                value="\n".join(exp_ranking),
                inline=False
            )

            # Xếp hạng theo trung bình tu vi
            sorted_by_avg = sorted(sect_stats.items(), key=lambda x: x[1]["avg_exp"], reverse=True)
            avg_ranking = []
            for i, (name, stats) in enumerate(sorted_by_avg, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                avg_ranking.append(f"{medal} {SECT_EMOJIS.get(name, '🏯')} {name}: {stats['avg_exp']:,} EXP/người")

            embed.add_field(
                name="⚡ Xếp Hạng Theo Trung Bình Tu Vi",
                value="\n".join(avg_ranking),
                inline=False
            )

            # Xếp hạng theo số thành viên
            sorted_by_members = sorted(sect_stats.items(), key=lambda x: x[1]["members"], reverse=True)
            members_ranking = []
            for i, (name, stats) in enumerate(sorted_by_members, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                members_ranking.append(f"{medal} {SECT_EMOJIS.get(name, '🏯')} {name}: {stats['members']} thành viên")

            embed.add_field(
                name="👥 Xếp Hạng Theo Số Thành Viên",
                value="\n".join(members_ranking),
                inline=False
            )

            # Xếp hạng theo hoạt động
            # Tính điểm hoạt động: monsters + bosses*5 + pvp_wins*2
            activity_scores = {name: stats["monsters"] + stats["bosses"] * 5 + stats["pvp_wins"] * 2
                               for name, stats in sect_stats.items()}
            sorted_by_activity = sorted(activity_scores.items(), key=lambda x: x[1], reverse=True)

            activity_ranking = []
            for i, (name, score) in enumerate(sorted_by_activity, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                activity_ranking.append(f"{medal} {SECT_EMOJIS.get(name, '🏯')} {name}: {score:,} điểm")

            embed.add_field(
                name="⚔️ Xếp Hạng Theo Hoạt Động",
                value="\n".join(activity_ranking),
                inline=False
            )

            # Thêm footer
            embed.set_footer(text="Sử dụng !phai [tên_môn_phái] để xem thông tin chi tiết về một môn phái")

            # Xóa thông báo đang tải và gửi kết quả
            await loading_msg.delete()
            await ctx.send(embed=embed)

        except Exception as e:
            print(f"Error showing sect ranking: {e}")
            await ctx.send("Có lỗi xảy ra khi hiển thị bảng xếp hạng môn phái!")

    @commands.command(name="mysect", aliases=["myphai", "phaiinfo"], usage="")
    async def my_sect(self, ctx):
        """Xem thông tin môn phái của bản thân"""
        try:
            # Kiểm tra người chơi
            player = await self.db.get_player(ctx.author.id)
            if not player or not player.get('sect'):
                await ctx.send("Bạn chưa gia nhập môn phái nào! Hãy sử dụng lệnh `!tongmon` để chọn môn phái.")
                return

            # Lấy tên môn phái
            sect_name = player.get('sect')

            # Hiển thị thông tin môn phái
            await self.show_specific_sect_info(ctx, sect_name)

        except Exception as e:
            print(f"Error showing my sect: {e}")
            await ctx.send("Có lỗi xảy ra khi hiển thị thông tin môn phái!")

    @commands.command(name="leavesect", aliases=["roiphai", "leave"], usage="")
    async def leave_sect(self, ctx):
        """Rời khỏi môn phái hiện tại"""
        try:
            # Kiểm tra người chơi
            player = await self.db.get_player(ctx.author.id)
            if not player or not player.get('sect'):
                await ctx.send("Bạn chưa gia nhập môn phái nào!")
                return

            # Lấy tên môn phái hiện tại
            current_sect = player.get('sect')

            # Hiển thị xác nhận
            confirm_embed = discord.Embed(
                title="❓ Xác Nhận Rời Môn Phái",
                description=(
                    f"Bạn có chắc chắn muốn rời khỏi {SECT_EMOJIS.get(current_sect, '🏯')} **{current_sect}**?\n\n"
                    "**Lưu ý:**\n"
                    "• Bạn sẽ mất tất cả chức vụ và đặc quyền trong môn phái\n"
                    "• Bạn sẽ trở thành người không môn phái\n"
                    "• Bạn sẽ không nhận được bonus từ môn phái\n"
                    "• Bạn có thể gia nhập môn phái khác ngay lập tức"
                ),
                color=0xff9900
            )

            # Tạo view với các nút xác nhận/hủy
            class ConfirmView(discord.ui.View):
                def __init__(self, cog):
                    super().__init__(timeout=60)  # Timeout sau 60 giây
                    self.cog = cog
                    self.value = None

                @discord.ui.button(label="Xác Nhận", style=discord.ButtonStyle.danger)
                async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if interaction.user.id != ctx.author.id:
                        await interaction.response.send_message("Bạn không thể sử dụng nút này!", ephemeral=True)
                        return

                    await interaction.response.defer()
                    self.value = True
                    self.stop()

                @discord.ui.button(label="Hủy", style=discord.ButtonStyle.secondary)
                async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if interaction.user.id != ctx.author.id:
                        await interaction.response.send_message("Bạn không thể sử dụng nút này!", ephemeral=True)
                        return

                    await interaction.response.defer()
                    self.value = False
                    self.stop()

            # Gửi embed xác nhận
            view = ConfirmView(self)
            message = await ctx.send(embed=confirm_embed, view=view)

            # Chờ phản hồi
            await view.wait()

            # Xử lý kết quả
            if view.value is None:
                # Timeout
                await message.edit(content="Đã hết thời gian xác nhận!", embed=None, view=None)
                return
            elif view.value is False:
                # Hủy
                await message.edit(content="Đã hủy rời môn phái!", embed=None, view=None)
                return

            # Xác nhận rời môn phái
            # Xóa role môn phái
            role = discord.utils.get(ctx.guild.roles, name=current_sect)
            if role and role in ctx.author.roles:
                try:
                    await ctx.author.remove_roles(role)
                except discord.Forbidden:
                    print(f"Không đủ quyền để xóa role {role.name}")

            # Cập nhật database
            await self.db.update_player(
                ctx.author.id,
                sect=None,
                sect_joined_at=None
            )

            # Thông báo kết quả
            result_embed = discord.Embed(
                title="✅ Đã Rời Môn Phái",
                description=(
                    f"Bạn đã rời khỏi {SECT_EMOJIS.get(current_sect, '🏯')} **{current_sect}**!\n\n"
                    "Bạn hiện là người không môn phái. Sử dụng lệnh `!tongmon` để gia nhập môn phái mới."
                ),
                color=0x2ecc71,
                timestamp=datetime.now()
            )

            await message.edit(embed=result_embed, view=None)

        except Exception as e:
            print(f"Error leaving sect: {e}")
            await ctx.send("Có lỗi xảy ra khi rời khỏi môn phái!")


async def setup(bot):
    await bot.add_cog(Sect(bot, bot.db))