// for BN6GXX
.open "BN6GXX_SoundMod.gba", "BN6GXX_SoundMod_asm.gba", 0x08000000

.gba

.org 0x080711D0 // free? space

playRandomSound:
  push r14
  cmp r0, 0x15  // is virus battle song?
  bne isBossBattleSong

  isVirusSong:
    ldr r0, =virusPlayList
    b pickRandomSong

  isBossBattleSong:
    cmp r0, 0x16  // is boss battle song?
    bne isInternetSong
    ldr r0, = bossPlayList
    b pickRandomSong

  isInternetSong:
    cmp r0, 0x13  // is internet song?
    bne originalProcessing
    ldr r0, = internetPlayList

  pickRandomSong:
    ldr r3, =0x2001120  // fluctuating value
    ldrb r3, [r3, 0h]
    lsr r3, r3, 5 // get 3bit value to select from playList
    ldrb r0, [r0, r3]

  originalProcessing:
    lsl r0, r0, 0x10
    ldr r3, =0x8159DC8

  pop r15

.pool
virusPlayList:  // virus play list
  .byte 21, 38, 41, 45, 49, 52, 55, 57 // virus battle songs

bossPlayList:
  .byte 22, 39, 42, 44, 46, 50, 53, 56  // boss battle songs

internetPlayList:
  .byte 19, 58, 59, 60, 61, 62, 63, 19  // internet songs

// Hook
.org 0x08150476  // 0x8150474 maybe playSound(r0)
  bl playRandomSound

.close
