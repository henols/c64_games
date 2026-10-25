# The computer opponent (game_v1)

The computer moves a fighter when no player holds the joystick of that fighter. In the one-player game, the computer controls fighter 1 against the player, from opponent 0 to opponent 7. In the demo, the computer controls both fighters. In each pass, the AI reads the pose of the other fighter and the distance between the fighters. Then it gives one joystick value to its own fighter. The value goes through the same move tables as the joystick of a player, so the computer obeys the same move rules. The AI keeps no plan and no timers. Four tables and one counter select each answer. This page tells how the tables work, how the skill grows with the opponent number, and where the random numbers come from. The project is Part 2, build V 05 05 87.

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge.
- A *pass* is one run of `main_loop`. The loop does not wait for a raster line. A *frame* is one PAL video frame (50 each second).
- *Fighter 0* is the player (joystick port 2). *Fighter 1* is the computer in the one-player game.
- The *watched fighter* is the fighter whose pose the AI reads. The *moved fighter* is the other fighter. It gets the joystick value.
- The *opponent number* is `opponent_index`, 0-7. It is also the *level* of the AI.
- A *pose* is the image number in `fighter_pose`, `$00-$5A`. A *move* is the number in `fighter_move`, `$00-$1D`, written without bit 7. [fighters.md](fighters.md) tells the moves.
- The *distance* is `fighter_distance`, the difference of the two `fighter_x` values in columns of 8 pixels. A *band* is the distance group 0-7 from `distance_bands`.
- A *row list* is 8 bytes, one byte for each band. Each byte selects a *joystick row*. A joystick row holds 8 joystick values, the *columns* 0-7.
- A *column table* holds 32 column numbers for one level. The *index* is the position 0-31 in the column table.
- A *joystick value* has bit 0 up, bit 1 down, bit 2 left, bit 3 right and bit 4 fire. A bit with the value 1 is pressed.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## How it works

~~~mermaid
flowchart TB
  A{"Bout runs? (no walk-in, set-up, turn, time out, loser, final stage)"}
  A -- no --> Z["No input from the AI"]
  A -- yes --> B["Column table of the opponent number"]
  B --> C["Watched fighter: the player, or each fighter in the demo"]
  C --> D["Pose of the watched fighter: row list"]
  D --> E["Distance: band, then joystick row"]
  E --> F["Counter or CIA timers: index, then column"]
  F --> G["Joystick value into the move tables"]
  G --> H{"Demo and one more fighter?"}
  H -- yes --> C
~~~

`main_loop` calls [`ai_choose_moves` `$870C`](../src/ai/computer_moves.asm#L6) one time in each pass, directly after `read_joysticks`. The routine does these steps (**Code**):

1. **The checks.** It returns at once when bit 7 of `turn_request`, `bout_loser`, `walk_in_active`, `setup_active`, `time_out_active` or `final_stage` is set. Thus the AI runs only while the fighters fight. Drax in the final stage does not use the AI.
2. **The level.** `opponent_index` selects one pointer of `ai_column_ptrs`. The pointer goes into `ai_level_ptr`.
3. **The fighters.** The routine loads X with `demo_mode`. X is the watched fighter, and X EOR 1 is the moved fighter. The loop counts X down to 0.
4. **The row list.** The pose of the watched fighter selects a pointer of `ai_row_ptrs`.
5. **The joystick row.** `get_fighter_distance` gives the distance, and `distance_bands` gives the band. The byte of the band in the row list is the joystick row number n. The row is at `$CB38` + 8n.
6. **The column.** The routine adds 1 to `ai_random`. In the demo, it writes a value from the CIA timers over it. The value AND `$1F` is the index. The column table gives the column at that index.
7. **The move.** The joystick value of that column goes to `joystick_to_direction`, `find_move_row` and [`start_new_move` `$868D`](../src/input/joystick.asm#L84). `read_joystick` uses the same three routines for the player.

The game modes use the loop in this way (**Code**):

| Game mode | `demo_mode`, `two_players` | Watched fighter, moved fighter | Level | Index from |
|---|---|---|---|---|
| Demo | 1, 0 | fighter 1, fighter 0. Then fighter 0, fighter 1. | 4 | CIA 1 timers |
| One-player game | 0, 0 | fighter 0, fighter 1 | Opponent 0-7 | The count in `ai_random` |
| Two-player game | 0, 1 | none | - | - |

Part 2 writes only 0 into `two_players`, so the two-player exit never runs in this program (**Code**). **Conclusion**: the exit comes from the code that part 1 shares.

### The same rules as the joystick

The AI gives a joystick value, not a move. `find_move_row` then selects the next move from the current move of the computer fighter and from the fire bit. `start_new_move` changes nothing while bit 7 of `fighter_move_lock` is set. Each move except `$00-$02` (stand and the two walks) sets this lock. `animate_fighter` clears the lock only at the last pose of the move. Thus the AI choice of a pass has no effect while such a move of the computer runs. The computer can change a stand or a walk in each pass. (**Code**)

The AI always uses the direction list [`joystick_dirs_0` `$CDF0`](../src/input/move_select.asm#L9). For a player, `read_joystick` selects the list by `fighter_facing`. In list 0, right is forward and left is back. Thus a joystick value of the AI means forward and back for each facing. The AI tables need no copy for the other facing. (**Code**)

The AI selects the joystick value only from the pose of the other fighter, the distance, the level and the index. The energy, the time, the facing and the own move have no effect on the value. (**Code**)

### The order in a pass

The player moves before the computer. `read_joysticks` runs before `ai_choose_moves`, and `start_new_move` writes the first pose of a new move into `fighter_pose` at once. Thus the computer sees a new attack of the player in the same pass. (**Code**)

The demo is not the same for the two fighters. The loop moves fighter 0 first, and its new pose is in `fighter_pose` before the loop moves fighter 1. Thus fighter 1 answers a new move of fighter 0 in the same pass. Fighter 0 answers a new move of fighter 1 one pass later. (**Code**) Whether fighter 1 wins more demo bouts is not known. See [Still open](#still-open).

## The data

### The column tables: the level

[`ai_column_ptrs` `$C8A2`](../src/ai/ai_tables.asm#L6) holds 8 pointers, one for each opponent number. Each pointer goes to a column table of 32 bytes. The bytes in each table go up from the low columns to the high columns. The table gives the number of entries of each column, and the mean column (**Code**):

| Level | Column 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | Mean column |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 2 | 2 | 2 | 4 | 8 | 14 | 5.75 |
| 1 | 0 | 2 | 1 | 2 | 3 | 5 | 8 | 11 | 5.38 |
| 2 | 2 | 2 | 3 | 4 | 4 | 5 | 5 | 7 | 4.38 |
| 3 | 3 | 3 | 3 | 4 | 4 | 4 | 6 | 5 | 4.00 |
| 4 | 5 | 5 | 4 | 4 | 4 | 4 | 3 | 3 | 3.13 |
| 5 | 7 | 5 | 5 | 4 | 4 | 3 | 2 | 2 | 2.63 |
| 6 | 11 | 8 | 5 | 3 | 2 | 2 | 1 | 0 | 1.59 |
| 7 | 14 | 8 | 4 | 2 | 2 | 2 | 0 | 0 | 1.25 |

Opponent 0 never uses columns 0 and 1. Opponent 7 never uses columns 6 and 7. Column 7 is `$00`, no input, in 13 of the 22 joystick rows. (**Code**)

**Conclusion**: the authors put the best answer of each joystick row in column 0 and the weakest answer in column 7. The level only moves the choice toward column 0. All opponents use the same row lists and joystick rows.

### The distance bands

[`distance_bands` `$C9B2`](../src/ai/ai_tables.asm#L51) has 40 entries, one for each distance 0-39 (**Code**):

| Distance | 0 | 1 | 2 | 3 | 4 | 5-6 | 7-13 | 14-39 |
|---|---|---|---|---|---|---|---|---|
| Band | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |

The walk-in of a bout ends when the distance is less than 6, so the fight starts in band 5 or lower. Each used row list holds joystick row `$04` for band 6 and row `$08` for band 7. These two rows have the same bytes: forward in 7 columns, down-forward in column 1. Thus at a distance of 7 or more, each computer fighter walks to the other fighter or starts move `$11`. The pose of the watched fighter has no effect there. (**Code**)

### The row lists

[`ai_row_ptrs` `$C9DA`](../src/ai/ai_tables.asm#L56) holds 91 pointers, one for each pose `$00-$5A` of the watched fighter. Each pointer goes to a row list. The row lists start at `$CA90`, so row list n is at `$CA90` + 8n. The bands 6 and 7 are `$04 $08` in each list except `$12`. (**Code**)

| Row list | Address | Joystick rows of bands 0-5 | Poses of the watched fighter (moves) |
|---|---|---|---|
| `$00` | `$CA90` | `00 01 01 06 06 06` | `$00-$03` (stand, `$01`), `$34-$37` (`$02`), `$44`, `$45` |
| `$01` | `$CA98` | `13 05 05 14 14 14` | `$04-$07` (`$03`) |
| `$02` | `$CAA0` | `00 01 01 0D 0D 0D` | The 44 other poses |
| `$03` | `$CAA8` | `0C 12 12 12 14 14` | `$0A` (`$05`) |
| `$04` | `$CAB0` | `0C 12 12 14 14 14` | `$0B` (`$05`) |
| `$05` | `$CAB8` | `00 01 01 14 14 14` | `$0C` (`$05`) |
| `$06` | `$CAC0` | `10 11 11 07 07 07` | `$0E-$10` (`$07`, `$1D`) |
| `$07` | `$CAC8` | `00 06 06 0D 0D 0D` | `$14` (`$08`), `$51` (`$10`), `$53` (`$1A`), `$56`, `$59` (`$1B`), `$58` (`$0E`) |
| `$08` | `$CAD0` | `0A 0B 0B 02 04 03` | `$16`, `$55` (`$09`) |
| `$09` | `$CAD8` | `0A 0B 0B 0D 0D 0D` | `$17` (`$09`) |
| `$0A` | `$CAE0` | `10 11 11 0D 0D 0D` | none |
| `$0B` | `$CAE8` | `0E 0F 0F 0D 0D 0D` | `$1F`, `$20` (`$0E`), `$47` |
| `$0C` | `$CAF0` | `09 09 09 02 04 03` | `$23-$25` (`$11`) |
| `$0D` | `$CAF8` | `00 01 01 02 04 03` | `$26` (`$11`), `$27`, `$50` (`$10`) |
| `$0E` | `$CB00` | `13 01 01 14 14 14` | `$39` (`$05`) |
| `$0F` | `$CB08` | `13 14 14 14 14 14` | `$3A` (`$06`), `$3B` (`$14`) |
| `$10` | `$CB10` | `10 11 11 06 06 06` | `$41`, `$42` (`$0B`) |
| `$11` | `$CB18` | `15 01 01 0D 0D 0D` | `$4D`, `$4E` (`$19`) |
| `$12` | `$CB20` | `00 00 00 00 00 00` | none |
| `$13` | `$CB28` | `0C 01 01 14 14 14` | `$5A` (`$05`) |
| `$14` | `$CB30` | `11 11 11 07 07 07` | `$19` (`$07`) |

The moves in brackets are the moves whose sequences show the pose. Pose `$00` is also the last pose of some other moves, for example `$04`. Poses `$15`, `$27`, `$2A`, `$2E` and `$47` are in no move sequence. (**Code**)

Two row lists have no pointer. Row list `$0A` is [`ai_row_0a` `$CAE0`](../src/ai/ai_tables.asm#L102). Row list `$12` follows [`ai_row_11` `$CB18`](../src/ai/ai_tables.asm#L116) and holds only zeros. (**Code**) **Conclusion**: row list `$0A` is an older or a spare answer. It has the bytes of row list `$06` with joystick row `$0D` in bands 3-5.

In bands 3-5, the 44 poses of row list `$02` select joystick row `$0D`. Its columns give forward, down-forward and one back attack `$07`. (**Code**)

### The joystick rows

[`ai_joystick_rows` `$CB38`](../src/ai/ai_tables.asm#L125) holds 22 rows of 8 joystick values. The AI uses the direction list 0, so right is forward and left is back. This table gives the move that each value starts when the computer is in one of the moves `$00-$04`. The names of the moves come from [fighters.md](fighters.md) (**Code**):

| Direction | Value | Move without fire | Move with fire (value + `$10`) |
|---|---|---|---|
| none | `$00` | `$00` stance | `$00` stance |
| forward | `$08` | `$01` walk forward | `$09` thrust at body height |
| back | `$04` | `$02` walk back | `$07` sword round the head |
| down | `$02` | `$17` step into the crouch | `$17` step into the crouch |
| up | `$01` | `$04` jump | `$0B` thrust at head height |
| down-forward | `$0A` | `$11` forward roll | `$0C` kick |
| up-forward | `$09` | `$0A` high guard | `$0F` overhead cut |
| down-back | `$06` | `$12` back roll | `$0E` sword swing |
| up-back | `$05` | `$10` front guard | `$03` low sword swing |

The 22 joystick rows, and the move from a stand for each column (**Code**):

| Row | Address | Values, columns 0-7 | Moves from a stand, columns 0-7 |
|---|---|---|---|
| `$00` | `$CB38` | `19 1A 16 15 12 11 00 18` | `0F 0C 0E 03 17 0B 00 09` |
| `$01` | `$CB40` | `16 12 15 11 18 12 16 00` | `0E 17 03 0B 09 17 0E 00` |
| `$02` | `$CB48` | `12 08 08 15 15 08 00 00` | `17 01 01 03 03 01 00 00` |
| `$03` | `$CB50` | `14 14 15 15 08 08 00 00` | `07 07 03 03 01 01 00 00` |
| `$04` | `$CB58` | `08 0A 08 08 08 08 08 08` | `01 11 01 01 01 01 01 01` |
| `$05` | `$CB60` | `0A 0A 0A 0A 04 04 04 00` | `11 11 11 11 02 02 02 00` |
| `$06` | `$CB68` | `0A 0A 0A 0A 08 08 00 08` | `11 11 11 11 01 01 00 01` |
| `$07` | `$CB70` | `15 12 15 12 0A 06 02 00` | `03 17 03 17 11 12 17 00` |
| `$08` | `$CB78` | `08 0A 08 08 08 08 08 08` | `01 11 01 01 01 01 01 01` |
| `$09` | `$CB80` | `01 01 04 04 06 02 04 00` | `04 04 02 02 12 17 02 00` |
| `$0A` | `$CB88` | `19 19 09 09 09 09 09 00` | `0F 0F 0A 0A 0A 0A 0A 00` |
| `$0B` | `$CB90` | `0A 09 09 09 09 09 09 00` | `11 0A 0A 0A 0A 0A 0A 00` |
| `$0C` | `$CB98` | `1A 1A 01 01 06 06 06 04` | `0C 0C 04 04 12 12 12 02` |
| `$0D` | `$CBA0` | `14 0A 0A 0A 08 08 00 08` | `07 11 11 11 01 01 00 01` |
| `$0E` | `$CBA8` | `19 12 06 05 05 05 02 04` | `0F 17 12 10 10 10 17 02` |
| `$0F` | `$CBB0` | `12 12 05 05 05 05 02 00` | `17 17 10 10 10 10 17 00` |
| `$10` | `$CBB8` | `19 1A 0A 06 02 02 04 02` | `0F 0C 11 12 17 17 02 17` |
| `$11` | `$CBC0` | `12 12 0A 06 02 02 04 02` | `17 17 11 12 17 17 02 17` |
| `$12` | `$CBC8` | `0A 0A 01 01 01 06 04 00` | `11 11 04 04 04 12 02 00` |
| `$13` | `$CBD0` | `1A 1A 1A 15 15 18 18 00` | `0C 0C 0C 03 03 09 09 00` |
| `$14` | `$CBD8` | `0A 15 15 0A 0A 0A 0A 00` | `11 03 03 11 11 11 11 00` |
| `$15` | `$CBE0` | `12 15 1A 1A 0A 06 06 00` | `17 03 0C 0C 11 12 12 00` |

Rows `$04` and `$08` have the same 8 bytes (**Code**). **Conclusion**: the authors kept two copies, maybe to change the far band later.

From another move, the same value can start a different move. For example, a computer fighter in move `$17` starts the low thrust `$05` for each value with fire. (**Code**)

## The level of each opponent

F1 starts the set-up with opponent 0. After each won bout, `end_bout` adds 1 to `opponent_index`. After the win against opponent 7, the final stage starts. [game_flow.md](game_flow.md) tells the bouts. (**Code**)

The level changes only the column table. The row lists and the joystick rows are the same for all opponents. Opponent 0 uses columns 6 and 7 in 22 of 32 passes. Opponent 7 uses columns 0 and 1 in 22 of 32 passes. (**Code**) In the `decapitation` recording, opponent 7 cuts off the head of a player who does nothing (**Observed**). [combat.md](combat.md) tells the decapitation.

The tables explain this result. The idle poses `$52-$54` of the player select row lists `$02` and `$07`. In bands 3-5, both lists select joystick row `$0D`. Its column 0 is `$14`, back and fire, and that value starts move `$07`. Move `$07` is the only move that decapitates. Opponent 7 uses column 0 in 14 of 32 passes. (**Code**) **Conclusion**: at a distance of 3-6, opponent 7 can start move `$07` against an idle player in each cycle of 32 passes. Opponent 0 never uses column 0.

[`init_game_state` `$9272`](../src/init/state.asm#L6) sets `opponent_index` to 4 at each start of the demo. The demo does not change it after a bout, so the demo always fights at level 4. (**Code**)

## The random source

### The one-player game: a counter

In the one-player game, the AI adds 1 to `ai_random` in each pass in which it runs. Nothing else in the program writes `ai_random`. Thus the index steps through the column table in order: 0, 1, 2 to 31, then 0 again. (**Code**)

The bytes of each column table go up, so the column of the computer goes from low to high in each cycle of 32 passes. Opponent 7 uses column 0 for 14 passes in a row, then column 1 for 8 passes. Opponent 0 uses column 7 for 14 passes in a row. (**Code**)

In the `attract` recording, `main_loop` runs 1497 times in about 15000 frames. That is about 5 passes in each second, with the waits between the bouts (**Observed**). **Conclusion**: one cycle of 32 passes takes about 6 seconds. A player can learn the phase of the strong answers.

The counter is not random. F1 stops the AI during the set-up, so the first value in a game is the last value of the demo. (**Code**) **Conclusion**: the phase of the cycle at the start of a game comes from the CIA timers of the last demo pass.

### The demo: the CIA timers

In the demo, the AI writes `CIATBLO` EOR `CIATALO` into `ai_random`. These are the low bytes of timer B and timer A of CIA 1. The timers run all the time. Timer A has a period of `$2710` cycles. Timer B starts with `$5161` cycles, and the music command `cmd_tempo` (`$F6`) loads other values from `tempo_latches`. Thus the value depends on the cycle of the read. (**Code**) The demo reads the two timers two times in each pass, one time for each fighter. In the `attract` recording, the program reads each timer 2448 times in 1495 calls of `read_keys` (**Observed**). Thus the AI ran in about 1224 passes, and the other passes were walk-ins, turns and bout ends (**Conclusion**).

The record files give `$DC04` and `$DC06` as inputs. All 7 recordings replay on the default build with no pins (**Observed**). **Conclusion**: the CIA reads are the only random source of the AI. A replay that gives the same timer values repeats each choice of the computer.

## The demo

![The demo in the throne room: Drax on the throne, the princess beside him, one fighter down](images/demo_throne_room.png)

The demo in the throne room, from the `attract` steps: one computer fighter is down.

The demo is the title of the game. Both fighters are computer fighters with the column table of level 4, and the CIA timers give each index. After a bout, the demo changes the background picture and starts the next bout. F1 ends the demo and starts the set-up. (**Code**)

## The worked example

This example decodes one pass by hand from the tables. The game is a one-player game against opponent 7. The player stands, so `fighter_pose` of fighter 0 is `$00`. The distance is 2. The counter `ai_random` becomes `$25` in this pass. (**Code**)

1. `opponent_index` = 7. The word at `$C8A2` + 14 = `$C8B0` is `$C992`, the start of `ai_columns_7`.
2. `demo_mode` = 0 and `two_players` = 0, so X = 0. The player is the watched fighter, and fighter 1 is the moved fighter.
3. Pose `$00` reads the word at `$C9DA`. That word is `$CA90`, row list `$00`.
4. Distance 2 reads `$C9B4`, band 2. The byte at `$CA90` + 2 = `$CA92` is `$01`, joystick row `$01` at `$CB38` + 8 = `$CB40`.
5. `$25` AND `$1F` = 5. The byte at `$C992` + 5 = `$C997` is `$00`, column 0.
6. The byte at `$CB40` is `$16`: down, left and fire. In list 0, `$06` is down-back, entry 7.
7. Fighter 1 stands, and fire is pressed. `move_rows_fire` gives row 8 at `$CE3A` + 72 = `$CE82`. Entry 7 is `$8E`: move `$0E` with the lock bit.

In the next 8 passes, the index is 6-13 and the column stays 0. The lock of move `$0E` makes these passes have no effect until its last pose. At index 14, the column becomes 1, and the value `$12` gives move `$17`. (**Code**)

The same pass against opponent 0 reads `$C8B2` + 5 = `$C8B7`, column 4. The byte at `$CB44` is `$18`, forward and fire, and the move is `$09`. In 32 passes against a standing player at distance 2, opponent 0 gives no input in 14 passes. Opponent 7 gives a value with fire or down in each pass. (**Code**)

## Changes in V 05 10 87

The later build `game_v2` changes some AI tables (**Code**, game_v2 source):

- A new row list `$15`, `14 01 01 0D 0D 0D 04 08`. Poses `$1B` and `$1F` select it. V 05 05 87 selects row lists `$02` and `$0B` for these poses.
- Band 0 of row list `$01` selects a new joystick row `$16`, `0A 1A 0A 15 0A 15 0A 00`. V 05 05 87 selects row `$13`.
- Joystick row `$15` has `$1A` in columns 0, 5 and 6. V 05 05 87 has `$12`, `$06` and `$06`.

The routine and the column tables stay the same. The details are on [../../docs/versions.md](../../docs/versions.md).

## Still open

- How many frames does one pass take in a bout, and how long is the cycle of 32 passes? — Run the `fight` steps and log the frame number at each `main_loop` while `walk_in_active` is clear.
- Does fighter 1 win more demo bouts, because it answers in the same pass? — Replay the `attract` recording and count the values of `bout_loser` at each bout end.
- Does the cut in the `decapitation` recording come from column 0 of joystick row `$0D`, as the tables tell? — Replay it with a breakpoint at `start_new_move` for X = 1 and log `ai_random`, `fighter_distance` and `fighter_move+1`.
- Did the authors use row list `$0A` in an older build? — No run can answer this. A copy of an earlier build can.
