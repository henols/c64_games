; Bruce Lee: default build entry (hand-written, not generated).
;
; Builds the game with the copy protection disabled: it sets the switch NO_PROTECTION to 1
; and includes the generated main.asm. The 13 patches of the switch (see constants.asm and
; docs/protection.md) make each protection check take its passing path, so the game no
; longer needs the loader marks ($00 = $EF, $02 = $32, RTS at $0080) or the key page $CF00.
;
; Build:            assemble.ts --source-root src --entry bruce_lee.asm --out build/bruce_lee.prg
; Original program: --define NO_PROTECTION=0, or assemble main.asm (byte-identical to the game).

!ifndef NO_PROTECTION { NO_PROTECTION = 1 }
!source "main.asm"
