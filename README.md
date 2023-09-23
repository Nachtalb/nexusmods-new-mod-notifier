# NexusMods Notifier

## Description

This script fetches information about latest changes for mods on
[NexusMods](https://www.nexusmods.com/) and notifies you via Telegram.

Managed by Poetry. See `pyproject.toml` and `poetry.lock` for version info.

## Setup

1. Install the required Python packages using Poetry:

   ```sh
   poetry install
   ```

2. Get your API key from Nexus Mods and Telegram bot token.

## Usage

Choose your subcommand and get notified.

- `additions`: Newly published mods
- `updates`: Updates to mods you track

If both the Telegram token and Chat ID are omitted, it will not send any
messages via Telegram and act as a CLI only tool.

```txt
usage: main.py [-h] -k API_KEY -g GAME_NAME [-c CHAT_ID] [-t TG_TOKEN]
               [-o TOPIC_ID] [-a] [-l] [-f FREQUENCY]
               {additions,updates} ...

positional arguments:
  {additions,updates}
    additions           Get updates for new mods
    updates             Get updates for new updates

options:
  -h, --help            show this help message and exit
  -k API_KEY, --api-key API_KEY
                        API key for Nexus Mods
  -g GAME_NAME, --game-name GAME_NAME
                        Game domain name for Nexus Mods, eg. 'starfield'
  -c CHAT_ID, --chat-id CHAT_ID
                        Telegram chat ID
  -t TG_TOKEN, --tg-token TG_TOKEN
                        Telegram bot token
  -o TOPIC_ID, --topic-id TOPIC_ID
                        Telegram group topic ID
  -a, --hide-adult-content
                        Hide adult content
  -l, --no-loop         Don't loot forever
  -f FREQUENCY, --frequency FREQUENCY
                        Frequency of checks (defaults: 300s new mods, 3600s
                        (1h) updates)
```

## Exit

Press `Ctrl+C` to exit the script.

## License

LGPL 3.0
