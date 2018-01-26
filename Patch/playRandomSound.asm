.open "ROCKEXE6_GXX.gba", "ROCKEXE6_GXX_MOD.gba", 0x08000000

.gba

.org 0x08072C20 // free? space

playRandomSound:
  push r14
  cmp r0, 0x15  // is virus battle song?
  bne isBossBattleSong

  isVirusSong:
    ldr r0, =virusPlayList
    b pickRandomSong

  isBossBattleSong:
    cmp r0, 0x16  // is boss battle song?
    bne originalProcessing
    ldr r0, = bossPlayList

  pickRandomSong:
    ldr r3, =0x2001120  // fluctuating value
    ldrb r3, [r3, 0h]
    lsr r3, r3, 5 // get 3bit value to select from playList
    ldrb r0, [r0, r3]

  originalProcessing:
    lsl r0, r0, 0x10
    ldr r3, =0x8164C8C

  pop r15

.pool
virusPlayList:  // virus play list
  .byte 21, 34, 38, 41, 45, 48, 49, 52  // virus battle songs

bossPlayList:
  .byte 22, 39, 42, 44, 46, 50, 53, 22  // boss battle songs

// Hook
.org 0x0815B33A  // playSound
  bl playRandomSound

.close
