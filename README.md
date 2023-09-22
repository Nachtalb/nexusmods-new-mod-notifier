# Nexus Mods Latest Mods Notifier

## Description

This script fetches the latest mods from Nexus Mods for a specific game and
notifies you via Telegram.

Managed by Poetry. See `pyproject.toml` and `poetry.lock` for version info.

## Setup

1. Install the required Python packages using Poetry:
   ```sh
   poetry install
   ```
2. Get your API key from Nexus Mods and Telegram bot token.

## Usage

Run the script using the following command:

```sh
python main.py -k API_KEY -g GAME_NAME -c CHAT_ID -t TG_TOKEN [-a]
```

### Arguments

- `-k, --api-key`: API key for Nexus Mods. (Required)
- `-g, --game-name`: Game domain name for Nexus Mods, e.g., 'starfield'.
  (Required)
- `-c, --chat-id`: Telegram chat ID. (Required)
- `-t, --tg-token`: Telegram bot token. (Required)
- `-a, --hide-adult-content`: Flag to hide adult content. (Optional)

## Exit

Press `Ctrl+C` to exit the script.

## License

LGPL 3.0
