# Bruce Lee leftovers

The original memory image of Bruce Lee holds blocks that the game does not need: bytes left by the development
(older builds, source text, the assembler symbol table, the music file, uninitialised RAM) and the last stage of the
original protected loader. The game source in [src/](../src/) leaves these blocks out. This folder keeps them as
generated ACME sources, one folder per knowledge space, so that the bytes are preserved and documented.

What the blocks are and what they tell about the development: [docs/leftovers.md](../docs/leftovers.md).

| Folder | Space | Range | Origin | What it holds |
|---|---|---|---|---|
| [build_10f8_63ea/](build_10f8_63ea/main.asm) | bank1 | `$10F8-$63EA` | development | The reversed vector routine, unused texts, Atari key codes, the shifted copies at +`$7BC` and +`$A3B`, the assembler source text, the old sprite masks PLANTB / PLEORTB, the frame ADWONL22. |
| [build_8180_8fff/](build_8180_8fff/main.asm) | bank2 | `$8180-$8FFF` | development (the tool: unknown) | The old room charsets C and A, the end of room map 19, the C64 bitmap tool fragment, the assembler symbol table. |
| [key_page_cf00/](key_page_cf00/main.asm) | bank3 | `$CF00-$CFFF` | unknown | The bytes of the protection key page that no check reads (power-on RAM). |
| [build_e009_f5ff/](build_e009_f5ff/main.asm) | bank4 | `$E009-$F5FF` | development | Uninitialised RAM, the MicroPearl music file header, the old voice 0, song 1, old effect streams, old code pages, the old demo recording. |
| [original_loader_stage_encoded/](original_loader_stage_encoded/main.asm) | bank6 | `$033C-$038E` | original release | The last stage of the original protected loader, encoded, as the release file carries it. |
| [original_loader_stage/](original_loader_stage/main.asm) | bank7 | `$033C-$038E` | original release | The same stage, decoded: the `$0080` RTS mark, the decrypting mover, the start of the game. |

- In each space, the ranges that belong to the game are `!fill` lines of zeros (files `*_game_*.asm`); the game
  bytes are in `src/`.
- The space bank5 (`$FE00-$FFF9`, a tape turbo loader and a RAM-under-ROM utility) is crack or release tooling, not
  development. It is deliberately not generated here.
- The crack intro, mover and relocator are not kept.

## Rebuild

The sources are generated from the knowledge. Do not edit them: change the knowledge and generate again. From the
workspace root:

```
node .claude/skills/c64-source/scripts/generate.ts --project bruce_lee --space bank1 --out leftovers/build_10f8_63ea
node .claude/skills/c64-source/scripts/generate.ts --project bruce_lee --space bank2 --out leftovers/build_8180_8fff
node .claude/skills/c64-source/scripts/generate.ts --project bruce_lee --space bank3 --out leftovers/key_page_cf00 --entry '$cf00'
node .claude/skills/c64-source/scripts/generate.ts --project bruce_lee --space bank4 --out leftovers/build_e009_f5ff
node .claude/skills/c64-source/scripts/generate.ts --project bruce_lee --space bank6 --out leftovers/original_loader_stage_encoded --entry '$033c'
node .claude/skills/c64-source/scripts/generate.ts --project bruce_lee --space bank7 --out leftovers/original_loader_stage
```

Each `main.asm` assembles with ACME (`acme -f plain -o out.bin main.asm` in its folder) to the bytes of the image
in the leftover ranges.

The scenario [tests/leftovers_unused.json](../tests/leftovers_unused.json) shows that the game needs none of these
bytes: it fills every leftover block with `$A5` at the game entry, and the game behaves the same at all 10
checkpoints.
