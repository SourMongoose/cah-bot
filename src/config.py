import random
import aiosqlite
from cardcast import api

packs = {
    "red": "Red expansion pack",
    "blue": "Blue expansion pack",
    "green": "Green expansion pack",
    "90": "90's Nostalgia Pack",
    "america": "CAH Saves America Pack",
    "box": "Box Expansion",
    "cats": "CATS Musical Pack",
    "college": "College Pack",
    "dad": "Dad Pack",
    "desert": "Desert Bus For Hope Pack",
    "fantasy": "Fantasy Pack",
    "fascism": "Fascism Pack",
    "food": "Food Pack",
    "hanukkah": "Hanukkah Pack",
    "hidden": "Hidden Compartment Pack",
    "holiday12": "2012 Holiday Pack",
    "holiday13": "2013 Holiday Pack",
    "holiday14": "2014 Holiday Pack",
    "house": "House of Cards Pack",
    "jew": "Jew Pack",
    "masseffect": "Mass Effect Pack",
    "paxeast13": "Pax East 2013 Pack",
    "paxeast14": "Pax East 2014 Pack",
    "paxprime13": "Pax Prime 2013 Pack",
    "paxprime14": "Pax Prime 2014 Pack",
    "period": "Period Pack",
    "pride": "Pride Pack",
    "procedure": "Procedurally-Generated Cards",
    "reject": "Reject Pack",
    "reject2": "Reject Pack 2",
    "retail": "Retail Mini Pack",
    "posttrump": "Post-Trump Pack",
    "product": "Retail Product Pack",
    "science": "Science Pack",
    "scifi": "Sci-Fi Pack",
    "seasons": "Season's Greetings Pack",
    "tabletop": "Tabletop Pack",
    "theatre": "Theatre Pack",
    "votehillary": "Vote For Hillary Pack",
    "votetrump": "Vote For Trump Pack",
    "weed": "Weed Pack",
    "www": "World Wide Web Pack"
}

thirdparty = {
    "2016": "2016 Election Game",
    "babies": "Babies vs. Parents",
    "cakes": "Cakes Athrist Hilarity",
    "carbs": "Carbs of the Huge Manatee",
    "carps": "Carps & Angsty Manatee",
    "cats2": "Cats Abiding Horribly",
    "charlie": "Charlie Foxtrot",
    "clones": "Clones Attack Hilarity",
    "cocks": "Cocks Abreast Hostility",
    "cows": "Cows Grilling Hamburgers",
    "crabs": "Crabs Adjust Humidity",
    "crows": "Crows Adopt Vulgarity",
    "guards": "Guards Against Insanity",
    "hombre": "Bad Hombres Against Fake News",
    "punish": "Cards and Punishment"
}

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
    
    C[ch]["admin"] = False

async def shuffle(ch):
    global C
    
    random.shuffle(C[ch]["black"])
    random.shuffle(C[ch]["white"])

async def getPack(pack):
    async with aiosqlite.connect('packs.db') as db:
        async with db.execute('select card from cards where pack=? and black=1', (pack,)) as cursor:
            b = await cursor.fetchall()
        async with db.execute('select card from cards where pack=? and black=0', (pack,)) as cursor:
            w = await cursor.fetchall()
        return b, w

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
                C[ch]["black"] += [x[0] for x in cards[0]]
                C[ch]["white"] += [x[0] for x in cards[1]]
            elif p in packs or p in thirdparty:
                cards = await getPack(p)
                C[ch]["black"] += [x[0] for x in cards[0]]
                C[ch]["white"] += [x[0] for x in cards[1]]
            else:
                b, w = api.get_deck_blacks_json(p), api.get_deck_whites_json(p)
                C[ch]["black"] += ['_'.join(c["text"]) for c in b]
                C[ch]["white"] += [''.join(c["text"]) for c in w]

async def getCount(pack):
    async with aiosqlite.connect('packs.db') as db:
        async with db.execute('select black, white from pack_count where pack=?', (pack,)) as cursor:
            return await cursor.fetchone()

async def nextBlack(ch):
    global C
    
    # make sure there are cards left
    if not C[ch]['black']:
        await getCards(ch)
    
    card = C[ch]["black"].pop()
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
        or "two cards" in C[ch]["curr"]
        or "(2)" in C[ch]["curr"]):
        return 2
    elif (C[ch]["curr"].count('_') == 3
        or "aiku" in C[ch]["curr"] 
        or "(3)" in C[ch]["curr"]):
        return 3
    
    return 1

def done(ch):
    return C[ch]["played"].count(True) == C[ch]["nPlayers"]-1
