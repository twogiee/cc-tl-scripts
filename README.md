# CROSS†CHANNEL VN script

The script of the visual novel CROSS†CHANNEL, developed by FlyingShrine and written by Tanaka Romeo.
The purpose of this project is to gather all of the scripts and translations for this game in one place so they can easily be compared,
warts and all.

One day it would be cool if we ever got a good translation of this game, huh?

Copyright: No copyright infringement intended. No assets are included in this repository that will allow for piracy or other rights infringement.
Please, just buy the game people. It's 10 bucks on Steam.

## Current scripts

- [EN] Amaterasu Translations (Ixrec) (2009)
  - The one I think the majority of EN readers have read. An incredibly literal and very cozy fan translation, but very rough. Think classic 2000s anime
    sub quality.
- [EN] George Henry Shaft (2013)
  - Fever dream translation. Is generally higher in quality, but also more deliberately wrong. I highly recommend reading the internal notes GHS wrote throughout
    the entire script if you want to see the ramblings of a madman. It's kind of fascinating in its own way.
- [EN] Steam Edition (Moenovel) (2018) 
  - The official translation, and surprisingly the worst. Generally drops about 50-80% of everything from the dialogue. I get the impression that whoever was
    contracted to do this gave no fucks and did not really give a shit at keeping any humor, nuance or anything beyond the basic meaning of a sentence.

- [JP] FINAL COMPLETE (2014)
  - The most polished, intended to be complete release. Includes animations and other fancy things. For now, I just have a raw dump to check for differences.

## Planned for inclusion

- [JP] Original release (2003)
- [JP] Reprint edition (2012)
- [JP] For all people (console release) (2014)

## How to Use

### Standard (dsf format)

```
python extract_scripts.py <input directory> <output directory>
```

### Moenovel binary format

```
python extract_moenovel.py raw/moenovel/scripts
```