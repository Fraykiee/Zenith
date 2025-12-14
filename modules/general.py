# requires: numpy, pillow, requests, psutil
import os
from telethon import events
import logging
import platform
import sys
from datetime import datetime


try:
    import psutil
except ImportError:
    psutil = None

logger = logging.getLogger("Module:General")


BANNER_FILENAME = "banner.png" 
BANNER_PATH = os.path.join("assets", BANNER_FILENAME)
CACHED_BANNER = None

def load(client):
    

    @client.on(events.NewMessage(pattern=r'(?i)^\.info$', outgoing=True))
    async def info_handler(event):
        global CACHED_BANNER
        await event.delete()

        me = await client.get_me()
        user_link = f"<a href='tg://user?id={me.id}'>{me.first_name}</a>"
        

        if hasattr(client, 'uptime'):
            uptime_delta = datetime.now() - client.uptime
            uptime_str = str(uptime_delta).split('.')[0]
        else:
            uptime_str = "0:00:00"
        

        uname = platform.uname()
        system_name = "Android (Termux)" if "Android" in uname.system or "localhost" in uname.node else f"{uname.system} {uname.release}"
        
     
        cpu_usage = "N/A"
        ram_usage = "N/A"
        
        if psutil:
            try:
   
                cpu_usage = f"{psutil.cpu_percent(interval=None)}%"
            except:
                cpu_usage = "Restricted"

            try:
                mem = psutil.virtual_memory()
                ram_usage = f"{mem.percent}%"
            except:
                ram_usage = "Restricted"
        
  
        if "Windows" in system_name:
            os_icon = "<emoji document_id='5431376038628238641'>🪟</emoji>"
        elif "Android" in system_name:
            os_icon = "<emoji document_id='5431376038628238641'>🤖</emoji>"
        else:
            os_icon = "<emoji document_id='5431376038628238641'>🐧</emoji>"


        info_text = (
            f"<emoji document_id='5431449001532594346'>👤</emoji> <b>Владелец:</b> {user_link}\n"
            f"<emoji document_id='5373103444648795554'>🔮</emoji> <b>Юзербот:</b> <code>𝐙 𝐄 𝐍 𝐈 𝐓 𝐇  (v1.0)</code>\n\n"
            
            f"<emoji document_id='5431566367805414571'>⏳</emoji> <b>Аптайм:</b> <code>{uptime_str}</code>\n"
            f"<emoji document_id='5312389146864131596'>🌳</emoji> <b>Ветка:</b> <code>main</code>\n\n"
            
            f"<emoji document_id='5372990380674883134'>⚙️</emoji> <b>CPU:</b> <code>{cpu_usage}</code>\n"
            f"<emoji document_id='5431665489703120159'>🧠</emoji> <b>RAM:</b> <code>{ram_usage}</code>\n"
            f"{os_icon} <i>{system_name}</i>"
        )
        
    
        try:
            if CACHED_BANNER:
                await client.send_file(event.chat_id, CACHED_BANNER, caption=info_text, parse_mode='html')
            elif os.path.exists(BANNER_PATH):
                msg = await client.send_file(event.chat_id, BANNER_PATH, caption=info_text, parse_mode='html')
                CACHED_BANNER = msg.media
            else:
                await client.send_message(event.chat_id, info_text, parse_mode='html')
        except Exception as e:
      
            await client.send_message(event.chat_id, info_text, parse_mode='html')


    @client.on(events.NewMessage(pattern=r'(?i)^\.ping$', outgoing=True))
    async def ping_handler(event):
        start = datetime.now()
        await event.edit("<emoji document_id='5372990380674883134'>🏓</emoji> <b>Pong!</b>", parse_mode='html')
        end = datetime.now()
        ms = (end - start).microseconds / 1000
        
        if hasattr(client, 'uptime'):
            upt = str(datetime.now() - client.uptime).split('.')[0]
        else:
            upt = "Unknown"
        
        msg = (
            f"<emoji document_id='5372990380674883134'>🏓</emoji> <b>Pong!</b>\n"
            f"📶 <b>Ping:</b> <code>{ms}ms</code>\n"
            f"⏳ <b>Uptime:</b> <code>{upt}</code>"
        )
        await event.edit(msg, parse_mode='html')

    @client.on(events.NewMessage(pattern=r'(?i)^\.save$', outgoing=True))
    async def save_handler(event):
        if event.is_reply:
            reply = await event.get_reply_message()
            await client.forward_messages('me', reply)
            await event.delete()
        else:
            await event.edit("⚠️ Reply to a message.")

    @client.on(events.NewMessage(pattern=r'(?i)^\.id$', outgoing=True))
    async def id_handler(event):
        chat_id = event.chat_id
        msg = f"📍 <b>Chat ID:</b> <code>{chat_id}</code>"
        if event.is_reply:
            r = await event.get_reply_message()
            msg += f"\n👉 <b>User ID:</b> <code>{r.sender_id}</code>"
        await event.edit(msg, parse_mode='html')

    @client.on(events.NewMessage(pattern=r'(?i)^\.chats$', outgoing=True))
    async def chats_handler(event):
        dialogs = await client.get_dialogs(limit=10)
        lines = ["📋 <b>Recent Chats:</b>"]
        for d in dialogs:
            name = d.name if d.name else "Deleted"
            lines.append(f"- {name} (<code>{d.id}</code>)")
        await event.edit("\n".join(lines), parse_mode='html')
