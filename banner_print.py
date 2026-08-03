#!/usr/bin/env python3
# Small renderer for the CYBERGHOST banner using colorama for robust terminal colors.

from colorama import init, Fore, Style
init(autoreset=True)

BANNER = [
" /$$$$$$$  /$$   /$$ /$$$$$$$$ /$$$$$$$   /$$$$$$  /$$$$$$$  /$$$$$$  /$$$$$$$  /$$$$$$  /$$$$$$$ ",
"| $$__  $$| $$$ | $$| $$_____/| $$__  $$ /$$__  $$| $$__  $$ /$$__  $$| $$__  $$|_  $$_/ | $$__  $$",
"| $$  \\ $$| $$$$| $$| $$      | $$  \\ $$| $$  \\ $$| $$  \\ $$| $$  \\ $$| $$  \\ $$  | $$   | $$  \\ $$",
"| $$  | $$| $$ $$ $$| $$$$$   | $$$$$$$/| $$  | $$| $$$$$$$/| $$  | $$| $$$$$$$/  | $$   | $$$$$$$/",
"| $$  | $$| $$  $$$$| $$__/   | $$__  $$| $$  | $$| $$__  $$| $$  | $$| $$__  $$  | $$   | $$__  $$",
"| $$  | $$| $$\\  $$$| $$      | $$  \\ $$| $$  | $$| $$  \\ $$| $$  | $$| $$  \\ $$  | $$   | $$  \\ $$",
"|  $$$$$$/| $$ \\  $$| $$$$$$$$| $$  | $$|  $$$$$$/| $$  | $$|  $$$$$$/| $$  | $$ /$$$$$$ | $$  | $$",
" \\______/ |__/  \\__/|________/|__/  |__/ \\______/ |__/  |__/ \\______/ |__/  |__/|______/ |__/  |__/"
]

print(Fore.CYAN + "\n".join(BANNER) + Style.RESET_ALL)
print(Fore.YELLOW + "Decimal ASCII Values: " + Style.BRIGHT + "67 89 66 69 82 71 72 79 83 84")
print(Fore.YELLOW + "Hex (ASCII): " + Style.BRIGHT + "435942455247484F5354\n")
print(Fore.GREEN + "Binary (developer handle): " + Style.BRIGHT + "1010000 1101001 1101110 1101111 1111001 1010101 1101110 1101011 1101110 1101111 1110111 1101110")
print(Fore.MAGENTA + "powered by : " + Fore.CYAN + "TeamWhiteHat " + Fore.WHITE + "x " + Fore.BLUE + "github.com/TeamWHiteHatDev\n")
print("="*60)
print(Fore.CYAN + "Developer: " + Fore.YELLOW + "instagram.com/pinoyunknown")
print(Fore.CYAN + "Purpose: " + Fore.YELLOW + "Create and manage Wi‑Fi hotspots on Linux (GUI via PyQt5 and terminal edition; Python + Bash).")
print("="*60)