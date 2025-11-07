# World In Windows

A Dungeons and Dragons management tool

## The Executable

You download the latest release **[here](https://github.com/oscarfIt/World-in-Windows/releases/latest/download/WorldInWindows.exe)**

If you would like to build it yourself from the source code I'm sure you're also savvy enough to figure out.

## Data and Media Directories

World in Windows require the path for **Data** and **Media** directories. This can be set in the app under Settings -> Configure Paths.  
The Data directory is for general information about your specific campaign and should include the following files:
- npcs.json
- locations.json
- spells.json
- items.json
- class_actions.json
- conditions.json

See the corresponding .py files for the structure of these json entries.  
  
The Media directory is for stat block images from the monster manual (or custom) and spell/item images. It should contain the following subdirectories:
- Spells
- MonsterManual
- NPCs
- Image References  (WIP for AI generated images, see below)

These file names should be match the spell/npc/monstermanual name, but replace spaces with underscores and convert to all lowercase (e.g. *Steve the Hobhoblin* -> *steve_the_hobgoblin*).

## Image and Sound Generation

To do this I'm afraid you must have a Stability AI API key (and some credits obviously). Then set a path variable, STABILITY_API_KEY, to this key.