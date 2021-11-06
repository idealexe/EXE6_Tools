// for BN6FXX
.open "BN6FXX_SoundMod.gba", "BN6FXX_SoundMod_asm.gba", 0x08000000

.gba

.org 0x08070340 // free? space

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
    lsr r3, r3, 4 // get 4bit value to select from playList
    ldrb r0, [r0, r3]

  originalProcessing:
    lsl r0, r0, 0x10
    ldr r3, =0x8158278

  pop r15

.pool
virusPlayList:
  .byte 21, 38, 42, 47, 52, 56, 60, 21, 38, 42, 47, 52, 56, 60, 21, 38  // virus battle songs

bossPlayList:
  .byte 22, 34, 39, 43, 45, 48, 50, 53, 57, 61, 62, 22, 34, 39, 43, 45 // boss battle songs

internetPlayList:
  .byte 19, 41, 46, 51, 55, 59, 63, 19, 41, 46, 51, 55, 59, 63, 19, 41  // internet songs

// Hook
.org 0x0814E926
  bl playRandomSound

.close
