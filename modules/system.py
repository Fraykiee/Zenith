import os
import sys
import re
import asyncio
import configparser
import importlib
from telethon import events


META = {
    'name': 'System',
    'version': '4.2',
    'description': 'Ядро управления юзерботом (установка, рестарт, помощь).',
    'author': 'Fraykiee'
}

SYSTEM_MODULES = ['system', 'general', 'afk', 'info', 'spam', 'tagall', 'ai'] 
ICON_ID = "5431449001532594346" 
SYS_ICON = "5431376038628238641" 

config = configparser.ConfigParser()

def load(client):

    @client.on(events.NewMessage(pattern=r'(?i)^\.help$', outgoing=True))
    async def help_handler(event):
        modules_dir = 'modules'
        sys_list = []
        custom_list = []
        
        files = [f for f in os.listdir(modules_dir) if f.endswith('.py') and not f.startswith('_')]
        
        for filename in sorted(files):
            name = filename[:-3]
            try:

                mod = importlib.import_module(f"modules.{name}")
                

                with open(os.path.join(modules_dir, filename), 'r', encoding='utf-8') as f:
                    content = f.read()
                    matches = re.findall(r"pattern=r['\"](?:\(\?i\))?\^\\\.([a-zA-Z0-9_]+)", content)
                    commands = sorted(list(set(matches)))
                
   
                meta = getattr(mod, 'META', None)
                if meta:
                    ver = f"v{meta.get('version', '1.0')}"
                    desc = meta.get('description', '')

                    title = f"<b>{name.capitalize()}</b> {ver}"
                else:
                    title = f"<b>{name.capitalize()}</b>"
                    desc = ""

                cmds_str = " | ".join(commands) if commands else ""
                

                
                entry = f"{title}"
                if desc: entry += f"\n<i>{desc}</i>"
                entry += f"\n( <code>{cmds_str}</code> )\n"

                if name in SYSTEM_MODULES:
                    icon = f"<emoji document_id='{SYS_ICON}'>⚙️</emoji>"
                    sys_list.append(f"{icon} {entry}")
                else:
                    icon = f"<emoji document_id='{ICON_ID}'>📂</emoji>"
                    custom_list.append(f"{icon} {entry}")

            except Exception as e:
     
                custom_list.append(f"⚠️ <b>{name}</b> (Error: {e})")


        text = f"🔮 <b>Zenith Modules:</b>\n\n"
        
        if sys_list:
            text += f"⚙️ <b>System:</b>\n<blockquote>" + "\n".join(sys_list) + "</blockquote>\n\n"
        
        if custom_list:
            text += f"📂 <b>Custom:</b>\n<blockquote>" + "\n".join(custom_list) + "</blockquote>\n\n"
        else:
            text += f"📂 <b>Custom:</b>\n<blockquote><i>Нет установленных модулей.</i></blockquote>\n\n"
            
        await event.edit(text, parse_mode='html')


    @client.on(events.NewMessage(pattern=r'(?i)^\.restart$', outgoing=True))
    async def restart_handler(event):
        config.read('config.ini')
        bot_username = config['System'].get('bot_username', '')
        
        if bot_username:
            try:
                await event.delete()
                results = await client.inline_query(bot_username, 'restart_panel')
                if results: await results[0].click(event.chat_id)
                else: await client.send_message(event.chat_id, "❌ Бот не отвечает.")
            except:
                msg = await client.send_message(event.chat_id, f"⚠️ Inline Fail. Text Mode...")
                with open('.restart_info', 'w') as f: f.write(f"text|{event.chat_id}|{msg.id}")
                await asyncio.sleep(1)
                os.execl(sys.executable, sys.executable, "main.py")
        else:
            msg = await event.edit("🔄 **Перезагрузка...**")
            with open('.restart_info', 'w') as f: f.write(f"text|{event.chat_id}|{msg.id}")
            await asyncio.sleep(1)
            os.execl(sys.executable, sys.executable, "main.py")

    
    @client.on(events.NewMessage(pattern=r'(?i)^\.lm(?: |$)(.*)', outgoing=True))
    async def install_handler(event):
        arg = event.pattern_match.group(1).strip()
        reply = await event.get_reply_message()
        file_name = ""
        file_content = b""
        await event.edit("🔄 <b>Загрузка...</b>", parse_mode='html')
        try:
            if reply and reply.media:
                file_name = reply.file.name
                file_content = await client.download_file(reply, bytes)
            elif arg.startswith("http"):
                file_name = arg.split("/")[-1]
                import requests
                r = requests.get(arg)
                file_content = r.content
            
            if not file_name.endswith(".py"): file_name += ".py"
            mod_name = file_name[:-3]

            if mod_name in SYSTEM_MODULES:
                await event.edit(f"❌ <b>Ошибка:</b> Модуль <code>{mod_name}</code> защищен!", parse_mode='html')
                return

            path = os.path.join("modules", file_name)
            with open(path, "wb") as f: f.write(file_content)
            

            try:
                import importlib
                mod = importlib.import_module(f"modules.{mod_name}")
                importlib.reload(mod)
                meta = getattr(mod, 'META', {})
                info = f"v{meta.get('version', '1.0')} by {meta.get('author', '?')}"
            except: info = "Installed"

            await event.edit(f"✅ <b>{mod_name}</b> ({info})\nЖми <code>.restart</code>", parse_mode='html')
        except Exception as e:
            await event.edit(f"Error: {e}")


    @client.on(events.NewMessage(pattern=r'(?i)^\.ml (.*)', outgoing=True))
    async def upload_mod_handler(event):
        mod = event.pattern_match.group(1).strip()
        path = f"modules/{mod}.py"
        if os.path.exists(path):
            await event.edit(f"📤 <b>Выгружаю {mod}...</b>", parse_mode='html')
            await client.send_file(event.chat_id, path, caption=f"📦 <b>Module:</b> <code>{mod}.py</code>", parse_mode='html')
        else:
            await event.edit(f"❌ Модуль <code>{mod}</code> не найден.", parse_mode='html')


    @client.on(events.NewMessage(pattern=r'(?i)^\.dlm (.*)', outgoing=True))
    async def delete_handler(event):
        mod = event.pattern_match.group(1).strip()
        if mod in SYSTEM_MODULES: return await event.edit("⚠️ Системный модуль!")
        path = f"modules/{mod}.py"
        if os.path.exists(path):
            os.remove(path)
            await event.edit(f"🗑 Модуль <b>{mod}</b> удален.", parse_mode='html')
        else:
            await event.edit("❌ Модуль не найден.")


    @client.on(events.NewMessage(pattern=r'(?i)^\.off$', outgoing=True))
    async def shutdown_handler(event):
        await event.edit("🔌 <b>Отключение...</b>", parse_mode='html')
        await client.disconnect()
        sys.exit(0)