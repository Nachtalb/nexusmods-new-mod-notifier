import argparse
import asyncio
import json
import re
import time
from pathlib import Path
from typing import Any, Literal

from aiohttp import ClientSession
from tabulate import tabulate

class NM:
    def __init__(self, api_key: str, session: ClientSession) -> None:
        self.api_key = api_key
        self.session = session

    async def _nm_request(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        headers = {
            "apikey": self.api_key,
            "User-Agent": "NexusMods Notifier/0.2.0 (+https://github.com/Nachtalb/nexusmods-notifier)",
        }
        url = f"https://api.nexusmods.com/v1/{endpoint}"
        async with  self.session.get(url, headers=headers, params=params) as response:
            return await response.json()


    async def fetch_games(self) -> list[dict[str, Any]]:
        return await self._nm_request("games.json", {"include_unapproved": "false"})  # type: ignore[no-any-return]


    async def game_categories(self, game_domain_name: str) -> dict[int, Any]:
        cache_file = Path("game_categories.json")
        if (cache := load_state(cache_file)) and game_domain_name in cache:
            return {int(id): value for id, value in cache[game_domain_name].items()}

        games = await self.fetch_games()
        cache = {
            game["domain_name"]: {category["category_id"]: category["name"] for category in game["categories"]}
            for game in games
        }
        save_state(cache_file, cache)
        return cache[game_domain_name]  # type: ignore[no-any-return]


    async def fetch_latest_mods(self, game_domain_name: str) -> list[dict[str, Any]]:
        return await self._nm_request(f"games/{game_domain_name}/mods/latest_added.json")  # type: ignore[no-any-return]


    async def fetch_tracked_mods(self, game_domain_name: str = "") -> list[dict[str, Any]]:
        mods: list[dict[str, Any]] = await self._nm_request("user/tracked_mods.json")
        if game_domain_name:
            mods = [mod for mod in mods if mod["domain_name"] == game_domain_name]
        return mods


    async def fetch_mod(self, game_domain_name: str, mod_id: int) -> dict[str, Any]:
        return await self._nm_request(f"games/{game_domain_name}/mods/{mod_id}.json")  # type: ignore[no-any-return]


    async def fetch_updated_mods(
        self, game_domain_name: str, time_period: Literal["1d", "1w", "1m"] = "1w"
    ) -> list[dict[str, Any]]:
        return await self._nm_request(  # type: ignore[no-any-return]
            f"games/{game_domain_name}/mods/updated.json",
            params={"period": time_period},
        )


    async def fetch_mod_changelogs(self, game_domain_name: str, mod_id: int) -> dict[str, list[str]]:
        return await self._nm_request(f"games/{game_domain_name}/mods/{mod_id}/changelogs.json")  # type: ignore[no-any-return]



class TG:
    def __init__(self, session: ClientSession, tg_token: str) -> None:
        self.session = session
        self.tg_token = tg_token


    async def _tg_request(self, endpoint: str, data: dict[str, Any] | None = None) -> Any:
        if data:
            data= {key: value for key, value in data.items() if value is not None}
        url = f"https://api.telegram.org/bot{self.tg_token}/{endpoint}"
        async with self.session.post(url, data=data) as response:
            return await response.json()

    async def send_message(self, chat_id: int | str, text: str, topic_id: int | str | None = None, disable_web_page_preview: bool = False) -> None:
        data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": disable_web_page_preview}
        if topic_id:
            data["message_thread_id"] = topic_id
        await self._tg_request("sendMessage", data=data)



def load_state(state_file: str | Path) -> Any:
    state_file = Path(state_file)
    if state_file.is_file():
        return json.loads(state_file.read_text())


def save_state(state_file: str | Path, seen_mods: Any) -> None:
    Path(state_file).write_text(json.dumps(seen_mods))


def tagify(text: str) -> str:
    return "#" + re.sub(r"[ -/]", "_", re.sub(r",", "", text)).lower()


async def additions(
    session: ClientSession,
    api_key: str,
    game_domain_name: str,
    chat_id: str,
    tg_token: str,
    hide_adult_content: bool,
    loop: bool,
    topic_id: str,
    frequency: int,
) -> None:
    state_file = "seen_mods.json"
    seen_mods: set[int] = set(load_state(state_file) or [])  # pyright: ignore[reportGeneralTypeIssues]
    new_mods_data = []
    nm = NM(api_key, session)
    tg = TG(session, tg_token)
    categories = await nm.game_categories(game_domain_name)

    while True:
        print("Starting new mod check...")
        mods = await nm.fetch_latest_mods(api_key)
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
                    "Cagegory": categories[mod["category_id"]],
                    "Link": f"https://nexusmods.com/{mod['domain_name']}/mods/{mod['mod_id']}",
                }
                new_mods_data.append(new_mod_data)

                if tg_token:
                    await tg.send_message(
                        chat_id=chat_id,
                        text=(
                            "<b><a"
                            f" href=\"https://nexusmods.com/{mod['domain_name']}/mods/{mod['mod_id']}\">"
                            f"{mod.get('name', 'N/A')}</a></b>\n{mod['author']} -"
                            f" Version {mod['version']}\n{tagify(categories[mod['category_id']])}"
                        ),
                        topic_id=topic_id,
                    )

        if new_mods_data:
            print("New mods found:")
            print(tabulate(new_mods_data, headers="keys", tablefmt="pretty"))
            new_mods_data.clear()
        else:
            print("No new mods found.")

        save_state(state_file, list(seen_mods))
        if loop:
            print(f"Sleeping for {frequency / 60} minute/s...")
            time.sleep(frequency)
        else:
            break


async def updates(
    session: ClientSession,
    api_key: str,
    game_domain_name: str,
    chat_id: str,
    tg_token: str,
    hide_adult_content: bool,
    loop: bool,
    topic_id: str,
    frequency: int,
) -> None:
    nm = NM(api_key, session)
    tg = TG(session, tg_token)
    cache_file_path = "update_cache.json"
    local_cache: dict[int, dict[str, Any]] = {
        int(mod_id): value for mod_id, value in (load_state(cache_file_path) or {}).items()
    }
    tracked_mod_ids: set[int] = set()
    categories = await nm.game_categories(game_domain_name)

    mods_with_new_version: list[dict[str, Any]] = []

    # Initial population of tracked mods (do this carefully to stay within API limits)
    if not local_cache:
        print("Fetching initial list of tracked mods...")
        updated_mods = await nm.fetch_updated_mods(game_domain_name)
        updated_mod_data = {mod["mod_id"]: mod["latest_file_update"] for mod in updated_mods}

        tracked_mods = await nm.fetch_tracked_mods(game_domain_name)
        tracked_mod_ids = {mod["mod_id"] for mod in tracked_mods}
        for mod_id in tracked_mod_ids:
            mod_info = await nm.fetch_mod(game_domain_name, mod_id)
            local_cache[mod_id] = {
                "version": mod_info["version"],
                "is_adult": mod_info["contains_adult_content"],
                "latest_file_update": updated_mod_data.get(mod_id, None),
            }
        save_state(cache_file_path, local_cache)
        print("Initial population of tracked mods complete.")

    while True:
        new_mods = []
        try:
            print("Starting update check...")
            # Fetch list of all recently updated mods
            updated_mods = await nm.fetch_updated_mods(game_domain_name)
            updated_mod_data = {mod["mod_id"]: mod["latest_file_update"] for mod in updated_mods}

            # Refresh the list of tracked mods
            tracked_mods = await nm.fetch_tracked_mods(game_domain_name)
            tracked_mod_ids = {mod["mod_id"] for mod in tracked_mods if not hide_adult_content or not mod["is_adult"]}

            for mod_id in tracked_mod_ids:
                cached_latest_file_update: int | None = local_cache.get(mod_id, {}).get("latest_file_update", None)
                new_latest_file_update: int | None = updated_mod_data.get(mod_id, None)

                if mod_id not in local_cache:
                    print(f"Tracking new mod [id={mod_id}], fetching...")
                    mod_details = await nm.fetch_mod(game_domain_name, mod_id)
                    local_cache[mod_id] = {
                        "version": mod_details["version"],
                        "latest_file_update": new_latest_file_update,
                        "is_adult": mod_details["contains_adult_content"],
                    }
                    new_mods.append(
                        {
                            "Author": mod_details["author"],
                            "Name": mod_details["name"],
                            "Link": f"https://nexusmods.com/{game_domain_name}/mods/{mod_id}",
                        }
                    )
                    continue

                # If the latest_file_update has changed or is new, there might be a new version
                if new_latest_file_update and cached_latest_file_update != new_latest_file_update:
                    mod_details = await nm.fetch_mod(game_domain_name, mod_id)
                    new_version = mod_details["version"]
                    old_version = local_cache.get(mod_id, {}).get("version", None)

                    if old_version and new_version and old_version != new_version:
                        print(f"Mod [id={mod_id}] has been updated to from {old_version} to {new_version}")
                        changelogs = await nm.fetch_mod_changelogs(game_domain_name, mod_id)
                        last_version_index = (
                            list(changelogs.keys()).index(old_version) if old_version in changelogs else -2
                        )

                        new_versions = dict(list(changelogs.items())[last_version_index + 1 :])

                        changelog_text = "\n".join(
                            "<b>{}</b>\n- {}".format(version, "\n- ".join(changelog))
                            for version, changelog in new_versions.items()
                        )

                        if tg_token:
                            await tg.send_message(
                                chat_id=chat_id,
                                text=(
                                    f'<b><a href="https://nexusmods.com/{game_domain_name}/mods/{mod_id}">'
                                    f'{mod_details["name"]}</a></b>\n{mod_details["author"]} - Version {old_version} ->'
                                    f' {new_version}\n{tagify(categories[mod_details["category_id"]])}\n\n'
                                    f"Changelog:\n{changelog_text}"
                                ),
                                topic_id=topic_id,
                            )

                        for version in new_versions:
                            mods_with_new_version.append(
                                {
                                    "ID": mod_id,
                                    "Author": mod_details["author"],
                                    "Name": mod_details["name"],
                                    "Category": categories[mod_details["category_id"]],
                                    "Link": f"https://nexusmods.com/{mod_details['domain_name']}/mods/{mod_id}",
                                    "Old Version": old_version or "N/A",
                                    "New Version": version,
                                }
                            )

                    local_cache[mod_id] = {
                        "version": new_version,
                        "latest_file_update": new_latest_file_update,
                        "is_adult": mod_details["contains_adult_content"],
                    }

            save_state(cache_file_path, local_cache)
            if new_mods:
                message = "New mods found:\n" + "\n".join(
                    f'<a href="{mod["Link"]}">{mod["Name"]}</a> - {mod["Author"]}\n'
                    for mod in new_mods
                )
                await tg.send_message(
                    chat_id=chat_id,
                    text=message,
                    topic_id=topic_id,
                    disable_web_page_preview=True,
                )

        except Exception as e:
            print(f"An error occurred: {e}")

        if mods_with_new_version:
            print("Updated mods:")
            print(tabulate(mods_with_new_version, headers="keys", tablefmt="pretty"))
            mods_with_new_version.clear()
        else:
            print("No updated mods found.")

        if loop:
            print(f"Sleeping for {frequency / 60 / 60} hour/s...")
            time.sleep(frequency)
        else:
            break

async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-k", "--api-key", required=True, help="API key for Nexus Mods")
    parser.add_argument("-g", "--game-name", required=True, help="Game domain name for Nexus Mods, eg. 'starfield'")
    parser.add_argument("-c", "--chat-id", help="Telegram chat ID")
    parser.add_argument("-t", "--tg-token", help="Telegram bot token")
    parser.add_argument("-o", "--topic-id", help="Telegram group topic ID", default="")
    parser.add_argument("-a", "--hide-adult-content", action="store_true", help="Hide adult content", default=False)
    parser.add_argument("-l", "--no-loop", action="store_true", help="Don't loot forever", default=False)
    parser.add_argument(
        "-f",
        "--frequency",
        help="Frequency of checks (defaults: 300s new mods, 3600s (1h) updates)",
        default=0,
        type=int,
    )

    sub_parser = parser.add_subparsers(dest="command")
    sub_parser.required = True

    additions_parser = sub_parser.add_parser("additions", help="Get updates for new mods")
    additions_parser.set_defaults(command="additions")

    updates_parser = sub_parser.add_parser("updates", help="Get updates for new updates")
    updates_parser.set_defaults(command="updates")

    args = parser.parse_args()

    if (args.tg_token or args.chat_id) and (not args.tg_token or not args.chat_id):
        print("Both chat ID and Telegram token must be provided")
        exit(1)

    if not args.tg_token:
        print("Telegram token not provided, not sending messages")

    async with ClientSession() as session:
        match args.command:
            case "additions":
                await additions(
                    session=session,
                    api_key=args.api_key,
                    game_domain_name=args.game_name,
                    chat_id=args.chat_id,
                    tg_token=args.tg_token,
                    hide_adult_content=args.hide_adult_content,
                    loop=not args.no_loop,
                    topic_id=args.topic_id,
                    frequency=args.frequency or 300,
                )
            case "updates":
                await updates(
                    session=session,
                    api_key=args.api_key,
                    game_domain_name=args.game_name,
                    chat_id=args.chat_id,
                    tg_token=args.tg_token,
                    hide_adult_content=args.hide_adult_content,
                    loop=not args.no_loop,
                    topic_id=args.topic_id,
                    frequency=args.frequency or 3600,
                )
            case _:
                print("Invalid command")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\rExiting...")
        exit(0)
