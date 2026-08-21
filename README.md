# 🐱 Nibble — Discord Economy & Collecting Bot

## Layout
```
nibble/
├── main.py            # entry point, logging, cog loader, error handler
├── config.py          # loads .env
├── database.py        # all SQL lives here (aiosqlite)
├── game_data.py        # fish species, rarities, rods — edit this to rebalance
├── utils/rolls.py      # weighted fish roll logic
├── cogs/
│   ├── core.py         # /balance /daily /profile
│   ├── fishing.py      # /fish
│   ├── inventory.py    # /inventory /collection /sell /sell-all
│   └── economy.py      # /shop /buy /leaderboard
├── data/nibble.db      # sqlite file (created automatically)
├── logs/               # rotating log files (created automatically)
└── deploy/nibble.service  # systemd unit for EC2
```

## Gameplay loop (V1)
Fish → discover a species → grow your collection → sell duplicates →
save up → buy a better rod → unlock rarer fish → repeat, then climb the
leaderboards. Trading, quests, achievements, minigames, and timed events
are the natural V2 additions — the schema (`trades` table, `inventory`
quantities) is already laid out for trading; I left it out of V1 wiring
since it's the single riskiest anti-abuse surface and deserves its own
pass (see "What's next" below).

## 1. Create the Discord bot
1. https://discord.com/developers/applications → New Application.
2. **Bot** tab → Reset Token → copy it (you'll only see it once).
3. **OAuth2 → URL Generator**: scopes `bot` + `applications.commands`,
   permissions: Send Messages, Embed Links, Use Slash Commands. Open the
   generated URL to invite it to your server.
4. No privileged intents (message content, members, presence) are needed
   for V1 — it's slash-commands only.

## 2. Run it locally
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # paste your bot token in
# optional: set DEV_GUILD_ID to your test server's ID for instant command sync
python3 main.py
```
Global slash command sync can take up to an hour to show up everywhere;
set `DEV_GUILD_ID` while developing so `/fish` etc. appear instantly in
one server.

## 3. Deploy on EC2

**Instance**: Ubuntu 22.04/24.04, t3.micro/t4g.micro is plenty for V1
(low traffic, SQLite, no web server). No inbound ports needed — the bot
only makes outbound connections to Discord, so you don't even need to
open anything in the security group beyond default SSH (22).

```bash
# on the EC2 instance
sudo apt update && sudo apt install -y python3-venv python3-pip git

git clone <your-repo-url> nibble   # or scp the folder up
cd nibble
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
nano .env        # paste DISCORD_TOKEN, leave DEV_GUILD_ID blank for prod

mkdir -p logs data
```

**Run continuously with systemd** (survives reboots and crashes):
```bash
sudo cp deploy/nibble.service /etc/systemd/system/nibble.service
sudo nano /etc/systemd/system/nibble.service   # fix User/paths if not "ubuntu"/"/home/ubuntu/nibble"
sudo systemctl daemon-reload
sudo systemctl enable --now nibble
sudo systemctl status nibble        # confirm it's active (running)
journalctl -u nibble -f             # tail logs live
```

To ship an update later:
```bash
cd ~/nibble && git pull   # or re-upload changed files
sudo systemctl restart nibble
```

**Backups**: `data/nibble.db` is the entire game state. Cron a nightly
copy somewhere durable, e.g.:
```bash
0 4 * * * cp /home/ubuntu/nibble/data/nibble.db /home/ubuntu/nibble/data/backup-$(date +\%F).db
```

## What's next (not built yet, on purpose)
- **Trading** (`/trade`): the `trades` table exists in `database.py` but
  there's no cog for it yet. It needs a confirm-both-sides flow with a
  Discord View/buttons and careful locking so neither side can back out
  after the other confirms — worth its own focused session rather than
  bolting on quickly.
- **Quests / achievements / events**: layer cleanly on top of the
  existing `inventory`/`users` tables once the core loop is validated
  with real players.
- **Postgres migration**: `database.py` is the only file with SQL in it,
  so swapping `aiosqlite` for `asyncpg` and `?` placeholders for `$1`
  style is contained to that one file.
