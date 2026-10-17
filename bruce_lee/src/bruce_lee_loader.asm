; Bruce Lee: default runnable build (hand-written, not generated).
;
; The generated loader (loader.asm) with the copy protection disabled: it sets the switch
; NO_PROTECTION to 1 and includes loader.asm. The result is a PRG with a BASIC start line
; that copies the game into place, sets the entry state and jumps to cold_start.
;
; Build:            assemble.ts --source-root src --entry bruce_lee_loader.asm --out build/bruce_lee_loader.prg
; With protection:  --define NO_PROTECTION=0, or use the generated src/loader.prg.

!ifndef NO_PROTECTION { NO_PROTECTION = 1 }
!source "loader.asm"
