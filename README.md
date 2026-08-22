# Logging Bot

A per-server activity logger: message edits/deletes, member joins/leaves,
kicks/bans, channel and role changes, voice movement, invites, and emoji/
sticker/server updates. Config is per-guild and stored in SQLite -- no
external database needed.

## Setup

1. `python -m venv venv && source venv/bin/activate` (or your preferred env tool)
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and drop in your bot token, or export
   `BOT_TOKEN` directly.
4. Enable **Server Members Intent** and **Message Content Intent** in the
   Discord Developer Portal under your application's Bot tab -- both are
   required for the events this bot logs.
5. `python bot.py`

## Commands

- `/settings channel` -- pick the channel logs get sent to
- `/settings events` -- turn categories of events on/off
- `/settings toggle` -- kill switch for all logging
- `/settings status` -- see current config
- `/vote` -- links out to the vote page (placeholder URL in `utils/config.py`
  until the listing is live)
- `/help` -- command reference

## Project layout

```
bot.py                  entrypoint, loads cogs + intents
utils/config.py          theme color, event registry
utils/database.py        SQLite access layer
utils/embeds.py          shared embed builder
utils/views.py           button rows (ID reveal, jump links)
utils/audit.py           audit log lookups for kick/ban attribution
cogs/settings.py         /settings command group
cogs/vote.py             /vote command
cogs/help.py             /help command
cogs/events/*.py         one file per event category
```

## A note on Components V2

You linked the Discord4J Components V2 docs, but this build is on
discord.py per your answer to the language question. discord.py 2.4+ can
send Components V2 layouts (the `IS_COMPONENTS_V2` message flag with
`Container`/`Section` primitives), but that support is newer and less
ergonomic than plain embeds + views -- and mixing it with `discord.Embed`
isn't allowed by Discord (CV2 messages can't use embeds at all). Given you
also asked for embeds that match the Koira screenshot (title, fields,
timestamp, footer, buttons), I built this on standard embeds + persistent
`discord.ui.View` button rows, which is what that screenshot is actually
using. If you'd rather go full Components V2 (no embeds, `Container`-based
layout), say so and I'll rebuild the embed layer -- just flagging it now
instead of guessing.

## Extending

Per-event channel overrides (route one event type to a different channel
than the guild default) are already supported in `utils/database.py` via
`set_event_channel` / `resolve_log_channel` -- they're just not wired up to
a slash command yet since `/settings events` covers the common case. Add a
`/settings override <event> <channel>` command if you want to expose it.
