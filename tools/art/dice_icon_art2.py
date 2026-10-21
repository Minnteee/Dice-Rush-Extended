"""ASCII pixel icons (part 2) + special features (ears / horns / spoiler)."""
from pix import sprite, hexc, mix, lighten, darken, lum, outline_arr, pad, flip_h
import fonts
import numpy as np

A = {}
P = {}


def ic(name, art, pal=None):
    A[name] = art
    if pal:
        P[name] = pal


# ---------------------------------------------------------------- memes / faces
ic('frog', """
..eeee....eeee..
.eEEEEe..eEEEEe.
eEWWWWEeeEWWWWEe
eWWWKKWeeWWWKKWe
eWWWKKWEEWWWKKWe
.eWWWWEEEEWWWWe.
eEEEEEEEEEEEEEEe
eEEEEEEEEEEEEEEe
eEnnnnnnnnnnnnEe
eErrrrrrrrrrrrEe
.eEEEEEEEEEEEEe.
..eeeeeeeeeeee..""", {'E': '#5cb83a', 'e': '#2a6a1a', 'n': '#7a2a1a', 'r': '#b8503a'})

ic('frog_smug', """
..eeee....eeee..
.eEEEEe..eEEEEe.
eEEEEEEeeEEEEEEe
eeeeeeeeeeeeeeee
eWWWKKWeeWWWKKWe
.eWWWWeEEeWWWWe.
eEEEEEEEEEEEEEEe
eEEEEEEEEEEEEnne
eEEEEEEEEEnnnrEe
eEEnnnnnnnrrrEEe
.eEErrrrrrEEEEe.
..eeeeeeeeeeee..""", {'E': '#5cb83a', 'e': '#2a6a1a', 'n': '#7a2a1a', 'r': '#b8503a'})

ic('troll', """
...KKKKKKKKKK...
..KWWWWWWWWWWK..
.KWWKKWWWWKKWWK.
KWWKWWKWWKWWKWWK
KWWWKKWWWWKKWWWK
KWWWWWWWWWWWWWWK
KWKKKKKKKKKKKKWK
KWKWKWKWKWKWKKWK
KWWKKKKKKKKKKWWK
.KWWWWKKKKWWWWK.
..KKWWWWWWWWKK..
....KKKKKKKK....""")

ic('doge', """
.o............o.
.oo..........oo.
.oWo........oWo.
.oWWoooooooooWWo
oOOOOOOOOOOOOOOo
oOWWOOOOOOOOWWOo
oOOKOOOOOOOOKOOo
oOWWWOOOOOOWWWOo
oWWWWWWKKWWWWWWo
.oWWWWWKKWWWWWo.
..oWWWKKKKWWWo..
...ooWWWWWWoo...
.....oooooo.....""", {'O': '#e8a040', 'o': '#a8661c', 'W': '#fff2d8', 'K': '#2a1a10'})

ic('chad', """
...KKKKKKKKK...
..KwwwwwwwwwK..
.KwwWWWWWwwwwK.
.KwWWWWWWWWwwK.
.KwKKKWWWKKKwK.
.KWWKWWWWWKWWK.
.KWWWWWgWWWWWK.
.KWWWWWgWWWWWK.
.KWWWWggWWWWWK.
.KgWWWWWWWWWgK.
.KgWWKKKKKWWgK.
.KggWWWWWWWggK.
..KggggggggggK.
...KKKKKKKKKK..""", {'W': '#f2f2f2', 'w': '#5a5a5a', 'g': '#a8a8a8'})

ic('head', """
....SSSSS....
..SSSSSSSSS..
.SSSSSSSSSSS.
.SSSSSSSSSSS.
SSWWSSSSSWWSS
SSWKSSSSSWKSS
SSSSSSsSSSSSS
SSSSSSsSSSSSS
SsSKKKKKKKSsS
.SSKWWWWWKSS.
.SSSKKKKKSSS.
..SSSSSSSSS..
....SSSSS....""")

ic('dog_hat', """
....XXXXXX....
...XXXXXXXX...
...XRRRRRRX...
.XXXXXXXXXXXX.
NNYYYYYYYYYYNN
NNYYYYYYYYYYNN
NNYWKYYYYWKYNN
NNYYYYYYYYYYNN
.NYYYYKKYYYYN.
..YYYYYYYYYY..
..YYYKKKKYYY..
...YYYYYYYY...""", {'Y': '#ffcf5a', 'N': '#b8742a', 'X': '#3a2414', 'R': '#7a4a24'})

ic('zombie', """
...ZZZZZZZZ...
..ZZZZZZZZZZ..
.ZZZzzZZZZZZZ.
.ZZZZZZZZzZZZ.
ZZKKKZZZZKKKZZ
ZZKRKZZZZKRKZZ
ZZKKKZZzZKKKZZ
ZZZZZZZZZZZZZZ
ZZZKKKKKKKKZZZ
.ZZKWKWWKWKZZ.
.ZZZKKKKKKZZZ.
..ZZZZzZZZZZ..
...zZZZZZZz...""", {'Z': '#a8cc8a', 'z': '#6a8a54', 'R': '#e83a2a'})

ic('alien', """
....wwwwww....
..wwWWWWWWww..
.wWWWWWWWWWWw.
wWWWWWWWWWWWWw
wWKKKKWWKKKKWw
wWKKKWWWWKKKWw
wWKKWWWWWWKKWw
.wWWWWWWWWWWw.
..wWWWWWWWWw..
...wWWKKWWw...
....wWWWWw....
.....wwww.....""", {'W': '#b8e8b0', 'w': '#6aa868', 'K': '#141a14'})

ic('crewmate', """
....rrrrr...
..rrRRRRRr..
.rRRRRRRRRr.
rrRRIIIIIIIr
rRRIJJIIIIIr
rRRIIIIIIIir
rRRRiiiiiiR.
rRRRRRRRRRr.
rRRRRRRRRRr.
rRRRRRRRRRr.
.rRRRRRRRRr.
.rRRr..rRRr.
.rrrr..rrrr.""", {'R': '#d01a14', 'r': '#7a0c08'})

ic('ninja', """
....XXXXXX....
..XXXXXXXXXX..
.XXXXXXXXXXXX.
.RRRRRRRRRRRRRRR
.XXXXXXXXXXXXR.R
XXSSSSSSSSSSXX..
XXSKKSSSSKKSXX..
XXSSSSSSSSSSXX..
XXXXXXXXXXXXXX..
.XXXXXXXXXXXX...
..XXXXXXXXXX....
....XXXXXX......""", {'X': '#26262e', 'R': '#e8261c'})

ic('viking', """
T..............T
TT............TT
TTt....ww....tTT
.TTt.wwWWww.tTT.
.tTTwWWWWWWwTTt.
..tTWWWWWWWWTt..
...YYYYYYYYYY...
...SSSSggSSSS...
...SKSSggSSKS...
...OOSSSSSSOO...
...OOOOOOOOOO...
...OOOoOOoOOO...
....OOOOOOOO....
.....OOOOOO.....
......oOOo......""", {'O': '#e86a1a', 'o': '#a84a10', 'T': '#f2e8c8', 't': '#b8a878', 'W': '#d8dce8', 'w': '#8a8e9c'})

ic('fox', """
.K............K.
.OK..........KO.
.OOK........KOO.
.OWOK......KOWO.
.OOOOOOOOOOOOOO.
OOOOOOOOOOOOOOOO
OOOKKOOOOOOKKOOO
WOOOOOOOOOOOOOOW
WWWOOOOOOOOOOWWW
.WWWWWOOOOWWWWW.
..WWWWWWWWWWWW..
....WWWKKWWW....
......WWWW......""", {'O': '#ff8a2a', 'K': '#2a1408'})

ic('owl', """
.n............n.
.nn..........nn.
.nNn........nNn.
.nNNnnnnnnnnNNn.
nNTTTTNNNNTTTTNn
nTTIIITTTTIIITTn
nTIIKKITTIKKIITn
nTIIKKITTIKKIITn
nTTIIITOOTIIITTn
nNTTTTNOONTTTTNn
nNNNNNNNNNNNNNNn
nNTNNTNNNNTNNTNn
.nNNNNNNNNNNNNn.
..nnnnnnnnnnnn..""", {'N': '#9a724a', 'n': '#4a3018', 'T': '#e8d0a8', 'O': '#ff9a1f'})

ic('wolf', """
.g............g.
.gg..........gg.
.gWg........gWg.
.gWWgggggggggWWg
.ggggggggggggggg
gggIIgggggggIIgg
ggKIIgggggggIIKg
gggggggggggggggg
.ggwwwwwgwwwwwg.
..gwwwwKKwwwwg..
...gwwwKKwwwg...
....gwwwwwwg....
.....gggggg.....""", {'g': '#8a8e9c', 'w': '#e0e4ec', 'W': '#4a4c58'})

ic('bunny', """
..ww....ww..
.wWIw..wIWw.
.wWIw..wIWw.
.wWIw..wIWw.
.wWIw..wIWw.
..wWwwwwWw..
.wWWWWWWWWw.
wWWWWWWWWWWw
wWWKWWWWKWWw
wWWKWWWWKWWw
wWIWWIIWWIWw
wWWWWwwWWWWw
.wWWWWWWWWw.
..wwwwwwww..""", {'W': '#ffffff', 'w': '#b8b8c4'})

ic('robot_head', """
..ww.......ww..
..wWw.....wWw..
...wWWWWWWWw...
.wWWWWWWWWWWWw.
wWWWWWWWWWWWWWw
wWWbbbWWWbbbWWw
wWbbbbbWbbbbbWw
wWbbWbbWbbWbbWw
wWbbbbbWbbbbbWw
wWWbbbWWWbbbWWw
wWWWWWWWWWWWWWw
wWbWWbWWWbWWbWw
.wWWWWWWWWWWWw.
..wwwwwwwwwww..""", {'W': '#f4f8ff', 'w': '#9cc8ec', 'b': '#2c5d82'})

ic('robot', """
......II......
......gg......
..wwwwwwwwww..
.wWWWWWWWWWWw.
.wWGGGGGGGGWw.
.wWGIIGGIIGWw.
.wWGIIGGIIGWw.
.wWGGGGGGGGWw.
gwWWWWWWWWWWwg
gwWGWGWGWGWWwg
.wWWWWWWWWWWw.
..wwwwwwwwww..""", {'W': '#e0e8f0', 'w': '#7a8494', 'G': '#2a3038', 'g': '#5a6270'})

ic('golem', """
..gggggggggg..
.gwwwwwwwwwwg.
gwwgwwwwwwwgwg
gwGGGwwwwGGGwg
gwIIGwwwwGIIwg
gwwwwwggwwwwwg
gwgwwwggwwwwwg
gwwGGGGGGGGwwg
gwwGwGwGwGGwwg
gwwwwwwwwwgwwg
.gggggggggggg.""", {'w': '#a8a090', 'g': '#5a5448', 'G': '#2a2620'})

ic('kraken', """
....IIIIII....
..IIIIIIIIII..
.IIJJIIIIIIII.
.IJJIIIIIIIII.
.IIIIIIIIIIII.
.IIKWIIIIKWII.
.IIKKIIIIKKII.
..IIIIIIIIII..
.IIIIIIIIIIII.
II.II.II.II.II
I..I..II..I..I
I.II..I...II.I
.II..II....II.""")

# ---------------------------------------------------------------- creatures / animals
ic('snail', """
.K..K...........
.K..K...ooooo...
.KSSK..oNNNNNo..
SSSSS.oNooooNNo.
SSSSS.oNoNNoNoNo
.SSSS.oNoNoNNoNo
..SSSoNNoooNNoNo
..SSSSoNNNNNoNNo
..SSSSSoooooNNo.
..SSSSSSSSSSoo..
...SSSSSSSSSSSSS""", {'S': '#cfd8a0', 'K': '#4a5030', 'N': '#d88a3a', 'o': '#7a4214'})

ic('shell', """
....IIIIIII....
..IIJIJIJIJII..
.IJIJIJIJIJIJI.
IJIJIJIJIJIJIJI
IJIJIJIJIJIJIJI
IJIJIJIJIJIJIJI
.IJIJIJIJIJIJI.
..IIJIJIJIJII..
....IIIIIII....
.....iIIIi.....
....iiiiiii....""")

ic('bat', """
.I............I.
.II...I..I...II.
IIII..IIII..IIII
IIIII.IIII.IIIII
IIIIIIIWWIIIIIII
IIIIIIIIIIIIIIII
.IIIIIIIIIIIIII.
..II.III.III.II.
...I..I...I..I..""", {'W': '#ffffff'})

ic('bee', """
...ww...ww....
..wWWw.wWWw...
..wWWw.wWWw...
...ww...ww....
...KYYKKYYK...
..KYYKKYYKYYK.
KKKYYKKYYKYYYK
KWKYYKKYYKYYYK
KKKYYKKYYKYYK.
..KYYKKYYKKK..
...KKKKKKK....""", {'Y': '#ffd21f', 'W': '#ffffff', 'w': '#a8d8f0'})

ic('phoenix', """
O..............O
OY............YO
OYY....RR....YYO
.OYY..RYYR..YYO.
.OOYY.RYYR.YYOO.
..OOYYRRRRYYOO..
..ROOYRYYRYOOR..
...RROOYYOORR...
....RRRYYRRR....
......RYYR......
.....RYOOYR.....
....RY.OO.YR....
....R..OO..R....""", {'O': '#ff7a1f', 'Y': '#ffe25a', 'R': '#e8301a'})

ic('dragon', """
...........I....
..........II....
.........II..I..
....IIIIIIIIII..
..IIIIIIIIIIIII.
.IJIIIKKIIIIIII.
IIIIIIIIIIIIIIII
.W.W.WIIIIIIIII.
......IIIIIIIII.
.W.W.IIIIIIIIIII
IIIIIIIIIIIIIII.
.IIIIIIIIIIIIIII
........IIIIIIi.
.........IIIIIi.""", {'W': '#ffffff', 'K': '#c81a1a'})

ic('tentacle', """
.......IIII.....
.....IIIIIII....
....IIIiiIIII...
....III...III...
....IIJ..IIII...
....III..III....
.....III........
......IIJ.......
.......III......
.......IIIJ.....
........IIII....
.........IIIIII.
..........IIIII.""")

ic('tail', """
..........WWW.
........WWWWWW
.......OWWWWWW
......OOOOWWW.
.....OOOOOOo..
....OOOOOOOo..
...OOOOOOOo...
..OOOOOOOo....
.OOOOOOoo.....
OOOOOoo.......
OOooo.........""", {'O': '#ff8a2a', 'o': '#b84e10'})

ic('feather', """
...........III
.........IIIJI
........IIIJI.
.......IIIJII.
......IIIJII..
.....IIIJII...
....IIIJII....
...IIIJII.....
...IIJII......
..IIJII.......
..IJI.........
.iJ...........
i.............""")

ic('wing', """
...........II
.........IWWI
.......IIWWWI
.....IIWWWWWI
...IIWWWWWWI.
..IWWWWWWWWI.
.IWWWIWWWWI..
IWWWIWWWIWI..
.IWWIWWIWWI..
..IWIWWIWI...
...IIWIWI....
.....III.....""", {'W': '#ffffff'})

ic('halo', """
..I........I..
.III......III.
..I........I..
....IIIIII....
..IIJJJJJJII..
.IJJIIIIIIJJI.
IJI........IJI
IIi........iII
.IiiIIIIIIiiI.
..IIiiiiiiII..
....IIIIII....""")

# ---------------------------------------------------------------- objects
ic('chat', """
.WWWWWWWWWWWW.
WWWWWWWWWWWWWW
WWWWvvWWWvvWWW
WWWWvvWWWvvWWW
WWWWvvWWWvvWWW
WWWWWWWWWWWWWW
.WWWWWWWWWWWW.
...WWW........
...WW.........
...W..........""", {'v': '#5a23b8'})

ic('live', """
.RRRRRRRRRRRRRRR.
RRRRRRRRRRRRRRRRR
RRWRRRWRWRWRWWWRR
RRWRRRWRWRWRWRRRR
RRWRRRWRWRWRWWRRR
RRWRRRWRWRWRWRRRR
RRWWWRWRRWRRWWWRR
RRRRRRRRRRRRRRRRR
.RRRRRRRRRRRRRRR.""", {'R': '#e81c1c'})

ic('play', """
.WWWWWWWWWWWWW.
WWWWWWWWWWWWWWW
WWWWWRWWWWWWWWW
WWWWWRRRWWWWWWW
WWWWWRRRRRWWWWW
WWWWWRRRRRRRWWW
WWWWWRRRRRWWWWW
WWWWWRRRWWWWWWW
WWWWWRWWWWWWWWW
WWWWWWWWWWWWWWW
.WWWWWWWWWWWWW.""", {'R': '#e81c1c'})

ic('skull', """
....IIIIII....
..IIIIIIIIII..
.IIIIIIIIIIII.
IIIIIIIIIIIIII
IIIIIIIIIIIIII
III...II...III
III...II...III
III...II...III
IIIIII..IIIIII
.IIIII..IIIII.
..IIIIIIIIII..
..I.I.II.I.I..
..IIIIIIIIII..""")

ic('coin', """
....yyyyy....
..yyYYYYYyy..
.yYYYYYYYYWy.
.yYYYYyYYYYy.
yYYYYyyyyYYYy
yYYYyYyYYYYYy
yYYYYyyyYYYYy
yYYYYYyYyYYYy
yYYYyyyyYYYYy
.yYYYYyYYYYy.
.yYYYYYYYYYy.
..yyYYYYYyy..
....yyyyy....""")

ic('chest', """
..nnnnnnnnnn..
.nNNNNNNNNNNn.
nNNNNNNNNNNNNn
nYYYYYYYYYYYYn
nNNNNNYYNNNNNn
nnnnnnYYnnnnnn
nNNNNYKKYNNNNn
nNNNNYYYYNNNNn
nNNNNNNNNNNNNn
nYYYYYYYYYYYYn
nNNNNNNNNNNNNn
nnnnnnnnnnnnnn""", {'N': '#b8742a', 'n': '#5a3414', 'Y': '#ffd23a'})

ic('gamepad', """
..IIIIIIIIIIII..
.IIIIIIIIIIIIII.
IIIIIIIIIIIIIIII
III.IIIIIIII.III
II...IIIIII.I.II
III.IIIIIIII.III
IIIIIIIIIIIIIIII
IIIIII....IIIIII
IIIII......IIIII
.III........III.""")

ic('btn_a', """
...EEEEEE...
.EEEEEEEEEE.
.EEEEWWEEEE.
EEEEWEEWEEEE
EEEEWEEWEEEE
EEEEWWWWEEEE
EEEEWEEWEEEE
EEEEWEEWEEEE
.EEEEEEEEEE.
.eEEEEEEEEe.
...eeeeee...""", {'E': '#3ac04a', 'e': '#1e7a2a'})

ic('btn_b', """
...RRRRRR...
.RRRRRRRRRR.
.RRRWWWRRRR.
RRRRWRRWRRRR
RRRRWWWRRRRR
RRRRWRRWRRRR
RRRRWRRWRRRR
RRRRWWWRRRRR
.RRRRRRRRRR.
.rRRRRRRRRr.
...rrrrrr...""", {'R': '#e8301c', 'r': '#8a120c'})

ic('seven', """
IIIIIIIIIII
IJJJJJJJJII
IIIIIIIJIII
......IJII.
.....IJII..
....IJIII..
....IJII...
...IJIII...
...IJII....
...IJII....
...IIII....
...IIII....""")

ic('cherry', """
........eEe..
.......eEEEe.
......n.ee...
.....n.n.....
....n...n....
...n.....n...
.RRRR...RRRR.
RRWRRR.RRWRRR
RWRRRR.RWRRRR
RRRRRR.RRRRRR
rRRRRr.rRRRRr
.rrrr...rrrr.""", {'R': '#e8261c', 'r': '#8a0c08', 'n': '#5a3414'})

ic('bell', """
......oo......
.....oOOo.....
....oYYOOo....
...oYOOOOOo...
...oYOOOOOo...
...oYOOOOOo...
...oYOOOOOo...
..oYOOOOOOOo..
..oYOOOOOOOo..
.oYOOOOOOOOOo.
oOOOOOOOOOOOOo
oooooooooooooo
.....oOOo.....
......oo......""", {'O': '#ffb020', 'o': '#8a4a08', 'Y': '#fff0a0'})

ic('vault', """
.IIIIIIIIIIII.
IJJJJJJJJJJJJI
IJiiiiiiiiiiJI
IJiIiiJJJiiiJI
IJiiiJiiiJiiJI
IJiiJiiIiiJIJI
IJiiJiIJIiJIJI
IJiiJiiIiiJIJI
IJiiiJiiiJiiJI
IJiIiiJJJiiiJI
IJiiiiiiiiiiJI
IJJJJJJJJJJJJI
.IIIIIIIIIIII.
.II........II.""")

ic('dial', """
.....IJI.....
...IIIJIII...
..IiiiJiiiI..
.IiJiiiiiJiI.
.IiiiIIIiiiI.
IIJiIJJJIiJII
IiiiIJIJIiiiI
IIJiIJJJIiJII
.IiiiIIIiiiI.
.IiJiiiiiJiI.
..IiiiJiiiI..
...IIIIIII...""")

ic('honey', """
...OOOOOOO...
..OYYOOOOOO..
.nOOnOOnOOOn.
nNOnNNOnNNNNn
nNOnNNNNNNNNn
nNNNNNNNNNNNn
nNTTTTTTTTTNn
nNTNNNNNNNTNn
nNTTTTTTTTTNn
nNNNNNNNNNNNn
.nNNNNNNNNNn.
..nnnnnnnnn..""", {'O': '#ffb020', 'Y': '#ffe890', 'N': '#b8742a', 'n': '#5a3414', 'T': '#f2d8a0'})

ic('flame', """
.....R......
.....RR.....
....RRR..R..
...RRORR.RR.
...RROORRRR.
..RROOORRORR
.RRROOYOOORR
.RROOYYOOORR
RROOYYYYOOOR
RROYYWWYYOOR
RROYWWWWYOOR
.RROYWWYYOR.
..RROYYYORR.
...RRRRRRR..""", {'R': '#e0301a', 'O': '#ff9a1f', 'Y': '#ffe25a', 'W': '#fff8d0'})

ic('carrot', """
..........E.E
.........EEE.
.......eEEEEE
.......OOEEe.
......OOOOe..
.....OOoOO...
....OOOOO....
....OOoOO....
...OOOOO.....
...OoOO......
..OOOO.......
..OOO........
.OO..........
.O...........""", {'O': '#ff8a1f', 'o': '#c05a10', 'E': '#4fc040', 'e': '#23772a'})

ic('donut', """
....nnnnnn....
..nnPPPPPPnn..
.nPPPPWPPPPPn.
.nPYPPPPPBPPn.
nPPPPPnnPPPPPn
nPPPPn..nPRPPn
nPBPPn..nPPPPn
nPPPPPnnPPPYPn
.nPPPPPPPPPPn.
.nNPPRPPPPPNn.
..nNNNPPPNNn..
....nnnnnn....""", {'P': '#ff7ac8', 'n': '#7a4a2a', 'N': '#d9a05b', 'B': '#4a9aff', 'Y': '#ffe25a', 'R': '#ff3a3a'})

ic('cookie', """
....tttttt....
..ttTTTTTTtt..
.tTTnTTTTTTTt.
.tTnnTTTTnTTt.
tTTTTTTTnnTTTt
tTTTTTnTTTTTTt
tTTnTTnnTTTnTt
tTnnTTTTTTnnTt
tTTTTTTnTTTTTt
.tTTTnTnnTTTt.
.tTTTTTTTTnTt.
..ttTTTTTTtt..
....tttttt....""", {'T': '#f2c98c', 't': '#b07838', 'n': '#4a2a12'})

ic('pizza', """
.NNNNNNNNNNN.
NnNNNNNNNNNnN
.YYYYYYYYYYY.
.YRRYYYYYRRY.
..RRYYYYYRR..
..YYYYRRYYY..
...YYYRRYY...
...YYYYYYY...
....YRRYY....
....YRRY.....
.....YYY.....
.....YY......
......Y......""", {'N': '#d8903a', 'n': '#a05a1a', 'Y': '#ffd85a', 'R': '#d8301a'})

ic('burger', """
....oooooo....
..ooOOOOOOoo..
.oOOWOOOOWOOo.
oOOOOOOOWOOOOo
oooooooooooooo
EEEeEEEEeEEEEE
YYYYYYYYYYYYYY
.YnnnnnnnnnnY.
nnnnnnnnnnnnnn
nNnnnNnnnnNnnn
oooooooooooooo
.oOOOOOOOOOOo.
..oooooooooo..""", {'O': '#e8a050', 'o': '#a8661c', 'W': '#fff4d8', 'E': '#5ac83a', 'e': '#2a8a1a', 'Y': '#ffd23a', 'n': '#6a3416', 'N': '#8a4a22'})

ic('sushi', """
..OOOOOOOOOO..
.OOWOOOOWOOOO.
OOOOWOOOOWOOOO
.OOOOOOOOOOOO.
.WWWWWkkWWWWW.
WWWWWWkkWWWWWW
WWWWWWkkWWWWWW
.wwwwwkkwwwww.""", {'O': '#ff8a5a', 'W': '#ffffff', 'w': '#d0d4dc', 'k': '#1e3a1e'})
A['sushi'] = A['sushi'].replace('OOWOOOOWOOOO', 'OOTOOOOTOOOO').replace('OOOOWOOOOWOOOO', 'OOOOTOOOOTOOOO')
P['sushi']['T'] = '#ffd0b8'

ic('nori', """
....kkkkkk....
..kkWWWWWWkk..
.kWWWWWWWWWWk.
.kWWWOOOWWWWk.
kWWWOOOOEWWWWk
kWWWOOOOEEWWWk
kWWWWOOOEWWWWk
.kWWWWWWWWWWk.
.kwWWWWWWWWwk.
..kkwwwwwwkk..
....kkkkkk....""", {'k': '#1e3a1e', 'O': '#ff7a5a', 'E': '#7ad84a', 'w': '#d0d4dc'})

ic('salmon', """
......OOOO.......
....OOOOOOOO..OO.
..OOTOOTOOTOOOO..
.OKOOOOOOOOOOOO..
OOOOOOOOOOOOOOOO.
.OOTTTTTTTTOOOOO.
..OOTTTTTTOO..OO.
....OOOOOO.......""", {'O': '#ffb098', 'T': '#fff0e8', 'K': '#1b1b1b'})

ic('tile', """
.wwwwwwwwww.
wWWWWWWWWWWe
wWWWWRWWWWWe
wWWRRRRRRWWe
wWWRWRWWRWWe
wWWRWRWWRWWe
wWWRRRRRRWWe
wWWWWRWWWWWe
wWWWWRWWWWWe
wWWWWWWWWWWe
.eeeeeeeeee.""", {'W': '#fafaf0', 'w': '#c8c8b8', 'R': '#d81a1a', 'e': '#2e8a4a'})

ic('mic', """
..wwww..
.wWgWgw.
.wgWgWw.
.wWgWgw.
.wgWgWw.
..wwww..
..YYYY..
..XXXX..
..XXXX..
...XX...
...XX...
...XX...
...XX...
..XXXX..""", {'X': '#3a3a44'})

ic('note', """
....IIIIII
....IIIIII
....II..II
....II...I
....II....
....II....
....II....
.IIIII....
IIIIII....
IIIIII....
.IIII.....""")

ic('moon', """
....IIII....
..IIIII.....
.IIII.......
.IIJ........
IIIJ........
IIIJ........
IIIJ........
IIII........
.IIII.......
.IIIII....I.
..IIIIIIIII.
....IIIII...""")

ic('crater', """
....iiiiiii....
..iiiiiiiiiii..
.iiIIIIIIIIIii.
iiIIiiiiiiiIJii
iIIiiiiiiiiiJIi
iIIiiiiiiiiiJIi
.iIJiiiiiiiJJi.
..iIJJJJJJJJIi.
...iiIIIIIIii..
.....iiiiii....""")

ic('muscle', """
.........SSS..
........SSSSS.
........SsSSS.
........SSSSs.
.........SSS..
.....ss..SSS..
....sSSs.SSS..
...sSSSSsSSS..
..SSSSSSSSSs..
.SSSSSSSSSSs..
SSSSSSSSSss...
SSSSsssss.....""", {'S': '#f6c896', 's': '#c8905a'})

ic('katana', """
..............WW
.............WWw
............WWw.
...........WWw..
..........WWw...
.........WWw....
........WWw.....
.......WWw......
......YWw.......
.....YYY........
....XRY.........
...XRX..........
..XRX...........
.XRX............
XX..............""", {'W': '#f0f4ff', 'w': '#8a94a8', 'X': '#1b1b1b', 'R': '#c41a1a', 'Y': '#e8b830'})

ic('sword', """
...W...
..WWw..
..WWg..
..WWg..
..WWg..
..WWg..
..WWg..
..WWg..
..WWg..
..WWg..
YYYYYYY
.yYYYy.
...N...
...N...
...n...
..YYY..""", {'W': '#f0f4ff', 'g': '#8a94a8', 'N': '#8a5a2a', 'n': '#5a3414'})

ic('knife', """
.............W
............WW
...........WWw
..........WWw.
.........WWw..
........WWw...
.......WWw....
......WWw.....
.....gWg......
....XXg.......
...XXX........
..XXX.........
.XXX..........
XX............""", {'W': '#f0f4ff', 'w': '#8a94a8', 'X': '#2a2a30'})

ic('axe', """
......NN......
.gg...NN...gg.
gWWg..NN..gWWg
gWWWggNNggWWwg
gWWWWWNNWWWWwg
gWWWWWNNWWWWwg
gWWWggNNggWWwg
gWWg..NN..gwwg
.gg...NN...gg.
......NN......
......NN......
......NN......
......nn......""", {'W': '#e8ecf4', 'w': '#9aa0ae', 'g': '#4a4e5c', 'N': '#b8743a', 'n': '#5a3414'})

ic('hammer', """
.gggg.......
gwwwwgg.....
gwWWWwgg....
gwwwwwwg....
.gggwwgN....
....ggNNN...
......NNN...
.......NNN..
........NNN.
.........NN.""", {'W': '#eef0f6', 'w': '#a8aebc', 'g': '#5a5e6c', 'N': '#b8743a'})

ic('bat_club', """
............tT
...........tTT
..........tTTT
.........tTTT.
........tTTT..
.......tTTT...
......tTT.....
.....tTT......
....tT........
...nT.........
..nn..........
.nN...........
nn............""", {'T': '#f0c890', 't': '#b0763a', 'n': '#3a2410', 'N': '#6a4420'})

ic('bone', """
.WW........WW.
WWWW......WWWW
WWWWWWWWWWWWWW
.WWWWWWWWWWWW.
WWWWwwwwwwWWWW
WWww......wwWW
.ww........ww.""", {'W': '#fffaf0', 'w': '#c8c0a8'})

ic('key', """
.IIII..........
IIJJII.........
IJ..IIIIIIIIIII
II..IIIIIIIIIII
IIJJII.....I.II
.IIII......I.I.""")

ic('lock', """
...IIIII...
..II...II..
.II.....II.
.II.....II.
.II.....II.
IIIIIIIIIII
IJJJJJJJJJI
IJIIIIIIIJI
IJIII.IIIJI
IJIII.IIIJI
IJIII.IIIJI
IJIIIIIIIJI
IIIIIIIIIII""")

ic('mug', """
...w..w....
..w..w.....
...w..w....
.WWWWWWWW..
.WnnnnnnW..
.WWWWWWWWWW
.WRRRRRRWWW
.WWWWWWWW.W
.WWWWWWWWWW
.WWWWWWWW..
..wwwwww...""", {'W': '#ffffff', 'w': '#c8ccd8', 'n': '#5a3414', 'R': '#d84a2a'})

ic('toilet', """
.wwwwwwwwww.
.wWWWWWWWWw.
.wWWWWWWWWw.
.wwwwwwwwww.
..wWWWWWWw..
wwwwwwwwwwww
wWWWWWWWWWWw
.wWWWWWWWWw.
..wWWWWWWw..
...wWWWWw...
...wWWWWw...
..wwwwwwww..""", {'W': '#ffffff', 'w': '#9aa8b8'})

ic('witch_hat', """
..........XX.
........XXX..
.......XXX...
......XXXX...
.....XXXXX...
.....XXXXXX..
....XXXXXXX..
....IIIIIII..
...XIIYYIIX..
XXXXXXXXXXXXX
.XXXXXXXXXXX.""", {'X': '#3a2450', 'Y': '#ffd23a'})

ic('hat', """
......BB......
.....BBBb.....
.....BYBb.....
....BBBBBb....
....BBBBYb....
...BYBBBBBb...
...BBBBBBBb...
..BBBBBYBBBb..
..YYYYYYYYYY..
.BBBBBBBBBBBb.
bbbbbbbbbbbbbb""", {'B': '#4a5aff', 'b': '#222a9a', 'Y': '#ffd23a'})

ic('cauldron', """
...I...I.I...
..I.I.I......
.IIIIIIIIIII.
XJIIIIIIIIIJX
XXXXXXXXXXXXX
.XXXXXXXXXXX.
XXXXXXXXXXXXX
XXGXXXXXXXXXX
XXGXXXXXXXXXX
.XXXXXXXXXXX.
..XX.....XX..""", {'X': '#26222e', 'G': '#5a566a'})

ic('potion', """
....NN....
....NN....
...wwww...
....ww....
...wWWw...
..wWWWWw..
.wWIIIIIw.
wWIIJIIIIw
wIIIIIIIIw
wIIIIIIIIw
.wIIIIIIw.
..wwwwww..""", {'W': '#e8f8ff', 'w': '#8ab8d0', 'N': '#a8642a'})

ic('ufo', """
.....CCCCCC.....
....CWCCCCCC....
....CCCCCCCC....
.gggggggggggggg.
gwwwwwwwwwwwwwwg
gYgwYgwYgwYgwYgg
.gggggggggggggg.""", {'C': '#5ae8c8', 'w': '#d8dce8', 'g': '#7a7e8c', 'Y': '#ffe25a'})

ic('beam', """
....gwwwwg....
..gggggggggg..
.gYgYgYgYgYgg.
..gggggggggg..
....LLLLLL....
....LLLLLL....
...LLLLLLLL...
...LLLLLLLL...
..LLLWWKWLLL..
..LLLWWWWLLL..
.LLLLWLLWLLLL.
.LLLLLLLLLLLL.""", {'L': '#f6f0a0', 'w': '#d8dce8', 'g': '#7a7e8c', 'Y': '#ffe25a'})

ic('train', """
..XX............
..XX......XXXX..
.XXXX.....XCCX..
..RR......XCCX..
RRRRRRRRRRRRRRR.
RYYYYYYYYYYRRRR.
RRRRRRRRRRRRRRR.
RRRRRRRRRRRRRRR.
YXXXXRRXXXXRXXX.
.XgX..XgX..XgX..
..X....X....X...""", {'R': '#d0281c', 'X': '#1b1b1f', 'Y': '#ffd23a', 'C': '#9ee8ff', 'g': '#8a8e9c'})

ic('car', """
......RRRR......
.....RCCCRR.....
.RRRRRCCCRRRRR..
RRRRRRRRRRRRRRRR
RWWWWRRRWWRRRRRR
RRRRRRRRRWWRRRRR
rKKKrrrrrrrKKKrr
KKgKK.....KKgKK.
.KKK.......KKK..""", {'R': '#e8261c', 'r': '#8a120c', 'C': '#9ee8ff', 'K': '#1b1b1f', 'g': '#a8aebc'})

ic('rocket', """
.....I.....
....III....
...IIIII...
...WWWWW...
..WWWWWWw..
..WWBBBWw..
..WBCCBWw..
..WBCCBWw..
..WWBBBWw..
..WWWWWWw..
.IWWWWWWwI.
IIWWWWWWwII
II.wwwww.II
I...OYO...I
....OYO....
.....O.....""", {'W': '#ffffff', 'w': '#b8bcc8', 'B': '#4a5a8a', 'C': '#5ad8ff', 'O': '#ff8a1f', 'Y': '#ffe25a'})

ic('bomb', """
.........Y.Y.
..........O..
.........Y.Y.
........n....
.......n.....
....GGGn.....
..GXXXXXGG...
.GXwXXXXXXG..
GXwXXXXXXXXG.
GXXXXXXXXXXG.
GXXXXXXXXXXG.
GXXXXXXXXXXG.
.GXXXXXXXXG..
..GXXXXXXG...
....GGGG.....""", {'X': '#1e1e26', 'G': '#4a4a58', 'w': '#8a8aa0', 'n': '#c8a878', 'O': '#ff5a1f', 'Y': '#ffe25a'})

ic('fuse', """
..........Y..Y
...........OY.
.........YOWOY
..........YO..
.........n..Y.
........n.....
...RRRRn......
..RRRRRRR.....
.RRRRRRRRR....
RRWRRRRRRRR...
RRRRRRRRRRR...
.RRRRRRRRR....
..rRRRRRr.....
...rrrrr......""", {'R': '#e0301c', 'r': '#8a120c', 'n': '#d8c890', 'O': '#ff8a1f', 'W': '#ffffff', 'Y': '#ffe25a'})
# dynamite bundle with a lit fuse
A['fuse'] = """
.......Y...Y.
.........O...
........OWO.Y
.....Y...O...
.......nY....
......n......
.....n.......
.rrrrnrrrrr..
.RWRrRWRrRRr.
.RWRrRWRrRRr.
.RRRrRRRrRRr.
.XXXXXXXXXXX.
.RRRrRRRrRRr.
.RRRrRRRrRRr.
.RRRrRRRrRRr.
..rr..rr..rr."""
P['fuse'] = {'R': '#e0301c', 'r': '#8a120c', 'n': '#e8d8a8', 'O': '#ff8a1f', 'W': '#ffffff', 'Y': '#ffe25a', 'X': '#2a2420'}

ic('question', """
..IIIIIII..
.IIIIIIIII.
IIII...IIII
III.....III
.......IIII
......IIII.
.....IIII..
....IIII...
....III....
...........
....III....
....III....""")

ic('bolt', """
.....IIII
....IIII.
...IIII..
..IIII...
.IIIIIII.
IIIIIIII.
....IIII.
...IIII..
...III...
..III....
..II.....
.II......
.I.......""")

ic('bolt_small', """
...GGGG...
.GGGGGGGG.
.GwwwwwwG.
.GwwwIwwG.
.GwwIIwwG.
.GwIIwwwG.
.GwIIIIwG.
.GwwwIIwG.
.GwwIIwwG.
.GwwIwwwG.
.GwwwwwwG.
.GGGGGGGG.""", {'G': '#3a3f4a', 'w': '#e0e8f0'})

ic('cloud', """
......wwww......
....wwWWWWw.....
...wWWWWWWWw....
.wwWWWWWWWWWww..
wWWWWWWWWWWWWWw.
wWWWWWWWWWWWWWWw
wWWWWWWWWWWWWWWw
.wwwwwwwwwwwwww.
.......II.......
......II........
.....IIII.......
.......II.......
......II........""", {'W': '#f4f6ff', 'w': '#a8acc8'})

ic('ghost', """
....WWWWW....
..WWWWWWWWW..
.WWWWWWWWWWW.
.WWWWWWWWWWw.
WWWKKWWWKKWWw
WWWKKWWWKKWWw
WWWWWWWWWWWWw
WWWWWKKKWWWWw
WWWWWKKKWWWWw
WWWWWWWWWWWWw
WWWWWWWWWWWww
WW.WWW.WWW.Ww
W...W...W...w""", {'W': '#ffffff', 'w': '#b8bce0', 'K': '#2a2a4a'})

ic('arrow_up', """
......I......
.....III.....
....IIIII....
...IIIIIII...
..IIIIIIIII..
.IIIIIIIIIII.
IIIIIIIIIIIII
....IIIII....
....IIIII....
....IIIII....
....IIIII....
....IIIII....
....IIIII....""")

ic('chart', """
w.........IIII
w..........III
w.........II.I
w........II...
w...I...II....
w..III.II.....
w.II.III......
wII...I.......
wI............
w.............
wwwwwwwwwwwwww""", {'w': '#c8ccd8'})

ic('shield', """
YYYYYYYYYYYY
YIIIIWWIIIIY
YIIIIWWIIIIY
YIIIIWWIIIIY
YWWWWWWWWWWY
YWWWWWWWWWWY
YIIIIWWIIIIY
YIIIIWWIIIIY
.YIIIWWIIIY.
.YIIIWWIIIY.
..YIIWWIIY..
...YIWWIY...
....YWWY....
.....YY.....""", {'Y': '#e8b830', 'W': '#f4f4f8'})

ic('triangle', """
....bbbbbb....
..bbbbbbbbbb..
.bbCCCCCCCCbb.
.bbCCWCCWCCbb.
bbbbCCCCCCbbbb
bbbbCWCWCCbbbb
bbbbbCCCCbbbbb
bbbbbCCCCbbbbb
.bbbbbCCbbbbb.
.bbbbbCCbbbbb.
..bbbbbbbbbb..
....bbbbbb....""", {'b': '#141a3a', 'C': '#3a6aff', 'W': '#c8d8ff'})

ic('star', """
......I......
......I......
.....III.....
.....IJI.....
IIIIIIJIIIIII
.IIIIJJIIIII.
..IIIIIIIII..
...IIIIIII...
...IIIIIII...
..IIII.IIII..
..III...III..
.II.......II.""")

ic('wand', """
.........Y...
........YYY..
......YYYWYYY
........YYY..
.......W.Y...
......WW.....
.....NW......
....NN.......
...NN........
..NN.........
.NN..........
NN...........""", {'Y': '#ffd23a', 'W': '#ffffff', 'N': '#3a2a1a'})

ic('sparkle', """
.....I.......
.....I.....I.
....III...III
....III....I.
...IIJII.....
IIIIJJJIIII..
...IIJII.....
....III......
....III...I..
.....I...III.
.....I....I..""")

ic('comet', """
I.............
.I..I.........
..II.I........
.I.III.I......
...IIII.I.....
....IIIII.....
.....IIIIJ....
......IJJJJ...
.......JJJJJ..
.......JJJJJ..
........JJJ...""")

ic('jackolantern', """
......ee......
......e.......
..oOOOOOOOOo..
.oOOoOOOOoOOo.
oOOoOOOOOOoOOo
oOYYoOOOOoYYOo
oOYYYoOOoYYYOo
oOOoOOYYOOoOOo
oOYoYYoYYoYYOo
oOYYYYYYYYYYOo
.oOYoYYoYYoOo.
..oOOOOOOOOo..""", {'O': '#ff8a1f', 'o': '#a8500a', 'Y': '#ffe25a', 'e': '#3a8a2a'})

ic('leaf', """
..........EE
.......EEEEE
.....EEEEEeE
....EEEEEeEE
...EEEEEeEEE
..EEEEEeEEE.
..EEEEeEEE..
.EEEEeEEEE..
.EEEeEEEE...
.EEeEEEE....
.EeEEE......
.e..........
e...........""", {'E': '#5ac83a', 'e': '#23772a'})

ic('rainbow', """
.....RRRRRR.....
...RROOOOOORR...
..ROOYYYYYYOOR..
.ROYYEEEEEEYYOR.
.ROYEEBBBBEEYOR.
ROYEBBVVVVBBEYOR
ROYEBV....VBEYOR
ROYEBV....VBEYOR
WWWWWW....WWWWWW
.WWWW......WWWW.""", {'R': '#ff3a3a', 'O': '#ff9a1f', 'Y': '#ffe25a', 'E': '#4fd040', 'B': '#3a8aff', 'V': '#a04aff', 'W': '#ffffff'})

ic('nyan', """
......TTTTTTT....
RRRRRTPPPPPPPT...
RRRRRTPpPPpPPTgg.
OOOOOTPPPPPPgggg.
OOOOOTPPpPPPgKgKg
YYYYYTPPPPPPggggg
YYYYYTPpPPPPgPgPg
EEEEETPPPPPpTggg.
EEEEETTTTTTTT....
BBBBB.g.g..g.g...""", {'T': '#f2c88a', 'P': '#ff9ad0', 'p': '#ff3a8a', 'g': '#9a9aa8', 'R': '#ff3a3a', 'O': '#ff9a1f', 'Y': '#ffe25a', 'E': '#4fd040', 'B': '#3a8aff'})

ic('fangs', """
.rrrrrrrrrrrr.
rRRRRRRRRRRRRr
rRRRRRRRRRRRRr
rWWWWWWWWWWWWr
.WWW......WWW.
..WW......WW..
..WW......WW..
...W......W...
.rrrrrrrrrrrr.
..rRRRRRRRRr..
....rrrrrr....""", {'R': '#d01a3a', 'r': '#6a0a1a', 'W': '#ffffff'})

ic('volcano', """
....R..R.....
...R.RR.R....
.....RR......
....nOOn.....
...nnOOnn....
...nnnOnnn...
..nnnnnnnnn..
..nNnnnnnNn..
.nnnnnNnnnnn.
.nnNnnnnnnNnn
nnnnnnnnnnnnn""", {'n': '#6a4a3a', 'N': '#9a7a6a', 'O': '#ff8a1f', 'R': '#ff4a1f'})

ic('lava', """
..OOOOOOOO..
.OYYYYOOOOO.
OYYWYOOOOOOO
OOYYOOOOOOOO
OOOOOOOOrOOO
.OOOOOrOOOO.
..OO.OOOO...
..OO..OO....
...O..OO....
......O.....""", {'O': '#ff6a1f', 'Y': '#ffd23a', 'W': '#fff6c0', 'r': '#b8200a'})

ic('crown', """
.Y.....Y.....Y.
YYY...YYY...YYY
.Y....YIY....Y.
.YY...YYY...YY.
.YYY.YYYYY.YYY.
.YYYYYYYYYYYYY.
.YIYYYYIYYYYIY.
.YYYYYYYYYYYYY.
.yyyyyyyyyyyyy.""", {'Y': '#ffd23a', 'y': '#a8700c'})

ic('meteor', """
..........OY.
.........OYO.
........OYO..
......OOYO...
....nnnOO....
...nNNnn.....
..nNNNNn.....
..nNnNNn.....
..nNNNNn.....
...nnnn......""", {'n': '#5a3a2a', 'N': '#a8806a', 'O': '#ff8a2a', 'Y': '#ffe25a'})

ic('rune', """
...gggggg...
..gwwwwwwg..
.gwwwIwwwwg.
.gwwwIIwwwg.
.gwwwIwIwwg.
.gwwwIwwIwg.
.gwwwIIwwwg.
.gwwwIwIwwg.
.gwwwIwwwwg.
.gwwwwwwwwg.
.gggggggggg.""", {'w': '#a8a090', 'g': '#5a5448'})

ic('hourglass', """
NNNNNNNNNNN
.wwwwwwwww.
.wYYYYYYYw.
..wYYYYYw..
...wYYYw...
....wYw....
.....w.....
....wYw....
...wwYww...
..wwwYwww..
.wwYYYYYww.
.wYYYYYYYw.
NNNNNNNNNNN""", {'N': '#8a5a2a', 'w': '#d8e8f0', 'Y': '#ffd23a'})

ic('blueprint', """
WWWWWWWWWWWWWW
WbbbbbbbbbbbbW
WbWWWWWWWbbbbW
WbWbbbbbWbbbbW
WbWbbbbbWWWWbW
WbWbbbbbbbbWbW
WbWWWbWWWWWWbW
WbbbbbbbbbbbbW
WbbWbWbWbWbbbW
WWWWWWWWWWWWWW""", {'W': '#f0f8ff', 'b': '#1f4a9a'})

ic('brick', """
....hhhhhhh....
...hBBBBBBBd...
...hBBBBBBBd...
...hBBBBBBBd...
....ddddddd....
hhhhhhh.hhhhhhh
hBBBBBBdhBBBBBd
hBBBBBBdhBBBBBd
hBBBBBBdhBBBBBd
.dddddd..dddddd""", {'B': '#c8502a', 'h': '#f08a5a', 'd': '#6a2412'})

ic('clover', """
.....II.II.....
....IIIIIII....
....IIIiIII....
.....IIiII.....
.II...IiI...II.
IIII...I...IIII
IIiiiiiIiiiiiII
IIII...I...IIII
.II...IiI...II.
.....IIiII.....
....IIIiIII.ii.
....IIIIIII..ii
.....II.II....i""")

ic('corn', """
.....YY.....
....YyYY....
....YYyY....
...YyYYyY...
...YYyYYY...
...YyYYyY...
..EYYyYYYE..
..EEyYYyEE..
.EEEYYyYEEE.
.EEEEYYEEEE.
..EEEEEEEE..
....EEEE....""", {'Y': '#ffd83a', 'y': '#c8901a', 'E': '#5ac83a'})

ic('circuit', """
..I..I..I....
..I..I..I....
.IIIIIIIIII..
.I........I..
III.JJJJ.IIII
.I..J..J..I..
.I..J..J..I..
III.JJJJ.IIII
.I........I..
.IIIIIIIIII..
..I..I..I....
..I..I..I....""")

ic('hand', """
...ZZ.ZZ......
.ZZZZ.ZZ.ZZ...
.ZZ.Z.ZZ.ZZ...
.ZZ.Z.ZZ.ZZ...
.ZZ.Z.ZZ.ZZ.ZZ
.ZZZZZZZZZZ.ZZ
.ZZZZZZZZZZZZZ
.ZZZZZZZZZZZZ.
..ZZZZZZZZZZ..
...ZZZZZZZZ...
...ZZZZZZZZ...
..nnnnnnnnnn..""", {'Z': '#a8cc8a', 'n': '#5a3a2a'})

ic('gem', """
...JJJJJJJJ...
..JJJIJJIJJJ..
.JJIIIJJIIIJJ.
IIIIIIIIIIIIII
.IIiIIIIIIiII.
..IIiIIIIiII..
...IIiIIiII...
....IIiiII....
.....IIII.....
......II......""")

ic('horn', """
..............T.
.............TT.
............TTt.
...........TTt..
..........YYy...
.........TTt....
.......TTTTt....
.....YYYYYy.....
...TTTTTTt......
.KKTTTTTTt......
KKKTTTTTt.......
KKKTTTTt........
.KKtttt.........""", {'T': '#f2e8c8', 't': '#a89870', 'Y': '#c8902a', 'K': '#3a2a1a'})

ic('bank', """
......II......
....IIIIII....
..IIIJJJJIII..
IIIIIIIIIIIIII
.IIIIIIIIIIII.
..II.II.II.II.
..II.II.II.II.
..II.II.II.II.
..II.II.II.II.
.IIIIIIIIIIII.
IIIIIIIIIIIIII
IIIIIIIIIIIIII""")

ic('boo', None)  # filled below from the font


def _boo():
    m = fonts.text_mask('BOO!', fonts.S7, spacing=1, bold=True)
    out = np.full(m.shape, '.', dtype='<U1')
    out[m > 0] = 'I'
    return '\n'.join(''.join(r) for r in out)


A['boo'] = _boo()


def register_ascii(icon):
    for k, v in A.items():
        if v is None:
            continue
        icon(k, v, P.get(k))


# ---------------------------------------------------------------- special features
# Left-hand sprites; the right one is mirrored about the cube centre column (32).
# (x, y) = top-left of the outlined sprite in native 64x64 space.
EARS = {
    'ears_bunny': ("""
.ww......
wWWw.....
wWPWw....
wWPPWw...
.wWPPWw..
.wWPPWw..
..wWPPWw.
..wWPPWw.
...wWPPWw
...wWPPWw
....wWPWw
....wWWWw
.....www.""", {'W': '#ffffff', 'w': '#b8b8c4', 'P': '#ff9ac0'}, (17, 1)),
    'ears_dog': ("""
w.......
ww......
wWw.....
wWWw....
wPWWw...
wPPWWw..
wPPPWWw.
wwwwwwww""", None, (12, 2)),
    'ears_fox': ("""
K.......
KK......
KOK.....
KWOO....
OWWOO...
OWWWOO..
OWWWWOO.
OOOOOOOO""", {'O': '#ff8a2a', 'K': '#2a1408', 'W': '#fff4e0'}, (12, 1)),
    'ears_owl': ("""
n......
nn.....
nNn....
nNNn...
.nNNn..
.nNNNn.
..nNNNn""", {'N': '#9a724a', 'n': '#4a3018'}, (12, 4)),
}

HORN = ("""
T...........
TT..........
tTT.........
tTTT........
.tTTT.......
.tTTTT......
..tTTTTT....
..ttTTTTTT..
...ttTTTTTTT
....tttTTTTT
......tttttt""", {'T': '#f4ecd0', 't': '#a89870'})


def _mirror_x(x0, w):
    return 65 - x0 - w


def special_parts(name, die):
    parts = []
    outline = die['art']['outline']
    if name in EARS:
        art, pal, (lx, ly) = EARS[name]
        if name == 'ears_dog':
            pal = {'W': die['art']['top'], 'w': darken(die['art']['top'], 0.45),
                   'P': mix(die['art']['top'], '#ffffff', 0.6)}
        s = sprite(art, pal)
        s = outline_arr(pad(s, 1), outline)
        h, w = s.shape[:2]
        parts.append((s, lx, ly))
        parts.append((flip_h(s), _mirror_x(lx, w), ly))
        return parts
    if name == 'horns':
        art, pal = HORN
        s = sprite(art, pal)
        s = outline_arr(pad(s, 1), outline)
        h, w = s.shape[:2]
        lx, ly = 2, 2
        parts.append((s, lx, ly))
        parts.append((flip_h(s), _mirror_x(lx, w), ly))
        return parts
    if name == 'spoiler':
        from pix import Canvas
        cv = Canvas(64, 64)
        red, dred, hi, blk, grey = '#e8261c', '#8a120c', '#ff9a90', '#1b1b1f', '#5a5e6c'
        # struts first (behind the wing), standing on the top face
        for (sx, sy) in ((18, 13), (25, 9)):
            cv.rect(sx, sy, sx + 1, sy + 3, grey)
        # chunky wing parallel to the back-left edge, raised above the top face
        x0, y0, x1, y1 = 13, 11, 30, 1
        for i in range(0, x1 - x0 + 1):
            x = x0 + i
            y = int(round(y0 + (y1 - y0) * i / (x1 - x0)))
            cv.px(x, y, hi)
            cv.px(x, y + 1, red)
            cv.px(x, y + 2, red)
            cv.px(x, y + 3, dred)
        # end plates
        for (ex, ey) in ((x0, y0), (x1, y1)):
            cv.rect(ex, ey - 1, ex, ey + 4, dred)
        a = outline_arr(cv.a, outline)
        parts.append((a, 0, 0))
        return parts
    return parts
