While browsing the Internet, I still haven’t found any +-convenient tools to patch CS:GO and give the game a modified code.pbin. Of course, this topic has been raised on cheating forums - code.pbin can be changed by patching the panorama.dll file.

Using material from https://www.unknowncheats.me/forum/counterstrike-global-offensive/287000-panorama-checks-code-pbin.html I was able to write a small script that can unpack code.pbin, pack code.pbin and patch panorama.dll to launch the game without injection in runtime.

# Usage
## Installation
### First option:
Install the latest version of Python.

Download the entire contents of the repository and put it in the path `<CS:GO root>/csgo/panorama/`.

To use the script, open a terminal in the same folder as the script and run it using `python pbin.py`

### Second option:
Download `pbin.exe` from releases, from the repository download `code.pbin.end`. Place these both files in `<CS:GO root>/csgo/panorama/`, to use, open a terminal in the same folder with the program and run it using `pbin.exe`

## Patching panorama.dll
Make sure that the script is located on the path `<CS:GO root>/csgo/panorama/`.

Run the following commands
```bash
# If you downloaded the Python script
python pbin.py patch_panorama

# If you downloaded an executable program
./pbin.exe patch_panorama
```

## Unpacking code.pbin
For convenience, rename your original `code.pbin` to `_code.pbin`.
Run the following commands
```bash
# If you downloaded the Python script
python pbin.py unpack _code.pbin

# If you downloaded an executable program
./pbin.exe unpack _code.pbin
```

## Packaging code.pbin
First, extract the original code.pbin if you haven't already.
Make any acceptable changes to the panorama code.

Run the following commands
```bash
# If you downloaded the Python script
python pbin.py pack

# If you downloaded an executable program
./pbin.exe pack
```

# glhf
