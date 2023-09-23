# Nexus Mods Notifier

## Description

This script fetches information about latest changes for mods on
[Nexus Mods](https://www.nexusmods.com/) and notifies you via Telegram.

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

```sh
python main.py <SUB COMMAND> -k API_KEY -g GAME_NAME -c CHAT_ID -t TG_TOKEN [-a] [-l] [-o TOPIC_ID]
```

### Arguments

- `-h, --help`: Show help message.
- `-k, --api-key`: API key for Nexus Mods. (Required)
- `-g, --game-name`: Game domain name for Nexus Mods, e.g., 'starfield'.
  (Required)
- `-c, --chat-id`: Telegram chat ID. (Required)
- `-o, --thread-id`: Telegram group topic ID. (Optional)
- `-t, --tg-token`: Telegram bot token. (Required)
- `-a, --hide-adult-content`: Flag to hide adult content. (Optional)
- `-l`, `--no-loop`: Don't loot forever. (Optional)

## Exit

Press `Ctrl+C` to exit the script.

## License

LGPL 3.0
