.open "ROCKEXE6_GXX.gba", "ROCKEXE6_GXX_MOD.gba", 0x08000000

.gba

.org 0x08072C20 // free? space

playRandomSound:
  push r14
  cmp r0, 0x15  // is virus battle song?
  bne originalProcessing

  selectSound:
    ldr r0, =playList
    ldr r3, =0x2001120  // fluctuating value
    ldrb r3, [r3, 0h]
    lsr r3, r3, 5 // get 3bit value to select from playList
    ldrb r0, [r0, r3]
    b originalProcessing

  originalProcessing:
    lsl r0, r0, 0x10
    ldr r3, =0x8164C8C

  pop r15

.pool
playList:  // play list
  .byte 21, 34, 38, 41, 45, 48, 49, 52  // virus battle

// Hook
.org 0x0815B33A  // playSound
  bl playRandomSound

.close
