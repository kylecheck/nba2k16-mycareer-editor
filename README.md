# NBA 2K16 MyCareer Editor

A simple native editor for **offline MyCareer**. Built by **Kyle Check**, with coding assistance from **OpenAI Codex**.

Dark NBA 2K-inspired menus, yellow sliders, and no browser or complicated memory-scanning interface.

## What it does

- Finds the running game and your active MyCareer player.
- Height up to **10 feet**, displayed in feet and inches.
- Height and wingspan sliders that snap to one-inch steps.
- Weight and visual arm length.
- Individual attributes and **Max attributes**.
- Individual badges and **All badges** (Gold skill badges, personality badges On).
- **Undo last apply**.

## Downloads and status

**[Download the latest release](https://github.com/kylecheck/nba2k16-mycareer-editor/releases/latest)**. Choose `NBA2K16-Linux.zip` for Steam Deck/Linux or `NBA2K16-Windows-x64-preview.zip` for Windows. Extract the ZIP before opening the app.

| Platform | Status | Start |
|---|---|---|
| Steam Deck / Linux x64 | Game-tested by Kyle on Steam Deck | `Launch.sh` |
| Windows x64 | Preview; needs a Windows game test | `Launch-Windows.bat`, or the packaged executable when available |

**Compatibility is limited to one verified NBA2K16 executable build.** This is not a universal trainer for every patch, Steam release, or repack. The editor checks the loaded executable before enabling edits. It works with Kyle's non-Steam copy through Proton; that does not establish compatibility with other copies.

## Steam Deck: quick start

1. Switch to Desktop Mode and extract the Linux download into a folder.
2. Start NBA 2K16 and load your MyCareer in your gym/loading area.
3. Run `Launch.sh` in Konsole. If needed, right-click it and choose a terminal/run option.
4. Select the actual `NBA2K16.exe` process and press **Connect**.
5. If access is denied, press **Enable memory access**, approve the system prompt, then connect again.
6. Change your settings and press **Apply changes**.

Python 3 is required. The app uses Tk when available and a native X11 fallback otherwise. No pip packages are needed for Linux use.

## Windows: quick start (preview)

For the source download: install **64-bit Python 3.12 or later**, including **Tcl/Tk**, then double-click `Launch-Windows.bat`.

For the packaged Windows release: extract its whole folder and open `NBA2K16-MyCareer-Editor.exe`. Python installation is not needed. The package passes automated Windows tests and an executable startup check; live game testing is still needed.

Start the game, load your MyCareer, select `NBA2K16.exe`, Connect, change settings and Apply. **Enable memory access** restarts the editor with a Windows administrator prompt; select the process and reconnect in the new window.

## A few things to know

- Back up your MyCareer save before editing. The editor writes live memory; it does not edit save files or game files directly.
- **Max attributes** sets the source table's raw bytes to 255. The conversion to displayed ratings is not established for every field.
- Recorded wingspan and visual arm length are separate controls. Use **Arm length scale** for visibly longer arms.
- Apply height enables the live limit override. Keep the editor open during that session. Closing normally restores its code changes. Kyle confirmed that playing a game and saving retained his edited body values; behavior on another executable/save is unverified.
- Use the game's normal save flow. Undo reverses the last apply, not a save already written by the game.
- If you change careers, restart the game, or load another player, reconnect. Identity and pointer checks prevent applying to a stale player.
- The permanent on-disk patch from experimental version 1.1 has been removed. This release does not modify executables.

## Troubleshooting

**Access denied:** use Enable memory access and reconnect. On Windows, run the editor at the same permission level as the game.

**No matching image:** choose the actual game process, not a Steam/Proton wrapper. If it still fails, your executable may be a different build. Do not substitute guessed offsets.

**Player not loaded:** finish loading MyCareer and reconnect from the gym. No player-stats screen is required.

**Visual body change is delayed:** leave and re-enter the scene so the game can rebuild the player model.

**Report a problem:** include platform, editor version, game build and the exact error. Do not upload game executables, save files, personal paths, or private logs to public issues.

## Development

Python standard library only at runtime.

API references: [ReadProcessMemory](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-readprocessmemory), [VirtualProtectEx](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-virtualprotectex), and [PyInstaller runtime information](https://pyinstaller.org/en/stable/runtime-information.html). Windows uses documented Win32 process-memory APIs; Linux uses `/proc`. UI and player logic are shared so fixes can reach both platforms.

```sh
python -m unittest discover -s tests -v
python app.py
```

GitHub Actions runs platform tests and can build a Windows x64 folder package with PyInstaller. The Windows preview must pass a real NBA 2K16 session before being marked stable.

To publish an update, change `VERSION` to a new version (for example `v1.3`) and push to `main`. After tests and both builds pass, GitHub Actions publishes the new release with both downloads. Existing releases are preserved; ordinary pushes without a version change do not replace them.

## Credits and license

Product direction, UI feedback and live Steam Deck testing: **Kyle Check**. Implementation assistance: **OpenAI Codex**. Field names and mappings were informed by the supplied `Nba2k16-Patch6_V1.0.CT` table; its author was not identified in the supplied material. Original game data, executables and third-party trainers are not included.

The editor implementation is released under the MIT license. NBA 2K16 and its names are owned by their respective holders. This independent project is not affiliated with or endorsed by 2K.
