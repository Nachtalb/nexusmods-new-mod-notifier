import atexit
import readline
import subprocess
import sys
from pathlib import Path

from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import IniLexer

readline.parse_and_bind("tab: complete")
readline.parse_and_bind("set editing-mode vi")
readline.set_completer_delims(" \t\n;")
readline.set_history_length(1000)
readline.set_auto_history(True)

if Path(".history").exists():
    readline.read_history_file(".history")
else:
    Path(".history").touch()
h_len = readline.get_current_history_length()


def save(prev_h_len: int, histfile: str) -> None:
    new_h_len = readline.get_current_history_length()
    readline.set_history_length(1000)
    readline.append_history_file(new_h_len - prev_h_len, histfile)


atexit.register(save, h_len, ".history")


def run_command(command: list[str]) -> None:
    try:
        printc(f"{' '.join(command)}", "33")
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError:
        print(f"❌ Failed to run command: {command}")


def save_with_privileges_check(file_path: Path, content: str) -> None:
    try:
        file_path.write_text(content)
        print(f"✅ Saved to {file_path}")
    except PermissionError:
        print(f"⚠️ Permission denied: {file_path}")
        if input("🔑 Retry with sudo? [Y/n]: ").lower().startswith("y"):
            try:
                command = ["sudo", "tee", str(file_path)]
                printc(f"{' '.join(command)}", "33")
                subprocess.run(command, input=content, text=True, check=True)
                print(f"✅ Saved to {file_path} with sudo")
            except subprocess.CalledProcessError:
                print("❌ Failed to save with sudo")


def required_input(prompt: str) -> str:
    while True:
        value = input(prompt)
        if value:
            return value
        print("❌ This field is required.")


def printc(text: str, color: str = "32") -> None:
    print(f"\033[{color}m{text}\033[0m")


def main() -> None:
    print("\n🔥 Systemd Service File Generator for NexusMods Notifier 🔥")
    print("=" * 80)

    print("\n👉 Default values are inside square brackets [].")
    print("👉 Press 'Enter' to use the default value.")
    print("=" * 80, "\n")

    sub_command_choice = input("🔧 Do you want updates for new mods or for updated mods? [ADDITIONS/updates]: ")
    if (sub_command_choice or "a").lower().startswith("a"):
        sub_command = "additions"
    else:
        sub_command = "updates"

    printc(sub_command)

    api_key = required_input("🔑 Enter your NexusMods API key: ")
    printc(api_key)
    telegram_token = required_input("🔑 Enter your Telegram bot token: ")
    printc(telegram_token)
    telegram_chat_id = required_input("🔑 Enter your Telegram chat ID: ")
    printc(telegram_chat_id)

    telegram_group_topic_id = input("💬 Enter your Telegram group topic ID [leave empty if not using groups topics]: ")
    if telegram_group_topic_id:
        printc(telegram_group_topic_id)

    game_name = "starfield"
    game_name = input(f"🎮 Enter the name of the game [{game_name}]: ") or game_name
    printc(game_name)

    hide_adult_content = (input("🔞 Hide adult content? [y/N]: ") or "n").lower().startswith("y")
    printc(f"{hide_adult_content}")

    print("=" * 80)

    service_name = f"nexusmods-notifier-{game_name}-{sub_command}"
    service_name = input(f"📛 Enter the name of the service [{service_name}]: ") or service_name
    printc(service_name)

    service_description = f"NexusMods Notifier service for {game_name} " + (
        "for new mods" if sub_command == "additions" else "for updated mods"
    )
    service_description = (
        input(f"📝 Enter a description for the service [{service_description}]: ") or service_description
    )
    printc(service_description)

    python_bin = sys.executable
    while True:
        python_bin = input(f"🐍 Path to the Python binary [{python_bin}]: ") or python_bin
        if "poetry" not in python_bin:
            print("⚠️ WARNING: Using a non-poetry Python binary might cause issues.")
            print("👉 Consider using a poetry Python binary.")
            if not input("Continue? [y/N]: ").lower().startswith("y"):
                continue
        break
    printc(python_bin)

    main_file = Path(__file__).resolve().parent / "main.py"
    while True:
        main_file = Path(input(f"📄 Path to the main Python script [{main_file}]: ") or main_file)
        if not main_file.exists():
            print(f"❌ ERROR: Could not find main file {main_file}")
            continue
        break
    printc(f"{main_file}")

    arguments = f'-l -k "{api_key}" -t "{telegram_token}" -c "{telegram_chat_id}" -g "{game_name}" '
    if telegram_group_topic_id:
        arguments += f'-o "{telegram_group_topic_id}" '
    if hide_adult_content:
        arguments += "-a "
    arguments += sub_command

    systemd_template = f"""[Unit]
Description={service_description}
After=network.target

[Service]
Type=simple
WorkingDirectory={main_file.parent}
ExecStart={python_bin} {main_file} {arguments}
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""

    print("-" * 80)

    timer_in_s = 300 if sub_command == "additions" in arguments else 3600
    while True:
        timer_in_s_str = input(f"⏳ Timer interval in seconds [{timer_in_s}]: ") or timer_in_s
        try:
            timer_in_s = int(timer_in_s_str)
            break
        except ValueError:
            print(f"❌ ERROR: Invalid timer interval: {timer_in_s_str}")
    printc(f"{timer_in_s}s")

    timer_description = f"Timer for {service_description}"
    timer_description = input(f"📝 Timer description [{timer_description}]: ") or timer_description
    printc(timer_description)

    timer_name = f"{service_name}.timer"
    timer_name = input(f"🔖 Timer name [{timer_name}]: ") or timer_name
    printc(timer_name)

    timer_template = f"""[Unit]
Description={timer_description}

[Timer]
OnBootSec=1min
OnUnitActiveSec={timer_in_s}s
Unit={service_name}.service

[Install]
WantedBy=timers.target
"""

    print("=" * 80)

    requires_sudo = False
    while True:
        save_location = Path.home() / ".config/systemd/user/"
        save_location = Path(input(f"📂 Enter the path to save the files to [{save_location}]: ") or save_location)
        printc(f"{save_location}")

        if save_location == Path("/etc/systemd/system/"):
            requires_sudo = True

        elif save_location not in (Path.home() / ".config/systemd/user/", Path("/etc/systemd/system/")):
            print("⚠️ WARNING: You are saving the files to a non-standard location.")
            print("👉 Consider saving the files to ~/.config/systemd/user/ or /etc/systemd/system/.")
            if not input("Continue? [y/N]: ").lower().startswith("y"):
                continue
            else:
                if input("🔑 Do you need sudo to save files to this location? [y/N]: ").lower().startswith("y"):
                    requires_sudo = True
        break

    print("=" * 80)
    print(highlight(systemd_template, IniLexer(), TerminalFormatter()))
    print("=" * 80)

    if (input("💾 Save the service file? [Y/n]: ") or "y").lower().startswith("y"):
        service_file = save_location / f"{service_name}.service"
        service_file.parent.mkdir(parents=True, exist_ok=True)
        save_with_privileges_check(service_file, systemd_template)
    else:
        print("❌ Service file not saved.")

    print("=" * 80)
    print(highlight(timer_template, IniLexer(), TerminalFormatter()))
    print("=" * 80)

    if (input("💾 Save the timer file? [Y/n]: ") or "y").lower().startswith("y"):
        timer_file = save_location / f"{service_name}.timer"
        save_with_privileges_check(timer_file, timer_template)
    else:
        print("❌ Timer file not saved.")

    print("=" * 80)

    # Damon reload
    if (input("🔃 Reload daemon? [Y/n]: ") or "y").lower().startswith("y"):
        try:
            if requires_sudo:
                run_command(["sudo", "systemctl", "daemon-reload"])
            else:
                run_command(["systemctl", "--user", "daemon-reload"])
            print("✅ Daemon reloaded")
        except subprocess.CalledProcessError:
            print("❌ Failed to reload daemon")
    else:
        print("❌ Daemon not reloaded")

    # Enable timer
    if (input("🔃 Enable timer? [Y/n]: ") or "y").lower().startswith("y"):
        try:
            if requires_sudo:
                run_command(["sudo", "systemctl", "enable", "--now", f"{service_name}.timer"])
            else:
                run_command(["systemctl", "--user", "enable", "--now", f"{service_name}.timer"])
            print("✅ Timer enabled")
        except subprocess.CalledProcessError:
            print("❌ Failed to enable timer")
    else:
        print("❌ Timer not enabled")

    print("✅ Done!\n")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n👋 Exiting...")
