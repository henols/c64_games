# Part 1, part 2 and the two builds

Barbarian exists as four programs. The game has two parts: part 1 (Combat Practice) and part 2 (the story game). Each part exists in two builds, V 05 05 87 and V 05 10 87. This page compares part 1 with part 2 of the same build. Then it compares build V 05 05 87 with build V 05 10 87 of the same part. A table gives each difference and its code. A section for each difference follows. The pages of the projects explain each part of the game in depth.

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge. A label before a name gives its project: `practice_v1:`, `practice_v2:`, `game_v1:` or `game_v2:`.
- *Part 1* is Combat Practice (`practice_v1`, `practice_v2`). *Part 2* is the story game (`game_v1`, `game_v2`).
- *V 05 05 87* is the earlier build (`practice_v1`, `game_v1`). *V 05 10 87* is the later build (`practice_v2`, `game_v2`). CTRL+V shows these version texts.
- A *pass* is one run of the main loop. The main loop does not wait for a frame, and a pass takes about 10 frames in the demo.
- *Fighter 0* is player 1. *Fighter 1* is player 2 or the computer.
- A *move* is a number `$00-$1D` with bit 7 set in `fighter_move`. A *pose* is a picture of a fighter, `$00-$5A`. A move sequence is a list of poses.
- A *shift* is the address in one program minus the address in the other, for example -$16C.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

The facts come from a compare of the generated source of the four projects, line by line, without the comments. A fact in a table is **Code** when the table does not give a different mark.

## Overview

The four programs share almost all code and data. The two parts of one build differ only in the parts of the story. The two builds of one part differ in a set of small corrections. Each correction of V 05 10 87 is the same in part 1 and in part 2 (**Code**).

~~~mermaid
flowchart LR
  G1["Part 2, V 05 05 87<br/>game_v1"]
  P1["Part 1, V 05 05 87<br/>practice_v1"]
  G2["Part 2, V 05 10 87<br/>game_v2"]
  P2["Part 1, V 05 10 87<br/>practice_v2"]
  G1 -- "no final stage,<br/>F1 selects players,<br/>other pictures" --> P1
  G2 -- "the same changes" --> P2
  G1 -- "corrections,<br/>new AI rows, 90 s" --> G2
  P1 -- "the same corrections" --> P2
~~~

The arrows show the changes, not a proved order of work. **Conclusion:** the authors made part 1 from the source of part 2 in each build. Part 1 keeps dead code and data of the final stage, see [Dead story parts in part 1](#dead-story-parts-in-part-1). V 05 10 87 is the later build, see [development.md](development.md).

| # | Difference | Programs | Code (game_v1 / game_v2) | Effect |
|---|---|---|---|---|
| 1 | Part 1 has no final stage | part 1 | final_stage_attack `$84AC` / `$84B6`, end_bout_final_stage `$848D` / `$8497` | After opponent 7, part 1 changes the scene and stays at opponent 7. |
| 2 | Part 1 has two players | part 1 | read_keys_f1_clock `$9406` / `$941A` (part 1: `$929A` / `$92AE`) | F1 toggles 1PLR and 2PLR. Part 2 always sets one player. **Observed** |
| 3 | Other pictures | part 1 | bitmap `$6000`, screen_ram `$4400`, arena2 `$D000-$E7E7`, scene_top_colour `$7F40` | Sunset and forest in part 1, throne room and dungeon in part 2. **Observed** |
| 4 | Dead story parts in part 1 | part 1 | set_end_figure copy, end_scene data, end_story_sprites `$FC40`, texts 9 and 10 | Nothing calls or reads them in part 1. |
| 5 | C128 MMU code | part 2 | unused_ff80 `$FFD0-$FFEF` | Only part 2 has it. Part 1 has the RAM fill pattern there. |
| 6 | Version text | build | text_version `$BAAF` / `$BAD1` | "V 05 05 87", or "V 05 10 87" with "WHY DID YOU PRESS ME". |
| 7 | Bout clock | build | reset_timer `$92B2` / `$92BE` | 60 s, now 90 s. **Observed** |
| 8 | Pause and version text stop the sprites | build | read_keys `$939B` / `$93A7`, raster_irq_bottom `$9539` / `$954F` | V 05 05 87 moves the sprites and counts the clock during F5. |
| 9 | Raster IRQ busy flag | build | raster_irq_busy `$CE` (new), raster_irq_bottom | No second sprite update while one runs. The music variables move up by 1. |
| 10 | One routine sets the poses | build | set_fighter_poses `$878C` (new) | The pose is the pose on the screen. Four stores of V 05 05 87 are gone. |
| 11 | Turn after the hit check | build | main_loop `$80BB` | check_turn_around comes after check_hits. |
| 12 | Hit check guards | build | check_attack_hit `$87B9` / `$87C7`, apply_hit_damage, add_hit_score | No hit after a fighter is beaten, no energy below 0. |
| 13 | Hit lists | build | hit_list_00 `$C2EA` / `$C325`, hit_list_05 `$C533` / `$C56E` | Pose $5B becomes $5A. List 5 gets new defender poses. |
| 14 | Move tables | build | move_seq_12 `$BD2F` / `$BD69`, move_select_rows `$CE3A` / `$CE8B` | Move $12 gets pose $2E. Row 7 has no down-back move. |
| 15 | AI tables | build | ai_row_ptrs `$C9DA` / `$CA1B`, ai_row_15, ai_joystick_row_22 (new) | The computer reacts differently to 6 poses at close range. |
| 16 | Demo scores | build | end_bout_reset `$842A` / `$842D` | The demo clears both scores after each bout. |
| 17 | Move row address | build | find_move_row `$8663` / `$866D` | A new order of the add. The same result. |
| 18 | Unused RAM | build | unused_cf20 `$CF20`, unused_fc04 `$FC04` and others | Other fill bytes in the unused areas. |

## How the layout moved

The four programs have the same order of modules. Most modules start at a new address. A few rules give each shift (**Code**).

**Part 1 against part 2.** The main loop of part 1 has two JSR less, so the shift is -6 after it. Part 1 also removes 31 bytes of `end_of_bout` and the final stage code of 327 bytes. Thus the shift is -$16C from `wait_frames` on. The F1 code of part 1 is 2 bytes longer, so from `read_keys_check_f3` (`$92A7` in part 1) on, the shift is -$16A. All data from the texts to the end of the part tables also has the shift -$16A.

**V 05 05 87 against V 05 10 87.** The shift of the code changes along the program. New code makes it larger, and each removed pose store makes it smaller. It is +3 after the main loop, +$0A after `end_of_bout` and +$1C after the hit check. At the end of the music, it is +$22. The data tables grow by the new version text, one pose byte, 6 bytes of hit lists and 16 bytes of AI rows. Thus the shift of the data grows from +$22 to +$51.

The table gives the main areas. The memory maps of the reference give each variable: [game_v1](../game_v1/docs/reference/memory-map.md) and [game_v2](../game_v2/docs/reference/memory-map.md).

| Contents | practice_v1 | practice_v2 | game_v1 | game_v2 |
|---|---|---|---|---|
| Fighter pieces, screen, sprites, background bitmap | `$0840-$7FFF` | `$0838-$7FFF` | `$0838-$7FFF` | `$0838-$7FFF` |
| Cartridge header, init | `$8000-$80BA` | `$8000-$80BA` | `$8000-$80BA` | `$8000-$80BA` |
| Main loop | `$80BB-$80FC` | `$80BB-$80FF` | `$80BB-$8102` | `$80BB-$8105` |
| Status line, walk-in, end of a bout | `$80FD-$8486` | `$8100-$8490` | `$8103-$84AB` | `$8106-$84B5` |
| Final stage | - | - | `$84AC-$85F2` | `$84B6-$85FC` |
| Joysticks, AI, new pose routine | `$8487-$862E` | `$8491-$863C` | `$85F3-$879A` | `$85FD-$87A8` |
| Hits, animation, drawing | `$862F-$8B76` | `$863D-$8B90` | `$879B-$8CE2` | `$87A9-$8CFC` |
| Dead set_end_figure copy | `$8CAB-$8D06` | `$8CC5-$8D20` | - | - |
| Live set_end_figure | - | - | `$8E17-$8E72` | `$8E31-$8E8C` |
| Scene, sprites, keys, IRQ | `$8D07-$978C` | `$8D21-$97AE` | `$8E73-$98F6` | `$8E8D-$9918` |
| Music driver and tunes | `$978D-$A50D` | `$97AF-$A52F` | `$98F7-$A677` | `$9919-$A699` |
| Work bitmap | `$A50E-$AFFF` | `$A530-$AF2F` | `$A678-$AFFF` | `$A69A-$B099` |
| Texts | `$B90E-$BAD8` | `$B930-$BB12` | `$BA78-$BC42` | `$BA9A-$BC7C` |
| Move sequences, poses, hit tables | `$BB1D-$C72F` | `$BB57-$C770` | `$BC87-$C899` | `$BCC1-$C8DA` |
| AI tables | `$C738-$CA7D` | `$C779-$CACE` | `$C8A2-$CBE7` | `$C8E3-$CC38` |
| End scene data | `$CB33-$CB78` (dead) | `$CB84-$CBC9` (dead) | `$CC9D-$CCE2` | `$CCEE-$CD33` |
| Move selection, part layout | `$CC82-$CDB5` | `$CCD3-$CE06` | `$CDEC-$CF1F` | `$CE3D-$CF70` |
| Unused RAM | `$CDB6-$CFFF` | `$CE07-$CFFF` | `$CF20-$CFFF` | `$CF71-$CFFF` |
| Second arena, font, corners, high tunes | `$D000-$FC03` | `$D000-$FC03` | `$D000-$FC03` | `$D000-$FC03` |
| End story sprites | `$FC40-$FF7F` | `$FC40-$FF7F` | `$FC40-$FF7F` | `$FC40-$FF7F` |

The first bytes, the work bitmap end and the unused RAM have other limits in each release. The cracks copy colour bytes and code into these areas, and the captures leave them out. [releases.md](releases.md) gives each area.

## Part 1 against part 2

The two parts of one build have the same code for the fight, the computer opponent, the music and the sprites. Part 1 removes the end of the story and adds a two-player game.

### Part 1 has no final stage

In part 2, a win against opponent 7 starts the final stage with Drax and the princess. [`game_v1:end_bout_player_won` `$847C`](../game_v1/src/combat/end_of_bout.asm#L81) compares the opponent with 7 and jumps to `end_bout_final_stage`. In part 1, the same compare jumps to `end_bout_swap_background` (**Code**). Thus part 1 changes the scene, and the player fights opponent 7 again. The final stage is on [../game_v1/docs/final_stage.md](../game_v1/docs/final_stage.md).

The main loop of part 1 has 21 calls in V 05 05 87 and 22 calls in V 05 10 87. [`practice_v1:main_loop` `$80BB`](../practice_v1/src/main/main_loop.asm#L6) does not call `final_stage_attack` and `set_end_figure`. The module of the final stage, `$84AC-$85F2` in `game_v1`, is not in part 1 (**Code**).

Part 1 keeps each test of the `final_stage` flag. For example, `check_hits`, `ai_choose_moves` and `quit_to_demo` still read it. Only `init_game_state` writes it, with 0 (**Code**).

### Part 1 has two players

The F1 key starts the set-up in both parts. Before F7, F1 also selects the number of players. [`practice_v1:read_keys_f1_clock` `$929A`](../practice_v1/src/input/keyboard.asm#L59) toggles `two_players` between 0 and 1. [`game_v1:read_keys_f1_clock` `$9406`](../game_v1/src/input/keyboard.asm#L59) writes 0 (**Code**).

The part 1 code toggles once in each pass while F1 stays down. Thus an odd number of passes gives 2PLR. A press of 3 frames gives two players in the recording `two_players` of `practice_v1` (**Observed**).

Part 2 keeps the two-player code. For example, `check_time_out` ends a bout at time 0 only in a two-player game. No run of part 2 executed this code (**Code**). The game flow is on [../game_v1/docs/game_flow.md](../game_v1/docs/game_flow.md).

### Other pictures

Part 1 has other background pictures at the same addresses. The bitmap at `$6000-$7F3F` and the screen at `$4400` hold the first picture. The second picture is at `$D000-$DFFF`, `$E000` and `$E400` (**Code**).

| Data | Part 1 | Part 2 |
|---|---|---|
| First picture, scene 0 | the arena with the sunset | the throne room with Drax on the throne |
| Second picture, scene 1 | the forest | the dungeon with Drax and the princess in the windows |
| scene_top_colour `$7F40`, 2 bytes | `$09` (brown) | `$0B` (dark grey) |

The raster IRQ at line `$72` writes `scene_top_colour` into the background colour register (**Code**). The pictures are **Observed** in the runs of each part.

![Part 1 in the demo: the arena with the sunset](../practice_v1/docs/images/practice_sunset.png)

The image shows the first picture of part 1, the arena with the sunset.

![Part 2 in the demo: the throne room](../game_v1/docs/images/demo_throne_room.png)

The image shows the first picture of part 2, the throne room.

### Dead story parts in part 1

Part 1 holds parts of the story that no code of part 1 uses (**Code**):

- **A copy of `set_end_figure`.** [`practice_v1:set_end_figure` `$8CAB`](../practice_v1/src/leftovers/leftover_8cab.asm#L6) is the routine of part 2. Nothing calls it. Each data address in it is $16A lower than in part 2. This is the shift of the data of part 1.
- **The sprite set-ups of the end scene.** `end_scene_ptrs` and the bolt tables (`bolt_motions`) are at `$CB33-$CB78` in `practice_v1`. Only the dead copy reads them.
- **The end story sprites.** `end_story_sprites` at `$FC40-$FF7F` hold 13 sprites of the end of the story. `swap_end_shapes` swaps them in only when `final_stage` bit 7 is set. Part 1 never sets it.
- **Texts 9 and 10.** "YOUR END HAS COME" and "THANKS BIG BOY" are in the text table of part 1. No code of part 1 prints them.

**Conclusion:** the authors removed the calls of the final stage and its main routine from part 2. They did not remove the data and the routines that only the final stage needs. In the dead copy, the data addresses agree with the data of part 1. Thus the authors assembled part 1 again after the change. They did not patch the bytes of part 2. [development.md](development.md) tells more.

### The C128 MMU code

The game builds have 6502 code at `$FFD0-$FFEF` that writes the C128 MMU registers `$FF00` and `$D505`. Part 1 has the `$00`/`$FF` fill pattern of RAM there. The program does not run this code in either part (**Code**). [development.md](development.md) explains it.

## V 05 05 87 against V 05 10 87

The changes of V 05 10 87 are corrections and small changes of the game play. The same changes are in part 1 and in part 2. The only difference between the two compares is the address of the Hotline trainer patch in V 05 05 87 (**Code**).

### The version text

CTRL+V prints text $81 while CTRL and V stay down. [`game_v2:text_version` `$BAD1`](../game_v2/src/text/texts.asm#L17) holds "V 05 10 87". After a line feed, a second line at column 10, row 18 holds "WHY DID YOU PRESS ME". Build V 05 05 87 has only "V 05 05 87". The new text is 24 bytes longer (**Code**). [development.md](development.md) explains the dates.

### The bout clock

[`game_v2:reset_timer` `$92BE`](../game_v2/src/init/state.asm#L45) sets `time_left` to 90 seconds. Build V 05 05 87 sets 60 seconds (**Code**). The runs show 60 s in V 05 05 87 and 90 s in V 05 10 87 (**Observed**).

### Pause and version text stop the sprites

F5 stops the main loop until the player presses F5 again. CTRL+V stops it while the keys stay down. The raster IRQ continues in both builds. It moves the sprites, runs the sprite scripts and counts down the clock and the idle timers (**Code**).

In V 05 05 87, the F5 code stores the set-up flag in `sprites_frozen`. The flag is 0 at that point, so the sprites do not stop. In V 05 10 87, [`game_v2:read_keys` `$93A7`](../game_v2/src/input/keyboard.asm#L6) writes `$80` to `sprites_frozen` for the pause and for the version text. [`game_v2:raster_irq_bottom` `$954F`](../game_v2/src/irq/irq_handler.asm#L57) then skips the sprite update (**Code**).

| Part | V 05 05 87 | V 05 10 87 |
|---|---|---|
| F5 | stores the set-up flag (0) in sprites_frozen | stores $80 |
| CTRL+V | does not write sprites_frozen | stores $80, then 0 when the player releases V |
| IRQ test | BNE: any value that is not 0 | BMI: bit 7 |

**Conclusion:** in V 05 05 87, the bout clock counts down during a pause, and the hit sprites and the goblin continue to move. The fighters stop, because the main loop draws them.

### The raster IRQ busy flag

The raster IRQ at line `$FA` enables interrupts with CLI before the sprite update. V 05 10 87 adds the flag `raster_irq_busy` at `$CE`. The handler sets bit 7 before the update and clears it after. A second IRQ at line `$FA` during the update returns at once. `init_game_state` clears the flag (**Code**).

**Conclusion:** without the flag, a slow sprite update can start a second sprite update in the same handler. V 05 05 87 has no protection against it.

The new flag takes `$CE`. The music variables of V 05 05 87 at `$CE-$EC` move up by 1 to `$CF-$ED`. For example, `sound_request` moves from `$DC` to `$DD` (**Code**).

### One routine sets the poses

`fighter_pose` holds the pose of each fighter. The AI, the hit check and the turn read it. V 05 05 87 writes it at four places. These are the start of a new move, the idle move, the turn and each step of the animation (**Code**).

V 05 10 87 has one place. The new routine [`game_v2:set_fighter_poses` `$878C`](../game_v2/src/fighter/pose_update.asm#L6) runs after `animate_fighters` in each pass. It reads the pose byte before `fighter_move_step` in the move sequence, or byte 0 at step 0. The four old stores are gone. `start_new_move`, `check_player_idle` and `check_turn_around` now only set the step to 0 (**Code**).

**Conclusion:** in V 05 05 87, a new move of player 1 sets the new pose before `ai_choose_moves` runs. Thus the computer sees the pose one pass before the screen shows it. In V 05 10 87, the computer sees the pose that the last pass drew. The fighter pages explain the move sequences: [../game_v1/docs/fighters.md](../game_v1/docs/fighters.md).

### The turn after the hit check

[`game_v2:main_loop` `$80BB`](../game_v2/src/main/main_loop.asm#L6) calls `check_turn_around` after `check_hits` and `mirror_shared_sprites`. V 05 05 87 calls it before `check_hits` (**Code**).

| Step | V 05 05 87 | V 05 10 87 |
|---|---|---|
| after animate_fighters | check_decapitation | set_fighter_poses, then check_decapitation |
| after get_fighter_distance | check_turn_around, check_hits, mirror_shared_sprites | check_hits, mirror_shared_sprites, check_turn_around |

**Conclusion:** the new order changes no hit. `check_turn_around` works only when `turn_request` bit 7 is set. `check_hits` does nothing in that condition.

### The hit check guards

[`game_v2:check_attack_hit` `$87C7`](../game_v2/src/combat/hits.asm#L25) examines the attack of one fighter against the pose of the other fighter. `check_hits` calls it for fighter 1, then for fighter 0. V 05 10 87 adds these tests (**Code**):

1. **No hit after a beaten fighter.** The routine returns when `bout_loser` bit 7 is set.
2. **No hit on a pose `$5B` or higher.** The table of poses has the poses `$00-$5A` only, so this test never stops a hit.
3. **No second distance.** V 05 05 87 calls `get_fighter_distance` again after `get_hit_record`. V 05 10 87 uses the distance of the main loop.
4. **No energy below 0.** [`game_v2:apply_hit_damage_energy` `$8895`](../game_v2/src/combat/hits.asm#L151) skips the DEC of `fighter_energy` when the energy is 0.
5. **Score numbers 1-4 only.** [`game_v2:add_hit_score` `$88FC`](../game_v2/src/combat/hits.asm#L219) adds nothing for a score number of 5 or higher. The hit records use only the numbers 0-4.
6. **A CLC before the add of `$87`.** The carry is 0 at that point in both builds.

**Conclusion:** in V 05 05 87, one pass can give two hits. Fighter 1 can beat fighter 0, and then the pose of fighter 0 can still hit fighter 1. If fighter 1 then has 0 energy, `bout_loser` changes to fighter 1. Tests 1 and 4 stop this case. Tests 2, 3, 5 and 6 change no result. The combat page explains the hits: [../game_v1/docs/combat.md](../game_v1/docs/combat.md).

### The hit lists

A hit list gives pairs of a defender pose and a hit record. The 12 attack poses each select one list (**Code**).

| Change | V 05 05 87 | V 05 10 87 |
|---|---|---|
| Lists 0, 1, 3, 5, 8, 9 and 10 | defender pose $5B | defender pose $5A |
| List 5 (attack pose $1C) | pose $23 with record 12 | poses $0E, $0F, $10 and $19 with record 10, no pose $23 |

Pose `$5A` is the 4th pose of move `$05`. No pose `$5B` exists. **Conclusion:** in V 05 05 87, these 7 attacks cannot hit a fighter in pose `$5A`. V 05 10 87 corrects the pose number.

Record 10 hits only at distance 0. Record 12 hits at distance 0 and 1. Both take 1 energy and give 100 points (**Code**). [`game_v2:hit_list_05` `$C56E`](../game_v2/src/combat/hit_tables.asm#L97) shows the new list.

### The move tables

Two moves change (**Code**):

- [`game_v2:move_seq_12` `$BD69`](../game_v2/src/fighter/move_sequences.asm#L55) ends with the poses `$2D`, `$2E`. In V 05 05 87, the sequence ends after `$2D`. Move `$12` is the move of the joystick direction down-back from a stand.
- Row 7 of `move_select_rows` gives the next move for each joystick direction during move `$18`. For down-back, it gives the back roll `$12` in V 05 05 87 and the stance `$00` in V 05 10 87. Down and down-forward give the stance `$00` in both builds.

**Conclusion:** V 05 10 87 makes row 7 consistent. All three down directions now give the stance during move `$18`.

In the final stage, the back roll `$12` lets a high bolt (path 0) pass, but the stance does not (**Code**: `bolt_pass_moves_0`). Thus in V 05 10 87, a player who presses down-back during move `$18` stands, and a high bolt kills him (**Conclusion**).

### The AI tables

The computer selects a joystick value from three tables. The pose of the other fighter selects an AI row. The distance band selects a byte of the row. That byte selects a joystick row, and a random column selects the value. The AI page explains the choice: [../game_v1/docs/ai.md](../game_v1/docs/ai.md).

V 05 10 87 adds the AI row [`game_v2:ai_row_15` `$CB79`](../game_v2/src/ai/ai_tables.asm#L126) and the joystick row [`game_v2:ai_joystick_row_22` `$CC31`](../game_v2/src/ai/ai_tables.asm#L155). The other changes are in the table (**Code**).

| Table | Entry | V 05 05 87 | V 05 10 87 |
|---|---|---|---|
| ai_row_ptrs | pose $1B | ai_row_02 | ai_row_15 |
| ai_row_ptrs | pose $1F | ai_row_0b | ai_row_15 |
| ai_row_01 (poses $04-$07) | band 0 | joystick row $13 | joystick row $16 (new) |
| ai_row_15 (new) | bands 0-7 | - | $14,$01,$01,$0D,$0D,$0D,$04,$08 |
| ai_joystick_rows | row $15, columns 0, 5, 6 | $12, $06, $06 | $1A, $1A, $1A |
| ai_joystick_rows | row $16 (new) | - | $0A,$1A,$0A,$15,$0A,$15,$0A,$00 |

A joystick value has bit 0 up, bit 1 down, bit 2 left, bit 3 right and bit 4 fire. For example, `$1A` is fire with down and right (**Code**).

**Conclusion:** the computer reacts differently at close range to the poses `$04-$07`, `$1B` and `$1F`. The poses `$1B` and `$1F` belong to the moves `$0C` and `$0E`. The AI takes its index from the counter [`game_v2:ai_random` `$CD`](../game_v2/src/constants.asm#L114). The counter counts passes: it adds 1 for each computer fighter in each pass in which the AI runs. Thus a recording repeats the same choices.

### The demo scores

[`game_v2:end_bout_reset` `$842D`](../game_v2/src/combat/end_of_bout.asm#L37) resets both fighters for the next bout. In the demo, V 05 10 87 also calls `clear_fighter_score` for each fighter. V 05 05 87 keeps the scores of the demo from bout to bout (**Code**).

### The move row address

[`game_v2:find_move_row` `$866D`](../game_v2/src/input/joystick.asm#L60) calculates the address of a row of `move_select_rows`: base + 9 x row. V 05 05 87 adds the low byte of the base with the carry of the first add. V 05 10 87 adds the high byte first and the low byte last, with an INC of the high byte on a carry (**Code**).

**Conclusion:** both builds give the same address. The largest row offset is 99, and no add gives a carry. The INC of V 05 10 87 never runs, and the coverage of the runs marks it as not executed.

### The unused RAM

The unused areas hold other bytes in each build (**Code**):

| Area | V 05 05 87 | V 05 10 87 |
|---|---|---|
| End of `$CFxx` (part 2) | `$CF20-$CFFF`: the `$00`/`$FF` fill pattern | `$CF71-$CF7F` and `$CFA2-$CFFF`: zeros and one `$FF` |
| End of `$CFxx` (part 1) | `$CDB6-$CFFF`: the fill pattern | `$CE07-$CEFF`: 9 x `$FF`, then `$A3`. `$CF22-$CFFF`: `$A3` |
| `$FC04-$FC3F` (part 1) | the fill pattern | 4 bytes of the pattern, then zeros |
| `$FF80-$FFF9` (part 1) | the fill pattern, then the bytes of `$9FF0-$9FF9` | zeros |
| `$FFF0-$FFFE` (part 2) | the bytes of `$9FF0-$9FFE` | the bytes of `$9FF0-$9FFE` |

In both game builds, `$FFF0-$FFFE` holds the bytes at `$9FF0-$9FFE`. These are bytes of `freq_table`. The music moved by +$22, so the bytes differ between the builds. Part 1 of V 05 05 87 has the same copy for `$FFF0-$FFF9`. Part 1 of V 05 10 87 has zeros there. **Conclusion:** the authors saved the files of V 05 10 87 from a machine with other RAM contents. The cracks also use some of these areas, see [releases.md](releases.md).

## What did not change

These parts have the same code and data in all four programs. Only the addresses in the instructions change with the shift (**Code**):

- The music driver, the tunes, the instruments and the sound effects.
- The fighter pieces, the poses and the sprite frames.
- The sprite scripts, the animations, the motions and the goblin.
- The corner animations, the font and the end story sprites.
- The init code at `$8009-$80BA` and the cartridge header with its CBM80 signature.

## Still open

- Can one pass of V 05 05 87 give a hit to each fighter, and change `bout_loser` to the second fighter? — a run with 1 energy on each fighter and two attacks that meet in the same frame.
- Does the bout clock of V 05 05 87 count down during F5? — a run that presses F5 in a bout and compares `time_left` before and after the pause.
- Did the raster IRQ of V 05 05 87 ever start a second sprite update? — a trace of `raster_irq_bottom` that counts the nested calls in a full demo.
- Why did the authors change the AI rows for the poses `$04-$07`, `$1B` and `$1F`? — a compare of the computer moves in both builds with the same recording.
- Does the computer of V 05 05 87 react one pass earlier to a new move of player 1? — a trace of `fighter_pose` at `ai_choose_moves` in both builds.
