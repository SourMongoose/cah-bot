changelog = \
"""**4/11/19 Update:**
- Added warning message when using `c!add` before starting a game

**3/6/19 Update:**
- `c!cancel` is now deprecated for `c!reset`
- Added admin mode

**2/11/19 Update:**
- Fixed bug where timer would go off prematurely

**1/5/19 Update:**
- Fixed bug with CardCast packs

**12/20/18 Update:**
- Bot now uses auto-sharding
- Added `c!donate`

**11/22/18 Update:**
- Added French as a language option
- Added `c!faq`

**11/4/18 Update:**
- Added warning when player tries to play card in private messages
- Bug fixes for blank cards

**10/23/18 Update:**
- Private messages will now show the current black card
- Added error message for when wrong number of cards are played

**10/13/18 Update:**
- Scoreboard will now show 'Czar' next to current czar
- Added `c!invite` and `c!vote`

**9/27/18 Update:**
- `c!contents` can now access CardCast packs
- Bot will no longer ping every player in the game when someone joins, but will ping everyone when the game starts
- Base pack is no longer automatically added after starting a new game
- Private messages now show server name

**9/24/18 Update:**
- Added CardCast support

**9/21/18 Update:**
- Fixed bug where `c!kick` would not function properly if players joined mid-game
- Server admins can now reset a game even when they are not playing

**9/17/18 Update:**
- Blank cards should now be completely functional

**9/11/18 Update:**
- `c!commands` now directly shows the list of commands

**9/3/18 Update:**
- Packs/timer/blanks/etc. will no longer be reset after each game
- List of current packs is now shown
- Max players increased to 20 (careful, a game with 10+ players could get cramped)
- A few other minor text fixes

**8/29/18 Update:**
- Added idle timer; edit with `c!timer`
- Adding packs with `c!add all` is less cluttered (and a LOT faster!)

**8/22/18 Update:**
- Added dividing lines for scoreboard

**8/18/18 Update:
- Scoreboard and other messages now use display name instead of nickname
- Scoreboard now shows which players have already played their card(s)

**8/17/18 Update:**
- Added German as a language option

**8/16/18 Update:**
- Added option for custom prefix with `c!prefix`

**8/15/18 Update:**
- Added `c!support` to bring up a link to the support server

**8/13/18 Update:**
- Added `c!kick` for those pesky AFKs!
- Fixed bug where cards played were not being shuffled

**8/10/18 Update:**
- Changed format of hand sent

**8/6/18 Update:**
- Added blank cards! Use `c!setblank` to add blank cards to your game
- Commas and spaces are now allowed when playing multiple cards

**8/3/18 Update:**
- Added error message when bot is unable to send a player their hand

**7/27/18 Update:**
- Added a whole bunch of third party config.packs!
- Made adding config.packs a bit faster
- Updated `c!config.packs` with number of cards in each pack
- Separated official CAH config.packs from third party config.packs

**7/18/18 Update:**
- Added Holiday config.packs, PAX config.packs, and more
- Added `c!config.packs` and `c!contents` commands
- Fixed bug where language would randomly switch to Portuguese

**7/16/18 Update:**
- Added Spanish as a language option
- Added the `c!commands` command

**7/14/18 Update:**
- Added even more config.packs!
- Fixed bug where game would freeze if czar left

**7/11/18 Update:**
- Added the `c!whatsnew` command
- Added a bunch more config.packs
"""

commands = \
"""**List of available commands:**

Global commands:
• c!help - Brings up a help message
• c!whatsnew - Show the changelog
• c!commands - Show a list of all commands
• c!support - Brings up a link to the support server
• c!invite - Brings up the bot's invite link
• c!vote - Brings up a link to the bot's vote page on discordbots.org
• c!prefix <letter> - Change command prefix to given letter
• c!donate - Brings up donation links

Pre-game commands:
• c!start - Start a game of Cards Against Humanity
• c!reset - Cancel a game of CAH (will not reset settings)
• c!add <pack(s)> - Add a pack (use "c!add all" to add all available packs)
• c!remove/c!rm <pack(s)> - Remove a pack (use 'base' for original pack)
• c!packs - Show a list of all available packs
• c!contents <pack> - Show all cards in a certain pack
• c!setwin <points> - Set number of points needed to win
• c!timer <seconds> - Set idle timer
• c!setblank <blanks> - Set number of blank cards
• c!join - Join a game of CAH
• c!leave - Leave a game of CAH

Ongoing game commands:
• c!play/c!p <card(s)> - Play the selected cards
• c!display - Re-display the current scoreboard/black card
• c!reset - Reset an ongoing game of CAH
• c!join - Join the current game
• c!leave - Leave the current game
• c!kick <player> - Vote to kick a player
"""
