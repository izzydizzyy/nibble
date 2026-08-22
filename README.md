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

## Components V2

Every message the bot sends -- logs, `/settings`, `/vote`, `/help` -- is a
real `discord.ui.LayoutView` (`Container` + `TextDisplay`/`Section`/
`Separator`/`ActionRow`), not an embed. Discord doesn't allow mixing the
two in one message, so there's no `discord.Embed` anywhere in this
codebase -- `utils/layout.py` is the one place that builds these, and
every cog just calls `LogLayout(...)` and does `channel.send(view=...)`.
This needs `discord.py>=2.6.0`; CV2 support landed there.

## Emojis

`utils/emojis.py` is the single place every emoji lives, keyed by event
name (`message_delete`, `member_kick`, etc). It ships with Unicode
defaults so the bot works with zero setup. To use emoji.gg art instead:
custom emojis only get a usable Discord ID once they're uploaded to a
server your bot can see -- emoji.gg hosts the image files, not IDs -- so
pull art from categories like [Mod](https://emoji.gg/emojis/mod),
[Shield](https://emoji.gg/emojis/shield), or [Ban](https://emoji.gg/emojis/ban),
upload each to your server (Server Settings -> Emoji), and paste the
resulting `<:name:id>` string into the matching key in that file. Nothing
else needs to change.

## Extending

Per-event channel overrides (route one event type to a different channel
than the guild default) are already supported in `utils/database.py` via
`set_event_channel` / `resolve_log_channel` -- they're just not wired up to
a slash command yet since `/settings events` covers the common case. Add a
`/settings override <event> <channel>` command if you want to expose it.
