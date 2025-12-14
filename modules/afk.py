from telethon import events
import logging

logger = logging.getLogger("Module:AFK")

AFK_STATE = {'is_afk': False, 'reason': None}

def load(client):

    @client.on(events.NewMessage(pattern=r'(?i)^\.afk(?:\s+(.*))?', outgoing=True))
    async def set_afk(event):
        reason = event.pattern_match.group(1)
        AFK_STATE['is_afk'] = True
        AFK_STATE['reason'] = reason if reason else "Busy"
        await event.edit(f"😴 **AFK Mode On.**\nReason: {AFK_STATE['reason']}")

    @client.on(events.NewMessage(incoming=True))
    async def afk_responder(event):
        if not AFK_STATE['is_afk']: return
        if event.is_private or event.mentioned:
            await event.reply(f"🤖 **Auto-Reply:**\nI am currently AFK.\nReason: {AFK_STATE['reason']}")


    @client.on(events.NewMessage(outgoing=True, pattern=r'(?i)(?!^\.afk)')) 
    async def unset_afk(event):
        if AFK_STATE['is_afk']:
            AFK_STATE['is_afk'] = False
            AFK_STATE['reason'] = None
            await event.reply("👋 **I'm back!** AFK disabled.")
