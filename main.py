import discord
import asyncio
from discord.ext import commands
from database.mongo_handler import MongoDB
import platform
import time
import sys
import logging
import traceback
from config import TOKEN, PREFIX, DEBUG_MODE, OWNER_ID
import os
from dotenv import load_dotenv

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler("logs/bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('main')

# Đảm bảo thư mục logs tồn tại
if not os.path.exists('logs'):
    os.makedirs('logs')

# Load environment variables
load_dotenv()

# Thời gian bắt đầu
start_time = time.time()

# Initialize bot
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# Lưu trữ database trong bot để các module có thể truy cập
bot.db = None


# Hàm tiện ích để xóa lệnh nếu đã tồn tại
def remove_command_if_exists(command_name):
    """Xóa lệnh nếu nó đã tồn tại"""
    if bot.get_command(command_name):
        bot.remove_command(command_name)
        logger.info(f"Đã xóa lệnh {command_name} cũ để tránh xung đột")


# Hàm xử lý xung đột lệnh trước khi load module
def prepare_for_module_loading():
    """Xóa các lệnh có thể xung đột trước khi load modules"""
    # Xóa lệnh help mặc định
    remove_command_if_exists('help')

    # Danh sách các lệnh có thể xung đột
    potential_conflicts = ['xephang', 'danhquai', 'daily', 'rank', 'levels']
    for cmd in potential_conflicts:
        remove_command_if_exists(cmd)


@bot.event
async def on_ready():
    # ASCII Art Banner
    print(f'''
╔════════════════════════════════════════╗
║             TU TIÊN BOT                ║
╚════════════════════════════════════════╝
    ''')

    # Thông tin hệ thống
    print(f'Bot: {bot.user}')
    print(f'ID: {bot.user.id}')
    print(f'Discord.py version: {discord.__version__}')
    print(f'Python version: {platform.python_version()}')
    print(f'Running on: {platform.system()} {platform.release()}')
    print(f'Debug mode: {DEBUG_MODE}')
    print('═' * 40)

    try:
        # Khởi tạo MongoDB
        print("\n[1/4] Đang kết nối MongoDB...")
        bot.db = MongoDB()
        await bot.db.setup_indexes()
        print("✓ Đã kết nối MongoDB và tạo indexes thành công!")

        # Xóa các lệnh có thể xung đột
        print("\n[2/4] Đang chuẩn bị load modules...")
        prepare_for_module_loading()
        print("✓ Đã xóa các lệnh có thể xung đột!")

        # Load modules
        print("\n[3/4] Đang load các modules...")
        await load_cogs()
        print("✓ Tất cả modules đã được load thành công!")

        # Set activity
        print("\n[4/4] Đang cập nhật trạng thái...")
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{PREFIX}tutien | Tu luyện"
            ),
            status=discord.Status.online
        )
        print("✓ Đã cập nhật trạng thái bot!")

        # Hoàn tất khởi động
        elapsed_time = time.time() - start_time
        print(f"\n✓ Bot đã sẵn sàng! (Khởi động trong {elapsed_time:.2f} giây)")
        print('═' * 40)

        # Thông báo cho owner nếu có
        if OWNER_ID:
            try:
                owner = await bot.fetch_user(OWNER_ID)
                if owner:
                    embed = discord.Embed(
                        title="✅ Bot Đã Khởi Động",
                        description=f"Bot đã khởi động thành công trong {elapsed_time:.2f} giây.",
                        color=0x2ecc71,
                        timestamp=discord.utils.utcnow()
                    )
                    embed.add_field(name="Phiên bản", value=f"Discord.py {discord.__version__}", inline=True)
                    embed.add_field(name="Prefix", value=PREFIX, inline=True)
                    embed.add_field(name="Debug Mode", value=str(DEBUG_MODE), inline=True)

                    await owner.send(embed=embed)
            except Exception as e:
                logger.error(f"Không thể gửi thông báo cho owner: {e}")

    except Exception as e:
        logger.error(f"Lỗi khi khởi tạo: {e}")
        print(f"\n❌ Lỗi khi khởi tạo: {e}")
        print("Bot sẽ tắt trong 5 giây...")
        await asyncio.sleep(5)
        await bot.close()


async def load_cogs():
    # Danh sách các extension cần load
    extensions = [
        'modules.cultivation',
        'modules.combat',
        'modules.monster',
        'modules.sect',
        'modules.help',
        'modules.daily',
        'modules.error_handler',
        'modules.commands'
    ]

    # Xóa các lệnh có thể xung đột trước
    conflict_commands = ['daily', 'help', 'xephang', 'danhquai', 'rank', 'levels']
    for cmd in conflict_commands:
        remove_command_if_exists(cmd)

    loaded_count = 0
    for i, extension in enumerate(extensions, 1):
        try:
            module_name = extension.split('.')[-1].capitalize()

            try:
                # Thử load extension
                await bot.load_extension(extension)
                print(f"  ✓ [{i}/{len(extensions)}] Đã load module: {module_name}")
                loaded_count += 1
            except discord.ext.commands.errors.CommandRegistrationError as e:
                # Nếu có lỗi xung đột lệnh, xóa lệnh đó và thử lại
                cmd_name = str(e).split("The command ")[1].split(" is")[0] if "The command " in str(e) else str(e)
                print(f"  ⚠️ Phát hiện xung đột lệnh '{cmd_name}', đang xử lý...")
                remove_command_if_exists(cmd_name)

                # Thử load lại
                await bot.load_extension(extension)
                print(f"  ✓ [{i}/{len(extensions)}] Đã load module: {module_name} (sau khi xử lý xung đột)")
                loaded_count += 1

        except Exception as e:
            error_msg = f"  ❌ [{i}/{len(extensions)}] Lỗi khi load module {module_name}: {e}"
            print(error_msg)
            logger.error(error_msg)
            logger.error(traceback.format_exc())

    if loaded_count == len(extensions):
        print(f"✓ Đã load thành công {loaded_count}/{len(extensions)} modules!")
    else:
        print(f"⚠️ Đã load {loaded_count}/{len(extensions)} modules.")


# Graceful shutdown
async def cleanup():
    """Dọn dẹp trước khi tắt bot"""
    print("\nĐang tắt bot...")
    try:
        # Đóng kết nối database
        if bot.db:
            await bot.db.close()
            print("✓ Đã đóng kết nối MongoDB")

        # Các tác vụ dọn dẹp khác
        print("✓ Đã lưu trạng thái")
        print("✓ Đã tắt bot an toàn")
    except Exception as e:
        print(f"❌ Lỗi khi tắt bot: {e}")
        logger.error(f"Lỗi khi tắt bot: {e}")


# Error handler cho các lỗi không mong muốn
@bot.event
async def on_error(event, *args, **kwargs):
    error_msg = f"Lỗi trong event {event}: {sys.exc_info()[1]}"
    print(error_msg)
    logger.error(error_msg)
    logger.error(traceback.format_exc())


# Lệnh reload module
@bot.command(name="reload", hidden=True)
@commands.is_owner()
async def reload_module(ctx, module_name: str):
    """Reload một module cụ thể (chỉ dành cho chủ bot)"""
    try:
        # Xóa module cũ
        module_path = f"modules.{module_name.lower()}"
        await bot.reload_extension(module_path)
        await ctx.send(f"✅ Đã reload module `{module_name}` thành công!")
    except Exception as e:
        await ctx.send(f"❌ Lỗi khi reload module `{module_name}`: {e}")
        logger.error(f"Lỗi khi reload module {module_name}: {e}")


# Run bot
if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except Exception as e:
        logger.critical(f"Lỗi khi khởi động bot: {e}")
        print(f"❌ Lỗi khi khởi động bot: {e}")
    finally:
        # Chạy cleanup khi bot tắt
        asyncio.run(cleanup())
