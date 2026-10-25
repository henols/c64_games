# Combat: hits, energy and the end of a bout

A bout in Barbarian ends in one of two ways only. One fighter loses all 12 units of energy, or a sword cuts off his head. The game does not use the sprite collision of the VIC-II to find a hit. In each pass, it compares two pose numbers: the pose of the attacker and the pose of the defender. A table gives one record for each pair of poses that can touch. The record gives the distances where the blade hits and the reaction of the defender. It also gives the sound, the energy loss, the red hit sprite and the points. After a death or a decapitation, the winner makes his winner move, and a green goblin drags the body out of the arena. This page tells how the code does each step in build V 05 05 87 of Part 2.

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge.
- A *pass* is one run of `main_loop`. The main loop has no frame wait, so a pass takes about 10 frames. Each fighter shows one pose for each pass.
- A *pose* is the number in `fighter_pose` (`$00-$5B`). A *move* is the number in `fighter_move`, with bit 7 set: `$8D` is move `$0D`.
- The *attacker* is the fighter that the code tests for a hit. The *defender* is the other fighter.
- An *attack pose* is one of the 12 poses in `attack_poses`. Only these poses can hit.
- The *distance* is the difference of the two `fighter_x` values, in columns of 8 pixels, without a sign.
- A *hit record* is one of the 39 entries of 4 bytes in `hit_records`.
- Fighter 0 is player 1 (port 2). Fighter 1 is the computer in a one-player game of Part 2.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## How it works

~~~mermaid
flowchart TB
  A["Each pass: check_hits"] --> B{"Bout over, turn, walk-in, set-up or final stage?"}
  B -- yes --> Z["No test in this pass"]
  B -- no --> C["Attacker = fighter 1, then fighter 0"]
  C --> D{"Attacker in an attack pose? (find_attack_pose)"}
  D -- no --> N["Next attacker"]
  D -- yes --> E["Next entry of the hit list of that pose"]
  E --> F{"Entry for the defender pose?"}
  F -- "no, end of list" --> N
  F -- yes --> G{"Distance bit set in the hit record?"}
  G -- no --> E
  G -- yes --> H["Reaction move, sound and damage (apply_hit_damage)"]
  H --> I["Hit sprite and score"]
  I --> N
~~~

[`check_hits` `$879B`](../src/combat/hits.asm#L6) runs in each pass, after the fighters have their new poses and after `get_fighter_distance`. It does nothing when bit 7 is 1 in one of six flags: `bout_loser`, `turn_request`, `walk_in_active`, `setup_active`, `time_out_active` or `final_stage`. Thus no hit can occur after the end of a bout, while the fighters turn or walk in, or in the final stage (**Code**). The bolts of Drax use other code, see [final_stage.md](final_stage.md).

[`check_attack_hit` `$87B9`](../src/combat/hits.asm#L25) tests one attacker. It does these steps (**Code**):

1. `find_attack_pose` looks for the pose of the attacker in `attack_poses`. When the pose is not an attack pose, the test ends.
2. The index of the attack pose selects a word in `hit_list_ptrs`. The word points to the hit list of that pose: pairs of defender pose and hit record number, with `$FF` at the end.
3. The code reads the list from the start. It skips each entry with another defender pose.
4. At an entry with the defender pose, `get_hit_record` calculates the address of the hit record: `hit_records` + 4 x number.
5. The code calculates the distance again. At a distance of 8 or more, the test ends with no hit.
6. The code takes the bit of the distance from `bit_masks` and does an AND with byte 0 of the record. When the result is 0, the code goes to the next entry of the list (step 3).
7. When the bit is 1, the hit occurs. `apply_hit_damage`, `spawn_hit_sprite` and `add_hit_score` use bytes 1-3 of the record. The test then ends, so an attacker makes at most one hit in a pass.

The code tests fighter 1 first, then fighter 0. It does not look at the facing of the fighters. The distance has no sign, so the same record applies when the defender stands behind the attacker (**Code**). After the turn of the fighters, this case is rare (**Conclusion**).

### The attacks

The 12 attack poses belong to nine moves that the joystick selects. The table gives the joystick for a fighter that stands and faces right. The details of the moves are on [fighters.md](fighters.md). The distances, points and sprites come from the records that most entries of each list use (**Code**).

| Attack pose | Move | Joystick | Distances of most entries | Reaction of the defender | Points | Hit sprite |
|---|---|---|---|---|---|---|
| `$05`, `$07` | `$83` | fire + up-back | 0 (also 0-1 or 0-2) | `$99` | 50 | effect 1 or 2 |
| `$0C` | `$85` | fire + down (after the crouch `$97`) | 0-2 | `$8D` | 100 | effect 3 |
| `$17` | `$89` | fire + forward | 0-1 | `$8D` | 200 | effect 4 |
| `$1A` | `$87` | fire + back (the move starts with the three poses of the turn) | 0-3, 0-2 or 0-1 | `$8D`, or `$88` (decapitation) | 200, or 500 | effect 6 |
| `$1C` | `$8C` | fire + down-forward | 0 | `$99` | 100 | none |
| `$20` | `$8E` | fire + down-back | 0-2 | `$99` | 100 | effect 5 |
| `$22` | `$8F` | fire + up-forward | 0 | `$99` | 200 | none |
| `$24`, `$25`, `$26` | `$91` | down-forward (the roll) | 0 or 0-1 | `$99` | 0, and no damage | none |
| `$43` | `$8B` | fire + up | 0-2 | `$8D` | 200 | effect 6 |

No record allows a distance above 3. The records 1, 7 and 9 are in no list (**Code**).

The reaction moves are short. Move `$8D` shows the poses `$1D`, `$1E` and `$00`. Move `$99` shows the poses `$4C-$4F`. The record writes the reaction move also into `fighter_move_lock`, so the joystick cannot change the move until its last pose (**Code**). The roll knocks the opponent with move `$99`, but it takes no energy and gives no points (**Code**).

### Clashes and safe poses

Some records have reaction move 0 and damage 0. They play sound 2 (requests `$DA`, `$DB` and `$DC`) and do nothing else. Most of these entries pair an attack pose with the same attack pose: two swords meet (**Conclusion**). An example is `hit_list_00`: the pose `$05` against the poses `$05` and `$07` gives this clash (**Code**).

A defender pose that is not in a list is safe from that attack. The lists have 30-61 entries each. The reaction poses `$1D`, `$1E` and `$4C-$4F`, the death poses `$56`, `$57`, `$21` and `$59`, and the decapitation poses `$11-$14` are in no list. Thus a fighter cannot get a second hit while he shows a reaction pose (**Code**). The crouch pose `$3A` (move `$86`) is not in the list of the attack pose `$1A`, so a crouch protects the neck (**Code**).

### A bug: the second entry for a defender pose

Fourteen list entries repeat a defender pose of the same list. The first entry gives one set of distances, and the second entry gives other distances. An example in `hit_list_00`: pose `$17` with record `$13` (distance 0), then pose `$17` with record `$10` (a clash at distance 1-3) (**Code**).

[`get_hit_record` `$8832`](../src/combat/hits.asm#L96) shifts the record number two times into the high byte of `move_ptr`. The code needs 0 in that byte. `check_attack_hit` writes the 0 only one time, before the first entry. The first matching entry leaves `$C7` or `$C8` there. Thus a second matching entry gets a wrong record address (**Code**):

| Attack pose | Defender poses | Record of the table | Address that the code reads | Bytes there in the release |
|---|---|---|---|---|
| `$05` | `$17` | `$10` (clash) | `$E3ED` (`arena2_screen_tail`) | `$98 $98 $98 $98` |
| `$07` | `$17` | `$10` (clash) | `$E7ED` (`arena2_colours_tail`) | `$A7 $F7 $B7 $A7` |
| `$1A` | `$1B`, `$1C` | `$0D` (clash) | `$E7E1` (`arena2_colours`) | `$C5 $20 $FC $FC` |
| `$1A` | `$3F`, `$40`, `$41`, `$42`, `$44`, `$47`, `$4B` | `$0B` (hit, 200) | `$E3D9` (`arena2_screen`) | `$BC $BC $5C $5C` |
| `$20` | `$15` | `$0D` (clash) | `$E7E1` (`arena2_colours`) | `$C5 $20 $FC $FC` |
| `$43` | `$1B`, `$1C` | `$0D` (clash) | `$E3E1` (`arena2_screen`) | `$C0 $5C $50 $B0` |

The bytes come from the bottom row of the screen and the colours of the second arena. Some come from the 24 bytes after them. The scene change does not write these cells. **Conclusion:** the intended clash or hit does not occur. At some distances, these bytes give a hit with wrong numbers. The move can be above `$1D`, and the sound, sprite and score entries can be above the ends of their tables. For example, the attack pose `$1A` against the defender pose `$3F` at distance 2 starts move `$3C`, which has no entry in `move_seq_ptrs`.

No run showed this case. The coverage maps of the recordings mark only the code, so they do not show which records the code read. Build V 05 10 87 keeps the bug. But it adds two checks: no hit on a defender pose of `$5B` or more, and no points for a score entry of 5 or more. **Conclusion:** the authors saw the effects and did not find the cause. The details are on [../../docs/versions.md](../../docs/versions.md).

## Damage and energy

[`apply_hit_damage` `$8845`](../src/combat/hits.asm#L109) uses byte 2 of the record (**Code**):

1. The high nibble selects a triplet in `hit_sounds`. The code writes each byte that is not 0 into `sound_request` of that voice.
2. When the low nibble is 0, the hit takes no energy. Each other value takes exactly 1 unit: the code does a `DEC`, not a subtraction of the nibble.
3. If the corner block of the defender does not play its hit animation, the code starts it. Fighter 0 gets animation 2, and fighter 1 gets animation 3.
4. `fighter_energy` of the defender goes down by 1.
5. At 0 energy, `bout_loser` gets `$80` + the defender, and the defender starts the death move `$9B`.

Each fighter starts a bout with 12 units. `reset_fighter` sets this value. Thus 12 hits with damage kill a fighter, if no decapitation occurs first (**Code**). The recordings `win_bout`, `final_lose` and `final_win` write 1 into the energy of the computer, and one hit then ends the bout (**Observed**).

### The energy bars

[`show_energy_scores` `$82DA`](../src/score/status_line.asm#L62) prints one of the texts `text_energy_00` to `text_energy_12` in each pass. Each text has 2 rows of 6 characters at the top of the screen: column 0 for fighter 0 and column 34 for fighter 1. The characters "(" and ")" draw the two halves of a round symbol. Thus 6 round symbols show 12 units, and each hit removes one half (**Code**).

The corner block is 4 x 4 cells under the energy bar. Its hit animation shows 7 frames, one for each pass, and then stops. A hit during the animation does not start it again, but the energy still goes down (**Code**). The details of the corner animations are on [graphics.md](graphics.md).

### The trainer

The Hotline release puts `JSR $CF20` and a `NOP` at `$8880`, in place of the store to `corner_anim_pos` and the `DEC`. The routine at [`unused_cf20` `$CF20`](../src/data/unused_cf20.asm#L6) does the store and the `DEC` only for fighter 1. Thus player 1 does not lose energy. The switch `TRAINER` builds this patch. It is off in the default build (**Code**). The details are on [../../docs/releases.md](../../docs/releases.md).

## The hit sprites

[`spawn_hit_sprite` `$8896`](../src/combat/hits.asm#L173) uses the high nibble of byte 3 of the record. When it is not 0, the code starts a sprite in the first free slot. The entry in `hit_sprite_effects` gives the animation, the Y position and an X offset (**Code**).

All six entries use the sprite animation `$8A`: one red image for 10 frames, then the sprite stops. Only the position differs. The Y positions are `$9F` to `$C0` (**Code**). **Conclusion:** the red spot shows the blood of the hit, at the head, the body or the legs.

`set_sprite_x` puts the sprite at the column of the attacker x 8 + the offset + `$18`. For an attacker that faces left, the offset becomes `$30` - offset. The search for a free slot always found slot 0 in the recordings. The code that tests the next slot never ran (**Observed**).

## The score

[`add_hit_score` `$88E5`](../src/combat/hits.asm#L225) uses the low nibble of byte 3 of the record. It selects 5 decimal digits in `score_values`: 500, 200, 100 or 50 points. `add_score_digits` adds them to the score text of the attacker, `text_score0` or `text_score1`, one digit at a time with a carry (**Code**).

The score is a text of 5 digit characters. No binary score exists. The computer also gets points for its hits. `init_fighters` clears both scores. The start code and `read_keys` call it, but the end of a bout does not. Thus the score of player 1 grows from bout to bout (**Code**). The time bonus of `add_time_bonus` runs only in a two-player game, and Part 2 has no two-player game. The details are on [game_flow.md](game_flow.md).

## The decapitation

Only the attack pose `$1A` of move `$87` (fire + back) can cut off a head. Its hit list gives the records 4 and 5 for 29 defender poses (**Code**):

- Record 4 at distance 0-2: the stance `$00`, the walk poses `$01-$03` and `$33-$37`, and the poses `$32`, `$48` and `$51-$54`.
- Record 5 at distance 0-1: 14 other poses, for example the poses `$04-$06` of move `$83`.

The idle move `$9A` of a human player shows the poses `$52-$54`. Thus a player who does nothing loses his head when the computer swings at the correct distance (**Code**). The recording `decapitation` shows this: opponent 7 decapitates the idle player (**Observed**).

The record gives the defender move `$88`, sound 3 and 500 points. It takes no energy, so the energy of the defender has no effect (**Code**). In the next pass, [`check_decapitation` `$90F0`](../src/combat/bout_end.asm#L6) finds move `$88` and sets `bout_loser`. It starts three sprites at the position of the defender (**Code**):

| Sprite | Animation | Motion | Y | Conclusion |
|---|---|---|---|---|
| 0 | `$80` or `$81` by facing: a turning multicolour image | `$81` or `$82`: an arc in the facing direction of the loser, two smaller bounces with sound `$DF`, then animation `$84` or `$85` without motion | `$9D` | the head |
| 1 | `$83`: one black image | `$83` or `$84`: along the floor, at the speed of the head | `$CD` | the shadow of the head |
| 2 | `$82`: four red images, then the sprite stops | `$80`: no motion | `$9D` | the blood |

`move88_sprite0_anims` holds `$80`, `$81`, `$84`, `$85`, and the code reads only the first two. The head gets `$84` or `$85` later, from its motion. `move88_sprite_x` holds `$18` and `$48` (**Code**).

Move `$88` shows the poses `$11-$14` and then holds `$14`: the body falls (**Conclusion**).

## The end of a bout

### The winner move

[`start_winner_move` `$917B`](../src/combat/bout_end.asm#L83) runs after a death in `check_hits`, and after the start of a decapitation. It writes `bout_winner` and gives the winner one of two moves (**Code**):

- After a decapitation, or at a distance of 2 or more: move `$93`. It shows the poses `$3C` and `$00`, then `$2F-$31` and again `$2F`, and then it holds `$2F`.
- After a death at a distance of 0 or 1: move `$9C`. It shows the poses of move `$8C` (fire + down-forward), and then it starts move `$93`.

The recordings `attract`, `fight` and `win_bout` ran the code of move `$9C`. The recordings `decapitation`, `fight`, `final_lose`, `final_win` and `win_bout` ran the code of move `$93` (**Observed**).

The test of `bout_loser` is at the start of `check_hits`, not between the two attackers. **Conclusion:** both fighters can lose their last unit in the same pass. Fighter 1 hits first and sets `bout_loser` to `$80`. Then fighter 0, still in its attack pose, can hit fighter 1 and set `$81`. Then player 1 wins the bout with 0 energy. Build V 05 10 87 adds a test of `bout_loser` before each attacker. No run showed this case.

### The goblin

![The goblin drags the body away](images/goblin.png)

The green goblin drags the body of the loser out of the throne room. The winner stands at the left (**Observed**).

[`start_goblin` `$91A7`](../src/combat/bout_end.asm#L113) waits until the loser shows the last pose of his fall: `$59` after a death, or `$14` after a decapitation. Then it puts sprites 3 and 4 at X `$27` at the left edge, one above the other. They walk to the right with the animations `$86` and `$87` and the motion `$85`. `goblin_active` gets `$FF` (**Code**).

The raster interrupt calls [`update_goblin` `$9639`](../src/story/goblin.asm#L6) in each frame. It does three tests (**Code**):

1. After a decapitation, when sprite 3 reaches the head (sprite 0), the head and its shadow get new motions. The head flies to the right, and the motion requests sound `$DF` (**Conclusion:** the goblin kicks the head).
2. When sprite 3 reaches the column of the body + 5, the goblin stops for 100 frames with the animations `$88` and `$89`. Then it walks to the right again. `goblin_drags` gets `$FF`, and the code requests sound `$E2`.
3. While bit 7 of `goblin_drags` is 1, the code can add 1 to `fighter_x` of the loser. It does this when sprite 3 is at the edge of a column and in front of the body. The body moves with the goblin.

The code that plays sound `$EB` on three voices in step 1 never ran (**Observed**). The goblin also comes after a death without a decapitation, because `start_goblin` waits for pose `$59` (**Code**).

### Back to the start

[`end_bout` `$83F8`](../src/combat/end_of_bout.asm#L6) waits until the body is at column 40 or more, out of the screen. Then the winner turns with move `$9D` if he does not face his start direction. He walks with move `$82` to his home column, 3 or 28. There, the code resets both fighters, clears the flags of the bout and starts the walk-in (**Code**).

Then the result decides the next step. When the player lost, the game waits 200 frames and starts the demo. When the player won, `opponent_index` goes up by 1, or the final stage starts after opponent 7. The details are on [game_flow.md](game_flow.md) (**Code**).

A one-player bout in Part 2 has no time limit. Only the two-player code reads the bout clock (**Code**). Thus each bout ends with a death or a decapitation.

## The data

### The hit lists

`attack_poses` has the 12 attack poses `$05`, `$07`, `$0C`, `$17`, `$1A`, `$1C`, `$20`, `$22`, `$24`, `$25`, `$26` and `$43`. `hit_list_ptrs` has one word for each, in the same order. The 12 lists fill `$C2EA-$C7AB` (**Code**):

| Byte | Meaning |
|---|---|
| 0 | Pose of the defender. `$FF` ends the list. |
| 1 | Number of the hit record, `$00-$26`. |

### The hit records

`hit_records` at `$C7AC-$C847` has 39 records of 4 bytes (**Code**):

| Byte | Bits | Meaning |
|---|---|---|
| 0 | bit n | Distance n gives a hit. The table uses only bits 0-3. |
| 1 | all | Reaction move of the defender: `$8D`, `$99` or `$88`. 0: no reaction move. |
| 2 | 7-4 | Entry of `hit_sounds`, 1-4. |
| 2 | 3-0 | 0: no damage. Not 0: the defender loses 1 unit. |
| 3 | 7-4 | Entry of `hit_sprite_effects`, 1-6. 0: no sprite. |
| 3 | 3-0 | Entry of `score_values`, 1-4. 0: no points. |

### The tables that the records select

| Table | Entry | Bytes |
|---|---|---|
| `hit_sounds` | 1 | `$E9`, 0, `$EA`: a normal hit |
| `hit_sounds` | 2 | `$DA`, `$DB`, `$DC`: a clash |
| `hit_sounds` | 3 | `$E1`, `$E1`, 0: a decapitation |
| `hit_sounds` | 4 | `$EE`, `$EE`, 0: the attack pose `$22` |
| `hit_sprite_effects` | 1-6 | animation `$8A`, then Y `$B8`, `$B8`, `$C0`, `$B5`, `$9F`, `$A4` and X offset `$20`, `$30`, `$30`, `$30`, `$28`, `$30` |
| `score_values` | 1-4 | 00500, 00200, 00100, 00050 |

Entry 0 of each table is not used. The sound bytes are tune requests for the three voices. The sound page of this project tells more about them.

## The state machine of the end of a bout

The flags `bout_loser`, `goblin_active`, `goblin_drags` and `walk_in_active` hold the state. `check_hits`, `check_decapitation`, `start_goblin`, `update_goblin` and `end_bout` make the changes.

~~~mermaid
stateDiagram-v2
  state "Fight" as Fight
  state "Death fall (move $9B)" as Death
  state "Head cut (move $88)" as Cut
  state "Loser falls, winner move" as Fall
  state "Goblin walks in" as Walk
  state "Goblin drags the body" as Drag
  state "Winner walks home" as Home
  [*] --> Fight
  Fight --> Death: energy 0
  Fight --> Cut: record with move $88
  Death --> Fall: same pass
  Cut --> Fall: next pass
  Fall --> Walk: loser pose $59 or $14
  Walk --> Drag: goblin at the body
  Drag --> Home: body at column 40
  Home --> [*]: winner at home column, walk-in
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Fight | `fighter_energy` of the defender becomes 0 | Death fall | `apply_hit_damage` |
| Fight | a record gives move `$88` | Head cut | `check_attack_hit` |
| Death fall | `bout_loser` bit 7 set after both attackers | Loser falls, winner move | `start_winner_move` |
| Head cut | a fighter in move `$88`, `bout_loser` clear | Loser falls, winner move | `check_decapitation` |
| Loser falls | `fighter_pose` of the loser is `$59` or `$14` | Goblin walks in | `start_goblin` |
| Goblin walks in | column of sprite 3 - 3 = column of the body + 5 | Goblin drags | `goblin_grab_body` |
| Goblin drags | `fighter_x` of the loser is `$28` or more | Winner walks home | `end_bout` |
| Winner walks home | `fighter_x` of the winner is the home column | walk-in of the next bout | `end_bout_reset` |

## The worked example

The recording `win_bout` attacks with fire + down at distance 2. This example decodes that attack against a computer fighter in the stance `$00`. The bytes come from the release (**Code**).

| Address | Table | Index | Bytes | Meaning |
|---|---|---|---|---|
| `$C2C8` | `attack_poses` | 2 | `$0C` | pose `$0C` of move `$85` is attack pose 2 |
| `$C2D6` | `hit_list_ptrs` | 2 | `$C3D2` | the list `hit_list_02` |
| `$C3D2` | `hit_list_02` | entry 0 | `$00 $19` | defender pose `$00`: record `$19` |
| `$C810` | `hit_records` | `$19` | `$07 $8D $11 $33` | the record |
| `$CEA8` | `bit_masks` | 2 | `$04` | the bit of distance 2 |
| `$C84B` | `hit_sounds` | 1 | `$E9 $00 $EA` | requests for voices 1 and 3 |
| `$C860` | `hit_sprite_effects` | 3 | `$8A $C0 $30` | animation `$8A`, Y `$C0`, X offset `$30` |
| `$C87B` | `score_values` | 3 | `$00 $00 $01 $00 $00` | 100 points |

The code does these steps:

1. `$04` AND `$07` = `$04`, not 0: a hit.
2. Byte 1 = `$8D`. The defender gets move `$8D` and `fighter_move_lock` = `$8D`, at step 0.
3. Byte 2 = `$11`. Sound entry 1 writes `$E9` and `$EA` into the requests of voices 1 and 3. The damage nibble is 1, so the energy goes down by 1.
4. Byte 3 = `$33`. Sprite entry 3 puts a red spot at Y `$C0`, the lowest of the six positions. Score entry 3 adds 100 to `text_score0`.

At distance 3, `$08` AND `$07` = 0. The list has no other entry for pose `$00`, so the attack misses. The same attack against pose `$0A`, the first pose of move `$85`, uses record `$1A` (`$03`). It hits only at distance 0 or 1 (**Code**).

## Still open

- **The wrong hit records.** What does the game do when the bug reads a record at `$E3D9`, `$E3E1`, `$E7E1` or `$E7ED`? Run: a fight with fire + back at distance 2 against an opponent in pose `$3F`, with a breakpoint at `check_attack_hit_entry` and a watch on `move_ptr`.
- **The double death.** Can both fighters reach 0 energy in one pass? Run: set the energy of both fighters to 1 and give attacks at the same time.
- **The roll.** Which poses of the computer let a roll knock it at distance 0 or 1? Run: the recording `fight` with a breakpoint at `check_attack_hit_apply`.
- **The clash.** Which sound do the requests `$DA`, `$DB` and `$DC` play? Run: two fighters with the same attack at distance 0-3.
