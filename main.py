import argparse
import json
import os
import time
from typing import Any

import requests
from tabulate import tabulate


def fetch_latest_mods(api_key: str, game_domain_name: str) -> list[dict[str, Any]]:
    headers = {"apikey": api_key, "User-Agent": "Nexus Mods Latest Mods Notifier / v0.1.0"}
    url = f"https://api.nexusmods.com/v1/games/{game_domain_name}/mods/latest_added.json"
    response = requests.get(url, headers=headers)
    return response.json()  # type: ignore[no-any-return]


def send_telegram_message(chat_id: str, text: str, tg_token: str) -> None:
    url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    requests.post(url, data=payload)


def load_state(state_file: str) -> set[int]:
    if os.path.exists(state_file):
        with open(state_file) as f:
            return set(json.load(f))
    else:
        return set()


def save_state(state_file: str, seen_mods: set[int]) -> None:
    with open(state_file, "w") as f:
        json.dump(list(seen_mods), f)


def main(api_key: str, game_domain_name: str, chat_id: str, tg_token: str) -> None:
    state_file = "seen_mods.json"
    seen_mods = load_state(state_file)
    new_mods_data = []

    while True:
        print("Fetching mods...")
        mods = fetch_latest_mods(api_key, game_domain_name)
        for mod in sorted(mods, key=lambda x: x["mod_id"]):
            mod_id = mod["mod_id"]
            if mod_id not in seen_mods:
                if not mod["available"]:
                    print("Mod not available yet, skipping...")
                    continue

                seen_mods.add(mod_id)

                new_mod_data = {
                    "ID": mod_id,
                    "Author": mod["author"],
                    "Name": mod.get("name", "N/A"),
                    "Link": f"https://nexusmods.com/{mod['domain_name']}/mods/{mod['mod_id']}",
                }
                new_mods_data.append(new_mod_data)

                send_telegram_message(
                    chat_id,
                    f"<b>{mod.get('name', 'N/A')}</b>\n{mod['author']} - Version {mod['version']}\nLink:"
                    f" https://nexusmods.com/{mod['domain_name']}/mods/{mod['mod_id']}",
                    tg_token,
                )

        if new_mods_data:
            print("New mods found:")
            print(tabulate(new_mods_data, headers="keys", tablefmt="pretty"))
            new_mods_data.clear()
        else:
            print("No new mods found.")

        print("Sleeping for 5 minutes...")
        save_state(state_file, seen_mods)
        time.sleep(300)


try:
    if __name__ == "__main__":
        parser = argparse.ArgumentParser()
        parser.add_argument("-k", "--api-key", required=True, help="API key for Nexus Mods")
        parser.add_argument("-g", "--game-name", required=True, help="Game domain name for Nexus Mods, eg. 'starfield'")
        parser.add_argument("-c", "--chat-id", required=True, help="Telegram chat ID")
        parser.add_argument("-t", "--tg-token", required=True, help="Telegram bot token")
        args = parser.parse_args()
        main(args.api_key, args.game_name, args.chat_id, args.tg_token)
except KeyboardInterrupt:
    print("\rExiting...")
    exit(0)
