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


def send_telegram_message(chat_id: str, text: str, tg_token: str, topic_id: str) -> None:
    url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if topic_id:
        payload["message_thread_id"] = topic_id
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


def main(
    api_key: str,
    game_domain_name: str,
    chat_id: str,
    tg_token: str,
    hide_adult_content: bool,
    loop: bool,
    topic_id: str,
) -> None:
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
                    print(f"Mod [id={mod_id}] not available yet, skipping...")
                    continue

                seen_mods.add(mod_id)

                if hide_adult_content and mod["contains_adult_content"]:
                    print("Mod contains adult content, skipping...")
                    continue

                new_mod_data = {
                    "ID": mod_id,
                    "Author": mod["author"],
                    "Name": mod.get("name", "N/A"),
                    "Link": f"https://nexusmods.com/{mod['domain_name']}/mods/{mod['mod_id']}",
                }
                new_mods_data.append(new_mod_data)

                send_telegram_message(
                    chat_id=chat_id,
                    text=(
                        f"<b>{mod.get('name', 'N/A')}</b>\n{mod['author']} - Version {mod['version']}\nLink:"
                        f" https://nexusmods.com/{mod['domain_name']}/mods/{mod['mod_id']}"
                    ),
                    tg_token=tg_token,
                    topic_id=topic_id,
                )

        if new_mods_data:
            print("New mods found:")
            print(tabulate(new_mods_data, headers="keys", tablefmt="pretty"))
            new_mods_data.clear()
        else:
            print("No new mods found.")

        save_state(state_file, seen_mods)
        if loop:
            print("Sleeping for 5 minutes...")
            time.sleep(300)
        else:
            break


try:
    if __name__ == "__main__":
        parser = argparse.ArgumentParser()
        parser.add_argument("-k", "--api-key", required=True, help="API key for Nexus Mods")
        parser.add_argument("-g", "--game-name", required=True, help="Game domain name for Nexus Mods, eg. 'starfield'")
        parser.add_argument("-c", "--chat-id", required=True, help="Telegram chat ID")
        parser.add_argument("-o", "--topic-id", help="Telegram group topic ID", default="")
        parser.add_argument("-a", "--hide-adult-content", action="store_true", help="Hide adult content", default=False)
        parser.add_argument("-l", "--no-loop", action="store_true", help="Don't loot forever", default=False)
        args = parser.parse_args()
        main(
            api_key=args.api_key,
            game_domain_name=args.game_name,
            chat_id=args.chat_id,
            tg_token=args.topic_id,
            hide_adult_content=args.hide_adult_content,
            loop=not args.no_loop,
            topic_id=args.topic_id,
        )
except KeyboardInterrupt:
    print("\rExiting...")
    exit(0)
