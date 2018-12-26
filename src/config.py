import random
import aiosqlite
from cardcast import api

languages = {
    "Portuguese": "pt",
    "Spanish": "sp",
    "German": "de",
    "French": "fr"
}

C = {} # channel dict
P = {} # list of players with blank cards
pre = {} # list of custom prefixes

# load custom prefixes
with open("prefix.txt", 'a') as f:
    pass

try:
    with open("prefix.txt", 'r') as f:
        l = f.readline().strip('\n')
        while len(l):
            ch, pfx = l.split(' ') # channel id and prefix letter
            pre[ch] = pfx
            l = f.readline().strip('\n')
except:
    pass

async def initChannel(ch):
    C[ch] = {}
    C[ch]["started"] = False
    C[ch]["playerMenu"] = False
    
    C[ch]["players"] = []
    C[ch]["played"] = []
    C[ch]["score"] = []
    C[ch]["kick"] = []
    
    C[ch]["win"] = 5
    C[ch]["timer"] = 60
    C[ch]["blanks"] = 0
    
    C[ch]["nPlayers"] = None
    
    C[ch]["packs"] = ["base"]
    
    C[ch]["lang"] = "English"
    
    C[ch]["pov"] = 0
    C[ch]["hands"] = []
    C[ch]["curr"] = ''
    C[ch]["mid"] = []
    C[ch]["msg"] = None

async def shuffle(ch):
    global C
    
    random.shuffle(C[ch]["black"])
    random.shuffle(C[ch]["white"])

async def getCards(ch):
    C[ch]["black"] = []
    C[ch]["white"] = []
    
    async with aiosqlite.connect('packs.db') as db:
        async def getPack(pack):
            async with db.execute('select card from cards where pack=? and black=1', (pack,)) as cursor:
                b = await cursor.fetchall()
            async with db.execute('select card from cards where pack=? and black=0', (pack,)) as cursor:
                w = await cursor.fetchall()
            return b, w
        
        for p in C[ch]["packs"]:
            if p == "base":
                cards = await getPack('base') if C[ch]['lang'] == 'English' else await getPack(languages[C[ch]['lang']])
                C[ch]["black"] += cards[0]
                C[ch]["white"] += cards[1]
            else:
                try:
                    cards = await getPack(p)
                    C[ch]["black"] += cards[0]
                    C[ch]["white"] += cards[1]
                except:
                    b, w = api.get_deck_blacks_json(p), api.get_deck_whites_json(p)
                    C[ch]["black"] += ['_'.join(c["text"]) for c in b]
                    C[ch]["white"] += [''.join(c["text"]) for c in w]

async def nextBlack(ch):
    global C
    
    card = C[ch]["black"].pop(0)
    if C[ch]["curr"] != '':
        C[ch]["black"].append(C[ch]["curr"])
    return card

async def reset(ch):
    global C
    
    C[ch]["started"] = False
    C[ch]["playerMenu"] = False
    
    C[ch]["players"] = []
    C[ch]["played"] = []
    C[ch]["score"] = []
    C[ch]["kick"] = []
    
    C[ch]["nPlayers"] = 0
    
    C[ch].pop("black", None)
    C[ch].pop("white", None)
    
    C[ch]["pov"] = 0
    C[ch]["hands"] = []
    C[ch]["curr"] = ''
    C[ch]["mid"] = []
    C[ch]["msg"] = None

def nCards(ch):
    if (C[ch]["curr"].count('_') == 2
        or "duo" in C[ch]["curr"]
        or "phrases" in C[ch]["curr"]
        or "(2)" in C[ch]["curr"]):
        return 2
    elif (C[ch]["curr"].count('_') == 3
        or "aiku" in C[ch]["curr"] 
        or "(3)" in C[ch]["curr"]):
        return 3
    
    return 1

def done(ch):
    return C[ch]["played"].count(True) == C[ch]["nPlayers"]-1
