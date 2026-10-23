# The computer opponent (version II)

The computer opponent plays the red fighter in the one-player game, and both fighters in the demo. In each frame it looks at the move of the opponent, the distance and its own move. Then it gives one move command, as a joystick does for a human player. Twelve skill levels set how fast it reacts, how often it attacks and how it answers an attack. The rank of the player selects the level, so the opponent gets stronger at each new dan.

Version II keeps the decision process of version I. It adds a new kind of answer and a table that changes high attacks into low attacks. It also adds a special action against the flying kick and new values in four level tables. It keeps the three bugs of version I. The page [../../v1/docs/ai.md](../../v1/docs/ai.md) explains the parts that stayed the same. The page [../../docs/versions.md](../../docs/versions.md) gives the full list of the changes between the versions.

**Conventions.**
- Addresses are C64 addresses of version II. Names are the names of the knowledge. A name with `v1:` is a name of version I.
- A *frame* is one pass of the bout loop. The AI runs one time in each frame for each fighter that the computer controls.
- A *move* is a value of `fighter_move` from `$00` to `$18`. A *command* is the move that the AI writes into `fighter_input` and `ai_command`. The page [fighters.md](fighters.md) lists the moves.
- This page uses the names of the moves in the table under this block.
- The *level* is `cpu_skill` of the fighter, 0 to 11. It is the index into the eight level tables.
- *Random* is the next value of `ai_next_random`, an 8-bit LFSR. It gives each value from 1 to 255 one time in 255 calls. It never gives 0.
- *d* is the signed distance of the opponent in `fighter_distance`.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

| Move | Name | Move | Name |
|---|---|---|---|
| `$01` | stand | `$0B` | low kick |
| `$02` | walk forward | `$0C` | mid kick |
| `$03` | walk back | `$0D` | high kick |
| `$04` | crouch | `$0E` | flying kick |
| `$05` | jump | `$0F` | roundhouse |
| `$06` | high punch | `$10` | back sweep |
| `$07` | crouch punch | `$11` | back kick |
| `$08` | back roll | `$12` | about turn |
| `$09` | somersault | `$13` | low block |
| `$0A` | foot sweep | `$14` | high block |
| `$18` | low punch | | |

## How it works

[`fighter_get_input` `$2834`](../src/fighter/fighter_input.asm#L30) jumps to [`ai_update` `$22CF`](../src/ai/ai_opponent.asm#L6) when `cpu_controlled` of the fighter is 1. `ai_update` does its tests in the same order in each frame. The first test that applies gives the command of the frame. The order is the same as in version I (**Code**).

~~~mermaid
flowchart TB
  A["Opponent shows a hit reaction?"] -->|yes| A1["Stand at once after a flying kick, else after the release time"]
  A -->|no| B["Special action pending?"]
  B -->|yes| B1["Run special action 1-9 (ai_dispatch_special)"]
  B -->|no| C["Opponent attacks?"]
  C -->|"stand or walk, attack in range"| D["Choose a response (ai_choose_response)"]
  C -->|"no attack, or own move busy"| E["Movement: hold, release, about turn"]
  D --> D1["Attack / block or jump / special action / random move"]
  E -->|"stand or walk"| F["Position: walk, stop or about turn"]
  F -->|"opponent close"| G["Attack delay, then the attack choice"]
  G --> G1["Distance table, move substitution, level rules"]
~~~

1. **The opponent is hit.** The AI keeps its attack command for `ai_release_timer` frames, then it stands. After a flying kick it stands at once. This step did not change (**Code**).
2. **A special action is pending.** `ai_special_action` holds an action from 1 to 9. [`ai_dispatch_special` `$2689`](../src/ai/ai_opponent_2521.asm#L235) jumps to it through `ai_special_jump_table`. Version II adds action 9 (**Code**).
3. **The danger check.** An opponent move with the flag in `move_attack_flags` is an attack, unless the move runs backwards. A correct block stays. A stand or a walk goes to step 4. Other own moves continue or return to the stance. Version II removed one test here, the held-crouch test (**Code**).
4. **The response.** `hit_range_test` must find the attack in range. After the reaction delay, the AI chooses one of four kinds of response with random AND `ai_response_mask`. Version I had three kinds (**Code**).
5. **The movement.** The AI holds an end pose for a random time, completes an about turn or repeats its command. This step did not change (**Code**).
6. **The position.** The AI walks toward the opponent, stops for a random time or turns when the opponent is far behind. The limits of d did not change (**Code**).
7. **The attack.** After a random attack delay, the AI reads a move from a distance table. Version II then applies the flying-kick rule and the move substitution. The old level rules and the variant of moves `$0F` and `$10` follow (**Code**).

The runs executed all code of the AI except special action 7 at `$2661-$2676`. They also executed all new code of version II (**Observed** in the coverage of the runs).

## What changed from version I

The changes come from an alignment of the instructions of `v1:ai_update` with `ai_update`. All other instructions are the same. Only the targets of the branches and jumps moved (**Code**).

### The held-crouch test is gone

In version I, [`v1:ai_check_opponent` `$1D65`](../../v1/src/ai/ai_opponent.asm#L24) had one more test at `$1D67-$1D7B`, 21 bytes. It applied when the opponent held the end pose of its move. At levels 5 and up, a held crouch (opponent input `$04`) sent the AI to the low-move test. Any other held pose sent it to the movement. Levels 0-4 treated a held attack as an attack (**Code**). Thus levels 5 and up of version I never attacked a player who held a crouch. The AI got the command stand, unless its own move was a crouch, a sweep, the low kick or the crouch punch (**Code**).

[`ai_check_opponent` `$22EC`](../src/ai/ai_opponent.asm#L24) of version II goes directly to the test of `anim_reverse`. A held pose now counts as an attack at all levels when its move has the attack flag. No test of version II compares the level with 5 (**Code**). **Conclusion:** the new move substitution replaces this rule. Version II answers a low opponent with low attacks at all levels.

### The response has four kinds

[`ai_choose_response` `$237D`](../src/ai/ai_opponent.asm#L105) masks a random value with `ai_response_mask`. Version I used bit 7 for an attack and bits 5-6 for a block or jump. All other values gave a special action. Version II divides the bits in this way (**Code**):

| Bits of random AND mask | Version I | Version II |
|---|---|---|
| bit 7 | attack choice at once | attack choice at once |
| bits 5-6 (v1), bits 4-6 (v2) | block or jump from `move_counter_moves` | block or jump from `move_counter_moves` |
| bits 0-3 | special action from `ai_special_by_move` | special action from `ai_special_by_move` |
| no bit | special action from `ai_special_by_move` | random move: somersault `$09` or low kick `$0B` |

The special action falls back to the block or jump when `ai_special_by_move` holds 0 for the opponent move. Of the attack moves, only the high kick `$0D` has 0. This did not change (**Code**).

The random move is new in [`ai_response_random_move` `$238E`](../src/ai/ai_opponent.asm#L116). It takes a second random value. When bit 7 of that value is 1, the command is the somersault `$09`. Else the command is the low kick `$0B` (**Code**). The new masks in the level tables decide how often each kind occurs, see [The level tables](#the-level-tables).

### The flying-kick rule

The flying-kick rule is new in the path for fighters that face each other. When the distance table gives the flying kick `$0E`, [`ai_attack_flying_kick` `$2521`](../src/ai/ai_opponent_2521.asm#L6) tests the level. Levels 7 and up walk forward with command `$02`. Levels 0-6 keep the flying kick. The move substitution does not apply to this result (**Code**).

`ai_attack_facing_table` holds `$0E` at the indexes `$40`, `$43` and `$45`. These indexes are d + spread = `$0D`, `$10` and `$12`, with the opponent in front (**Code**). Thus a strong computer opponent does not jump at a middle distance. It walks nearer and chooses again (**Conclusion**).

The path for fighters with the same facing has no flying-kick rule. Its table `ai_attack_same_facing_table` holds `$0E` at the indexes `$09`, `$0C` and `$0E` (**Code**).

### The move substitution

[`ai_substitute_move` `$2698`](../src/ai/ai_opponent_2521.asm#L244) is new. Both paths of the attack choice call it after the read of the distance table. It looks at the move of the opponent. It tests if the opponent is in the crouch `$04`, the crouch punch `$07`, the foot sweep `$0A` or the back sweep `$10`. In that case it replaces the chosen move with the entry of [`ai_move_substitute` `$12D0`](../src/game/entry_and_tables_1299.asm#L26). For all other opponent moves the chosen move stays. The routine keeps the chosen move in the new zero-page byte `ai_move_temp` (**Code**).

The table has one entry for each move `$00-$18`. These eight entries change the move (**Code**):

| Chosen move | Substitute |
|---|---|
| `$06` high punch | `$0B` low kick |
| `$07` crouch punch | `$0A` foot sweep |
| `$0C` mid kick | `$0A` foot sweep |
| `$0D` high kick | `$0B` low kick |
| `$0E` flying kick | `$0A` foot sweep |
| `$0F` roundhouse | `$10` back sweep |
| `$11` back kick | `$0A` foot sweep |
| `$18` low punch | `$0B` low kick |

Entry `$00` holds `$01`. The other 16 entries hold their own index. The tests of version I apply after the substitution. A foot sweep `$0A` needs level 2 or more, a crouch punch `$07` starts with a crouch, and `$0F` and `$10` get a variant (**Code**).

High attacks miss an opponent that crouches or sweeps. The table changes them into the low kick, the foot sweep or the back sweep, which can hit a low opponent (**Conclusion**). The table is not in the AI area. It is between the texts and the fighter tables of `entry_and_tables.asm` (**Code**).

The path for facing fighters tests `$0E` before the substitution. Thus only the same-facing path uses the entry `$0E` → `$0A`. Against a crouching opponent in front, levels 0-6 still use a flying kick (**Code**).

### The inverted branch

In version I, [`v1:ai_choose_attack` `$1F29`](../../v1/src/ai/ai_opponent.asm#L277) went to the same-facing path with one `beq`. The offset of that branch was `$76`. The flying-kick test, the call of the substitution and the flying-kick rule add 17 bytes between the branch and its target. The offset becomes `$87`, and a branch can go only `$7F` bytes forward (**Code**).

[`ai_choose_attack` `$24B1`](../src/ai/ai_opponent.asm#L284) of version II has `bne ai_check_opp_block` and a `jmp ai_choose_same_facing` at `$24B8-$24BC`. **Conclusion:** the assembler refused the branch, and the author inverted it by hand and added the JMP.

### The zero variant is gone

[`ai_attack_variant` `$2567`](../src/ai/ai_opponent_2521.asm#L49) changes the moves `$0F` and `$10` with random AND `ai_variant_mask`. In version I, the value 0 gave the somersault `$09`. Version II removed these 9 bytes at v1 `$1FD8-$1FE0`. The value 0 now keeps the move, as the values `$01-$1F` do (**Code**).

### Special action 9

`ai_special_by_move` gives the special action against each opponent move. Its entry for the flying kick `$0E` changed from 1 to 9. `ai_special_jump_table` got a tenth word, the address of [`ai_spec_high_kick_or_duck` `$26B8`](../src/ai/ai_opponent_2521.asm#L263). The other eight actions are the same code (**Code**).

Special action 9 works in this order (**Code**):

1. At levels 0-6 it sets the action to 1 and jumps to `ai_spec_duck_then_sweep`. The AI crouches and sweeps when the opponent stands again, as in version I.
2. At levels 7 and up it takes a random value. When bit 7 is 1, it does step 1. Action 1 sweeps at frame `$19` of the opponent at these levels.
3. Else it ends the special action and gives the high kick `$0D` at once.

All writes of action 9 use X, so it adds no bug of the kind in action 8 (**Code**).

### The level tables

[`ai_setup_level` `$2593`](../src/ai/ai_opponent_2521.asm#L82) copies one entry of each level table at the start of each bout. The code is the same as in version I. The tables have the same layout and size at `$27A9-$2807` (v1 `$21D4-$2232`). Four tables did not change: hold and release, spread, variant and reaction delay. The walk table changed only at level 8 (**Code**).

| Level | Attack delay v1 | v2 | Walk v1 | v2 | Stop v1 | v2 | Response v1 | v2 |
|---|---|---|---|---|---|---|---|---|
| 0 | `$7F` | `$7F` | `$1F` | `$1F` | `$3F` | `$3F` | `$80` | `$A3` |
| 1 | `$1F` | `$1F` | `$3F` | `$3F` | `$3F` | `$3F` | `$8F` | `$B2` |
| 2 | `$0F` | `$0F` | `$1F` | `$1F` | `$1F` | `$1F` | `$8F` | `$F1` |
| 3 | `$0F` | `$0F` | `$3F` | `$3F` | `$3F` | `$3F` | `$60` | `$F0` |
| 4 | `$0F` | `$0F` | `$3F` | `$3F` | `$1F` | `$1F` | `$60` | `$70` |
| 5 | `$07` | `$07` | `$3F` | `$3F` | `$1F` | `$1F` | `$0F` | `$8F` |
| 6 | `$07` | `$7F` | `$3F` | `$3F` | `$0F` | `$0F` | `$0F` | `$7F` |
| 7 | `$07` | `$1F` | `$3F` | `$3F` | `$00` | `$00` | `$FF` | `$0F` |
| 8 | `$07` | `$07` | `$3F` | `$1F` | `$00` | `$0F` | `$0F` | `$7F` |
| 9 | `$07` | `$0F` | `$3F` | `$3F` | `$00` | `$07` | `$0F` | `$7F` |
| 10 | `$07` | `$3F` | `$3F` | `$3F` | `$00` | `$1F` | `$0F` | `$7F` |
| 11 | `$07` | `$1F` | (`$3F`) | (`$3F`) | `$00` | `$0F` | `$0F` | `$7F` |

The attack delay is random AND the mask, in frames. A stop mask of 0 means that the AI never stops a walk. The walk table has only 11 entries, so level 11 reads the first stop mask, `$3F` (**Code**).

The response mask gives these shares of the 255 random values. The shares are attack / block or jump / special action / random move (**Code**, counted from the masks):

| Level | Version I | Version II |
|---|---|---|
| 0 | 50 / 0 / 50 / - | 50 / 25 / 19 / 6 |
| 1 | 50 / 0 / 50 / - | 50 / 38 / 6 / 6 |
| 2 | 50 / 0 / 50 / - | 50 / 44 / 3 / 3 |
| 3 | 0 / 75 / 25 / - | 50 / 44 / 0 / 6 |
| 4 | 0 / 75 / 25 / - | 0 / 88 / 0 / 12 |
| 5 | 0 / 0 / 100 / - | 50 / 0 / 47 / 3 |
| 6 | 0 / 0 / 100 / - | 0 / 88 / 12 / 0 |
| 7 | 50 / 38 / 12 / - | 0 / 0 / 94 / 6 |
| 8-11 | 0 / 0 / 100 / - | 0 / 88 / 12 / 0 |

At levels 6 and 8-11 the random move occurs only for one value of 255. Against the high kick `$0D`, the share of the special action goes to the block or jump (**Code**).

These changes have the effects that follow (**Conclusion**):

- Levels 4, 6 and 8-11 block or jump against 88 % of the attacks. In version I, levels 5-6 and 8-11 always used a special action.
- Level 3 now attacks back against half of the attacks, as levels 0-2 do. In version I, level 3 never attacked back.
- Levels 8-11 stop again while they walk. In version I, no level from 7 up stopped.
- Level 6 waits up to 127 frames before an attack, as level 0. Levels 7 and 9-11 also wait longer than in version I.

## The bugs of version I

Version II keeps three bugs of version I. The game flow of version II corrects the fourth bug, but `ai_setup_level` still has no limit (**Code**).

- **Shared parameters.** `ai_setup_level` writes `ai_hold_mask`, `ai_release_timer` of both fighters, `ai_spread_mask`, `ai_variant_mask`, `ai_attack_mask`, `ai_response_mask` and `ai_react_mask` without X. `bout_setup_fighters` calls it for fighter 0, then for fighter 1. Thus the level of fighter 1 sets these values for both fighters (**Code**). In the one-player game the computer is fighter 1, so its values are correct. In the demo, fighter 0 fights mostly with the level of fighter 1. Its own level applies only to the walk and stop masks and to the tests of `cpu_skill` (**Conclusion**).
- **`sta $92` without X.** Special action 8 in [`ai_spec_punch_or_crouch` `$263E`](../src/ai/ai_opponent_2521.asm#L181) writes action 5 with `sta ai_special_action` at `$2648`, now `sta $9D`. For fighter 1 it writes the slot of fighter 0 (**Code**). The v1 page tells the effect in the demo.
- **`cmp $0048,y`.** Special action 7, [`ai_spec_sweep_by_facing` `$2661`](../src/ai/ai_opponent_2521.asm#L206), compares with `cmp $0053,y`. Y is 14 from the dispatch, not the index of the opponent. Thus the compare reads `$0061`, `fighter_move` of fighter 0 (**Code**). No run executed this action (**Observed** in the coverage).
- **Levels above 11.** In version I the rank of the one-player game could grow to 22, and the AI then read the bytes after the level tables. Version II stops the promotions at `stage_counter` 10, see [Levels in the game and in the demo](#levels-in-the-game-and-in-the-demo) (**Code**).

## Levels in the game and in the demo

The level of the opponent comes from the game flow, not from the AI. All paths of version II give a level from 0 to 11, the range of the tables (**Code**).

- **The one-player game.** `game_one_player` sets `cpu_skill` of fighter 1 to 0 at NOVICE. Each promotion adds 1 to the level and to `stage_counter` together. [`game_1p_rank_cap_test` `$1C27`](../src/game/game_modes.asm#L146) stops the promotions at `stage_counter` 10, the rank 10TH DAN. Thus level 0 is NOVICE, level n is the rank nTH DAN, and the highest level is 10 (**Code**). The rank stays 10TH DAN in the run of `tests/rank_cap.json` (**Observed**).
- **After 10TH DAN.** [`game_1p_rank_wrap` `$1C5B`](../src/game/game_modes.asm#L170) gives fighter 1 a random level from 7 to 10 after each two won bouts: random AND 3, plus 7. Version I gave 2 to 10 (**Code**). The runs executed this code (**Observed** in the coverage).
- **The demo.** [`demo_play` `$1CD2`](../src/game/game_modes.asm#L239) copies `frame_random` into `ai_random` first. Version I did not do this. Then each fighter gets random AND 7, plus 3, plus the carry from `ai_next_random`. This gives the levels 3 to 11 (**Code**).

Level 11 occurs only in the demo. At level 11 the walk mask comes from the first stop mask, `$3F`. This value is the same as the walk mask of level 10, so the short table has no effect (**Code**).

Each new demo starts from the value of `frame_random`, so the demo levels change from one demo to the next (**Conclusion**). The one-player game also copies `frame_random` into `ai_random` at its start, as in version I (**Code**).

## The worked example

The computer is level 7 (7TH DAN) and faces the player. The player is in front at d = `$0E` and crouches with move `$04`. The values come from the bytes of the tables (**Code**).

1. d = `$0E` is below `$15`, so [`ai_attack_by_distance` `$24E8`](../src/ai/ai_opponent.asm#L313) runs after the attack delay.
2. The base index is d + `$33` = `$41`. The spread mask of level 7 is `$03`, so the index is `$41` to `$44`.
3. Bytes `$41-$44` of `ai_attack_facing_table` are `$0C $0A $0E $0A`.
4. Index `$41` gives the mid kick `$0C`. The opponent crouches, so the substitution gives `$12D0` + `$0C` = `$0A`. Level 7 is 2 or more, so the command is the foot sweep `$0A`.
5. Index `$42` or `$44` gives the foot sweep `$0A`. The substitution keeps it, and the command is `$0A`.
6. Index `$43` gives the flying kick `$0E`. Level 7 changes it to the command `$02`, walk forward.

Thus the computer sweeps with a chance of 3 in 4, and walks nearer with a chance of 1 in 4. At level 6 with the same random values, index `$43` gives a flying kick against the crouching player (**Code**).

In version I, the same case at level 7 gave no attack. The held-crouch test sent the AI to the low-move test, and a standing AI got the command stand. Levels 0-4 of version I reached the table and used the mid kick for index `$41` (**Code**).

## The development leftovers

- [`ai_dead_repeat_jump` `$251E`](../src/leftovers/leftover_251e.asm#L6) holds `JMP ai_repeat_command` after an RTS. Nothing jumps to it. It is the same leftover as v1 `$1F8C`. Its operand moved with the label, so the author assembled it from the source (**Code**). The new flying-kick code starts directly after it (**Code**).
- The inverted branch at `$24B8` is a trace of the inserted code (**Conclusion**).
- Version II changed the level 8 value of the walk table but did not add the missing twelfth entry (**Code**).
- Entries 0-7 of both distance tables are never read. The smallest index is `$08`. Entry `$4F` of the facing table is never read, because the largest index is `$47` + 7 (**Code**). The coverage marks the first line of each table as never read (**Observed**).

## Still open

- Does `cpu_skill` reach 11 in the demo? Break at `$1CE1` and `$1CEA` and read A in a run of the demo.
- In the demo, do the shared parameters at `$1A6E` match the tables of the level of fighter 1? Compare `ai_hold_mask`, `ai_spread_mask`, `ai_attack_mask`, `ai_response_mask`, `ai_variant_mask`, `ai_react_mask` and `ai_release_timer` with the tables.
- Does `$2648` write `ai_special_action` of fighter 0 while X = 1 in the demo? Watch `$9D`.
- How often does the random move at `$238E` start in play at levels 0-4, and which move starts?
- Does the substitution at `$26B4` give low attacks in play? Break there and log the opponent move and A.
- With the same facing and an opponent in the back sweep `$10` in range, does special action 7 run, and which move follows?
- Is the computer at 6TH DAN slower to attack than at 5TH DAN in play? The attack mask of level 6 is `$7F`.
