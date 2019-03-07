import discord
import asyncio
import random
import time
import pickle

from cardcast import api

import config
import info
import tokens

class Shard:
    def __init__(self, client):
        self.client = client
        
        # attempt to load a save state, if any
        try:
            with open('state.txt', 'rb') as f:
                config.C = pickle.load(f)
        except:
            print('Error loading save state')
    
    async def deal(self, ch):
        """Deals cards to each player within a given channel."""
        
        for i in range(config.C[ch]['nPlayers']):
            await self.dealOne(ch, i)
        config.C[ch]['time'] = time.time() # reset timer
    
    async def dealOne(self, ch, i):
        """Deal cards to one player in a given channel."""
        
        config.C[ch]['played'][i] = False
        
        # don't deal cards to czar
        #if i == config.C[ch]['pov']:
        #    return
        
        nCards = 10 if config.nCards(ch) < 3 else 12
        while len(config.C[ch]['hands'][i]) < nCards:
            config.C[ch]['hands'][i].append(config.C[ch]['white'].pop())
        await self.sendHand(ch,i)
    
    async def start_(self, ch):
        """Begin a game."""
        
        config.C[ch]['time'] = 1e15 # prevent weird timer_check bugs
        config.C[ch]['started'] = True
        
        for _ in range(config.C[ch]['nPlayers']):
            config.C[ch]['hands'].append([])
            config.C[ch]['played'].append(False)
            config.C[ch]['score'].append(0)
            config.C[ch]['kick'].append('')
        
        # create deck
        await config.getCards(ch)
        
        # add blanks
        for _ in range(config.C[ch]['blanks']):
            config.C[ch]['white'].append('')
        
        # check that there are enough cards
        if not (config.C[ch]['white'] and config.C[ch]['black']):
            await ch.send('Error starting game. Make sure there are enough black and white cards, then try again.')
            await config.reset(ch)
            return
        
        await config.shuffle(ch)
        config.C[ch]['curr'] = await config.nextBlack(ch)
        await self.deal(ch)
        
        config.C[ch]['pov'] = 0
    
    async def pass_(self, ch):
        """Move on to the next round."""
        
        config.C[ch]['pov'] = (config.C[ch]['pov']+1) % config.C[ch]['nPlayers'] # next czar
        config.C[ch]['curr'] = await config.nextBlack(ch)
        config.C[ch]['mid'] = []
        config.C[ch]['msg'] = None
        
        await self.deal(ch)
        await self.displayMid(ch)
    
    async def addPack(self, ch, s):
        """Given a pack name, try to add that pack."""
        
        s = s.strip()
        
        success = total = added = 0
        
        # CardCast
        try:
            if s not in config.C[ch]['packs']:
                _, _ = api.get_deck_blacks_json(s), api.get_deck_whites_json(s)
                
                config.C[ch]['packs'].append(s)
                
                success += 1
                total += 1
            else:
                added += 1
                total += 1
        except:
            pass
        
        s = s.lower()
        
        # add all official packs
        if s == 'all':
            await self.addPack(ch, ''.join(x for x in config.packs))
            return
        
        # add all third party packs
        if s == '3rdparty' or s == 'thirdparty':
            await self.addPack(ch, ''.join(x for x in config.thirdparty))
            return
        
        # add the red, green, and blue expansions
        if s == 'rgb':
            await self.addPack(ch, 'redbluegreen')
            return
        
        for p in config.packs:
            if p == 'cats' and s.count('cats') == s.count('cats2'):
                continue
            
            if p in s:
                total += 1
                if p not in config.C[ch]['packs']:
                    config.C[ch]['packs'].append(p)
                    success += 1
                else:
                    added += 1
        for p in config.thirdparty:
            if p in s:
                total += 1
                if p not in config.C[ch]['packs']:
                    config.C[ch]['packs'].append(p)
                    success += 1
                else:
                    added += 1
        
        if total:
            msg = 'Successfully added ' + str(success) + ' out of ' + str(total) + (' packs' if total > 1 else ' pack')
            if added: msg += '\n' + str(added) + (' packs' if added > 1 else ' pack') + ' already added'
            await ch.send(msg)
            await self.edit_start_msg(ch)
    
    async def removePack(self, ch, s):
        """Given a pack name, try to remove that pack."""
        
        s = s.strip()
        
        # CardCast
        if s in config.C[ch]['packs'] and s not in config.packs and s not in config.thirdparty and s != 'base':
            config.C[ch]['packs'].remove(s)
            await ch.send(s + ' removed!')
            await self.edit_start_msg(ch)
            return
        
        s = s.lower()
        
        for p in config.packs:
            if p in s and p in config.C[ch]['packs']:
                config.C[ch]['packs'].remove(p)
                await ch.send(config.packs[p] + ' removed!')
        for p in config.thirdparty:
            if p in s and p in config.C[ch]['packs']:
                config.C[ch]['packs'].remove(p)
                await ch.send(config.thirdparty[p] + ' removed!')
        
        # remove red, green, and blue expansions
        if s == 'rgb':
            await self.removePack(ch, 'redgreenblue')
        
        # remove base pack
        if 'base' in s and 'base' in config.C[ch]['packs']:
            config.C[ch]['packs'].remove('base')
            await ch.send('Base Cards Against Humanity removed!')
        
        # remove all packs
        if len(config.C[ch]['packs']) == 0 or s == 'all':
            config.C[ch]['packs'] = ['base']
            await ch.send('No cards left. Reverting to base pack')
        
        await self.edit_start_msg(ch)
    
    async def play(self, ch, p, s):
        s = s.strip().replace(' ','').replace(',','').replace('<','').replace('>','')
        
        # check that player is in current game
        try:
            player = config.C[ch]['players'].index(p)
        except:
            return
        
        # ignore czar/players who have already played card(s)
        if config.C[ch]['played'][player] or player == config.C[ch]['pov']:
            return
        
        try:
            newMid = []
            for x in s:
                card = config.C[ch]['hands'][player]['abcdefghijkl'.index(x)]
                if card in newMid:
                    return
                # check for blank
                if card == '':
                    await p.send("You tried to send a blank card without filling it in first!\nMessage me what you'd like to put in the blank.")
                    return
                newMid.append(card)
    
            if len(newMid) == config.nCards(ch):
                config.C[ch]['mid'].append([newMid,player])
                for c in newMid:
                    #config.C[ch]['white'].append(c)
                    config.C[ch]['hands'][player].remove(c)
                config.C[ch]['played'][player] = True
                await ch.send(p.display_name + ' has played!')
            else:
                await p.send(f'This prompt requires {config.nCards(ch)} white card(s).')
                return
            
            # update kicks
            for k in range(len(config.C[ch]['kick'])):
                if config.C[ch]['kick'][k] == p.mention:
                    config.C[ch]['kick'][k] = ''
            
            # all players are done
            if config.done(ch):
                random.shuffle(config.C[ch]['mid'])
                config.C[ch]['time'] = time.time()
            
            await self.displayMid(ch)
        except:
            pass
    
    async def sendHand(self, ch, i):
        t = f'Your white cards in #{ch.name} ({ch.guild.name}):'
        msg = ''
        hasBlank = False
        for card in range(len(config.C[ch]['hands'][i])):
            s = config.C[ch]['hands'][i][card]
            if s == '':
                s = '<blank card>'
                hasBlank = True
            msg += '**' + 'ABCDEFGHIJKL'[card] + ')** ' + s + '\n'
        
        if config.C[ch]['pov'] == i:
            msg += '\n**You are the Czar this round; you do NOT need to play any cards.**'
        msg += '\nBlack card:\n' + config.C[ch]['curr']
        msg = msg.replace('_', '\_'*5)
        
        em = discord.Embed(title=t, description=msg, colour=0xBBBBBB)
        
        player = config.C[ch]['players'][i]
        if hasBlank:
            if player not in config.P:
                config.P[player] = [ch]
            elif ch not in config.P[player]:
                config.P[player].append(ch)
            em.set_footer(text='It looks like you have one or more blank cards.\nTo fill in the blank, simply message me your answer.')
        
        try:
            await player.send(embed=em)
        except:
            try:
                await ch.send('Unable to send hand to ' + player.mention + ', do they have private messaging enabled?')
            except:
                pass
    
    async def displayMid(self, ch):
        # don't display if not enough players
        if config.C[ch]['nPlayers'] < 2: return
        
        msg = '─'*20 + '\n'
        for i in range(config.C[ch]['nPlayers']):
            msg += config.C[ch]['players'][i].display_name + ' - ' + str(config.C[ch]['score'][i])
            if config.C[ch]['played'][i] and not config.done(ch): msg += ' **Played!**'
            elif config.C[ch]['pov'] == i: msg += ' **Czar**'
            msg += '\n'
        
        if config.C[ch]['win'] not in config.C[ch]['score']:
            msg += '\nCurrent Czar: ' + config.C[ch]['players'][config.C[ch]['pov']].mention + '\n\n'
            msg += 'Black card:\n' + config.C[ch]['curr'].replace('_','\_'*5) + '\n'
        
        if config.done(ch):
            msg += '\n'
            for m in range(len(config.C[ch]['mid'])):
                msg += '**' + 'ABCDEFGHIJKL'[m] + ')** '
                for card in config.C[ch]['mid'][m][0]:
                    msg += card + '\n'
        
        msg += '─'*20
        
        try:
            #em = discord.Embed(description=msg, colour=0xBBBBBB)
            if config.C[ch]['msg'] == None or config.done(ch):
                #config.C[ch]['msg'] = await ch.send(embed=em)
                config.C[ch]['msg'] = await ch.send(msg)
                config.C[ch]['time'] = time.time()
            else:
                #await config.C[ch]['msg'].edit(embed=em)
                await config.C[ch]['msg'].edit(content=msg)
        except Exception as e:
            print('Error in displayMid() at', time.asctime())
            print(e)
            
            c = config.pre[ch.id] if ch.id in config.pre else 'c'
            await ch.send('Encountered error while displaying - answer selection may not function normally. If the czar is unable to select, try using `'+c+'!display`.')
            return
        
        if config.done(ch):
            letters = ['\U0001F1E6','\U0001F1E7','\U0001F1E8','\U0001F1E9','\U0001F1EA',
                       '\U0001F1EB','\U0001F1EC','\U0001F1ED','\U0001F1EE','\U0001F1EF']
            error_occured = False
            for i in range(config.C[ch]['nPlayers']-1):
                try:
                    await config.C[ch]['msg'].add_reaction(letters[i])
                except:
                    if not error_occured:
                        error_occured = True
                        await ch.send('An error occurred while adding a letter; if the letter of your choice is not shown, please choose it by adding the letter manually.')
    
    async def displayWinners(self, ch):
        winner = config.C[ch]['score'].index(max(config.C[ch]['score']))
        msg = '\U0001F947' + ' ' + config.C[ch]['players'][winner].display_name + '\n'
        c = config.pre[ch.id] if ch.id in config.pre else 'c'
        msg += 'Use `'+c+'!start` to start another game!'
        await ch.send(msg)
    
    async def addPlayer(self, ch, p):
        if config.C[ch]['nPlayers'] < 20:
            config.C[ch]['players'].append(p)
            config.C[ch]['nPlayers'] = len(config.C[ch]['players'])
            config.C[ch]['played'].append(False)
            config.C[ch]['score'].append(0)
            config.C[ch]['hands'].append([])
            config.C[ch]['kick'].append('')
            
            await ch.send(p.display_name + ' has joined the game.')
            await self.dealOne(ch,config.C[ch]['nPlayers']-1)
            await self.displayMid(ch)
        else:
            await ch.send('Game is at max capacity!')
    
    async def removePlayer(self, ch, p, kick=False):
        if p in config.C[ch]['players']:
            i = config.C[ch]['players'].index(p)
            
            if config.C[ch]['played'][i]:
                await ch.send('You have already played your cards and may not leave.')
                return
            
            for s in ['players', 'played', 'hands', 'score', 'kick']:
                config.C[ch][s].pop(i)
            
            if i < config.C[ch]['pov']:
                config.C[ch]['pov'] -= 1
            
            config.C[ch]['nPlayers'] = len(config.C[ch]['players'])
            config.C[ch]['pov'] %= config.C[ch]['nPlayers']
            
            # update cards already in the middle
            for j in range(len(config.C[ch]['mid'])):
                if config.C[ch]['mid'][j][1] > i:
                    config.C[ch]['mid'][j][1] -= 1
            
            # all players are done
            if config.done(ch):
                random.shuffle(config.C[ch]['mid'])
            
            if not kick:
                await ch.send(p.display_name + ' has left the game.')
            await self.displayMid(ch)
        if config.C[ch]['nPlayers'] < 2: # number of players has been reduced to 1
            await config.reset(ch)
            await ch.send('Not enough players, game has been reset.')
    
    async def get_start_msg(self, ch):
        c = config.pre[ch.id] if ch.id in config.pre else 'c'
        
        s = ("Use `{0}!join` to join (and `{0}!leave` if you have to go)!\n"
            "Use `{0}!add <pack>` to add an expansion pack (`{0}!packs` to show all available packs).\n"
            "Current packs: "+', '.join(p for p in config.C[ch]['packs'])+'\n'
            "Use `{0}!setwin <#>` to change the number of points to win (current: "+str(config.C[ch]['win'])+')\n'
            "Use `{0}!timer <# sec>` to change the duration of the idle timer (current: "+str(config.C[ch]['timer'])+"), or use `c!timer 0` to disable it.\n"
            "Use `{0}!setblank <#>` to change the number of blank cards (max 30, current: "+str(config.C[ch]['blanks'])+')\n'
            "Use `{0}!language <lang>` to change the language (current: "+str(config.C[ch]['lang'])+')\n'
            "Once everyone has joined, type `{0}!start` again to begin.").format(c)
        
        return s
    
    async def edit_start_msg(self, ch):
        if not config.C[ch]['playerMenu']: return
        
        s = await self.get_start_msg(ch)
        if config.C[ch]['msg']: await config.C[ch]['msg'].edit(content=s)
    
    async def on_ready(self):
        await self.client.change_presence(game=discord.Game(name='c!help'))
        
        print('Ready')

    async def on_message(self, message):
        #if (time.time() / 3600) - last_update > 1:
        #    await self.client.change_presence(game=discord.Game(name='on '+'_'*4+' servers. ' + str(len(client.guilds))+'.'))
        #    config.last_update = time.time() / 3600
        
        msg = message.content.lower()
        ch = message.channel
        au = message.author
        
        c = config.pre[ch.id] if ch.id in config.pre else 'c'
        
        # ignore own messages
        if au.id == 429024440060215296:
            return
        
        # fill in blank cards
        if isinstance(ch, discord.abc.PrivateChannel):
            # check for c!p or c!play
            if msg.startswith(c+'!p'):
                await au.send('Please play your card(s) in the corresponding channel and not as a private message.')
                return
            
            # iterate through all users with blank cards
            for p in config.P:
                if p.id == au.id:
                    for c in config.P[p]:
                        if config.C[c]['started'] and au in config.C[c]['players']: # check that user is currently playing
                            i = config.C[c]['players'].index(au)
                            if '' in config.C[c]['hands'][i]: # check that player has a blank
                                j = config.C[c]['hands'][i].index('')
                                config.C[c]['hands'][i][j] = message.content.replace('*','\*').replace('_','\_').replace('~','\~').replace('`','\`')
                                await self.sendHand(c, i)
                                break
            return
        
        # ignore irrelevant messages
        if not msg.startswith(c+'!'):
            return
        
        if ch not in config.C:
            config.C[ch] = {}
            await config.initChannel(ch)
        
        # warning
        if msg.startswith(c+'!warning') and au.id == 252249185112293376:
            for x in config.C:
                if config.C[x]['started']:
                    await x.send(message.content[9:])
        # check number of ongoing games
        if msg == c+'!ongoing' and (au.id == 252249185112293376 or au.id == 413516816137322506):
            nC = 0
            for x in config.C:
                if config.C[x]['started']:
                    nC += 1
            await ch.send(str(nC))
        # save state
        if (msg == c+'!save' or msg == c+'!savestate') and au.id == 252249185112293376:
            self.save_state()
        # number of servers
        if msg == c+'!servers' and (au.id == 252249185112293376 or au.id == 413516816137322506):
            await ch.send(str(len(self.client.guilds)))
#         # eval
#         if message.content.startswith(c+'!eval') and au.id == 252249185112293376:
#             try:
#                 print(eval(message.content[6:].strip()))
#                 await ch.send(str(eval(message.content[6:].strip())))
#             except:
#                 pass
        
        # changelog
        if msg == c+'!whatsnew' or msg == c+'!update' or msg == c+'!updates':
            s = info.changelog
            await ch.send(s[:s.index('**9/27')])
        
        # commands list
        if msg == c+'!commands' or msg == c+'!command':
            await ch.send(info.commands)
            
        # support server
        if msg == c+'!support' or msg == c+'!server' or msg == c+'!supp':
            await ch.send('https://discord.gg/qGjRSYQ')
        
        # FAQ
        if msg == c+'!faq':
            await ch.send('https://goo.gl/p9j2ve')
        
        # invite link
        if msg == c+'!invite':
            await ch.send('Use this link to invite the bot to your own server:\n<https://discordapp.com/api/oauth2/authorize?client_id=429024440060215296&permissions=134294592&scope=bot>')
        
        # vote link
        if msg == c+'!vote':
            await ch.send('Use this link to vote for the bot on discordbots.org:\n<https://discordbots.org/bot/429024440060215296/vote>')
        
        # donation links
        if msg == c+'!donate':
            await ch.send('Help support the bot:\n<http://buymeacoffee.com/sourmongoose>\n<https://paypal.me/sourmongoose>')
        
        # custom prefix setting
        if len(msg) == 10 and msg[:9] == c+'!prefix ' and 'a' <= msg[9] <= 'z':
            await ch.send('Command prefix set to `' + msg[9] + '`!')
            config.pre[ch.id] = msg[9]
            with open('prefix.txt', 'a') as f:
                f.write(str(ch.id) + ' ' + msg[9] + '\n')
        
        if not config.C[ch]['started']:
            if config.C[ch]['admin']:
                # Disable pre-game commands for users without Manage Channel permissions
                if not au.permissions_in(ch).manage_channels:
                    return
            # admin mode
            if msg == c+'!admin':
                await ch.send('Admin mode ' + ('disabled.' if config.C[ch]['admin'] else 'enabled.'))
                config.C[ch]['admin'] = not config.C[ch]['admin']
            
            # language change
            for l in config.languages:
                if msg == c+'!language '+l.lower():
                    if config.C[ch]['lang'] != l:
                        config.C[ch]['lang'] = l
                        await ch.send('Language changed to ' + l + '.\n(Note: Only the base pack will be translated.)')
                        await self.edit_start_msg(ch)
            
            if msg == c+'!help':
                await ch.send((
                    "Use `{0}!start` to start a game of Cards Against Humanity, or `{0}!reset` to cancel an existing one.\n"
                    "Use `{0}!commands` to bring up a list of available commands.\n"
                    "For a list of frequently asked questions and general directions, use `{0}!faq`.").format(c))
            elif msg == c+'!language english':
                if config.C[ch]['lang'] != 'English':
                    config.C[ch]['lang'] = 'English'
                    await ch.send('Language changed to English.')
                    await self.edit_start_msg(ch)
            elif msg == c+'!start':
                if not config.C[ch]['playerMenu']:
                    config.C[ch]['playerMenu'] = True
                    config.C[ch]['players'].append(au)
                    s = await self.get_start_msg(ch)
                    config.C[ch]['msg'] = await ch.send(s)
                    output = str(len(config.C[ch]['players'])) + '/20 Players: '
                    output += ', '.join(usr.display_name for usr in config.C[ch]['players'])
                    await ch.send(output)
                elif 2 <= len(config.C[ch]['players']) <= 20:
                    config.C[ch]['playerMenu'] = False
                    config.C[ch]['nPlayers'] = len(config.C[ch]['players'])
                    await self.start_(ch)
                    
                    await ch.send('Game is starting!\n' + ' '.join(usr.mention for usr in config.C[ch]['players']))
                    
                    config.C[ch]['msg'] = None
                    await self.displayMid(ch)
            elif msg.startswith(c+'!setwin'):
                try:
                    n = int(msg[8:].strip())
                    if n > 0:
                        config.C[ch]['win'] = n
                        await ch.send(f'Number of points needed to win has been set to {n}.')
                        await self.edit_start_msg(ch)
                except:
                    pass
            elif msg.startswith(c+'!timer') or msg.startswith(c+'!settimer'):
                #await ch.send('Idle timer is currently disabled.')
                try:
                    n = int(msg[msg.index('timer')+5:].strip())
                    if n >= 15:
                        config.C[ch]['timer'] = n
                        await ch.send(f'Idle timer set to {n} seconds.')
                        await self.edit_start_msg(ch)
                    elif n == 0:
                        config.C[ch]['timer'] = n
                        await ch.send('Idle timer is now disabled.')
                        await self.edit_start_msg(ch)
                    else:
                        await ch.send('Please choose a minimum of 15 seconds.')
                except:
                    pass
            elif msg.startswith(c+'!blank') or msg.startswith(c+'!setblank'):
                #await ch.send('Blank cards are currently disabled.')
                try:
                    n = int(msg[msg.index('blank')+5:].strip())
                    if 0 <= n <= 30:
                        config.C[ch]['blanks'] = n
                        await ch.send(f'Number of blanks has been set to {n}.')
                        await self.edit_start_msg(ch)
                    elif n > 30:
                        await ch.send('Please choose a maximum of 30 cards.')
                except:
                    pass
            elif msg == c+'!packs':
                output = ("**List of available packs:**\n"
                    "(pack code followed by name of pack, then number of black and white cards)\n"
                    "----------\n")
                for p in config.packs:
                    cnt = await config.getCount(p)
                    output += f'**{p}** - {config.packs[p]} ({cnt[0]}/{cnt[1]})\n'
                await ch.send(output)
                output = '\nThird party packs:\n'
                for p in config.thirdparty:
                    cnt = await config.getCount(p)
                    output += f'**{p}** - {config.thirdparty[p]} ({cnt[0]}/{cnt[1]})\n'
                output += ("\nUse `{0}!add <code>` to add a pack, or use `{0}!add all` to add all available packs.\n"
                    "(Note: this will only add official CAH packs; use `{0}!add thirdparty` to add all third party packs.)\n"
                    "Use `{0}!contents <code>` to see what cards are in a specific pack.").format(c)
                await ch.send(output)
            elif msg.startswith(c+'!contents'):
                pk = message.content[10:].strip()
                
                # check for CardCast packs
                try:
                    b, w = api.get_deck_blacks_json(pk), api.get_deck_whites_json(pk)
                    deck_b = ['_'.join(c['text']) for c in b]
                    deck_w = [''.join(c['text']) for c in w]
                    
                    output = '**Cards in ' + api.get_deck_info_json(pk)['name'] + '** (code: ' + pk + ')**:**\n\n'
                    output += '**Black cards:** (' + str(len(deck_b)) + ')\n'
                    for c in deck_b:
                        output += '- ' + c + '\n'
                        if len(output) > 1500:
                            await ch.send(output.replace('_','\_'*3))
                            output = ''
                    output += '\n**White cards:** (' + str(len(deck_w)) + ')\n'
                    for c in deck_w:
                        output += '- ' + c + '\n'
                        if len(output) > 1500:
                            await ch.send(output.replace('_','\_'*3))
                            output = ''
                    await ch.send(output.replace('_','\_'*3))
                    
                    return
                except:
                    pass
                
                # check built-in packs
                pk = pk.lower()
                if pk in config.packs or pk in config.thirdparty:
                    output = ''
                    if pk in config.packs:
                        output = '**Cards in ' + config.packs[pk] + ':**\n\n'
                    elif pk in config.thirdparty:
                        output = '**Cards in ' + config.thirdparty[pk] + ':**\n\n'
                    
                    cnt = await config.getCount(pk)
                    cards = await config.getPack(pk)
                    output += f'**Black cards:** ({cnt[0]})\n'
                    for card in cards[0]:
                        output += '- ' + card[0] + '\n'
                        if len(output) > 1500:
                            await ch.send(output.replace('_','\_'*3))
                            output = ''
                    output += f'\n**White cards:** ({cnt[1]})\n'
                    for card in cards[1]:
                        output += '- ' + card[0] + '\n'
                        if len(output) > 1500:
                            await ch.send(output.replace('_','\_'*3))
                            output = ''
                    await ch.send(output.replace('_','\_'*3))
            elif msg == c+'!reset' or msg == c+'!cancel':
                if config.C[ch]['playerMenu']:
                    config.C[ch]['playerMenu'] = False
                    config.C[ch]['players'] = []
                    await ch.send('Game cancelled!')
            
            if config.C[ch]['playerMenu']:
                curr = len(config.C[ch]['players'])
                if msg == c+'!join':
                    if au not in config.C[ch]['players']:
                        config.C[ch]['players'].append(au)
                elif msg == c+'!leave':
                    if au in config.C[ch]['players']:
                        config.C[ch]['players'].remove(au)
                if curr != len(config.C[ch]['players']):
                    output = str(len(config.C[ch]['players'])) + '/20 Players: '
                    output += ', '.join(usr.display_name for usr in config.C[ch]['players'])
                    await ch.send(output)
                if len(msg) > 6 and msg[:6] == c+'!add ':
                    await self.addPack(ch, message.content[6:])
                if len(msg) > 9 and msg[:9] == c+'!remove ':
                    await self.removePack(ch, message.content[9:])
                elif len(msg) > 5 and msg[:5] == c+'!rm ':
                    await self.removePack(ch, message.content[5:])
        else:
            if msg == c+'!help':
                await ch.send((
                    "To play white cards, use `{0}!play` followed by the letters next to the cards you want to play. "
                    "For example, `{0}!play b` would play card B, and `{0}!play df` would play cards D and F.\n"
                    "If you're the czar, react with the letter of your choice once everyone has played their cards.\n"
                    "To reset an ongoing game, use `{0}!reset`.\n"
                    "To leave an ongoing game, use `{0}!leave` or `{0}!quit`.\n"
                    "To join an ongoing game, use `{0}!join`.\n"
                    "To kick an AFK player, use `{0}!kick <player>`.\n"
                    "To refresh the scoreboard, use `c!display`.\n\n"
                    "Use `{0}!commands` to bring up a list of available commands.\n"
                    "For a list of frequently asked questions and general directions, use `{0}!faq`.").format(c))
            
            # player commands
            if au in config.C[ch]['players']:
                if msg == c+'!display':
                    config.C[ch]['msg'] = None
                    await self.displayMid(ch)
                    return
                elif msg == c+'!leave' or msg == c+'!quit':
                    if not config.done(ch):
                        await self.removePlayer(ch, au)
                    else:
                        await ch.send('Please wait for the czar to pick a card before leaving.')
                elif msg.startswith(c+'!kick'):
                    mt = message.content[6:].strip() # player to kick
                    if mt == au.mention:
                        await ch.send('You cannot kick yourself. To leave the game, use `'+c+'!leave`.')
                    else:
                        for i in range(len(config.C[ch]['players'])):
                            p = config.C[ch]['players'][i]
                            if mt == p.mention:
                                if not config.C[ch]['played'][i]:
                                    config.C[ch]['kick'][config.C[ch]['players'].index(au)] = p.mention
                                    cnt = config.C[ch]['kick'].count(p.mention)
                                    await ch.send(au.mention + ' has voted to kick ' + p.mention + '. ' \
                                        + str(cnt) + '/' + str(config.C[ch]['nPlayers']-1) + ' votes needed')
                                    if cnt == config.C[ch]['nPlayers'] - 1:
                                        await ch.send(p.mention + ' has been kicked from the game.')
                                        await self.removePlayer(ch, p, kick=True)
                                else:
                                    await ch.send('This player has already played and cannot be kicked.')
                                
                                break
                elif msg == c+'!reset':
                    await config.reset(ch)
                    await ch.send('Game reset!')
                    return
            else:
                if msg == c+'!join':
                    if not config.done(ch):
                        await self.addPlayer(ch, au)
                    else:
                        await ch.send('Please wait for the czar to pick an answer before joining.')
            
            # playing cards
            if msg.startswith('c!play'):
                await self.play(ch,au,msg[6:])
                try:
                    await message.delete()
                except:
                    pass
            elif msg.startswith(c+'!p '):
                await self.play(ch,au,msg[4:])
                try:
                    await message.delete()
                except:
                    pass
            
            # admin override
            if au.id == 252249185112293376 or au.permissions_in(ch).manage_channels:
                if msg == c+'!display':
                    config.C[ch]['msg'] = None
                    await self.displayMid(ch)
                elif msg == c+'!reset':
                    await config.reset(ch)
                    await ch.send('Game reset!')
    
    async def on_reaction_add(self, reaction, user):
        ch = reaction.message.channel
        
        if (ch not in config.C) or (not config.C[ch]['started']):
            return
        
        czar = config.C[ch]['players'][config.C[ch]['pov']]
        letters = ['\U0001F1E6','\U0001F1E7','\U0001F1E8','\U0001F1E9','\U0001F1EA',
                   '\U0001F1EB','\U0001F1EC','\U0001F1ED','\U0001F1EE','\U0001F1EF'][:config.C[ch]['nPlayers']-1]
    
        if config.done(ch) and config.C[ch]['msg'] != None and reaction.message.content == config.C[ch]['msg'].content and czar == user:
            if reaction.emoji in letters:
                try:
                    p = config.C[ch]['mid'][letters.index(reaction.emoji)][1]
    
                    config.C[ch]['score'][p] += 1
                
                    msg = czar.display_name + ' selected ' + 'ABCDEFGHIJ'[letters.index(reaction.emoji)] + '.\n'
                    msg += config.C[ch]['players'][p].display_name + ' wins the round!'
                    await ch.send(msg)
                    
                    if config.C[ch]['win'] in config.C[ch]['score']:
                        await self.displayWinners(ch)
                        await config.reset(ch)
                    else:
                        await self.pass_(ch)
                except Exception as e:
                    print('Error with answer selection at', time.asctime())
                    print(e)
    
    async def timer_check(self):
        await self.client.wait_until_ready()
        
        while not self.client.is_closed():
            channels = list(config.C.keys())
            for ch in channels:
                if config.C[ch]['started'] and 'time' in config.C[ch]:
                    if config.C[ch]['timer'] != 0 and time.time() - config.C[ch]['time'] >= config.C[ch]['timer']:
                        # reset timer
                        config.C[ch]['time'] = time.time()
                        
                        if config.done(ch):
                            try:
                                # pick random letter
                                l = len(config.C[ch]['mid'])
                                if l == 0:
                                    return
                                else:
                                    letter = random.randint(0, l-1)
                                
                                p = config.C[ch]['mid'][letter][1]
                                config.C[ch]['score'][p] += 1
                            
                                msg = "**TIME'S UP!**\nThe bot randomly selected " + 'ABCDEFGHIJ'[letter] + '.\n'
                                msg += config.C[ch]['players'][p].display_name + ' wins the round!'
                                await ch.send(msg)
                                await self.pass_(ch)
                                
                                if config.C[ch]['win'] in config.C[ch]['score']:
                                    await self.displayWinners(ch)
                                    await config.reset(ch)
                            except Exception as e:
                                print('Error in timer_check at', time.asctime())
                                print(e)
                                # unknown channel/missing access
                                if 'unknown' in str(e).lower() or 'missing' in str(e).lower():
                                    config.C.pop(ch)
                        else:
                            try:
                                await ch.send("**TIME'S UP!**\nFor those who haven't played, cards will be automatically selected.")
                            
                                N = config.nCards(ch)
                                for p in range(len(config.C[ch]['players'])):
                                    if not config.C[ch]['played'][p] and config.C[ch]['pov'] != p:
                                        cards = ''
                                        for c in range(len(config.C[ch]['hands'][p])):
                                            if config.C[ch]['hands'][p][c]:
                                                cards += 'abcdefghijkl'[c]
                                                if len(cards) == N:
                                                    await self.play(ch, config.C[ch]['players'][p], cards)
                                                    break
                            except Exception as e:
                                print('Error in timer_check at', time.asctime())
                                print(e)
                                # unknown channel/missing access
                                if 'unknown' in str(e).lower() or 'missing' in str(e).lower():
                                    config.C.pop(ch)
            
            await asyncio.sleep(2)
    
    def save_state(self):
        with open('state.txt', 'wb') as f:
            pickle.dump(config.C, f, protocol=pickle.HIGHEST_PROTOCOL)
        print('Saved state')
    
    def run(self):
        self.client.loop.create_task(self.timer_check())
        
        # beta token
        #self.client.run(tokens.beta_id)
        # live token
        self.client.run(tokens.live_id)
