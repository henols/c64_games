# The game flow (Part 1, V 05 10 87)

The game flow connects the fights of Part 1, Combat Practice, in build V 05 10 87. After the start, the program shows a demo: two computer fighters fight in the arena with the sunset. F1 starts the set-up and selects one or two players, and F7 starts the game. One player fights the computer at levels 0 to 7 until the player loses. Two players fight one bout against each other with a bout clock of 90 seconds. Part 1 has no final stage. (**Code**)

The flow starts the walk-in and ends each bout. It adds the time bonus, changes the scene between the sunset and the forest, and quits to the demo. It also reads the keys for the music, the pause, the version text and the quit. (**Code**)

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge of `practice_v2`.
- A *frame* is one PAL screen, 1/50 of a second. The raster interrupt runs one time in each frame.
- A *pass* is one run of `main_loop`. A pass has no frame wait, so it takes as many frames as its work needs.
- A *bout* is one fight from the walk-in to the kill. The *walk-in* is the start of a bout: the two fighters walk to each other.
- The *level* is [`opponent_index` `$BE`](../src/constants.asm#L99), 0-7. It selects the AI tables of the computer. The demo uses level 4.
- The *scene* is [`scene_index` `$C4`](../src/constants.asm#L105): 0 is the arena with the sunset, 1 is the forest.
- The *bout clock* is [`time_left` `$C8`](../src/constants.asm#L109), in seconds.
- A *flag* is a byte in which bit 7 set means "on". Many routines do nothing while a flag is on.
- Player 1 is fighter 0, joystick port 2. Fighter 1 is player 2 (joystick port 1) or the computer. In the demo, the computer moves both fighters.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## How it works

The program has no title screen. The demo is the title, and the game returns to the demo after each game. Each game mode uses the same main loop. Flags tell each routine of the loop if it must work in this pass. (**Code**)

~~~mermaid
flowchart TB
  A["Start: memory, VIC, interrupts, sound (start)"] --> B["Demo: computer against computer, level 4"]
  B -->|F1| C["Set-up: level 0, F1 changes 1PLR and 2PLR"]
  C -->|F7| D["Walk-in of a bout, clock 90 s"]
  D --> E["Bout: one pass of the main loop for each step"]
  E -->|two players, time 0| T["Time-out: both fighters go home"]
  T --> D
  E --> F["Kill: the goblin drags the loser away"]
  F --> G["Winner goes home, both fighters reset"]
  G -->|one player won| H["Next level, other scene"]
  H --> D
  G -->|one player lost| J["Wait 200 frames, quit to the demo"]
  G -->|two players| K["Time bonus, wait 200 frames"]
  K --> J
  J --> B
~~~

[`start` `$8009`](../src/init/init.asm#L6) prepares the machine and runs into [`main_loop` `$80BB`](../src/main/main_loop.asm#L6). The main loop never returns. Each end of a game goes through [`quit_to_demo` `$9357`](../src/main/quit_to_demo.asm#L6), which resets the stack and jumps to `restart`. The state machine at the end of the page gives each change of state. (**Code**)

### The start and the initialisation

The Fairlight crack jumps to `start` after its own code. The cartridge header CBM80 at `$8000` also points to `start`, so a hardware reset starts the game again. RESTORE does nothing, because the NMI vector points to an RTI. The page [../../docs/releases.md](../../docs/releases.md) tells about the crack. (**Code**)

`start` writes 0 into `sound_off`, so the game starts with the sound effects. Then [`restart` `$800E`](../src/init/init.asm#L11) does these steps in this order (**Code**):

1. [`init_game_state` `$9110`](../src/init/state.asm#L6) clears all flags of the game, also `two_players` and the new `raster_irq_busy`. It writes 1 into `demo_mode` and 4 into `opponent_index`, so the demo starts.
2. It writes `$25` into `$01`: RAM at `$A000` and `$E000`, I/O at `$D000`, no BASIC and no KERNAL.
3. It selects VIC bank 1, the screen at `$4400` and the bitmap at `$6000`, in multicolour bitmap mode.
4. It writes the IRQ vector (`$9394`) and the NMI vector (`$93C5`, an RTI). The raster interrupt comes at line `$FA`.
5. It clears the sprites, saves the clean fight background and resets the colours and the sprite scripts.
6. `init_fighters` puts both fighters at their start columns 0 and `$1F` with energy 12 and score 0. It sets `walk_in_active`, so the first bout starts with a walk-in.
7. It builds the mirror table at `$02AA` and the mask table at `$03AA`.
8. With the sound effects, it starts the CIA 1 timers A and B, silences the SID and fades the volume in. With the music, it keeps the timers, and the music continues.
9. It enables the interrupts and continues into `main_loop`.

A restart thus keeps the choice of F3, but it clears each other state of the game. The scores go back to 0, and `two_players` goes back to 0. (**Code**)

### The main loop

`main_loop` calls 22 routines and jumps back. Part 2 of the same build calls 24 routines: Part 1 has no `final_stage_attack` and no `set_end_figure`. Each routine tests its own flags. The calls come in this order (**Code**):

1. **The status texts.** It animates the corner blocks and prints the mode text, the counter, the energy bars and the scores. The texts are bitmap characters, so the loop prints them again in each pass.
2. **The time-out.** [`check_time_out` `$830A`](../src/combat/time_out.asm#L6) ends a two-player bout at time 0. See "The bout clock and the time-out".
3. **The input.** `read_joysticks` reads port 2 for player 1, and port 1 for player 2 in a two-player game. `ai_choose_moves` gives a joystick value to each computer fighter.
4. **The fighters.** It copies the clean background into the work bitmap and steps the move of each fighter. `set_fighter_poses` sets the pose of each fighter, and `check_decapitation` and `start_goblin` follow. Then it copies the work bitmap to the screen.
5. **The rules.** It calculates the distance, finds the hits, mirrors the shared sprites and turns the fighters after they pass each other.
6. **The flow.** `update_walk_in` runs the walk-in, `end_bout` ends a bout after a kill, and `check_player_idle` starts the idle move of a player who does nothing.
7. **The keys.** `read_keys` reads the function keys, Q and CTRL+V.

The main loop has no frame wait. A pass takes as long as its work, and the bitmap copies and the fighter drawing are slow. The attract recording has 1466 passes in about 15000 frames of the demo. A pass thus takes about 10 frames on average, about 5 passes each second. (**Observed**)

The raster interrupt does the work that needs a fixed pace. At line `$FA`, [`raster_irq_bottom` `$93E5`](../src/irq/irq_handler.asm#L57) moves the sprites, runs the sprite scripts and calls `count_down_timers`. This routine counts down the idle timers, `wait_counter` and the bout clock. When `sprites_frozen` bit 7 is set, the interrupt skips all of this work. (**Code**)

### The attract demo

The demo starts after each start and after each game. `demo_mode` is 1, so `read_joysticks` reads no joystick, and `ai_choose_moves` moves both fighters. Both fighters use the AI tables of level 4, and the counter shows `04`. The mode text shows DEMO. (**Code**)

![The arena with the sunset, from build V 05 05 87](../../practice_v1/docs/images/practice_sunset.png)

The arena with the sunset. The screenshot comes from `practice_v1`, build V 05 05 87. The bitmap and the screen bytes of the picture are the same in V 05 10 87 (**Code**).

In the demo, the random number of the computer comes from the CIA 1 timers: timer B low EOR timer A low. These timers drive the sound interrupts and run all the time. Thus the demo fights depend on the cycle of each read, not only on the frames. (**Code**) The recordings record each read of `$DC04` and `$DC06` for this reason (**Observed**).

A demo bout ends only with a kill, because `check_time_out` returns at once when `demo_mode` is not 0. After each kill, `end_bout` clears both scores and changes the scene. The next demo bout starts with a walk-in, and `opponent_index` stays 4. (**Code**) The attract recording runs the end of the demo bouts, the clear of the scores and the scene change (**Observed**, coverage).

### The keys

[`read_keys` `$923B`](../src/input/keyboard.asm#L6) reads the keyboard matrix one time in each pass. CIA 1 port A selects a row, and port B gives the columns. The routine has no edge test, so a key acts in each pass that finds it pressed. (**Code**)

| Key | Row, bit | Effect | Condition |
|---|---|---|---|
| CTRL+V | 7 bit 2, 3 bit 7 | Shows "V 05 10 87" and "WHY DID YOU PRESS ME" while V stays pressed | Always |
| F1 | 0 bit 4 | Starts the set-up, then changes 1PLR and 2PLR in each pass | Before F7 |
| F3 | 0 bit 5 | Changes between the sound effects and the music | Always |
| F5 | 0 bit 6 | Pauses until the next F5 | Not during the set-up |
| F7 | 0 bit 3 | Starts the game | Only during the set-up |
| Q | 7 bit 6 | Quits to the demo | Always |

The joystick in port 1 uses the same lines of CIA 1 port B as the keyboard columns. Thus player 2 can act as a key (**Code**):

- Left (bit 2) looks like CTRL. The routine then reads the V key.
- Right (bit 3) looks like F7, and fire (bit 4) looks like F1.

After F7, these keys have no effect. In the demo and the set-up, the fire button of player 2 acts as F1, and right acts as F7 (**Code**). The two_players recording shows it. Its F1 key press came before the first pass of `read_keys`. Later, each read of the F1 column with bit 4 clear has a value of port 1, for example `$EE` for up with fire. The test of the V key also ran without a CTRL press. (**Observed**) Thus player 2 started the set-up with fire and the game with right (**Conclusion**).

F3 first fades out the sound with `stop_sound`. Then it changes bit 7 of `sound_off`. Bit 7 set means "music, no effects", and bit 7 clear means "effects, no music". (**Code**) The keys recording executed the F3 code (**Observed**).

Q jumps to `quit_to_demo` from each state (**Code**). No recording executed the Q path (**Observed**, coverage).

### The pause and the version text

Both keys stop the main loop inside `read_keys`. The raster interrupt continues, so the music continues. (**Code**)

F5 writes `$80` into `sprites_frozen` and calls `busy_wait`, a loop of 65536 passes of 13 cycles, about 0.86 seconds. This wait lets the player release F5. Then [`read_keys_pause_wait` `$92F9`](../src/input/keyboard.asm#L101) reads F5 until the next press. After the press, it writes 0 into `sprites_frozen`. (**Code**)

With `sprites_frozen` set, the raster interrupt does not move the sprites and does not call `count_down_timers`. Thus the goblin and the hit sprites stop, and the bout clock stops during the pause. The text PAUSED is in the text table as text `$85`, but no code prints it. (**Code**)

A press of F5 longer than `busy_wait` ends the pause at once after the wait. When F5 is still pressed in the next pass, a new pause starts (**Code**). The keys recording executed the pause, and F1 came during the pause with no effect (**Observed**, coverage).

CTRL+V writes `$80` into `sprites_frozen` and prints text `$81` in a loop while V stays pressed. When the player releases V, it writes 0 into `sprites_frozen`, and `reset_fight_colours` removes the text. (**Code**) The keys recording executed this loop (**Observed**).

### The set-up: one or two players

F1 in the demo starts the set-up. `read_keys` writes `$80` into `setup_active` and 0 into `opponent_index`, `game_started` and `demo_mode`. When the forest shows, it calls `change_scene`, so each game starts with the sunset. Then it calls `init_fighters` and resets the sprite scripts. (**Code**)

Then F1 continues at [`read_keys_f1_clock` `$92AE`](../src/input/keyboard.asm#L63). Before F7, this code resets the bout clock and toggles `two_players` between 0 and 1. It does this in each pass that finds F1 pressed. (**Code**) These facts follow (**Conclusion**):

- `init_game_state` writes 0 into `two_players`. Thus a press of F1 that one pass finds gives 2PLR.
- A press that an even number of passes find gives 1PLR. The player sees the mode text and presses F1 again until it shows the wanted mode.
- A press shorter than a pass can fall between two reads, and then it has no effect.

The recordings show these cases. The facts come from the reads of the keyboard port in `read_keys` and from the coverage (**Observed**):

- In the decapitation, fight and win_bout recordings, exactly one pass found the F1 press of 10 frames. All three games started with two players.
- The fight recording reached the time-out, and win_bout ended with the time bonus. In decapitation, no fighter attacks, so no kill comes.
- In the two_decap, two_win and two_players recordings, the F1 press of 3 frames came before the first pass of `read_keys`. No pass found it.
- Thus two_decap and two_win stay in the demo. In two_players, the joystick of player 2 started the set-up and the game, see "The keys".

F1 has one more case. During the demo, a turn or a kill sets `turn_request` or `bout_loser`. F1 then skips the start of the set-up, but it still toggles `two_players` (**Code**). The next F1 that starts the set-up toggles it again (**Conclusion**).

During the set-up, the main loop runs, but most routines do nothing. `animate_fighters`, the joystick, the computer, the hits and the walk-in all test `setup_active`. F5 has no effect. (**Code**)

F7 during the set-up writes `$80` into `game_started` and 0 into `setup_active`, and resets the bout clock. Now F1 has no effect until the end of the game. `walk_in_active` is still set from `init_fighters`, so the walk-in of the first bout starts in the next pass. (**Code**)

### The walk-in

[`update_walk_in` `$8355`](../src/combat/walk_in.asm#L6) runs while bit 7 of `walk_in_active` is 1. It gives move `$01`, walk forward, to both fighters. It sets the bout clock to 90 seconds when it gives this move. It also requests the sound effects `$89`, `$8A` and `$8B`. (**Code**)

The walk-in also calls `add_time_bonus` in each pass. In the demo and in a one-player game, this call only clears `bout_winner`. (**Code**)

When `fighter_distance` is less than 6 columns, the walk-in ends. The routine clears `walk_in_active` and starts the idle timers of both fighters. Now the joysticks, the computer and the hit test work. (**Code**) All recordings executed the end of the walk-in (**Observed**, coverage).

### A one-player game

With 1PLR, the player fights the computer. `read_joysticks` reads port 2 for fighter 0. `ai_choose_moves` looks at the pose of fighter 0 and moves fighter 1. The counter shows the level, `00` to `07`. (**Code**)

A one-player bout has no time limit, because `check_time_out` works only in a two-player game. The bout ends only when one fighter dies: the energy reaches 0, or a decapitation hits. (**Code**)

`check_player_idle` starts the idle move when the player gives no joystick input until the idle timer is 0. The timer starts at `$FF`, so the wait is about 5 seconds. The computer can decapitate an idle player. (**Code**)

After the bout, `end_bout` selects the next step (**Code**):

- **The player won.** It increments `opponent_index` and changes the scene. At level 7, the level stays 7, and only the scene changes.
- **The player lost.** It waits 200 frames, 4 seconds, and jumps to `quit_to_demo`.

Thus a one-player game has no end. After level 7, the player fights level 7 again until he loses. The score stays from bout to bout. (**Code**) No recording of `practice_v2` executed the end of a one-player bout (**Observed**, coverage).

### A two-player game

With 2PLR, `read_joysticks` reads port 2 for fighter 0 and port 1 for fighter 1. `ai_choose_moves` does nothing, and `check_player_idle` works for both fighters. The counter shows the bout clock. (**Code**)

A two-player game has one bout. The bout ends with a kill. A time-out does not end it: the fighters go home and start the bout again with full energy. After the kill, `end_bout` adds the time bonus, waits 200 frames and jumps to `quit_to_demo`. (**Code**) The win_bout recording ran this path to the demo (**Observed**, coverage).

### The bout clock and the time-out

The walk-in sets `time_left` to 90 seconds with `reset_timer`. [`count_down_timers` `$97AF`](../src/irq/timers.asm#L6) decrements it after each 50 frames. It does not count during the walk-in, the time-out, the pause and after a kill. (**Code**) Build V 05 05 87 starts the clock at 60 seconds, see [../../docs/versions.md](../../docs/versions.md).

At time 0, `check_time_out` starts the time-out, only in a two-player game outside a turn (**Code**):

1. It sets `time_out_active`. The joysticks, the hit test and the idle move stop.
2. Each fighter walks back to the home column of its facing: column 3 for facing right, `$1C` for facing left.
3. When both fighters stand at home, it clears `time_out_active` and gives both fighters energy 12 and a full idle timer.
4. It sets `walk_in_active`. The next walk-in sets the clock to 90 seconds again.

The scores stay. The fight and two_players recordings executed each step of the time-out (**Observed**, coverage).

### The time bonus

[`add_time_bonus` `$83A6`](../src/score/time_bonus.asm#L6) works only in a two-player game outside the demo, and only when `bout_winner` bit 7 is set. `start_winner_move` sets this flag at the kill. (**Code**)

For each second left on the clock, the routine adds 10 points to the score of the winner. It then decrements `time_left`, prints the score and the counter, and waits one frame. The clock thus counts down to 0 on the screen, one second in each frame. At the end, the routine clears `bout_winner`. (**Code**) A win with 45 seconds left gives 450 points in about 45 frames (**Conclusion**). The win_bout recording executed the bonus loop (**Observed**, coverage).

### The end of a bout

A kill sets `bout_loser` to `$80` + the number of the loser. `start_winner_move` gives a winner move to the other fighter. When the loser lies on the floor, [`start_goblin` `$9045`](../src/combat/bout_end.asm#L115) starts the goblin as sprites 3 and 4. The goblin drags the body to the right. (**Code**)

[`end_bout` `$83F5`](../src/combat/end_of_bout.asm#L6) waits until the loser is at column `$28` or more, outside the screen. Then the winner turns to its start direction and walks to its home column: 3 for fighter 0, `$1C` for fighter 1. At the home column, `end_bout_reset` resets both fighters for the next bout (**Code**):

1. The loser goes to its start column, and both fighters stand in move `$00`, face to face.
2. Each fighter gets energy 12 and a full idle timer. In the demo, both scores go back to 0.
3. The routine sets `walk_in_active` again and clears `bout_loser` and the goblin flags.
4. When the computer lost and `sprite_mirror_state` is not 0, it requests the mirror back.

Then [`end_bout_next` `$8461`](../src/combat/end_of_bout.asm#L69) selects the next step (**Code**):

| Mode | Result | Next step |
|---|---|---|
| Demo | Each kill | Change the scene, next demo bout |
| Two players | Each kill | Time bonus, wait 200 frames, quit to the demo |
| One player | The player lost | Wait 200 frames, quit to the demo |
| One player | The player won, level 0-6 | Next level, change the scene |
| One player | The player won, level 7 | Change the scene, level 7 again |

In Part 2, the win against level 7 starts the final stage. In Part 1, the same jump goes to `end_bout_swap_background`. (**Code**)

### The scenes: the sunset and the forest

[`change_scene` `$8D21`](../src/screen/scene.asm#L6) changes the centre of the picture to the other stored picture. It fades the sound out and swaps the centre of the bitmap and the colours with the store at `$D000` and `$E000`. Then it fades the sound in, and `scene_index` changes between 0 and 1. (**Code**)

Each game starts with the sunset. The flow changes the scene after each demo bout and after each won bout of a one-player game. A two-player game never changes the scene. (**Code**) The attract and two_win recordings executed the scene change after a demo bout (**Observed**, coverage).

![The forest arena, from build V 05 05 87](../../practice_v1/docs/images/practice_forest.png)

The forest arena after the scene change. The screenshot comes from `practice_v1`, build V 05 05 87.

Both scenes have the same background colour. The raster interrupt at line `$72` writes `scene_top_colour` into the background colour register, and both bytes are `$09`, brown. (**Code**) The page [../../game_v2/docs/graphics.md](../../game_v2/docs/graphics.md) explains the stored picture.

### Quit to the demo

`quit_to_demo` switches off the sprites and removes the fighters from the screen. It mirrors the sprite images back when `sprite_mirror_state` is not 0. It tests `final_stage`, but Part 1 never sets this flag. When the forest shows, it changes back to the sunset. Then it resets the stack pointer to `$FF` and jumps to `restart`. (**Code**)

`restart` calls `init_game_state` again, so the demo starts with level 4, new scores and one player. A quit from inside a subroutine thus leaves no return addresses on the stack. (**Code**) The win_bout recording returned to the demo after the two-player bout (**Observed**, coverage).

## The data

### The flags of the flow

Most routines of the main loop start with a test of some of these flags. A flag with bit 7 set stops the routine. The flags are zero page bytes from [`bout_loser` `$AF`](../src/constants.asm#L84) to [`final_stage` `$BB`](../src/constants.asm#L96). (**Code**)

| Flag | Set by | Cleared by | Stops |
|---|---|---|---|
| `setup_active` | F1 | F7 | Fighter animation, joystick, computer, hits, walk-in, idle move, F5 |
| `game_started` | F7 | `init_game_state` | F1 |
| `walk_in_active` | `init_fighters`, `end_bout_reset`, the time-out | `update_walk_in` | Joystick, computer, hits, idle move, clock |
| `turn_request` | The fighters pass each other | The turn move | Joystick, computer, hits, time-out, start of the set-up |
| `bout_loser` | A kill (energy 0 or decapitation) | `end_bout_reset` | Joystick, computer, hits, idle move, clock, start of the set-up |
| `time_out_active` | Time 0, two players only | Both fighters at home | Joystick, computer, hits, idle move, clock |
| `bout_winner` | `start_winner_move` | `add_time_bonus` | Nothing: it selects the score of the time bonus |
| `final_stage` | No code of Part 1 | `init_game_state` | Computer, hits, walk-in |

Two bytes of the flow are not bit 7 flags. [`demo_mode` `$B3`](../src/constants.asm#L88) is not 0 in the demo. It stops the joystick and the idle move, and it gives both fighters to the computer. `two_players` is 0 for one player and 1 for two players. It is also the number of the highest human fighter, so the joystick loop reads fighter 1 only with two players. (**Code**)

### The status texts

`print_text` draws each text into the bitmap. A text record has a column, a row, a colour byte and the characters, and `$24` ends it. `$0D` starts a new line with a new column, row and colour byte. (**Code**)

| Text | Column, row | Content | Printed by |
|---|---|---|---|
| `$81` | 15, 17 and 10, 18 | `V 05 10 87` and `WHY DID YOU PRESS ME` | CTRL+V |
| `$82`, `$83`, `$84` | 18, 24 | `1PLR`, `2PLR`, `DEMO` | `show_mode_text` |
| `$85` | 17, 17 | `PAUSED` | No code |
| `$86` | 19, 5 | Two digits: level or time | `show_counter` |
| `$87`, `$88` | 12, 5 and 23, 5 | Score of fighter 0 and fighter 1, 5 digits | `show_energy_scores`, `add_time_bonus` |
| `$89` | 11, 17 | `YOUR END HAS COME` | No code of Part 1 |
| `$8A` | 9, 17 | `THANKS BIG BOY` | No code of Part 1 |
| `$8B-$97` | 0 and 34, rows 0-1 | The energy bar for energy 0-12 | `show_energy_scores` |

Text `$80` is `000` at row 22, and no code prints it. Texts `$89` and `$8A` belong to the final stage of Part 2. (**Code**)

## The state machine of the game

The state is a set of flags, not one byte. The diagram gives the states that a player sees. (**Code**)

~~~mermaid
stateDiagram-v2
  state "Demo (demo_mode 1)" as Demo
  state "Set-up (setup_active)" as Setup
  state "Walk-in (walk_in_active)" as Walk
  state "Bout" as Bout
  state "Time-out (time_out_active)" as TimeOut
  state "End of a bout (bout_loser)" as End
  state "Time bonus (bout_winner)" as Bonus
  [*] --> Demo
  Demo --> Setup: F1
  Setup --> Walk: F7
  Walk --> Bout: distance less than 6
  Bout --> TimeOut: two players, time 0
  TimeOut --> Walk: both fighters at home
  Bout --> End: kill
  End --> Walk: demo, or one player won
  End --> Demo: one player lost
  End --> Bonus: two players
  Bonus --> Demo: after 200 frames
  Bout --> Demo: Q
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Start | Always | Demo | `start` |
| Demo | F1, no turn, no kill | Set-up | `read_keys` |
| Demo | Kill | End of a bout | `check_hits`, `check_decapitation` |
| Set-up | F1 | Set-up, other number of players | `read_keys` |
| Set-up | F7 | Walk-in | `read_keys` |
| Walk-in | `fighter_distance` less than 6 | Bout | `update_walk_in` |
| Bout | Two players, `time_left` 0, no turn | Time-out | `check_time_out` |
| Time-out | Both fighters at home | Walk-in, energy 12 | `check_time_out` |
| Bout | Energy 0 or decapitation | End of a bout | `check_hits`, `check_decapitation` |
| End of a bout | Demo, loser at column `$28`, winner at home | Walk-in, other scene | `end_bout` |
| End of a bout | One player won | Walk-in, next level or level 7, other scene | `end_bout` |
| End of a bout | One player lost | Demo, after 200 frames | `end_bout` |
| End of a bout | Two players | Time bonus | `end_bout` |
| Time bonus | Clock at 0 | Demo, after 200 frames | `add_time_bonus`, `end_bout` |
| Each state | Q | Demo | `quit_to_demo` |
| Each state but the set-up | F5 | Same state, paused until F5 | `read_keys` |

## The worked example: the counter

This example decodes text `$86` and the change that `show_counter` makes to it. The bytes come from `text_counter` at `$B9AF`. (**Code**)

| Offset | Byte | Meaning |
|---|---|---|
| 0 | `$13` | Column 19 |
| 1 | `$05` | Row 5 |
| 2 | `$E3` | Colour byte |
| 3 | `$30` | Digit 1 |
| 4 | `$30` | Digit 2 |
| 5 | `$24` | End of the text |

In the demo and in a one-player game, [`show_counter` `$8291`](../src/score/status_line.asm#L19) writes `$30`, the character 0, into digit 1. It writes `opponent_index` OR `$30` into digit 2. Level 3 thus shows `03`. (**Code**)

In a two-player game, `show_counter` shows `time_left`. It subtracts 10 until the value is negative, and it counts the subtractions. With 59 seconds, the steps are (**Code**):

1. 59, 49, 39, 29, 19 and 9 are not negative. X counts 0 to 5, and `cur_fighter` keeps the last value, 9.
2. 9 - 10 is negative, so the loop ends with X = 5.
3. Digit 1 gets 5 OR `$30` = `$35`, the character 5. Digit 2 gets 9 OR `$30` = `$39`, the character 9.

The counter shows `59`. At the start of a bout, it shows `90`. (**Code**)

## Shared with Part 2

Part 1 and Part 2 of build V 05 10 87 share the code of the fight. The pages of `game_v2` explain these parts. The addresses in Part 1 are lower (**Code**):

| Part | Page | Shift of Part 1 against Part 2 |
|---|---|---|
| The status line, the walk-in, the end of a bout | This page | -6 |
| The joysticks, the AI, the hits, the fighter animation and drawing | [fighters](../../game_v2/docs/fighters.md), [combat](../../game_v2/docs/combat.md), [ai](../../game_v2/docs/ai.md) | -$16C |
| The scene change, the sprites, the goblin, `read_keys` to F1 | [graphics](../../game_v2/docs/graphics.md) | -$16C |
| From F3 in `read_keys`: the IRQ, the music and the sound | [sound](../../game_v2/docs/sound.md), [graphics](../../game_v2/docs/graphics.md) | -$16A |
| The texts and the tables of moves, hits and AI | [combat](../../game_v2/docs/combat.md), [ai](../../game_v2/docs/ai.md) | -$16A |
| The pictures, the font, the corners and the end story sprites from `$D000` | [graphics](../../game_v2/docs/graphics.md) | 0 |

For example, `change_scene` is at `$8D21` in Part 1 and at `$8E8D` in Part 2. Part 1 also keeps dead parts of the final stage: a copy of `set_end_figure` at `$8CC5` that nothing calls, and the data of the end scene. The page [../../docs/versions.md](../../docs/versions.md) gives each difference between the parts. (**Code**)

## Changes from V 05 05 87

The flow of Part 1 changed in these points from build V 05 05 87 (**Code**):

- The bout clock starts at 90 seconds, not 60.
- F5 and CTRL+V set `sprites_frozen`. The sprites and the bout clock stop during the pause and the version text.
- The version text has the second line "WHY DID YOU PRESS ME".
- The demo clears both scores after each bout.
- The flag `raster_irq_busy` stops a second sprite update in the raster interrupt.
- The main loop calls `set_fighter_poses`, and it calls `check_turn_around` after `check_hits`.

The page [../../docs/versions.md](../../docs/versions.md) explains each change, and `practice_v1` has the game flow of the earlier build.

## Still open

- How many passes find a press of F1 of 10 frames in the middle of the demo? In the recordings, the press came at the first pass. A run that counts the calls of `read_keys_f1_clock` can show it.
- Does the end of a one-player bout work as the code shows? No recording of `practice_v2` executed it. A run with two presses of F1 that wins and loses a one-player bout can show it.
- Can player 2 change the number of players with fire during the set-up, after a press of F1? A run that presses fire on port 1 between F1 and F7 can show it.
- Does F1 during a turn or a kill in the demo change the number of players of the next game? A run that presses F1 at that moment can show it.
- What does Q do in each state? No recording executed the Q path. A run that presses Q in the demo, the set-up, a bout and the time bonus can show it.
- How long does a pass take in the set-up, the walk-in and a bout? A run that counts the frames between two passes in each state can measure it.
