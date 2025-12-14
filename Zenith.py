import logging
import configparser
import os
import sys
import importlib
import asyncio
import traceback
import random
import string
from datetime import datetime
from telethon import TelegramClient, events, functions, types, Button
from telethon.errors import AuthKeyUnregisteredError, MessageIdInvalidError, MessageNotModifiedError, FloodWaitError


class TelegramLogHandler(logging.Handler):
    def emit(self, record):
        if record.levelno < logging.ERROR: return
        try:
            exc_name = record.exc_info[0].__name__ if record.exc_info else "Log Error"
            exc_msg = str(record.msg)
            tb_str = ""
            if record.exc_info:
                tb_str = "".join(traceback.format_exception(*record.exc_info))[-1000:]
            
            text = (
                f"🎯 **Source:** `{record.name}`\n"
                f"❓ **Error:** `{exc_name}: {exc_msg}`\n"
                f"💭 **Traceback:**\n`{tb_str}`"
            )
            
            target = bot_client if (bot_client and bot_client.is_connected()) else client
            if target and LOG_GROUP_ID:
                target.loop.create_task(target.send_message(LOG_GROUP_ID, text))
        except: pass

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ZenithCore")

config = configparser.ConfigParser()
config.read('config.ini')

try:
    API_ID = int(config['Telegram']['api_id'])
    API_HASH = config['Telegram']['api_hash']
    SESSION_NAME = config['Telegram']['session_name']
except KeyError:
    logger.error("❌ Config Error")
    sys.exit(1)

for d in ['session', 'modules', 'assets']:
    if not os.path.exists(d): os.makedirs(d)

user_session = os.path.join('session', SESSION_NAME)
client = TelegramClient(user_session, API_ID, API_HASH)
client.uptime = datetime.now()

bot_client = None 

def get_safe_int(s, k):
    val = config[s].get(k, '') if s in config else ''
    return int(val) if val.isdigit() or (val.startswith('-') and val[1:].isdigit()) else 0

LOG_GROUP_ID = get_safe_int('System', 'log_group_id')
BOT_USERNAME = config['System'].get('bot_username', '') if 'System' in config else ''

logging.getLogger().addHandler(TelegramLogHandler())


def generate_short_username():
    return f"Zenith_{''.join(random.choices(string.ascii_letters + string.digits, k=5))}_Bot"

async def setup_zenith():
    global LOG_GROUP_ID, bot_client, BOT_USERNAME
    
    if LOG_GROUP_ID == 0:
        try:
            c = await client(functions.channels.CreateChannelRequest("Zenith Logs 🔮", "Logs", megagroup=True))
            LOG_GROUP_ID = int(f"-100{c.chats[0].id}")
            if 'System' not in config: config['System'] = {}
            config['System']['log_group_id'] = str(LOG_GROUP_ID)
            with open('config.ini', 'w') as f: config.write(f)
        except: pass

    bot_token = config['System'].get('bot_token', '')
    if not bot_token:
        try:
            async with client.conversation('@BotFather', timeout=40) as conv:
                await conv.send_message('/newbot'); await conv.get_response()
                await conv.send_message("Zenith Helper"); await conv.get_response()
                while True:
                    u = generate_short_username()
                    await conv.send_message(u); r = await conv.get_response()
                    if "Done" in r.text:
                        bot_token = r.text.split('HTTP API:')[1].split('\n')[1].strip()
                        BOT_USERNAME = u
                        config['System']['bot_token'] = bot_token
                        config['System']['bot_username'] = u
                        with open('config.ini', 'w') as f: config.write(f)
                        break
                    if "Sorry" in r.text: continue
                    if "Too many" in r.text: return
                for cmd in ['/setinline', f'@{u}', 'Search...', '/setprivacy', f'@{u}', 'Disable']:
                    await conv.send_message(cmd); await conv.get_response()
        except: pass

    if LOG_GROUP_ID and BOT_USERNAME:
        try:
            await client(functions.channels.InviteToChannelRequest(LOG_GROUP_ID, [BOT_USERNAME]))
            await client(functions.channels.EditAdminRequest(LOG_GROUP_ID, BOT_USERNAME, types.ChatAdminRights(post_messages=True, edit_messages=True, delete_messages=True, invite_users=True, ban_users=True, pin_messages=True, add_admins=False, anonymous=False, manage_call=False, other=True), 'Helper'))
        except: pass

    global bot_client
    if bot_token:
        if os.path.exists(os.path.join('session', 'zenith_bot.session')):
            try: os.remove(os.path.join('session', 'zenith_bot.session'))
            except: pass
            
        bot_client = TelegramClient(os.path.join('session', 'zenith_bot'), API_ID, API_HASH)
        try:
            await bot_client.start(bot_token=bot_token)
            register_bot_handlers()
            logger.info("✅ Helper Bot запущен!")
        except FloodWaitError as e:
            logger.warning(f"⚠️ FloodWait бота: {e.seconds} сек.")
            bot_client = None
        except Exception as e:
            logger.error(f"❌ Helper Bot Error: {e}")
            if bot_client: await bot_client.disconnect()
            bot_client = None


async def load_all_plugins():
    loaded = 0
    if not os.path.exists('modules'): os.makedirs('modules')
    
    for f in os.listdir('modules'):
        if f.endswith('.py') and not f.startswith('_'):
            mod_name = f[:-3]
            try:
                mod = importlib.import_module(f"modules.{mod_name}")
                if hasattr(mod, 'load'):
                    mod.load(client)
                    loaded += 1
                    
                   
                    meta = getattr(mod, 'META', None)
                    if meta:
                        logger.info(f"🧩 Loaded: {meta.get('name', mod_name)} v{meta.get('version', '1.0')} by {meta.get('author', 'Unknown')}")
                    else:
                        logger.info(f"🧩 Loaded: {mod_name}")
                        
            except Exception as e:
                logger.error(f"Failed loading {f}: {e}")
    return loaded


def register_bot_handlers():
    if not bot_client: return

    @bot_client.on(events.NewMessage(pattern='/start'))
    async def bot_start(event):
        await event.reply("Zenith Helper Active.")

    @bot_client.on(events.InlineQuery)
    async def inline(event):
        if event.sender_id != (await client.get_me()).id:
            return await event.answer([event.builder.article("Error", text="Access Denied")])

        if event.text == 'restart_panel':
            await event.answer([
                event.builder.article(
                    title="Перезагрузка",
                    text="⚠️ **Вы уверены, что хотите перезагрузить Zenith?**", 
                    buttons=[
                        [Button.inline("✅ Да", b"restart_yes"), Button.inline("❌ Нет", b"restart_no")]
                    ]
                )
            ])

    @bot_client.on(events.CallbackQuery)
    async def callback(event):
        if event.sender_id != (await client.get_me()).id: return
        
        if event.data == b'restart_yes':
            await event.edit("🔄 **Перезагрузка...**")
            c_id = event.chat_id
            if not c_id:
                try: c_id = (await event.get_chat()).id
                except: c_id = 0
            
            with open('.restart_info', 'w') as f:
                f.write(f"inline|{c_id}|{event.message_id}")
            
            await asyncio.sleep(1)
            os.execl(sys.executable, sys.executable, "main.py")
            
        elif event.data == b'restart_no':
            await event.edit("❌ **Отменено.**")


async def main():
    try: await client.start()
    except AuthKeyUnregisteredError: sys.exit("Session Invalid")
    
    await setup_zenith()
    await load_all_plugins()
    

    if os.path.exists('.restart_info'):
        try:
            with open('.restart_info', 'r') as f:
                data = f.read().split('|')
            mode, chat_id, msg_id = data[0], int(data[1]), int(data[2])
            uptime = str(datetime.now() - client.uptime).split('.')[0]
            text = f"✅ **Zenith Online!**\n⏱ Загрузка: `{uptime}`"

            try:
                if chat_id != 0:
                    if mode == 'text': await client.get_entity(chat_id)
                    elif mode == 'inline' and bot_client: await bot_client.get_entity(chat_id)
                sender = bot_client if (mode == 'inline' and bot_client) else client
                if sender: await sender.edit_message(chat_id, msg_id, text)
            except: pass
        except: pass
        finally:
            if os.path.exists('.restart_info'): os.remove('.restart_info')

  
    target = bot_client if (bot_client and bot_client.is_connected()) else client
    if target and LOG_GROUP_ID:
        try:
            file_to_send = "assets/banner.png" if os.path.exists("assets/banner.png") else ("assets/logo.jpg" if os.path.exists("assets/logo.jpg") else None)
            caption = (f"🚀 **Zenith Started!**\n👤 **User:** {(await client.get_me()).first_name}\n🔢 **Version:** `v4.2 (Meta Update)`")
            if file_to_send: await target.send_file(LOG_GROUP_ID, file_to_send, caption=caption)
            else: await target.send_message(LOG_GROUP_ID, caption)
        except: pass


    tasks = [client.run_until_disconnected()]
    if bot_client and bot_client.is_connected():
        tasks.append(bot_client.run_until_disconnected())
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    if sys.platform == 'win32': asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try: client.loop.run_until_complete(main())
    except: pass