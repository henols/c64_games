# The final stage (game_v2)

After the win against opponent 7, the story game does not start a new bout. The sorcerer Drax leaves his window in the dungeon and throws bolts at the player. The player must pass each bolt with the correct move and walk to the right side of the arena. There, the princess Mariana leaves her window and the story ends with "THANKS BIG BOY". One bolt that hits kills the player, and the game shows "YOUR END HAS COME". This page tells how the final stage starts and how a bolt flies and hits. It also tells how the end scene plays and how the program returns to the demo. The project is Part 2, build V 05 10 87.

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge.
- A *pass* is one run of `main_loop`. A *frame* is one PAL video frame (50 each second). The raster IRQ moves the sprites one time in each frame.
- A *column* is a fighter position in `fighter_x`, in steps of 8 pixels. Fighter 0 is the player, and its home column is 3.
- A *move* is the number in `fighter_move`. The program keeps bit 7 set, so move `$04` is `$84` in memory.
- The *bolt* is sprite 4 in the final stage. The *path* of a bolt is 0 or 1 in `attack_path`.
- The *figure* is sprites 0-3: Drax, and later the princess. The *pose set* is the number in `final_scene_pose`.
- *V 05 05 87* is the earlier build (`game_v1`). *V 05 10 87* is this build.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## How it works

~~~mermaid
flowchart TB
  A["Win against opponent 7 (end_bout)"] --> B["Dungeon, Drax leaves his window (end_bout_final_stage)"]
  B --> C["Each pass: start or move the bolt (final_stage_attack)"]
  C --> D{"Bolt at the player?"}
  D -- no --> C
  D -- yes --> E{"Move in the list of the path? (check_attack_contact)"}
  E -- no --> F["Player falls, YOUR END HAS COME"]
  E -- yes --> G{"Player at column $1C or more? (check_final_goal)"}
  G -- no --> C
  G -- yes --> H["Princess, THANKS BIG BOY"]
  F --> I["Back to the demo (quit_to_demo)"]
  H --> I
~~~

The final stage is a short game of its own inside the main loop. The flag `final_stage` has bit 7 set for the full stage. Four parts of the game read this flag and stop their work (**Code**):

- The computer does not choose moves (`ai_choose_moves`), and the program does not test hits (`check_hits`).
- The walk-in of a bout (`update_walk_in`) does not run.
- `animate_fighters` animates and draws only fighter 0 into the work bitmap.

Fighter 1 is not on the screen. The bitmap shows only fighter 0, and fighter 1 stands at its start column `$1F`. `draw_fighter_sprites` gives no sprites to a fighter at column `$1E` or more (**Code**).

The player keeps the joystick and all moves. Drax and the princess are hardware sprites, not fighters. Two calls at the end of each pass control them: `final_stage_attack` for the bolt and `set_end_figure` for the figure (**Code**).

### The start of the final stage

[`end_bout` `$83FB`](../src/combat/end_of_bout.asm#L6) ends each bout. After a won bout, it compares `opponent_index` with 7. Below 7, the next opponent comes. At 7, it jumps to [`end_bout_final_stage` `$8497`](../src/combat/end_of_bout.asm#L98). The player then stands at the home column 3, because `end_bout` waited for the walk back (**Code**). That routine does these steps:

1. It shows the dungeon. When the throne room is on the screen, it calls `change_scene`. It also copies `scene_index` into `walk_in_active`, and both values have bit 7 clear.
2. It mirrors the shared sprite images back when a mirror is pending.
3. It sets `final_stage` to `$80` and draws one frame of the fighters with `update_fighters_frame`.
4. It waits 50 frames (1 second).
5. [`swap_block_col13` `$8D50`](../src/story/end_swaps.asm#L6) removes Drax from the middle window. It swaps a block of 4 x 4 characters at row 9, column 13 with a store.
6. `swap_end_shapes` swaps the 13 sprite shapes `$53-$5F` with the shapes of the end story.

The store of step 5 holds `$FF` bitmap bytes and colour `$0E`. `fill_block_stores` writes these values at each start of the game. Thus the window shows a plain colour where Drax stood (**Code**). Both recordings of the final stage executed the swap (**Observed**).

The shapes `$53-$5F` hold shared images of the fight. The final stage does not need them, so the program uses the same sprite pointers for Drax, the princess and the bolt (**Conclusion**). The store at `$FC40` holds 4 shapes of the princess, 6 shapes of Drax and 3 shapes of the bolt (**Code**).

![The 13 sprite shapes of the end story, in multicolour](reference/images/end_story_sprites-multicolour.png)

The 13 shapes of `end_story_sprites`: the princess (4), Drax (6) and the bolt (3).

### Drax and his bolts

[`final_stage_attack` `$84B6`](../src/story/final_stage.asm#L6) runs in each pass. It does nothing when `final_stage` is clear or when the player reached the goal. Else it does these steps (**Code**):

1. When no bolt flies, it starts one. Sprite 4 gets animation `$15` (three shapes, white, hi-res) at X `$FF`, Y `$A2`.
2. It reads `RASTER` at `$84D1` and keeps bit 0. This bit is the path of the bolt, and it selects motion `$0A` or `$0B` from `bolt_motions`.
3. It requests sound `$DD` on the three voices.
4. It changes the pose set between 0 and 1. Pose set 1 shows Drax with a raised arm.
5. It calculates the column of the bolt: X / 8 - 6. When that value is less than the column of the player, the bolt is at the player. Then it calls `check_attack_contact` and `check_final_goal`.

The pose set is 1 for one pass at the start of each bolt, then 0 again. Thus Drax raises his arm for one pass when he throws a bolt (**Code**). One instruction at `$84C4` loads `wait_counter`, and the next instruction loads A again. That load has no effect (**Code**).

The raster line at the read depends on the time of the code in the pass. A person cannot predict it, so the path is random for a player (**Conclusion**). The program uses no other random source here. A replay with the same input gives the same paths: all replays of `final_lose` and `final_win` pass (**Observed**).

The two motions fly at 4 pixels for each frame (**Code**):

| Path | Motion | Steps | Height of the bolt |
|---|---|---|---|
| 0 | `$0A` | left, 64 frames | Y `$A2` for the full flight |
| 1 | `$0B` | down and left, 8 frames, then left, 56 frames | Y `$A2` to `$C2`, then `$C2` |

`move_sprite_left` switches the sprite off below X `$38` (**Code**). Then `final_stage_attack` starts the next bolt in the next pass.

### The contact and how to pass a bolt

[`check_attack_contact` `$851B`](../src/story/final_stage.asm#L62) runs when the bolt is at the player. The path selects a list of 4 moves from `bolt_pass_move_ptrs`. When the move of the player is in the list, the bolt stops and switches off. When it is not in the list, the player dies (**Code**).

| Path | Moves in the list | Joystick of the moves (from `move_select_rows`) |
|---|---|---|
| 0 (high bolt) | `$06`, `$05`, `$11`, `$12` | `$06`: hold down in a crouch. `$05`: down and fire in a crouch. `$11`, `$12`: down with forward or back from a stand. |
| 1 (low bolt) | `$04` | up from a stand |

The list of path 1 has `$FF` in its last 3 entries, so only move `$04` passes a low bolt (**Code**). Move `$17`, the first move after down from a stand, is not in the list of path 0 (**Code**). **Conclusion:** a player who pushes down too late can die under a high bolt.

The check compares `fighter_move` only. It does not read `fighter_pose`, so the new pose routine of this build does not change the check (**Code**).

The two recordings show both paths. In `final_win`, the program read only the list of path 0, and the player passed each bolt with rolls and a crouch. In `final_lose`, the program read only the list of path 1, and the player who stood still died (**Observed**). In `final_lose`, the program also read both entries of `bolt_motions`. Thus it started at least one bolt on each path (**Observed**).

The program checks the bolt only at the contact. The bolt has no collision with the sprite or with the bitmap (**Code**). The contact comes early when the player is far to the right. The bolt starts at X `$FF`, which gives column `$19`. Thus at column `$1A` or more, the contact comes in the pass that starts the bolt (**Code**). The player cannot see the path before the contact there (**Conclusion**).

The first bolt reaches a player at column 3 when the bolt is below X 72. That takes about 46 frames, a little less than 1 second (**Conclusion**, from the motion speed).

### The goal and the princess

[`check_final_goal` `$856B`](../src/story/final_stage.asm#L107) runs only after a passed bolt. When the player is at column `$1C` or more, the story ends with a win. Column `$1C` is also the home column of fighter 1 in `fighter_home_column` (**Code**). The routine runs its own loops and does not return to the main loop (**Code**):

1. It sets `final_goal_reached` to `$80` and switches off sprites 0-4. Drax and the bolt go from the screen.
2. The player stands for 25 frames.
3. The player walks back (move `$02`) to column 3. Each step updates the fighter and waits 5 frames.
4. It requests the sounds `$89`, `$8A` and `$8B` on the three voices and waits 50 frames.
5. `swap_block_col23` removes the princess from the right window.
6. It sets the pose set to 2 and calls `set_end_figure`. The princess stands in the arena.
7. The player walks forward (move `$01`) to column `$17`.
8. The player does move `$13` and the program waits 150 frames.
9. It shows "THANKS BIG BOY", waits 250 frames and jumps to `quit_to_demo`.

**Conclusion:** the goal check needs a bolt contact. At column `$1C` or more, the next bolt comes at once, and its path is random. One move passes only one path. Thus the last bolt is a 50 % chance for a player who holds one move.

The loops of steps 3, 7 and 8 call `update_fighters_frame`. In this build, that routine does not set `fighter_pose`, see [The pose of the player in the end loops](#the-pose-of-the-player-in-the-end-loops).

![The barbarian with a raised arm beside the princess, at the end of the story (build V 05 05 87)](../../game_v1/docs/images/final_princess.png)

The end of `final_win` in build V 05 05 87: the player beside the princess, the right window empty, mode text 1PLR (**Observed** in `game_v1`). No image of this build exists.

### The lose path

`check_attack_contact_hit` runs when the move of the player is not in the list. It sets move `$1B` and locks it. The move sequence of `$1B` ends with a hold, so the player falls and stays on the floor (**Code**). Then the routine runs its own loop and updates the fighter until 150 frames pass. It shows "YOUR END HAS COME", waits 200 frames and jumps to `quit_to_demo` (**Code**). The player has no energy loss before the death: one bolt kills (**Code**).

The routine does not stop the bolt. The IRQ moves the bolt on until it is below X `$38` (**Code**).

![The final stage: YOUR END HAS COME, Drax at the right, the player down at the left (build V 05 05 87)](../../game_v1/docs/images/final_stage_drax.png)

The end of `final_lose` in build V 05 05 87: Drax at the right, the player on the floor, the princess in her window. **Observed** in `game_v1`. No image of this build exists.

### Back to the demo

[`quit_to_demo` `$94C1`](../src/main/quit_to_demo.asm#L6) ends both paths. When `final_stage` has bit 7 set, it calls `swap_block_col13` and `swap_end_shapes` again. Each swap undoes itself on the second call, so Drax returns to the window and the shared sprite shapes return (**Code**). After a win, it also calls `swap_block_col23`, and the princess returns. Then it shows the throne room and restarts the game in the demo (**Code**). `init_game_state` clears `final_stage`, `final_goal_reached` and `final_scene_pose` at the restart (**Code**).

## Changes from V 05 05 87

The code and the data of the final stage are the same in both builds. Only the addresses change: the final stage module moves by +$0A, `set_end_figure` by +$1A and the end scene data by +$51 (**Code**). The page of V 05 05 87 is [../../game_v1/docs/final_stage.md](../../game_v1/docs/final_stage.md). The shared page [../../docs/versions.md](../../docs/versions.md) lists all changes of the build. Four changes of the build touch the final stage.

### The pose of the player in the end loops

V 05 10 87 sets `fighter_pose` only in the new routine [`set_fighter_poses` `$878C`](../src/fighter/pose_update.asm#L6). `main_loop` calls it after `animate_fighters` in each pass. [`update_fighters_frame` `$85F0`](../src/story/final_stage.asm#L174) calls `animate_fighters` and `draw_fighter_sprites`, but not `set_fighter_poses` (**Code**). In V 05 05 87, `animate_fighter` writes `fighter_pose` at each step, so the same loops update the pose (**Code**).

`animate_fighter` draws the bitmap image of the fighter from the move sequence. `draw_fighter_sprites` sets the hardware sprite parts of the fighter from `fighter_pose` (**Code**). Thus, in the loops of the death and of the end story, the sprite parts keep the pose of the last pass (**Conclusion**). An example: pose `$31` of move `$13` has two sprite parts for fighter 0. The crouch pose `$3A` of move `$06` has none (**Code**). **Conclusion:** when the last pass shows the crouch, the end of the story can show move `$13` without its two sprite parts. The knowledge comment of `update_fighters_frame` says "The main loop does the same steps". That is not correct for this build.

### Another time for each pass

The main loop of V 05 10 87 has the new call `set_fighter_poses`, and the raster IRQ has a busy flag (**Code**). Thus a pass takes another time, and the bolts come at other frames for the same input (**Conclusion**). The `final_win` record file of this project holds the crouch for 70 frames before the second roll. The record file of V 05 05 87 holds it for 25 frames (**Observed**, `tests/record/final_win.json` of both projects). Both record files wait for the instruction after the store to `final_stage`: `$84A7` here and `$849D` in V 05 05 87.

### The move tables

Move `$12` is in the list of path 0. Its sequence now ends with the poses `$2D`, `$2E`. The move number stays the same, so it passes a high bolt as before (**Code**). Row 7 of `move_select_rows` gives the next move during move `$18`. For down-back, it gives move `$12` in V 05 05 87 and move `$00` in V 05 10 87 (**Code**). **Conclusion:** in V 05 05 87, down-back after a roll can start a move that passes a high bolt. In this build, the same input makes the player stand, and a high bolt kills.

### The sound request

The new flag `raster_irq_busy` takes `$CE`, so the music variables move up by 1. `final_stage_attack` and `check_final_goal` write the sound requests to `sound_request` at `$DD-$DF`. V 05 05 87 has them at `$DC-$DE`. The sound numbers `$DD` and `$89-$8B` are the same (**Code**).

## The data

### The figure records

[`set_end_figure` `$8E31`](../src/story/end_figure.asm#L6) runs in each pass while `final_stage` has bit 7 set. The pose set selects one of 4 records of 12 bytes from `end_scene_ptrs`. The routine writes the record into sprites 3-0 and restarts each animation at its first step. It also sets bit 8 of X for sprites 0-3 (**Code**).

| Bytes | Meaning |
|---|---|
| 0-3 | Animation of sprites 3, 2, 1, 0, with bit 7. 0 switches the sprite off. |
| 4-7 | X of sprites 3, 2, 1, 0. Bit 8 of X is always set. |
| 8-11 | Y of sprites 3, 2, 1, 0, minus `$A2`. |

| Record | Pose set | Sprite 3 | Sprite 2 | Sprite 1 | Sprite 0 | Shows |
|---|---|---|---|---|---|---|
| `end_scene_0` | 0 | off | `$0F` | `$10` | `$11` | Drax stands |
| `end_scene_1` | 1 | `$12` | `$13` | `$14` | `$11` | Drax throws |
| `end_scene_2` | 2 | off | `$0B` | `$0C` | `$0D` | the princess |
| `end_scene_3` | none | off | `$0B` | `$0E` | `$0D` | the princess with another body shape |

No code sets the pose set to 3. Thus `end_scene_3` and its shape `$56` are not used (**Code**). No recording read the pointer or the record of set 3 (**Observed**).

### The bolt tables

`bolt_motions` holds the two motions `$8A` and `$8B`. `bolt_pass_move_ptrs` points to `bolt_pass_moves_0` (`$86 $85 $91 $92`) and `bolt_pass_moves_1` (`$84 $FF $FF $FF`). Only the bolt of the final stage reads these tables (**Code**). The goblin uses `pair34_motions` and `pair34_anims` (**Code**).

### The block stores

`block_store_a` (128 bytes) and `block_colours_a` (16 bytes) hold the window of Drax while he is in the arena. `block_store_b` and `block_colours_b` hold the window of the princess. The bitmap rows of a block are `$140` bytes apart, and the colour RAM rows are 40 bytes apart (**Code**).

## The state machine of the final stage

~~~mermaid
stateDiagram-v2
  state "Bout" as Bout
  state "Bolt flies" as Fly
  state "Contact" as Contact
  state "Player dies" as Die
  state "End of the story" as End
  state "Demo" as Demo
  [*] --> Bout
  Bout --> Fly: win against opponent 7
  Fly --> Contact: bolt column < player column
  Fly --> Fly: bolt below X $38
  Contact --> Fly: move in the list, column < $1C
  Contact --> End: move in the list, column >= $1C
  Contact --> Die: move not in the list
  Die --> Demo: 350 frames
  End --> Demo: walks and 400 frames
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Bout | won bout, `opponent_index` = 7 | Bolt flies | `end_bout_final_stage` |
| Bolt flies | X / 8 - 6 < `fighter_x` | Contact | `final_stage_attack` |
| Bolt flies | X of the bolt below `$38` | Bolt flies (new bolt) | `move_sprite_left`, `final_stage_attack` |
| Contact | move in the list, `fighter_x` < `$1C` | Bolt flies (new bolt) | `check_attack_contact_avoided` |
| Contact | move in the list, `fighter_x` >= `$1C` | End of the story | `check_final_goal` |
| Contact | move not in the list | Player dies | `check_attack_contact_hit` |
| Player dies | 150 + 200 frames | Demo | `quit_to_demo` |
| End of the story | walks, 150 + 250 frames | Demo | `quit_to_demo` |

## The worked example: the throw of Drax

The record `end_scene_1` at `$CD02` has these bytes:

```
$92 $93 $94 $91   $00 $18 $18 $18   $00 $00 $15 $2A
```

1. Bytes 0-3 give the animations: sprite 3 `$12`, sprite 2 `$13`, sprite 1 `$14`, sprite 0 `$11`.
2. Bytes 4-7 give X. With bit 8 set, sprite 3 is at X 256 and sprites 2-0 are at X 280.
3. Bytes 8-11 give Y minus `$A2`: sprite 3 at `$A2`, sprite 2 at `$A2`, sprite 1 at `$B7`, sprite 0 at `$CC`.
4. Sprites 2, 1 and 0 are Drax from the head to the feet. Each sprite is 21 lines high, and the Y steps are 21 (`$15`).
5. Sprite 3 is 24 pixels to the left of the head. It shows the arm that throws.

Animation `$12` has one shape: the pointer byte `$3A` plus `$20` gives shape `$5A`. The animation flag `$84` gives a multicolour sprite with colour 4, purple. `end_scene_0` has 0 for sprite 3, so the arm goes off in the next pass (**Code**). The bolt starts at X `$FF`, Y `$A2`, at the height of the head of Drax (**Code**).

## Still open

- Does the end of the story of this build show move `$13` without its sprite parts? A run of `final_win` with a screen at the start of move `$13` can show it. The same run can show the sprite parts of the fall on the lose path.
- In `final_lose`, which bolt on path 0 did not reach the player? A trace of `final_stage_attack` and of `attack_path` in the final stage can show it.
- Can the player stand at column 0 or 1? There, the bolt usually goes off below X `$38` before the contact. Then no bolt kills the player, except when the IRQ comes between the two reads of the bolt. A run that walks back in the final stage can show it.
- Did the record file of V 05 05 87 fail on this build, and at which bolt? A replay of that input on this build can show it.
- What are the sounds `$DD` and `$89`-`$8B`: effects or a tune? The sound page can tell it.
- How many passes does the main loop take for each frame in the final stage? A trace of `main_loop` in the final stage can show it. The answer gives the exact time of the contact.
