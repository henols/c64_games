# Bruce Lee: object actions and poses

**Scope.**
- The action state of each actor: the number in [`actor_state`](../../src/constants.asm#L95) [`$BF`](../reference/variables.md#actor_state), its timer [`actor_state_timer`](../../src/constants.asm#L98) [`$CE`](../reference/variables.md#actor_state_timer) and its step delay [`actor_step_delay`](../../src/constants.asm#L122) [`$0106`](../reference/variables.md#actor_step_delay).
- The frame handlers of the states in [`continue_object_action`](../../src/object_actions.asm#L6) [`$2008`](../reference/modules/object_actions.md#continue_object_action) and the enemy behaviour states (spawn, appear, chase, walk, punch, strike, flying kick).
- Every state number, its meaning, its duration and its transitions, with three state diagrams and a full transition table.
- The pose selection in [`select_object_pose`](../../src/object_pose.asm#L6) [`$2780`](../reference/modules/object_pose.md#select_object_pose) and [`set_object_pose`](../../src/object_pose.asm#L311) [`$29A1`](../reference/modules/object_pose.md#set_object_pose): which pair of sprite frames each state shows.
- Sources: `src/object_actions.asm` (`$2008-$2508`), `src/object_pose.asm` (`$2780-$29C2`), the variables in `src/actor_vars.asm` and `src/constants.asm`, the tables [`action_delay_table`](../../src/room_tables.asm#L78) [`$4A8C`](../reference/modules/room_tables.md#action_delay_table) and [`actor_type_frame_base`](../../src/sprite_data.asm#L29) [`$59A5`](../reference/modules/sprite_data.md#actor_type_frame_base), and the sprite sheets in `assets/sprites/`.
- Reference: [object_actions.md](../reference/modules/object_actions.md), [object_pose.md](../reference/modules/object_pose.md), [actor_vars.md](../reference/modules/actor_vars.md), [actor_movement.md](../reference/modules/actor_movement.md).
- Not on this page: how the joystick or the demo stream selects a move ([actors.md](actors.md)), hits, damage and energy ([combat_collision.md](combat_collision.md)), how a frame number becomes sprite graphics ([sprites.md](sprites.md)), the order of the work in a pass ([main_loop.md](main_loop.md)).

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge.
- A *pass* is one run of [`main_loop`](../../src/main_loop.asm#L6) [`$1BC2`](../reference/modules/main_loop.md#main_loop), at most one pass every 3 frames. A *frame* is one raster interrupt chain (50 per second on PAL).
- An *actor* is one moving figure, numbered by its index X into the actor tables: actor 0 = Bruce, actor 1 = Yamo, actor 2 = the Ninja.
- A *step* of an actor is a pass in which [`actor_move_step`](../../src/actor_movement.asm#L32) [`$1C5B`](../reference/modules/actor_movement.md#actor_move_step) finds [`actor_step_delay`](../../src/constants.asm#L122) [`$0106`](../reference/variables.md#actor_step_delay) at 0. With a delay d in the table, the actor makes one step every d+1 passes.
- A *state* is the value of [`actor_state`](../../src/constants.asm#L95) [`$BF`](../reference/variables.md#actor_state). The *timer* is [`actor_state_timer`](../../src/constants.asm#L98) [`$CE`](../reference/variables.md#actor_state_timer). Y in the handlers is the timer at the start of the step.
- The *input step* is the step with timer 0: the code at [`actor_undo_moves`](../../src/actor_movement.asm#L98) [`$1D7E`](../../src/actor_movement.asm#L186) then picks the next move from the input. [actors.md](actors.md) explains it. Part of its code lies after [`actor_move_right`](../../src/actor_movement.asm#L377) [`$1EC4`](../reference/modules/actor_movement.md#actor_move_right) (`$1ED8-$1F7D`), so the reference names those places by [`actor_move_right`](../../src/actor_movement.asm#L377).
- The *facing* is [`actor_facing`](../../src/constants.asm#L87) [`$A4`](../reference/variables.md#actor_facing): 0 = left, 1 = right.
- A *pose* is the relative frame number in [`actor_frame_rel_a`](../../src/actor_vars.asm#L198) [`$4F48`](../reference/modules/actor_vars.md#actor_frame_rel_a) (always even). The actor shows frame pose and frame pose + 1, one per sprite layer.
- *Contact bits* are [`actor_contact`](../../src/constants.asm#L92) [`$B6`](../reference/variables.md#actor_contact): bit 0 = colour 1 under the frame mask, bit 2 = colour 3 in room-coloured cells, bit 3 = colour 3 in `$F8` cells. **Conclusion** from their use below: bit 0 is a floor, bit 2 is a climbing surface, bit 3 is a wall.
- Moves are in the units of [`actor_x`](../../src/constants.asm#L85) [`$9E`](../reference/variables.md#actor_x) and [`actor_y`](../../src/constants.asm#L86) [`$A1`](../reference/variables.md#actor_y): [`actor_move_left`](../../src/actor_movement.asm#L341) [`$1E86`](../reference/modules/actor_movement.md#actor_move_left) is [`actor_x`](../../src/constants.asm#L85) - 1, [`actor_move_up`](../../src/actor_movement.asm#L253) [`$1DF2`](../reference/modules/actor_movement.md#actor_move_up) is [`actor_y`](../../src/constants.asm#L86) - 1.
- **Observed** marks a fact that a run showed. Here this is mostly the coverage of all earlier runs: a line ran or did not run. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## 1. Overview

Each pass, [`update_actors`](../../src/actor_input.asm#L6) [`$179E`](../reference/modules/actor_input.md#update_actors) runs this for each active actor, from actor 2 down to 0:

~~~mermaid
flowchart TB
  UA["update_actors $179E"] --> WAKE["ai_wake_idle_enemies $2D7C<br/>idle enemy -> state $14"]
  UA --> MS["actor_move_step $1C5B"]
  MS -->|"delay > 0"| SKIP["count delay down, no step"]
  MS -->|"state $18, timer > 0"| BLK["action_blocked_step $24B7"]
  MS -->|"contact bit 3"| UNDO["actor_undo_moves $1CD4<br/>-> state $18"]
  MS -->|"timer > 0"| COA["continue_object_action $2008<br/>handler of the state"]
  MS -->|"timer = 0"| INP["input step $1D7E<br/>(actors.md)"]
  COA --> CAS["continue_action_state $24F4<br/>state, delay, timer - 1"]
  COA --> END["end_action_stand $2504<br/>state 0"]
  COA --> REC["start_attack_recovery $228C<br/>state 0 + timer"]
  UA --> POSE["select_object_pose $2780"]
  POSE --> SET["set_object_pose $29A1<br/>frames A and B"]
~~~

Other code writes the state too. In a pass, all of it runs before [`update_actors`](../../src/actor_input.asm#L6) [`$179E`](../reference/modules/actor_input.md#update_actors), except the set-up at a room start:

| Writer | When | State set |
|---|---|---|
| [`check_actors_background`](../../src/background_touch.asm#L6) [`$2E39`](../reference/modules/background_touch.md#check_actors_background) | each pass, for an actor in state `$17` | 0 with timer 0 ([`reset_actor_state`](../../src/actor_checks.asm#L129) [`$2E10`](../reference/modules/actor_checks.md#reset_actor_state)) |
| [`touch_char_62`](../../src/background_touch.asm#L430) [`$310C`](../reference/modules/background_touch.md#touch_char_62) | the actor touches char `$62` with contact bit 2 | `$17`, timer `$10` |
| [`touch_deadly_char`](../../src/background_touch.asm#L316) [`$304B`](../reference/modules/background_touch.md#touch_deadly_char) | Bruce touches a deadly char | `$19`, timer `$10` ([`set_character_hit_state`](../../src/room_tiles.asm#L32) [`$407D`](../reference/modules/room_tiles.md#set_character_hit_state)) |
| [`room18_wizard_alive`](../../src/room_update.asm#L939) [`$3D35`](../../src/room_update.asm#L953) | room 18: Bruce's sprites collide with sprites 6/7 ([rooms_10_19.md](rooms_10_19.md)) | `$19`, timer `$10` |
| [`apply_hit_effects`](../../src/combat_hits.asm#L227) [`$2B4E`](../reference/modules/combat_hits.md#apply_hit_effects) | a hit landed | attacker: 0 with a recovery timer; victim: `$0F`, `$13` or `$1B` ([combat_collision.md](combat_collision.md)) |
| [`object_knocked_out`](../../src/combat_hits.asm#L356) [`$2C24`](../reference/modules/combat_hits.md#object_knocked_out) | energy below 0 | `$13`, timer `$0C` |
| [`init_actor`](../../src/actors.asm#L6) [`$0B8E`](../reference/modules/actors.md#init_actor) | an actor is set up | 0, timer 0, delay 0 |
| [`spawn_yamo`](../../src/actors.asm#L177) [`$0CD5`](../reference/modules/actors.md#spawn_yamo) | Yamo appears | `$10`, timer `$0A` |
| [`spawn_ninja`](../../src/actors.asm#L355) [`$0DF8`](../reference/modules/actors.md#spawn_ninja) | the Ninja appears | 0, timer `$10` |
| [`draw_room_reset_bruce`](../../src/room_draw.asm#L97) [`$0A6B`](../reference/modules/room_draw.md#draw_room_reset_bruce) | a room is drawn | Bruce: 0, timer 4, delay 0 |

[`check_actor_knockouts`](../../src/actor_checks.asm#L6) [`$2D55`](../reference/modules/actor_checks.md#check_actor_knockouts) runs after [`update_actors`](../../src/actor_input.asm#L6) [`$179E`](../reference/modules/actor_input.md#update_actors). It ends a fall of Bruce ([`lose_fall`](../../src/game_over.asm#L6) [`$1818`](../reference/modules/game_over.md#lose_fall)) or removes an enemy ([`remove_actor`](../../src/background_touch.asm#L280) [`$3001`](../reference/modules/background_touch.md#remove_actor)) when the energy is below 0, except while state `$13` or `$19` still has a timer above 0 **Code**.

## 2. Catalogue

| Name | Address | Layout | Readers and writers |
|---|---|---|---|
| [`actor_state`](../../src/constants.asm#L95) | `$BF` | 3 bytes, one per actor: the state number (table in section 3) | written by the handlers, [`actor_set_action`](../../src/actor_movement.asm#L498) [`$1F92`](../reference/modules/actor_movement.md#actor_set_action), the writers of section 1; read by the handlers, [`select_object_pose`](../../src/object_pose.asm#L6) [`$2780`](../reference/modules/object_pose.md#select_object_pose), [`check_collision_partner`](../../src/combat_hits.asm#L76) [`$2A36`](../reference/modules/combat_hits.md#check_collision_partner) |
| [`actor_state_timer`](../../src/constants.asm#L98) | `$CE` | 3 bytes: the timer, in steps | [`continue_action_state`](../../src/object_actions.asm#L719) [`$24F4`](../reference/modules/object_actions.md#continue_action_state) writes Y - 1; [`actor_set_action`](../../src/actor_movement.asm#L498) [`$1F92`](../reference/modules/actor_movement.md#actor_set_action) writes 0 |
| [`actor_step_delay`](../../src/constants.asm#L122) | `$0106` | 3 bytes: passes to wait before the next step | [`continue_action_state`](../../src/object_actions.asm#L719) [`$24F4`](../reference/modules/object_actions.md#continue_action_state) and [`actor_set_action`](../../src/actor_movement.asm#L498) [`$1F92`](../reference/modules/actor_movement.md#actor_set_action) load it from [`action_delay_table`](../../src/room_tables.asm#L78) [`$4A8C`](../reference/modules/room_tables.md#action_delay_table); [`actor_move_step`](../../src/actor_movement.asm#L32) [`$1C5B`](../reference/modules/actor_movement.md#actor_move_step) counts it down |
| [`actor_prev_state`](../../src/constants.asm#L96) | `$C2` | 3 bytes: the state at the start of the last step | written by [`actor_move_step`](../../src/actor_movement.asm#L32) [`$1CB1`](../../src/actor_movement.asm#L78); read by the input step and [`ai_wake_idle_enemies`](../../src/actor_checks.asm#L33) [`$2D7C`](../reference/modules/actor_checks.md#ai_wake_idle_enemies) |
| [`actor_anim_step`](../../src/constants.asm#L97) | `$CB` | 3 bytes: 6 when the state changed, then 5, 4 ... 0 while it stays | [`actor_move_step`](../../src/actor_movement.asm#L32) [`$1CA9`](../../src/actor_movement.asm#L72); read by the walk and climb input (flying kick needs a value below 4) |
| [`temp_y`](../../src/constants.asm#L41) | `$52` | the timer of the actor in [`continue_object_action`](../../src/object_actions.asm#L6) [`$2008`](../reference/modules/object_actions.md#continue_object_action) | [`continue_action_state`](../../src/object_actions.asm#L719) [`$24F4`](../reference/modules/object_actions.md#continue_action_state) writes [`temp_y`](../../src/constants.asm#L41) - 1 into the timer |
| [`actor_climb_moved`](../../src/constants.asm#L89) | `$AA` | 3 bytes: 1 at the start of a state `$17` step, 0 after a climbing move | [`action_climb`](../../src/object_actions.asm#L205) [`$2180`](../reference/modules/object_actions.md#action_climb), [`climb_step_done`](../../src/object_actions.asm#L260) [`$21E5`](../reference/modules/object_actions.md#climb_step_done), [`touch_char_62`](../../src/background_touch.asm#L430) [`$310C`](../reference/modules/background_touch.md#touch_char_62); read by [`select_object_pose`](../../src/object_pose.asm#L6) [`$2969`](../../src/object_pose.asm#L279) |
| [`actor_climb_delay`](../../src/constants.asm#L90) | `$AD` | 3 bytes: steps until the next climbing move (4 after a move) | [`action_climb`](../../src/object_actions.asm#L205) [`$2180`](../reference/modules/object_actions.md#action_climb), [`climb_step_done`](../../src/object_actions.asm#L260) [`$21E5`](../reference/modules/object_actions.md#climb_step_done) |
| [`action_delay_table`](../../src/room_tables.asm#L78) | `$4A8C` | 28 bytes, one per state: the step delay | [`continue_action_state`](../../src/object_actions.asm#L719) [`$24F4`](../reference/modules/object_actions.md#continue_action_state), [`actor_set_action`](../../src/actor_movement.asm#L498) [`$1F92`](../reference/modules/actor_movement.md#actor_set_action), [`actor_set_action_timer_0f`](../../src/actor_movement.asm#L507) [`$1FA0`](../reference/modules/actor_movement.md#actor_set_action_timer_0f), [`actor_set_action_timer_0c`](../../src/actor_movement.asm#L516) [`$1FAE`](../reference/modules/actor_movement.md#actor_set_action_timer_0c) |
| [`actor_frame_updated`](../../src/actor_vars.asm#L280) | `$4FDB` | 3 bytes: 0 = choose a pose in this pass | cleared by [`actor_move_step`](../../src/actor_movement.asm#L32) [`$1C68`](../../src/actor_movement.asm#L40) at each step; set by [`select_object_pose`](../../src/object_pose.asm#L6) [`$2785`](../../src/object_pose.asm#L9), [`actor_set_idle`](../../src/actor_movement.asm#L491) [`$1F8D`](../../src/actor_movement.asm#L494), [`apply_hit_effects`](../../src/combat_hits.asm#L227) [`$2B65`](../../src/combat_hits.asm#L240) |
| [`actor_prev_frame_rel`](../../src/actor_vars.asm#L224) | `$4F54` | 3 bytes: the pose before this pass | [`select_object_pose`](../../src/object_pose.asm#L6) [`$278B`](../../src/object_pose.asm#L11) |
| [`actor_frame_rel_a`](../../src/actor_vars.asm#L198) / [`actor_frame_rel_b`](../../src/actor_vars.asm#L205) | `$4F48` / `$4F4B` | 3 bytes each: pose and pose + 1 | [`set_object_pose`](../../src/object_pose.asm#L311) [`$29A1`](../reference/modules/object_pose.md#set_object_pose) |
| [`actor_frame_a`](../../src/actor_vars.asm#L212) / [`actor_frame_b`](../../src/actor_vars.asm#L219) | `$4F4E` / `$4F51` | 3 bytes each: frame number = type base + pose, + 1 | [`set_object_pose`](../../src/object_pose.asm#L311) [`$29A1`](../reference/modules/object_pose.md#set_object_pose); read by [`draw_object_sprites`](../../src/sprite_render.asm#L6) [`$2584`](../reference/modules/sprite_render.md#draw_object_sprites) |
| [`actor_type_frame_base`](../../src/sprite_data.asm#L29) | `$59A5` | 3 bytes by [`actor_flags`](../../src/constants.asm#L82) [`$95`](../reference/variables.md#actor_flags) bits 7-6 | [`set_object_pose`](../../src/object_pose.asm#L311) [`$29B3`](../../src/object_pose.asm#L323) |

[`action_delay_table`](../../src/room_tables.asm#L78) [`$4A8C`](../reference/modules/room_tables.md#action_delay_table), decoded from the image:

| States | Delay | Effect |
|---|---|---|
| 0, 3-7, `$0C-$19`, `$1B` | 0 | one step each pass |
| 1, 2 (climb up, climb down) | 3 | one step every 4 passes |
| 8-`$0B` (no code sets them) | 3 | none |
| `$1A` (lie flat) | 1 | one step every 2 passes |

[`actor_type_frame_base`](../../src/sprite_data.asm#L29) [`$59A5`](../reference/modules/sprite_data.md#actor_type_frame_base), decoded from the image: `$00` for type 0 (Bruce, flags `$00`), `$8C` = 140 for type 1 (Ninja, flags `$40`), `$46` = 70 for type 2 (Yamo, flags `$80`).

## 3. The states

The state numbers come from every write to [`actor_state`](../../src/constants.asm#L95) [`$BF`](../reference/variables.md#actor_state) in the source. No code writes 8, 9, `$0A` or `$0B` **Code**. "Seen" tells if the coverage runs executed the handler or the setter of the state.

| State | Meaning | Actors | Set by (timer) | Handler | Duration | Poses | Seen |
|---|---|---|---|---|---|---|---|
| `$00` | stand; with a timer: locked (recovery, room start) | all | [`actor_set_idle`](../../src/actor_movement.asm#L491) [`$1F89`](../reference/modules/actor_movement.md#actor_set_idle) (0), [`end_action_stand`](../../src/object_actions.asm#L729) [`$2504`](../reference/modules/object_actions.md#end_action_stand) (0), [`start_attack_recovery`](../../src/object_actions.asm#L356) [`$228C`](../reference/modules/object_actions.md#start_attack_recovery) (6 / 3 / 1 / 12) | none: count down | timer steps | `$00`/`$02`, or `$0A`/`$0C` on a climbing surface | **Observed** |
| `$01` | climb up | all | [`actor_move_up`](../../src/actor_movement.asm#L253) [`$1DF2`](../reference/modules/actor_movement.md#actor_move_up) (0) | input step | 1 step (4 passes) | `$0A`/`$0C` cycle | **Observed** |
| `$02` | climb down | all | [`actor_move_down`](../../src/actor_movement.asm#L294) [`$1E39`](../reference/modules/actor_movement.md#actor_move_down) (0) | input step | 1 step (4 passes) | `$0A`/`$0C` cycle | not as an input move |
| `$03` | walk left | all | [`actor_move_left`](../../src/actor_movement.asm#L341) [`$1E86`](../reference/modules/actor_movement.md#actor_move_left) (0) | input step | 1 step | `$0E`/`$10` cycle | **Observed** |
| `$04` | walk right | all | [`actor_move_right`](../../src/actor_movement.asm#L377) [`$1EC4`](../reference/modules/actor_movement.md#actor_move_right) (0) | input step | 1 step | `$12`/`$14` cycle | **Observed** |
| `$05` | jump straight up | Bruce, human Yamo | [`actor_up_or_jump`](../../src/actor_movement.asm#L248) [`$1DEC`](../reference/modules/actor_movement.md#actor_up_or_jump) (`$0F`) | [`continue_object_action`](../../src/object_actions.asm#L6) [`$2008`](../reference/modules/object_actions.md#continue_object_action) | 15 steps | `$08`, `$1E`, `$20` | **Observed** |
| `$06` | jump to the left | Bruce, human Yamo | [`actor_move_right`](../../src/actor_movement.asm#L377) [`$1F37`](../../src/actor_movement.asm#L445) (`$0F`) | [`action_jump_left`](../../src/object_actions.asm#L114) [`$20D2`](../reference/modules/object_actions.md#action_jump_left) | 15 steps or to the floor | `$22`, `$24` | **Observed** |
| `$07` | jump to the right | Bruce, human Yamo | [`actor_move_right`](../../src/actor_movement.asm#L377) [`$1F4E`](../../src/actor_movement.asm#L457) (`$0F`) | [`action_jump_right`](../../src/object_actions.asm#L153) [`$2120`](../reference/modules/object_actions.md#action_jump_right) | 15 steps or to the floor | `$26`, `$28` | **Observed** |
| `$0C` | flying kick to the left | Bruce, Yamo | [`actor_left_or_fire_move`](../../src/actor_movement.asm#L327) [`$1E70`](../reference/modules/actor_movement.md#actor_left_or_fire_move) (`$0C`), [`chase_facing_bruce`](../../src/object_actions.asm#L508) [`$23A6`](../../src/object_actions.asm#L534) (`$0C`) | [`action_flying_kick_left`](../../src/object_actions.asm#L40) [`$2048`](../reference/modules/object_actions.md#action_flying_kick_left) | 12 steps or to the floor | `$16`, `$18` | **Observed** (Yamo) |
| `$0D` | flying kick to the right | Bruce, Yamo | [`actor_right_or_fire_move`](../../src/actor_movement.asm#L365) [`$1EB1`](../reference/modules/actor_movement.md#actor_right_or_fire_move) (`$0C`), [`chase_facing_bruce`](../../src/object_actions.asm#L508) [`$23B4`](../../src/object_actions.asm#L543) (`$0C`) | [`action_flying_kick_right`](../../src/object_actions.asm#L78) [`$208D`](../reference/modules/object_actions.md#action_flying_kick_right) | 12 steps or to the floor | `$1A`, `$1C` | **Observed** (Yamo) |
| `$0E` | fall | all | [`actor_descend_two_steps`](../../src/actor_movement.asm#L225) [`$1DC4`](../reference/modules/actor_movement.md#actor_descend_two_steps) and the landing code (0) | input step | 1 step | `$44` | **Observed** |
| `$0F` | knocked back | all | [`apply_hit_effects`](../../src/combat_hits.asm#L227) [`$2B4E`](../reference/modules/combat_hits.md#apply_hit_effects) (3 kick, 4 punch) | [`action_knocked_back`](../../src/object_actions.asm#L594) [`$240E`](../reference/modules/object_actions.md#action_knocked_back) | 3 or 4 steps | `$00`/`$02` | **Observed** |
| `$10` | wait before appearing | Yamo | [`spawn_yamo`](../../src/actors.asm#L177) [`$0CD5`](../reference/modules/actors.md#spawn_yamo) (`$0A`) | [`action_spawn_wait`](../../src/object_actions.asm#L303) [`$2235`](../reference/modules/object_actions.md#action_spawn_wait) | 9 steps | `$2A` | **Observed** |
| `$11` | punch | Bruce, Yamo | [`actor_still_fire_move`](../../src/actor_movement.asm#L484) [`$1F7E`](../reference/modules/actor_movement.md#actor_still_fire_move) (4) | [`action_punch`](../../src/object_actions.asm#L336) [`$226A`](../reference/modules/object_actions.md#action_punch) | 4 steps, the last starts the recovery | `$04`/`$06` | **Observed** |
| `$12` | appear (arms up) | Yamo | [`enemy_appear_facing_player`](../../src/object_actions.asm#L312) [`$2244`](../reference/modules/object_actions.md#enemy_appear_facing_player) (`$10`) | [`action_appear`](../../src/object_actions.asm#L589) [`$2407`](../reference/modules/object_actions.md#action_appear) | 16 steps | `$2C`/`$2E` | **Observed** |
| `$13` | knocked down, knocked out | all | [`apply_hit_effects`](../../src/combat_hits.asm#L227) [`$2B4E`](../reference/modules/combat_hits.md#apply_hit_effects) and [`object_knocked_out`](../../src/combat_hits.asm#L356) [`$2C24`](../reference/modules/combat_hits.md#object_knocked_out) (`$0C`) | [`action_knocked_down`](../../src/object_actions.asm#L621) [`$2440`](../reference/modules/object_actions.md#action_knocked_down) | 12 steps (11 for an enemy that recovers) | `$38`-`$3E` | **Observed** |
| `$14` | enemy chase (decide) | computer Yamo, Ninja | [`ai_wake_idle_enemies`](../../src/actor_checks.asm#L33) [`$2D7C`](../reference/modules/actor_checks.md#ai_wake_idle_enemies) (`$14`), [`action_enemy_walk`](../../src/object_actions.asm#L558) [`$23CD`](../reference/modules/object_actions.md#action_enemy_walk) (`$80`) | [`action_enemy_chase`](../../src/object_actions.asm#L425) [`$22F3`](../reference/modules/object_actions.md#action_enemy_chase) | until a decision; the timer does not count | walk cycle | **Observed** |
| `$15` | enemy walk | computer Yamo, Ninja | [`enemy_start_walk`](../../src/object_actions.asm#L456) [`$2327`](../reference/modules/object_actions.md#enemy_start_walk) (5 or more) | [`action_enemy_walk`](../../src/object_actions.asm#L558) [`$23CD`](../reference/modules/object_actions.md#action_enemy_walk) | timer - 1 steps, then `$14` | walk cycle | **Observed** |
| `$16` | the Ninja's strike | Ninja | [`chase_ninja_attack`](../../src/object_actions.asm#L545) [`$23C4`](../../src/object_actions.asm#L552) (`$13`) | [`action_kick`](../../src/object_actions.asm#L391) [`$22BD`](../reference/modules/object_actions.md#action_kick) | 19 steps, the last starts the recovery | `$30`-`$36` | **Observed** |
| `$17` | on the moving climbing texture | Bruce (an enemy: not seen) | [`touch_char_62`](../../src/background_touch.asm#L430) [`$310C`](../reference/modules/background_touch.md#touch_char_62) (`$10`) | [`action_climb`](../../src/object_actions.asm#L205) [`$2180`](../reference/modules/object_actions.md#action_climb) | while the actor touches char `$62` | keeps or cycles `$0A`/`$0C` | **Observed** |
| `$18` | stuck in a wall, being pushed out | all | [`actor_undo_moves`](../../src/actor_movement.asm#L98) [`$1CD4`](../reference/modules/actor_movement.md#actor_undo_moves) (`$40`) | [`action_blocked_step`](../../src/object_actions.asm#L681) [`$24B7`](../reference/modules/object_actions.md#action_blocked_step) | until contact bit 3 clears | the last pose, or `$08` | **Observed** |
| `$19` | dying | Bruce | [`set_character_hit_state`](../../src/room_tiles.asm#L32) [`$407D`](../reference/modules/room_tiles.md#set_character_hit_state) (`$10`) | [`action_dying`](../../src/object_actions.asm#L190) [`$216B`](../reference/modules/object_actions.md#action_dying) | 16 steps, then [`lose_fall`](../../src/game_over.asm#L6) [`$1818`](../reference/modules/game_over.md#lose_fall) | `$08` | **Observed** |
| `$1A` | lie flat | Bruce | [`actor_move_right`](../../src/actor_movement.asm#L377) `$1EEB`/`$1F1D` (0) | input step | 1 step (2 passes) | `$40`/`$42` | **Observed** |
| `$1B` | dropped on | all | [`apply_hit_effects`](../../src/combat_hits.asm#L227) [`$2B4E`](../reference/modules/combat_hits.md#apply_hit_effects) (8) | none: count down | 8 steps | `$38`-`$3E` | not seen |

**Code**: [`check_collision_partner`](../../src/combat_hits.asm#L76) [`$2A36`](../reference/modules/combat_hits.md#check_collision_partner) skips a victim in state `$18`, `$1A`, `$0F`, `$13`, `$19` or `$1B`. So lying flat and the hit states make an actor safe from a new hit. The table of the attacks that count is on [combat_collision.md](combat_collision.md).

## 4. Step by step

### 4.1 From [`actor_move_step`](../../src/actor_movement.asm#L32) to a handler

[`actor_move_step`](../../src/actor_movement.asm#L32) [`$1C5B`](../reference/modules/actor_movement.md#actor_move_step) (in [actor_movement.md](../reference/modules/actor_movement.md)) decides who handles the step **Code**:

1. When [`actor_step_delay`](../../src/constants.asm#L122) [`$0106`](../reference/variables.md#actor_step_delay) is not 0: count it down and return. No step, no new pose.
2. Clear [`actor_frame_updated`](../../src/actor_vars.asm#L280) [`$4FDB`](../reference/modules/actor_vars.md#actor_frame_updated), so [`select_object_pose`](../../src/object_pose.asm#L6) [`$2780`](../reference/modules/object_pose.md#select_object_pose) chooses a pose in this pass. Save the moves of the last step in [`actor_move_history`](../../src/actor_vars.asm#L239) [`$4F63`](../reference/modules/actor_vars.md#actor_move_history).
3. Update [`actor_anim_step`](../../src/constants.asm#L97) [`$CB`](../reference/variables.md#actor_anim_step) (6 on a state change or in state 0, else count down to 0). Copy the state to [`actor_prev_state`](../../src/constants.asm#L96) [`$C2`](../reference/variables.md#actor_prev_state).
4. State `$19`: go to the timer test of step 7 at once.
5. State `$18` with a timer above 0: jump to [`action_blocked_step`](../../src/object_actions.asm#L681) [`$24B7`](../reference/modules/object_actions.md#action_blocked_step).
6. Contact bit 3 (in a wall): [`actor_undo_moves`](../../src/actor_movement.asm#L98) [`$1CD4`](../reference/modules/actor_movement.md#actor_undo_moves) takes back the moves of the last step, may run the step again (at most 8 times), and ends with state `$18`, timer `$40`.
7. Timer above 0: jump to [`continue_object_action`](../../src/object_actions.asm#L6) [`$2008`](../reference/modules/object_actions.md#continue_object_action) with Y = timer.
8. Timer 0: the input step at [`actor_undo_moves`](../../src/actor_movement.asm#L98) [`$1D7E`](../../src/actor_movement.asm#L186). A state with no timer (1-4, `$0E`, `$1A`, 0) is chosen again in each input step.

### 4.2 [`continue_object_action`](../../src/object_actions.asm#L6) [`$2008`](../reference/modules/object_actions.md#continue_object_action)

1. Store Y (the timer) in [`temp_y`](../../src/constants.asm#L41) [`$52`](../reference/variables.md#temp_y).
2. Compare the state with `$05`, `$0C`, `$0D`, `$06`, `$07`, `$19`, `$17`, `$10`, `$11`, `$16`, `$14`, `$15`, `$12`, `$0F`, `$13`, `$18`, in this order. Each label tests one number and branches on to the next test.
3. A state with no handler (0-4, `$0E`, `$1A`, `$1B`) falls through [`action_blocked`](../../src/object_actions.asm#L677) [`$24B3`](../reference/modules/object_actions.md#action_blocked) into [`continue_action_state`](../../src/object_actions.asm#L719) [`$24F4`](../reference/modules/object_actions.md#continue_action_state) with A = the state. It only counts its timer down.

Most handlers end in [`continue_action_state`](../../src/object_actions.asm#L719) [`$24F4`](../reference/modules/object_actions.md#continue_action_state):

1. Store A as the new state.
2. Load [`actor_step_delay`](../../src/constants.asm#L122) [`$0106`](../reference/variables.md#actor_step_delay) from [`action_delay_table`](../../src/room_tables.asm#L78) [`$4A8C`](../reference/modules/room_tables.md#action_delay_table) by the state.
3. Store [`temp_y`](../../src/constants.asm#L41) - 1 as the timer.

So a handler entered with Y = T runs T steps. The step with Y = 1 leaves timer 0, and the next step is the input step. Two handlers add 1 to [`temp_y`](../../src/constants.asm#L41) first ([`climb_ride_texture`](../../src/object_actions.asm#L265) [`$220F`](../../src/object_actions.asm#L283), [`enemy_walk_step`](../../src/object_actions.asm#L485) [`$235B`](../../src/object_actions.asm#L491)): their timer does not change.

[`end_action_stand`](../../src/object_actions.asm#L729) [`$2504`](../reference/modules/object_actions.md#end_action_stand) ends the action at once: [`actor_set_action`](../../src/actor_movement.asm#L498) [`$1F92`](../reference/modules/actor_movement.md#actor_set_action) with A = 0 sets state 0, the delay of state 0 and timer 0.

### 4.3 The handlers

**State `$05`, jump straight up** ([`continue_object_action`](../../src/object_actions.asm#L6) [`$200A`](../../src/object_actions.asm#L8)):
1. Contact bit 2 (climbing surface): end, state 0.
2. Y = 15, 14, 13 and Y = 1: no move.
3. Y = 12: [`actor_y`](../../src/constants.asm#L86) - 4. Y = 11 to 8: [`actor_y`](../../src/constants.asm#L86) - 2 per step.
4. Y = 7 to 2: on a floor (bit 0): end. Else [`actor_y`](../../src/constants.asm#L86) + 2 per step.
5. The rise (12) and the fall (12) are equal.

**State `$06`, jump left** ([`action_jump_left`](../../src/object_actions.asm#L114) [`$20D2`](../reference/modules/object_actions.md#action_jump_left)); **state `$07`, jump right** ([`action_jump_right`](../../src/object_actions.asm#L153) [`$2120`](../reference/modules/object_actions.md#action_jump_right)) is the same to the right:
1. Contact bit 2: end, state 0.
2. Y = 15 to 11: [`actor_y`](../../src/constants.asm#L86) - 2 and [`actor_x`](../../src/constants.asm#L85) - 2. Y = 10: [`actor_y`](../../src/constants.asm#L86) - 1 and [`actor_x`](../../src/constants.asm#L85) - 2.
3. Y = 9 to 7: [`actor_x`](../../src/constants.asm#L85) - 2.
4. Y = 6 to 1 ([`jump_left_descend`](../../src/object_actions.asm#L139) [`$2105`](../reference/modules/object_actions.md#jump_left_descend)): on a floor (bit 0): end. Else [`actor_x`](../../src/constants.asm#L85) - 2 and [`actor_y`](../../src/constants.asm#L86) + 2.
5. **Code**: the test `cpy #$06` at [`jump_left_descend`](../../src/object_actions.asm#L139) [`$2111`](../../src/object_actions.asm#L145) should make the step at Y = 6 move down only 1, as the step at Y = 10 moves up only 1. But [`actor_move_left`](../../src/actor_movement.asm#L341) [`$1E86`](../reference/modules/actor_movement.md#actor_move_left) ends in [`actor_set_action`](../../src/actor_movement.asm#L498) [`$1F92`](../reference/modules/actor_movement.md#actor_set_action), which puts the state number 3 in Y. So Y is never 6 there, and the fall (12) is 1 more than the rise (11). The same is true at [`jump_right_descend`](../../src/object_actions.asm#L176) [`$215C`](../../src/object_actions.asm#L182) (Y = 4).

**States `$0C`/`$0D`, flying kick** ([`action_flying_kick_left`](../../src/object_actions.asm#L40) [`$2048`](../reference/modules/object_actions.md#action_flying_kick_left), [`action_flying_kick_right`](../../src/object_actions.asm#L78) [`$208D`](../reference/modules/object_actions.md#action_flying_kick_right)):
1. Contact bit 2 or 3: end, state 0.
2. Y = 12: sound `$84` ([`play_sound_effect`](../../src/sound_effects.asm#L6) [`$2509`](../reference/modules/sound_effects.md#play_sound_effect)).
3. Y = 12 to 10: [`actor_y`](../../src/constants.asm#L86) - 1 and [`actor_x`](../../src/constants.asm#L85) ∓ 1.
4. Y = 9 to 3: [`actor_x`](../../src/constants.asm#L85) ∓ 1.
5. Y = 2 and 1: on a floor: end. Else [`actor_y`](../../src/constants.asm#L86) + 1 and [`actor_x`](../../src/constants.asm#L85) ∓ 1.
6. **Code**: a flying kick hits only while the timer is below `$0A` ([`check_collision_partner`](../../src/combat_hits.asm#L76) [`$2A36`](../reference/modules/combat_hits.md#check_collision_partner)), that is in the pose with the leg out.

**State `$19`, dying** ([`action_dying`](../../src/object_actions.asm#L190) [`$216B`](../reference/modules/object_actions.md#action_dying)):
1. Bruce with Y = 1: jump to [`lose_fall`](../../src/game_over.asm#L6) [`$1818`](../reference/modules/game_over.md#lose_fall).
2. Else count down. [`check_actors_background`](../../src/background_touch.asm#L6) [`$2E39`](../reference/modules/background_touch.md#check_actors_background) skips an actor in state `$19`, so the timer is not set again.

**State `$17`, on the climbing texture** ([`action_climb`](../../src/object_actions.asm#L205) [`$2180`](../reference/modules/object_actions.md#action_climb)):
1. Contact bit 2 clear: end, state 0 (not seen).
2. Set [`actor_climb_moved`](../../src/constants.asm#L89) [`$AA`](../reference/variables.md#actor_climb_moved) to 1.
3. An enemy while [`human_opponent_mode`](../../src/variables.asm#L11) is 0 (not seen): set [`actor_joy_dir`](../../src/constants.asm#L83) [`$98`](../reference/variables.md#actor_joy_dir) to right or left by its facing.
4. When [`actor_climb_delay`](../../src/constants.asm#L90) [`$AD`](../reference/variables.md#actor_climb_delay) is not 0: count it down and do not move.
5. Else move 2 in the joystick direction (up `$0E`, down `$0D`, left `$0B`, right `$07`). After a move, [`climb_step_done`](../../src/object_actions.asm#L260) [`$21E5`](../reference/modules/object_actions.md#climb_step_done) clears [`actor_climb_moved`](../../src/constants.asm#L89) [`$AA`](../reference/variables.md#actor_climb_moved), sets [`actor_climb_delay`](../../src/constants.asm#L90) [`$AD`](../reference/variables.md#actor_climb_delay) to 4 and plays sound `$80` ([`play_sound_80_checked`](../../src/actor_movement.asm#L531) [`$1FC4`](../reference/modules/actor_movement.md#play_sound_80_checked)). So a held joystick moves the actor 2 every 5 steps.
6. [`climb_ride_texture`](../../src/object_actions.asm#L265) [`$21EE`](../reference/modules/object_actions.md#climb_ride_texture): when [`scroll_timer`](../../src/constants.asm#L49) [`$60`](../reference/variables.md#scroll_timer) = 1 (the texture moves now), move 2 up ([`scroll_direction`](../../src/constants.asm#L54) [`$65`](../reference/variables.md#scroll_direction) = 0) or down (1).
7. Clear the input copy ([`actor_joy_dir`](../../src/constants.asm#L83) [`$98`](../reference/variables.md#actor_joy_dir) = `$0F`, [`actor_joy_fire`](../../src/constants.asm#L84) [`$9B`](../reference/variables.md#actor_joy_fire) = 1), net the up and down counters of this step, keep the timer, and continue state `$17`.
8. [`check_actors_background`](../../src/background_touch.asm#L6) [`$2E39`](../reference/modules/background_touch.md#check_actors_background) sets the state to 0 at each pass, and [`touch_char_62`](../../src/background_touch.asm#L430) [`$310C`](../reference/modules/background_touch.md#touch_char_62) sets it back to `$17` while the actor still touches char `$62`. So state `$17` lasts while the actor touches the texture. The texture itself is on [rooms_00_09.md](rooms_00_09.md) (section 4.5).

**State `$10`, wait before appearing** ([`action_spawn_wait`](../../src/object_actions.asm#L303) [`$2235`](../reference/modules/object_actions.md#action_spawn_wait)): count down. At Y = 1, [`enemy_appear_facing_player`](../../src/object_actions.asm#L312) [`$2244`](../reference/modules/object_actions.md#enemy_appear_facing_player) turns the enemy towards Bruce, sets state `$12`, timer `$10`, delay 0, and plays sound `$81`.

**State `$12`, appear** ([`action_appear`](../../src/object_actions.asm#L589) [`$2407`](../reference/modules/object_actions.md#action_appear)): count down only.

**State `$11`, punch** ([`action_punch`](../../src/object_actions.asm#L336) [`$226A`](../reference/modules/object_actions.md#action_punch)):
1. Contact bit 2 or 3: end, state 0.
2. Y = 8: sound `$85`. **Code**: the punch starts with timer 4 ([`actor_set_action_timer_04`](../../src/actor_movement.asm#L525) [`$1FBC`](../reference/modules/actor_movement.md#actor_set_action_timer_04)), so Y is never 8 and this sound is never played. **Observed**: `$2278-$2282` never ran.
3. Y = 1: [`start_attack_recovery`](../../src/object_actions.asm#L356) [`$228C`](../reference/modules/object_actions.md#start_attack_recovery). Else continue.

**State `$16`, the Ninja's strike** ([`action_kick`](../../src/object_actions.asm#L391) [`$22BD`](../reference/modules/object_actions.md#action_kick)):
1. Contact bit 3: end, state 0 (not seen).
2. Y = 12: sound `$85`.
3. Y = 1: [`start_attack_recovery`](../../src/object_actions.asm#L356) [`$228C`](../reference/modules/object_actions.md#start_attack_recovery).
4. Else add 1 to [`actor_moved_right`](../../src/actor_vars.asm#L236) [`$4F60`](../reference/modules/actor_vars.md#actor_moved_right) or [`actor_moved_left`](../../src/actor_vars.asm#L233) [`$4F5D`](../reference/modules/actor_vars.md#actor_moved_left) by the facing, without a change of [`actor_x`](../../src/constants.asm#L85), and continue.
5. **Code**: the strike hits only while the timer is below 8 ([`check_collision_partner`](../../src/combat_hits.asm#L76) [`$2A36`](../reference/modules/combat_hits.md#check_collision_partner)).

**[`start_attack_recovery`](../../src/object_actions.asm#L356) [`$228C`](../reference/modules/object_actions.md#start_attack_recovery)** (end of a punch, a strike, a knock-back or a knock-down):
1. State 0, timer 6, delay 0.
2. Bruce: timer 3 when [`get_room_time_level`](../../src/room_state.asm#L110) [`$10D0`](../reference/modules/room_state.md#get_room_time_level) gives C = 0 and V = 0 ([`room_timer`](../../src/constants.asm#L77) [`$88`](../reference/variables.md#room_timer) below `$19`), else 12.
3. An enemy: timer 1 when [`room_timer`](../../src/constants.asm#L77) [`$88`](../reference/variables.md#room_timer) >= `$20`; 3 when it is `$19-$1F`; 1 when [`game_cycle`](../../src/constants.asm#L30) [`$40`](../reference/variables.md#game_cycle) is not 0; else 6.
4. While the timer runs the actor stands and cannot act (state 0 has no handler). [`ai_wake_idle_enemies`](../../src/actor_checks.asm#L33) [`$2D7C`](../reference/modules/actor_checks.md#ai_wake_idle_enemies) waits for timer 0.
5. **Code**: the longer Bruce stays in a room, the longer he waits after a punch (3 steps, 12 steps from [`room_timer`](../../src/constants.asm#L77) [`$88`](../reference/variables.md#room_timer) = `$19`, that is after 25 × 256 frames). The enemies wait shorter. **Observed**: the coverage runs reached only the timers 3 (Bruce) and 6 (enemy).

**State `$14`, enemy chase** ([`action_enemy_chase`](../../src/object_actions.asm#L425) [`$22F3`](../reference/modules/object_actions.md#action_enemy_chase)):
1. Not on a floor (bit 0 clear): on a climbing surface, [`enemy_walk_step`](../../src/object_actions.asm#L485) [`$2352`](../reference/modules/object_actions.md#enemy_walk_step); else [`actor_descend_two_steps`](../../src/actor_movement.asm#L225) [`$1DC4`](../reference/modules/actor_movement.md#actor_descend_two_steps) (state `$0E`) ([`chase_off_floor`](../../src/object_actions.asm#L502) [`$2372`](../reference/modules/object_actions.md#chase_off_floor)).
2. [`calc_delta_to_bruce`](../../src/actor_checks.asm#L92) [`$2DDD`](../reference/modules/actor_checks.md#calc_delta_to_bruce) gives [`delta_x_to_bruce`](../../src/constants.asm#L52) [`$63`](../reference/variables.md#delta_x_to_bruce) and [`delta_y_to_bruce`](../../src/constants.asm#L51) [`$62`](../reference/variables.md#delta_y_to_bruce) (distance up to `$30`, bit 7 = Bruce is right of / below the enemy).
3. Vertical distance `$10` or more ([`chase_other_height`](../../src/object_actions.asm#L494) [`$2362`](../reference/modules/object_actions.md#chase_other_height)): Bruce below: [`enemy_walk_step`](../../src/object_actions.asm#L485) [`$2352`](../reference/modules/object_actions.md#enemy_walk_step); Bruce above: [`face_toward_bruce`](../../src/actor_checks.asm#L137) [`$2E1C`](../reference/modules/actor_checks.md#face_toward_bruce) and [`start_attack_recovery`](../../src/object_actions.asm#L356) [`$228C`](../reference/modules/object_actions.md#start_attack_recovery).
4. The enemy faces away from Bruce: horizontal distance below `$21`: [`enemy_start_walk`](../../src/object_actions.asm#L456) [`$2327`](../reference/modules/object_actions.md#enemy_start_walk). Else turn round and [`enemy_walk_step`](../../src/object_actions.asm#L485) [`$2352`](../reference/modules/object_actions.md#enemy_walk_step).
5. The enemy faces Bruce, Yamo ([`actor_flags`](../../src/constants.asm#L82) [`$95`](../reference/variables.md#actor_flags) and `$81` = `$81`, [`chase_facing_bruce`](../../src/object_actions.asm#L508) [`$237B`](../reference/modules/object_actions.md#chase_facing_bruce)): distance below 5: [`enemy_start_walk`](../../src/object_actions.asm#L456) [`$2327`](../reference/modules/object_actions.md#enemy_start_walk); 5-`$0B`: [`actor_still_fire_move`](../../src/actor_movement.asm#L484) [`$1F7E`](../reference/modules/actor_movement.md#actor_still_fire_move) (punch, state `$11`); `$0C-$12`: flying kick `$0C` or `$0D` by the facing, timer `$0C`, delay 0; `$13` or more: [`enemy_walk_step`](../../src/object_actions.asm#L485) [`$2352`](../reference/modules/object_actions.md#enemy_walk_step).
6. The enemy faces Bruce, the Ninja ([`chase_ninja_attack`](../../src/object_actions.asm#L545) [`$23B8`](../reference/modules/object_actions.md#chase_ninja_attack)): distance `$0B` or more: [`enemy_walk_step`](../../src/object_actions.asm#L485) [`$2352`](../reference/modules/object_actions.md#enemy_walk_step); below 5: [`enemy_start_walk`](../../src/object_actions.asm#L456) [`$2327`](../reference/modules/object_actions.md#enemy_start_walk); 5-`$0A`: state `$16`, timer `$13`.

[`enemy_walk_step`](../../src/object_actions.asm#L485) [`$2352`](../reference/modules/object_actions.md#enemy_walk_step): move 2 in the facing direction ([`actor_right_two_steps`](../../src/actor_movement.asm#L362) [`$1EAE`](../reference/modules/actor_movement.md#actor_right_two_steps) or [`actor_left_two_steps`](../../src/actor_movement.asm#L324) [`$1E6D`](../reference/modules/actor_movement.md#actor_left_two_steps)), keep the timer and continue state `$14`.

[`enemy_start_walk`](../../src/object_actions.asm#L456) [`$2327`](../reference/modules/object_actions.md#enemy_start_walk): the target is [`actor_x`](../../src/constants.asm#L85) [`$9E`](../reference/variables.md#actor_x) of Bruce + `$0F` (Bruce to the left) or - `$0F` (Bruce to the right). The timer is the distance from the enemy to the target, at least 5. State `$15`, delay 0.

**State `$15`, enemy walk** ([`action_enemy_walk`](../../src/object_actions.asm#L558) [`$23CD`](../reference/modules/object_actions.md#action_enemy_walk)):
1. Not on a floor: [`actor_descend_two_steps`](../../src/actor_movement.asm#L225) [`$1DC4`](../reference/modules/actor_movement.md#actor_descend_two_steps) (state `$0E`).
2. Timer 1: turn round, state `$14`, timer `$80`, delay 0.
3. Else move 2 in the facing direction and continue `$15`.

**State `$0F`, knocked back** ([`action_knocked_back`](../../src/object_actions.asm#L594) [`$240E`](../reference/modules/object_actions.md#action_knocked_back)):
1. An enemy with Y = 1: [`start_attack_recovery`](../../src/object_actions.asm#L356) [`$228C`](../reference/modules/object_actions.md#start_attack_recovery).
2. Else move 2 against the facing and keep the facing (the moves would turn the actor). Continue `$0F`.

**State `$13`, knocked down** ([`action_knocked_down`](../../src/object_actions.asm#L621) [`$2440`](../reference/modules/object_actions.md#action_knocked_down)):
1. An enemy with energy ([`actor_energy`](../../src/constants.asm#L99) [`$D1`](../reference/variables.md#actor_energy)) 0 or more and Y = 1: [`start_attack_recovery`](../../src/object_actions.asm#L356) [`$228C`](../reference/modules/object_actions.md#start_attack_recovery).
2. Contact bits 0 and 2 clear: [`actor_y`](../../src/constants.asm#L86) + 1.
3. Move 2 against the facing and keep the facing. Continue `$13`.
4. At Y = 10 the Ninja (actor 2) moves 8 more to the left when it faces right, but only 4 more to the right when it faces left **Code**.
5. Bruce, or an enemy with energy below 0, runs all 12 steps. At timer 0, when the energy is below 0, [`check_actor_knockouts`](../../src/actor_checks.asm#L6) [`$2D55`](../reference/modules/actor_checks.md#check_actor_knockouts) ends the fall or removes the enemy.

**State `$18`, stuck in a wall** ([`action_blocked_step`](../../src/object_actions.asm#L681) [`$24B7`](../reference/modules/object_actions.md#action_blocked_step)):
1. Contact bit 3 clear: [`temp_y`](../../src/constants.asm#L41) [`$52`](../reference/variables.md#temp_y) = 1, so the timer becomes 0. The next step is the input step.
2. Contact bit 3 set and some move in [`actor_move_history`](../../src/actor_vars.asm#L239) [`$4F63`](../reference/modules/actor_vars.md#actor_move_history) (40 entries of this actor): [`actor_undo_moves`](../../src/actor_movement.asm#L98) [`$1CD4`](../reference/modules/actor_movement.md#actor_undo_moves) again (state `$18`, timer `$40`).
3. Contact bit 3 set and an empty history: [`current_actor`](../../src/constants.asm#L40) [`$51`](../reference/variables.md#current_actor) = 0, and [`enter_room`](../../src/background_touch.asm#L210) [`$2F8E`](../reference/modules/background_touch.md#enter_room) enters the current room again at [`room_spawn_x`](../../src/room_tables.asm#L156) [`$4BAE`](../reference/modules/room_tables.md#room_spawn_x) / [`room_spawn_y`](../../src/room_tables.asm#L161) [`$4BC2`](../reference/modules/room_tables.md#room_spawn_y). **Code**: this puts Bruce at the spawn point even when the stuck actor is an enemy. **Observed**: `$24DB-$24EA` ran in the coverage runs.

## 5. The state machine

Three diagrams: Bruce's moves, the hits and hazards, the enemy behaviour. "Input" is the input step (timer 0).

### 5.1 Bruce's moves

~~~mermaid
stateDiagram-v2
  state "Input step (timer 0)" as Input
  state "Climb up $01" as Up
  state "Climb down $02" as Down
  state "Walk left $03" as WL
  state "Walk right $04" as WR
  state "Lie flat $1A" as Lie
  state "Fall $0E" as Fall
  state "Jump up $05" as J5
  state "Jump left $06" as J6
  state "Jump right $07" as J7
  state "Flying kick left $0C" as K0C
  state "Flying kick right $0D" as K0D
  state "Punch $11" as P
  state "Recovery: $00 with timer" as Rec
  [*] --> Rec: room drawn, timer 4
  Rec --> Input: timer 0
  Input --> Up: up, climbing surface
  Input --> Down: down, climbing surface
  Input --> WL: left
  Input --> WR: right
  Input --> Lie: down-left or down-right on a floor
  Input --> Fall: no floor
  Input --> J5: up, no climbing surface
  Input --> J6: up-left
  Input --> J7: up-right
  Input --> P: fire, no direction
  WL --> K0C: left + fire while walking
  WR --> K0D: right + fire while walking
  Up --> Input
  Down --> Input
  WL --> Input
  WR --> Input
  Lie --> Input
  Fall --> Input: landed or still falling
  J5 --> Input: timer 0, floor, contact bit 2
  J6 --> Input: timer 0, floor, contact bit 2
  J7 --> Input: timer 0, floor, contact bit 2
  K0C --> Input: timer 0, floor, contact bits 2-3
  K0D --> Input: timer 0, floor, contact bits 2-3
  P --> Rec: timer 1
~~~

### 5.2 Hits and hazards (any actor)

~~~mermaid
stateDiagram-v2
  state "Any state" as Any
  state "Input step (timer 0)" as Input
  state "Recovery: $00 with timer" as Rec
  state "Knocked back $0F" as KB
  state "Knocked down $13" as KD
  state "Dropped on $1B" as DR
  state "Stuck in a wall $18" as BL
  state "On the texture $17" as CL
  state "Dying $19" as DY
  state "Fall lost or enemy removed" as Out
  state "Room entered again" as Re
  Any --> KB: kick or punch hit
  Any --> KD: flying kick hit, energy below 0
  Any --> DR: dropped on
  Any --> Rec: own hit landed
  Any --> BL: contact bit 3
  Any --> CL: touches char $62 with bit 2
  Any --> DY: Bruce on a deadly char
  KB --> Input: Bruce, timer 0
  KB --> Rec: enemy, timer 1
  KD --> Rec: enemy with energy, timer 1
  KD --> Input: Bruce with energy, timer 0
  KD --> Out: energy below 0, timer 0
  DR --> Input: timer 0
  BL --> Input: out of the wall
  BL --> BL: still in it, history not empty
  BL --> Re: still in it, history empty
  CL --> Input: no more char $62
  DY --> Out: Bruce, timer 1
  Rec --> Input: timer 0
~~~

### 5.3 Enemy behaviour (computer Yamo and Ninja)

~~~mermaid
stateDiagram-v2
  state "Wait $10 (Yamo)" as S10
  state "Appear $12" as S12
  state "Idle: $00, timer 0" as Idle
  state "Recovery: $00 with timer" as Rec
  state "Chase $14" as S14
  state "Walk $15" as S15
  state "Punch $11 (Yamo)" as S11
  state "Strike $16 (Ninja)" as S16
  state "Flying kick $0C/$0D (Yamo)" as FK
  state "Fall $0E" as S0E
  [*] --> S10: spawn_yamo, timer $0A
  [*] --> Rec: spawn_ninja, timer $10
  S10 --> S12: timer 1
  S12 --> Idle: timer 0
  Idle --> S14: on a floor or climbing surface
  Rec --> Idle: timer 0
  S14 --> S14: walk on
  S14 --> S15: close, or facing away
  S14 --> S11: Yamo, distance 5-$0B
  S14 --> FK: Yamo, distance $0C-$12
  S14 --> S16: Ninja, distance 5-$0A
  S14 --> Rec: Bruce higher up
  S14 --> S0E: no floor
  S15 --> S14: timer 1, turn round
  S15 --> S0E: no floor
  S11 --> Rec: timer 1
  S16 --> Rec: timer 1
  FK --> Idle: timer 0 or floor
  Idle --> Rec: last state was a flying kick
  S0E --> Idle: landed
~~~

The hits of section 5.2 also apply to the enemies.

### 5.4 The transition table

| State | Condition | Next state | Code |
|---|---|---|---|
| any | [`actor_step_delay`](../../src/constants.asm#L122) [`$0106`](../reference/variables.md#actor_step_delay) > 0 | same, no step | [`actor_move_step`](../../src/actor_movement.asm#L32) [`$1C5B`](../reference/modules/actor_movement.md#actor_move_step) |
| any but `$19` and a running `$18` | contact bit 3 | `$18`, timer `$40` (or the step again) | [`actor_undo_moves`](../../src/actor_movement.asm#L98) [`$1CD4`](../reference/modules/actor_movement.md#actor_undo_moves) |
| any, timer 0 | input step: the input and the contact bits | 0-7, `$0C`, `$0D`, `$0E`, `$11`, `$1A` | [`actor_undo_moves`](../../src/actor_movement.asm#L98) [`$1D7E`](../../src/actor_movement.asm#L186), see [actors.md](actors.md) |
| any, timer 0 | no floor and no climbing surface (contact bits 0 and 2 clear) | `$0E`, timer 0 | [`actor_descend_two_steps`](../../src/actor_movement.asm#L225) [`$1DC4`](../reference/modules/actor_movement.md#actor_descend_two_steps) |
| `$0E` | input step, landed (contact bits 0 or 2) | 0 (Bruce), 3 or 4 (an enemy steps 1 in its facing direction) | [`actor_undo_moves`](../../src/actor_movement.asm#L98) [`$1D7E`](../../src/actor_movement.asm#L186) |
| `$03` | input step, left, [`actor_anim_step`](../../src/constants.asm#L97) [`$CB`](../reference/variables.md#actor_anim_step) < 4, fire | `$0C`, timer `$0C` | [`actor_left_or_fire_move`](../../src/actor_movement.asm#L327) [`$1E70`](../reference/modules/actor_movement.md#actor_left_or_fire_move) |
| `$04` | input step, right, [`actor_anim_step`](../../src/constants.asm#L97) [`$CB`](../reference/variables.md#actor_anim_step) < 4, fire | `$0D`, timer `$0C` | [`actor_right_or_fire_move`](../../src/actor_movement.asm#L365) [`$1EB1`](../reference/modules/actor_movement.md#actor_right_or_fire_move) |
| any, timer 0 | up, no climbing surface, no wall | `$05`, timer `$0F` | [`actor_up_or_jump`](../../src/actor_movement.asm#L248) [`$1DEC`](../reference/modules/actor_movement.md#actor_up_or_jump) |
| any, timer 0 | up-left / up-right, no climbing surface | `$06` / `$07`, timer `$0F`, sound `$80` | [`actor_move_right`](../../src/actor_movement.asm#L377) [`$1F37`](../../src/actor_movement.asm#L445) / `$1F4E` |
| any, timer 0 | no direction, fire, no climbing surface | `$11`, timer 4 | [`actor_still_fire_move`](../../src/actor_movement.asm#L484) [`$1F7E`](../reference/modules/actor_movement.md#actor_still_fire_move) |
| any, timer 0 | Bruce, down-left / down-right (or down) on a floor | `$1A`, timer 0 | [`actor_move_right`](../../src/actor_movement.asm#L377) [`$1EEB`](../../src/actor_movement.asm#L400) / `$1F1D` |
| any, timer 0 | human Yamo, down on a floor (not seen) | `$12`, timer `$10` | [`actor_move_right`](../../src/actor_movement.asm#L377) [`$1F04`](../../src/actor_movement.asm#L414) → [`enemy_appear_facing_player`](../../src/object_actions.asm#L312) [`$2244`](../reference/modules/object_actions.md#enemy_appear_facing_player) |
| `$05` | contact bit 2 | 0 | [`continue_object_action`](../../src/object_actions.asm#L6) [`$2014`](../../src/object_actions.asm#L13) |
| `$05` | Y = 7 to 2 and on a floor | 0 | [`continue_object_action`](../../src/object_actions.asm#L6) [`$2026`](../../src/object_actions.asm#L23) |
| `$05` | Y = 1 | `$05`, timer 0 → input step | [`continue_object_action`](../../src/object_actions.asm#L6) [`$2030`](../../src/object_actions.asm#L28) |
| `$06` / `$07` | contact bit 2 | 0 | [`action_jump_left`](../../src/object_actions.asm#L114) [`$20DA`](../../src/object_actions.asm#L119) / [`action_jump_right`](../../src/object_actions.asm#L153) [`$2128`](../../src/object_actions.asm#L158) |
| `$06` / `$07` | Y = 6 to 1 and on a floor | 0 | [`jump_left_descend`](../../src/object_actions.asm#L139) [`$2109`](../../src/object_actions.asm#L142) / [`jump_right_descend`](../../src/object_actions.asm#L176) [`$2154`](../../src/object_actions.asm#L179) |
| `$06` / `$07` | Y = 1 | same, timer 0 → input step | [`jump_left_descend`](../../src/object_actions.asm#L139) [`$211D`](../../src/object_actions.asm#L151) / [`jump_right_descend`](../../src/object_actions.asm#L176) [`$2168`](../../src/object_actions.asm#L188) |
| `$0C` / `$0D` | contact bit 2 or 3 | 0 | [`action_flying_kick_left`](../../src/object_actions.asm#L40) [`$2050`](../../src/object_actions.asm#L45) / [`action_flying_kick_right`](../../src/object_actions.asm#L78) [`$2095`](../../src/object_actions.asm#L83) |
| `$0C` / `$0D` | Y = 2 or 1 and on a floor | 0 | [`action_flying_kick_left`](../../src/object_actions.asm#L40) [`$2080`](../../src/object_actions.asm#L71) / [`action_flying_kick_right`](../../src/object_actions.asm#L78) [`$20C5`](../../src/object_actions.asm#L108) |
| `$0C` / `$0D` | Y = 1 | same, timer 0 → input step | [`action_flying_kick_left`](../../src/object_actions.asm#L40) [`$208A`](../../src/object_actions.asm#L76) / [`action_flying_kick_right`](../../src/object_actions.asm#L78) [`$20CF`](../../src/object_actions.asm#L112) |
| `$0C` / `$0D` (last state), now 0 with timer 0 | enemy | 0 with timer `$18`, or 1 or 3 by the level | [`ai_wake_idle_enemies`](../../src/actor_checks.asm#L33) [`$2DC0`](../../src/actor_checks.asm#L73) |
| `$19` | Bruce, Y = 1 | fall lost | [`action_dying`](../../src/object_actions.asm#L190) [`$217A`](../../src/object_actions.asm#L200) → [`lose_fall`](../../src/game_over.asm#L6) [`$1818`](../reference/modules/game_over.md#lose_fall) |
| `$19` | else | `$19`, timer - 1 | [`action_dying`](../../src/object_actions.asm#L190) [`$2177`](../../src/object_actions.asm#L198) |
| `$17` | each pass | 0, timer 0 | [`check_actors_background`](../../src/background_touch.asm#L6) [`$2E39`](../reference/modules/background_touch.md#check_actors_background) |
| 0 (from `$17`) | the actor touches char `$62`, contact bit 2 | `$17`, timer `$10` | [`touch_char_62`](../../src/background_touch.asm#L430) [`$310C`](../reference/modules/background_touch.md#touch_char_62) |
| `$17` | contact bit 2 clear (not seen) | 0 | [`action_climb`](../../src/object_actions.asm#L205) [`$218B`](../../src/object_actions.asm#L212) |
| `$17` | else | `$17`, timer kept | [`climb_ride_texture`](../../src/object_actions.asm#L265) [`$2232`](../../src/object_actions.asm#L301) |
| `$10` | Y = 1 | `$12`, timer `$10`, sound `$81` | [`action_spawn_wait`](../../src/object_actions.asm#L303) [`$223D`](../../src/object_actions.asm#L308) → [`enemy_appear_facing_player`](../../src/object_actions.asm#L312) [`$2244`](../reference/modules/object_actions.md#enemy_appear_facing_player) |
| `$10` | Y > 1 | `$10`, timer - 1 | [`action_spawn_wait`](../../src/object_actions.asm#L303) [`$2241`](../../src/object_actions.asm#L310) |
| `$12` | each step | `$12`, timer - 1; timer 0 → input step → 0 | [`action_appear`](../../src/object_actions.asm#L589) [`$240B`](../../src/object_actions.asm#L592) |
| 0 | enemy, timer 0, energy 0 or more, on a floor or climbing surface (contact bits 0 or 2), last state not `$0C`/`$0D`; Yamo only without a human opponent | `$14`, timer `$14`, delay 0 | [`ai_wake_idle_enemies`](../../src/actor_checks.asm#L33) [`$2DB3`](../../src/actor_checks.asm#L64) |
| `$11` | contact bit 2 or 3 | 0 | [`action_punch`](../../src/object_actions.asm#L336) [`$2272`](../../src/object_actions.asm#L341) → [`action_kick`](../../src/object_actions.asm#L391) [`$22C7`](../../src/object_actions.asm#L400) |
| `$11` | Y = 1 | 0 with recovery timer | [`action_punch`](../../src/object_actions.asm#L336) [`$2285`](../../src/object_actions.asm#L352) → [`start_attack_recovery`](../../src/object_actions.asm#L356) [`$228C`](../reference/modules/object_actions.md#start_attack_recovery) |
| `$11` | else | `$11`, timer - 1 | [`action_punch`](../../src/object_actions.asm#L336) [`$2289`](../../src/object_actions.asm#L354) |
| `$16` | contact bit 3 (not seen) | 0 | [`action_kick`](../../src/object_actions.asm#L391) [`$22C7`](../../src/object_actions.asm#L400) |
| `$16` | Y = 1 | 0 with recovery timer | [`action_kick`](../../src/object_actions.asm#L391) [`$22F0`](../../src/object_actions.asm#L423) |
| `$16` | else | `$16`, timer - 1 | [`action_kick`](../../src/object_actions.asm#L391) [`$22ED`](../../src/object_actions.asm#L421) |
| `$14` | not on a floor, on a climbing surface | `$14`, walks 2 | [`chase_off_floor`](../../src/object_actions.asm#L502) [`$2376`](../../src/object_actions.asm#L505) |
| `$14` | not on a floor, no climbing surface | `$0E`, timer 0 | [`chase_off_floor`](../../src/object_actions.asm#L502) [`$2378`](../../src/object_actions.asm#L507) |
| `$14` | vertical distance `$10` or more, Bruce below | `$14`, walks 2 | [`chase_other_height`](../../src/object_actions.asm#L494) [`$2364`](../../src/object_actions.asm#L496) |
| `$14` | vertical distance `$10` or more, Bruce above | 0 with recovery timer, facing Bruce | [`chase_other_height`](../../src/object_actions.asm#L494) [`$2369`](../../src/object_actions.asm#L498) |
| `$14` | faces away, horizontal distance below `$21` | `$15` | [`action_enemy_chase`](../../src/object_actions.asm#L425) [`$231C`](../../src/object_actions.asm#L450) → [`enemy_start_walk`](../../src/object_actions.asm#L456) [`$2327`](../reference/modules/object_actions.md#enemy_start_walk) |
| `$14` | faces away, distance `$21` or more | `$14`, turned round, walks 2 | [`action_enemy_chase`](../../src/object_actions.asm#L425) [`$2324`](../../src/object_actions.asm#L454) |
| `$14` | Yamo faces Bruce, distance below 5 | `$15` | [`chase_facing_bruce`](../../src/object_actions.asm#L508) [`$2389`](../../src/object_actions.asm#L517) |
| `$14` | Yamo faces Bruce, distance 5-`$0B` | `$11`, timer 4; on a climbing surface 0 with recovery timer (not seen) | [`chase_facing_bruce`](../../src/object_actions.asm#L508) [`$238F`](../../src/object_actions.asm#L520) |
| `$14` | Yamo faces Bruce, distance `$0C-$12` | `$0C` / `$0D`, timer `$0C` | [`chase_facing_bruce`](../../src/object_actions.asm#L508) [`$23A8`](../../src/object_actions.asm#L536) |
| `$14` | Yamo faces Bruce, distance `$13` or more | `$14`, walks 2 | [`chase_facing_bruce`](../../src/object_actions.asm#L508) [`$239E`](../../src/object_actions.asm#L530) |
| `$14` | Ninja faces Bruce, distance `$0B` or more | `$14`, walks 2 | [`chase_ninja_attack`](../../src/object_actions.asm#L545) [`$23BE`](../../src/object_actions.asm#L549) |
| `$14` | Ninja faces Bruce, distance below 5 | `$15` | [`chase_ninja_attack`](../../src/object_actions.asm#L545) [`$23C2`](../../src/object_actions.asm#L551) |
| `$14` | Ninja faces Bruce, distance 5-`$0A` | `$16`, timer `$13` | [`chase_ninja_attack`](../../src/object_actions.asm#L545) [`$23C4`](../../src/object_actions.asm#L552) |
| `$15` | not on a floor | `$0E`, timer 0 | [`action_enemy_walk`](../../src/object_actions.asm#L558) [`$23D5`](../../src/object_actions.asm#L563) |
| `$15` | timer 1 | `$14`, timer `$80`, turned round | [`action_enemy_walk`](../../src/object_actions.asm#L558) [`$23E3`](../../src/object_actions.asm#L570) |
| `$15` | else | `$15`, timer - 1, walks 2 | [`action_enemy_walk`](../../src/object_actions.asm#L558) [`$23FC`](../../src/object_actions.asm#L583) / `$2404` |
| any | own attack landed (hit bit 0) | 0, delay 4, recovery timer | [`apply_hit_effects`](../../src/combat_hits.asm#L227) [`$2B4E`](../reference/modules/combat_hits.md#apply_hit_effects), see [combat_collision.md](combat_collision.md) |
| any | kick hit / punch hit | `$0F`, timer 3 / 4 | [`apply_hit_effects`](../../src/combat_hits.asm#L227) [`$2B4E`](../reference/modules/combat_hits.md#apply_hit_effects) |
| any | flying kick hit, or energy below 0 | `$13`, timer `$0C` | [`apply_hit_effects`](../../src/combat_hits.asm#L227) [`$2B4E`](../reference/modules/combat_hits.md#apply_hit_effects), [`object_knocked_out`](../../src/combat_hits.asm#L356) [`$2C24`](../reference/modules/combat_hits.md#object_knocked_out) |
| any | dropped on by an actor in state `$0E` | `$1B`, timer 8 | [`apply_hit_effects`](../../src/combat_hits.asm#L227) [`$2B4E`](../reference/modules/combat_hits.md#apply_hit_effects) |
| any | Bruce on a deadly char, or a room 18 fireball | `$19`, timer `$10` | [`set_character_hit_state`](../../src/room_tiles.asm#L32) [`$407D`](../reference/modules/room_tiles.md#set_character_hit_state) |
| `$0F` | enemy, Y = 1 | 0 with recovery timer | [`action_knocked_back`](../../src/object_actions.asm#L594) [`$243D`](../../src/object_actions.asm#L619) |
| `$0F` | else | `$0F`, timer - 1, pushed 2 | [`action_knocked_back`](../../src/object_actions.asm#L594) [`$242B`](../../src/object_actions.asm#L610) / `$243A` |
| `$13` | enemy with energy 0 or more, Y = 1 | 0 with recovery timer | [`action_knocked_down`](../../src/object_actions.asm#L621) [`$24B0`](../../src/object_actions.asm#L675) |
| `$13` | else | `$13`, timer - 1, pushed 2 | [`action_knocked_down`](../../src/object_actions.asm#L621) [`$248A`](../../src/object_actions.asm#L657) / `$24AD` |
| `$13` | timer 0, energy below 0 | fall lost (Bruce) or removed (enemy) | [`check_actor_knockouts`](../../src/actor_checks.asm#L6) [`$2D55`](../reference/modules/actor_checks.md#check_actor_knockouts) |
| `$18` | contact bit 3 clear | `$18`, timer 0 → input step | [`action_blocked_step`](../../src/object_actions.asm#L681) [`$24C3`](../../src/object_actions.asm#L688) |
| `$18` | contact bit 3, history not empty | `$18`, timer `$40` | [`action_blocked_step`](../../src/object_actions.asm#L681) [`$24F1`](../../src/object_actions.asm#L717) → [`actor_undo_moves`](../../src/actor_movement.asm#L98) [`$1CD4`](../reference/modules/actor_movement.md#actor_undo_moves) |
| `$18` | contact bit 3, history empty | Bruce at the spawn point, room drawn again | [`action_blocked_step`](../../src/object_actions.asm#L681) [`$24EA`](../../src/object_actions.asm#L713) → [`enter_room`](../../src/background_touch.asm#L210) [`$2F8E`](../reference/modules/background_touch.md#enter_room) |
| 0, `$1B`, others with timer | each step | same, timer - 1 | [`action_blocked`](../../src/object_actions.asm#L677) [`$24B5`](../../src/object_actions.asm#L679) → [`continue_action_state`](../../src/object_actions.asm#L719) [`$24F4`](../reference/modules/object_actions.md#continue_action_state) |

## 6. The poses

### 6.1 [`select_object_pose`](../../src/object_pose.asm#L6) [`$2780`](../reference/modules/object_pose.md#select_object_pose)

1. When [`actor_frame_updated`](../../src/actor_vars.asm#L280) [`$4FDB`](../reference/modules/actor_vars.md#actor_frame_updated) is not 0: return. It is not 0 when the actor made no step in this pass, or when [`actor_set_idle`](../../src/actor_movement.asm#L491) [`$1F89`](../reference/modules/actor_movement.md#actor_set_idle) kept an idle actor idle.
2. Set [`actor_frame_updated`](../../src/actor_vars.asm#L280) [`$4FDB`](../reference/modules/actor_vars.md#actor_frame_updated). Copy the pose to [`actor_prev_frame_rel`](../../src/actor_vars.asm#L224) [`$4F54`](../reference/modules/actor_vars.md#actor_prev_frame_rel). Y = the facing.
3. Choose the pose by the state (table 6.2). The tests run in the order of the table.
4. [`set_object_pose`](../../src/object_pose.asm#L311) [`$29A1`](../reference/modules/object_pose.md#set_object_pose): store the pose in [`actor_frame_rel_a`](../../src/actor_vars.asm#L198) [`$4F48`](../reference/modules/actor_vars.md#actor_frame_rel_a) and pose + 1 in [`actor_frame_rel_b`](../../src/actor_vars.asm#L205) [`$4F4B`](../reference/modules/actor_vars.md#actor_frame_rel_b). Take the type from [`actor_flags`](../../src/constants.asm#L82) [`$95`](../reference/variables.md#actor_flags) bits 7-6 (three ROL and AND 3: bit 7 to bit 1, bit 6 to bit 0). Store [`actor_type_frame_base`](../../src/sprite_data.asm#L29) [`$59A5`](../reference/modules/sprite_data.md#actor_type_frame_base) + pose in [`actor_frame_a`](../../src/actor_vars.asm#L212) [`$4F4E`](../reference/modules/actor_vars.md#actor_frame_a) and that + 1 in [`actor_frame_b`](../../src/actor_vars.asm#L219) [`$4F51`](../reference/modules/actor_vars.md#actor_frame_b).

The pose uses the timer after the step. So in the pass in which a state starts, the pose uses the start timer.

### 6.2 Pose by state

| State | Condition | Pose, facing left | Pose, facing right | Code |
|---|---|---|---|---|
| `$0E` fall | contact bit 3 (not seen) | `$08` | `$08` | [`select_object_pose`](../../src/object_pose.asm#L6) [`$279C`](../../src/object_pose.asm#L20) |
| `$0E` fall | else | `$44` | `$44` | [`select_object_pose`](../../src/object_pose.asm#L6) [`$27A1`](../../src/object_pose.asm#L23) |
| `$1A` lie flat | | `$40` | `$42` | [`select_object_pose`](../../src/object_pose.asm#L6) [`$27A6`](../../src/object_pose.asm#L26) |
| `$19` dying | | `$08` | `$08` | [`select_object_pose`](../../src/object_pose.asm#L6) [`$27BC`](../../src/object_pose.asm#L38) |
| `$18` stuck | last pose `$44`, or a wide frame ([`actor_body_wide`](../../src/constants.asm#L100) [`$D4`](../reference/variables.md#actor_body_wide) or [`actor_overlay_wide`](../../src/constants.asm#L101) [`$D7`](../reference/variables.md#actor_overlay_wide)) | `$08` | `$08` | [`select_object_pose`](../../src/object_pose.asm#L6) [`$27D5`](../../src/object_pose.asm#L51) |
| `$18` stuck | else | the last pose | the last pose | [`select_object_pose`](../../src/object_pose.asm#L6) [`$27D2`](../../src/object_pose.asm#L49) |
| `$1B` dropped on (not seen) | timer >= 4 / < 4 | `$3C` / `$3E` | `$38` / `$3A` | [`select_object_pose`](../../src/object_pose.asm#L6) [`$27DA`](../../src/object_pose.asm#L54) |
| `$13` knocked down | timer >= `$0A` / < `$0A` | `$3C` / `$3E` | `$38` / `$3A` | [`select_object_pose`](../../src/object_pose.asm#L6) [`$2800`](../../src/object_pose.asm#L76) |
| `$10` wait | | `$2A` | `$2A` | [`select_object_pose`](../../src/object_pose.asm#L6) [`$282A`](../../src/object_pose.asm#L99) |
| `$11` punch | | `$04` | `$06` (not seen) | [`select_object_pose`](../../src/object_pose.asm#L6) [`$282F`](../../src/object_pose.asm#L102) |
| `$12` appear | | `$2C` | `$2E` | [`select_object_pose`](../../src/object_pose.asm#L6) [`$2841`](../../src/object_pose.asm#L112) |
| `$16` strike | timer >= `$0B` / < `$0B` | `$30` / `$32` | `$34` / `$36` | [`select_object_pose`](../../src/object_pose.asm#L6) [`$2853`](../../src/object_pose.asm#L122) |
| `$0F` knocked back | | `$00` | `$02` | [`select_object_pose`](../../src/object_pose.asm#L6) [`$2879`](../../src/object_pose.asm#L143) |
| `$0C` flying kick left | timer >= `$0A` / < `$0A` | `$16` / `$18` | `$16` / `$18` | [`select_object_pose`](../../src/object_pose.asm#L6) [`$288B`](../../src/object_pose.asm#L153) |
| `$0D` flying kick right | timer >= `$0A` / < `$0A` | `$1A` / `$1C` | `$1A` / `$1C` | [`select_object_pose`](../../src/object_pose.asm#L6) [`$289F`](../../src/object_pose.asm#L164) |
| `$14`, `$15` enemy | by the facing | walk left | walk right | [`select_object_pose`](../../src/object_pose.asm#L6) [`$28B3`](../../src/object_pose.asm#L175) |
| `$03` walk left | contact bit 2: climb cycle; else last pose `$0E` → `$10`, else `$0E` | `$0E`/`$10` | `$0E`/`$10` | [`pose_walk_left`](../../src/object_pose.asm#L189) [`$28CB`](../reference/modules/object_pose.md#pose_walk_left) |
| `$04` walk right | contact bit 2: climb cycle (not seen); else last pose `$12` → `$14`, else `$12` | `$12`/`$14` | `$12`/`$14` | [`pose_walk_right`](../../src/object_pose.asm#L206) [`$28E9`](../reference/modules/object_pose.md#pose_walk_right) |
| `$05` jump up | timer >= `$0F` / `$0C-$0E` / `$02-$0B` / 1 / 0 | `$08` / `$1E` / `$20` / `$1E` / `$08` | same | [`select_object_pose`](../../src/object_pose.asm#L6) [`$2903`](../../src/object_pose.asm#L222) |
| `$06` jump left | timer >= `$0C` / `$03-$0B` / < 3 | `$22` / `$24` / `$22` | same | [`select_object_pose`](../../src/object_pose.asm#L6) [`$2932`](../../src/object_pose.asm#L248) |
| `$07` jump right | timer >= `$0C` / `$03-$0B` / < 3 | `$26` / `$28` / `$26` | same | [`select_object_pose`](../../src/object_pose.asm#L6) [`$294A`](../../src/object_pose.asm#L262) |
| `$17` texture | [`actor_climb_moved`](../../src/constants.asm#L89) [`$AA`](../reference/variables.md#actor_climb_moved) = 0 (moved): climb cycle; else the last pose | climb | climb | [`select_object_pose`](../../src/object_pose.asm#L6) [`$2962`](../../src/object_pose.asm#L276) |
| `$00` stand | contact bit 2 and last pose `$0A` or `$0C`: keep it; contact bit 2: climb cycle | climb | climb | [`select_object_pose`](../../src/object_pose.asm#L6) [`$2970`](../../src/object_pose.asm#L283) |
| `$00` stand | no contact bit 2 | `$00` | `$02` | [`pose_stand`](../../src/object_pose.asm#L303) [`$2996`](../reference/modules/object_pose.md#pose_stand) |
| all others (1, 2) | climb cycle: last pose `$0A` → `$0C`, else `$0A` | `$0A`/`$0C` | `$0A`/`$0C` | [`pose_climb_cycle`](../../src/object_pose.asm#L293) [`$2985`](../reference/modules/object_pose.md#pose_climb_cycle) |

**Code**: the walk cycles and the climb cycle change the pose at each step. So the walk cycle changes at each pass, and the climb cycle of states 1 and 2 changes every 4 passes (delay 3).

### 6.3 The pose pictures

The sheets show the 35 poses of each actor (top, 7 per row, pose `$00` at the top left, pose = 2 × (7 × row + column)) and the 70 single frames (bottom). The pictures are from `assets/sprites/` ([assets/README.md](../../assets/README.md)).

![Bruce: the 35 poses (top) and the 70 single frames (bottom)](../../assets/sprites/bruce.png)

Bruce's sheet: rows 0-4 of the top part are the poses `$00-$0C`, `$0E-$1A`, `$1C-$28`, `$2A-$36`, `$38-$44`.

![Yamo: the 35 poses (top) and the 70 single frames (bottom)](../../assets/sprites/yamo.png)

Yamo's sheet, in the same layout.

![The Ninja: the 35 poses (top) and the 70 single frames (bottom)](../../assets/sprites/ninja.png)

The Ninja's sheet, in the same layout.

The pictures in this table are **Conclusion** from the sheets.

| Pose | Row, column | Picture (Bruce) | States | Used by |
|---|---|---|---|---|
| `$00` / `$02` | 0, 0-1 | standing, two facings | 0, `$0F` | all |
| `$04` / `$06` | 0, 2-3 | punch to the left / right | `$11` | Bruce, Yamo |
| `$08` | 0, 4 | standing, seen from the front | `$05`, `$18`, `$19`, `$0E` | all |
| `$0A` / `$0C` | 0, 5-6 | climbing, seen from behind | 0, 1, 2, 3, 4, `$14`, `$15`, `$17` on a climbing surface | all |
| `$0E` / `$10` | 1, 0-1 | walking left | 3, `$14`, `$15` | all |
| `$12` / `$14` | 1, 2-3 | walking right | 4, `$14`, `$15` | all |
| `$16` / `$18` | 1, 4-5 | flying kick left: tucked / leg out | `$0C` | Bruce, Yamo |
| `$1A` / `$1C` | 1, 6 and 2, 0 | flying kick right: tucked / leg out | `$0D` | Bruce, Yamo |
| `$1E` / `$20` | 2, 1-2 | crouched / arms up, from the front | `$05` | Bruce, human Yamo |
| `$22` / `$24` | 2, 3-4 | jump left | `$06` | Bruce, human Yamo |
| `$26` / `$28` | 2, 5-6 | jump right | `$07` | Bruce, human Yamo |
| `$2A` | 3, 0 | standing (Bruce's frame is not used) | `$10` | Yamo |
| `$2C` / `$2E` | 3, 1-2 | Yamo with the arms up | `$12` | Yamo |
| `$30`-`$36` | 3, 3-6 | the Ninja's stick raised / lunge, left and right | `$16` | Ninja |
| `$38` / `$3A` | 4, 0-1 | falling backwards / lying (shown when facing right) | `$13`, `$1B` | all |
| `$3C` / `$3E` | 4, 2-3 | falling backwards / lying (shown when facing left) | `$13`, `$1B` | all |
| `$40` / `$42` | 4, 4-5 | lying flat on the floor | `$1A` | Bruce |
| `$44` | 4, 6 | arms up, from the front | `$0E` | all |

**Code**: no state shows Bruce's poses `$2A-$36`, the Ninja's poses `$04`, `$06`, `$16-$2E` or `$40`/`$42`, or Yamo's poses `$30-$36` and `$40`/`$42`. **Conclusion**: the sheets agree: these cells hold copies of a standing pose, except Yamo's `$42`, which is a broken picture.

## 7. Worked examples

### 7.1 Bruce jumps to the left

Bruce stands on a floor. The joystick is up-left ([`actor_joy_dir`](../../src/constants.asm#L83) [`$98`](../reference/variables.md#actor_joy_dir) = `$0A`). Each row is one step (one pass, delay 0). Moves are in [`actor_x`](../../src/constants.asm#L85)/[`actor_y`](../../src/constants.asm#L86) units. The table assumes that the frame touches no floor before the jump ends **Code**.

| Pass | Y | Moves | Timer after | Pose (frames) |
|---|---|---|---|---|
| 1 (input step) | 0 | none; facing 0, sound `$80`, state `$06` | `$0F` | `$22` (34, 35) |
| 2-4 | 15, 14, 13 | x - 2, y - 2 | 14, 13, 12 | `$22` |
| 5-6 | 12, 11 | x - 2, y - 2 | 11, 10 | `$24` (36, 37) |
| 7 | 10 | x - 2, y - 1 | 9 | `$24` |
| 8-10 | 9, 8, 7 | x - 2 | 8, 7, 6 | `$24` |
| 11-13 | 6, 5, 4 | x - 2, y + 2 | 5, 4, 3 | `$24` |
| 14-16 | 3, 2, 1 | x - 2, y + 2 | 2, 1, 0 | `$22` |
| 17 (input step) | 0 | the next move | | |

Sum: [`actor_x`](../../src/constants.asm#L85) - 30, [`actor_y`](../../src/constants.asm#L86) - 11 + 12 = + 1. With a floor under the start point, contact bit 0 ends the jump earlier, at the step where the frame touches the floor ([`jump_left_descend`](../../src/object_actions.asm#L139) [`$2109`](../../src/object_actions.asm#L142)).

### 7.2 Yamo punches to the right

Yamo (actor 1, [`actor_flags`](../../src/constants.asm#L82) [`$95`](../reference/variables.md#actor_flags) = `$81`) is in state `$11` and faces right.

1. [`select_object_pose`](../../src/object_pose.asm#L6) [`$282F`](../../src/object_pose.asm#L102): state `$11`, Y = facing 1 → pose `$06`.
2. [`set_object_pose`](../../src/object_pose.asm#L311) [`$29A1`](../reference/modules/object_pose.md#set_object_pose): [`actor_frame_rel_a`](../../src/actor_vars.asm#L198) [`$4F48`](../reference/modules/actor_vars.md#actor_frame_rel_a) = `$06`, [`actor_frame_rel_b`](../../src/actor_vars.asm#L205) [`$4F4B`](../reference/modules/actor_vars.md#actor_frame_rel_b) = `$07`.
3. `$81` ROL ROL ROL AND 3 = 2. [`actor_type_frame_base+2`](../../src/sprite_data.asm#L29) [`$59A7`](../reference/modules/sprite_data.md#actor_type_frame_base) = `$46`.
4. [`actor_frame_a`](../../src/actor_vars.asm#L212) [`$4F4E`](../reference/modules/actor_vars.md#actor_frame_a) = `$46` + `$06` = `$4C` (76), [`actor_frame_b`](../../src/actor_vars.asm#L219) [`$4F51`](../reference/modules/actor_vars.md#actor_frame_b) = `$4D` (77).
5. In the frame tables of the image: frame 76 has [`frame_src_lo`](../../src/sprite_data.asm#L43)/[`frame_src_hi`](../../src/sprite_data.asm#L72) = `$5F65`, [`frame_height`](../../src/sprite_data.asm#L101) = 16, [`frame_colour`](../../src/sprite_data.asm#L130) = `$F0`, [`frame_wide_flag`](../../src/sprite_data.asm#L150) = 1. Frame 77 has `$5F17`, 21, `$F5`, 1. So layer A is black and layer B is green, and both are wide.
6. The pair is pose 3 of the sheet: row 0, column 3 of `yamo.png`.

## 8. Still open

- The jump arc of states 6 and 7 falls 1 more than it rises (section 4.3). Does Bruce end 1 pixel lower, or does the floor test stop him first? A c64-testing run with joystick up-left on a flat floor, with [`actor_y`](../../src/constants.asm#L86) [`$A1`](../reference/variables.md#actor_y) read before and after the jump, can answer it.
- State `$1B` (dropped on) never ran. A run in which Yamo falls on Bruce from a ledge can show its timer and poses.
- Bruce's flying kicks (`$1F64-$1F75`) and the end phase of the left flying kick (`$207C-$208C`) never ran. A run that walks Bruce left for 3 steps and then presses fire can show them.
- A human Yamo (opponent option) pulling down starts state `$12` (`$1EFA-$1F06`, not seen). A two-player run with joystick 2 down can confirm it.
- A computer enemy on the climbing texture (`$2194-$21A8`) never ran. A run in room 5 or 8 with an enemy on the texture can show it.
- Which actor reached the room re-entry of [`action_blocked_step`](../../src/object_actions.asm#L681) [`$24DB`](../../src/object_actions.asm#L706) in the coverage runs, and can an enemy reach it? A run with a watchpoint on `$24DB` that logs X can answer it.
- What the move counts of state `$16` ([`action_kick`](../../src/object_actions.asm#L391) [`$22E3`](../../src/object_actions.asm#L415)) are for. A run with the Ninja striking at the room edge, with [`actor_moved_left`](../../src/actor_vars.asm#L233) [`$4F5D`](../reference/modules/actor_vars.md#actor_moved_left) and the exit checks watched, can answer it.
- Bruce's long recovery (12 steps, `$22B5`) and the short enemy recoveries (`$22B2`, `$22B8`) never ran. A run that stays more than 25 × 256 frames in one room can show them.
