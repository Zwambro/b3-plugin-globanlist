#
# ################################################################### #
#                                                                     #
#  Globanlist Plugin for BigBrotherBot(B3) (www.bigbrotherbot.com)    #
#  Copyright (c) 2020 Zwambro                                         #
#                                                                     #
#  This program is free software; you can redistribute it and/or      #
#  modify it under the terms of the GNU General Public License        #
#  as published by the Free Software Foundation; either version 2     #
#  of the License, or (at your option) any later version.             #
#                                                                     #
#  This program is distributed in the hope that it will be useful,    #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of     #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the       #
#  GNU General Public License for more details.                       #
#                                                                     #
#  You should have received a copy of the GNU General Public License  #
#  along with this program; if not, write to the Free Software        #
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA      #
#  02110-1301, USA.                                                   #
#                                                                     #
# ################################################################### #


__version__ = '1.0'
__author__ = 'Zwambro'

import b3
import b3.events
import b3.plugin
import uuid
import requests
import json
import datetime
import time
import re

from pytz import timezone
from b3 import functions
from b3 import clients
from collections import defaultdict

class DiscordEmbed:
    def __init__(self, url, **kwargs):
        self.url = url
        self.color = kwargs.get('color')
        self.gamename = kwargs.get('author')
        self.gamename_icon = kwargs.get('author_icon')
        self.title = kwargs.get('title')
        self.desc = kwargs.get('desc')
        self.mapview = kwargs.get('thumbnail')
        self.fields = kwargs.get('fields', [])
        self.footnote = kwargs.get('footer')

    def set_gamename(self, **kwargs):
        self.gamename = kwargs.get('name')
        self.gamename_icon = kwargs.get('icon')

    def set_title(self, title):
        self.title = title

    def set_desc(self, desc):
        self.desc = desc

    def set_mapview(self, url):
        self.mapview = url

    def textbox(self,**kwargs):
        name = kwargs.get('name')
        value = kwargs.get('value')
        inline = kwargs.get('inline')
        field = {'name' : name, 'value' : value, 'inline' : inline}
        self.fields.append(field)

    def set_footnote(self,**kwargs):
        self.footnote = kwargs.get('text')
        self.ts = str(datetime.datetime.utcfromtimestamp(time.time()))

    @property
    def push(self, *arg):
        data = {}
        data["embeds"] = []
        embed = defaultdict(dict)

        if self.gamename: embed["author"]["name"] = self.gamename
        if self.gamename_icon: embed["author"]["icon_url"] = self.gamename_icon
        if self.color: embed["color"] = self.color
        if self.title: embed["title"] = self.title
        if self.desc: embed["description"] = self.desc
        if self.mapview: embed["thumbnail"]['url'] = self.mapview
        if self.footnote: embed["footer"]['text'] = self.footnote
        if self.ts: embed["timestamp"] = self.ts

        if self.fields:
            embed["fields"] = []
            for field in self.fields:
                f = {}
                f["name"] = field['name']
                f["value"] = field['value']
                f["inline"] = field['inline']
                embed["fields"].append(f)

        data["embeds"].append(dict(embed))
        empty = all(not d for d in data["embeds"])
        if empty:
            data['embeds'] = []
        return json.dumps(data)

    def post(self):
        headers = {'Content-Type': 'application/json'}
        result = requests.post(self.url, data=self.push, headers=headers)


class GlobanlistPlugin(b3.plugin.Plugin):
    _bannedPlayer = []
    _adminPlugin = None

    def onStartup(self):

        self._adminPlugin = self.console.getPlugin('admin')

        if not self._adminPlugin:
            self.error('Could not find admin plugin')
            return

        self._adminPlugin.registerCommand(self, 'zwambro', 100, self.cmd_zwambro, 'zw')

        self.registerEvent(b3.events.EVT_CLIENT_AUTH, self.onConnect)
        self.registerEvent(b3.events.EVT_CLIENT_BAN, self.onBan)
        self.registerEvent(b3.events.EVT_CLIENT_DISCONNECT, self.onDisc)

    def onLoadConfig(self):
        self.url = str(self.config.get('settings', 'webhook'))
        return

    def stripColors(self, s):
        return re.sub('\^[0-9]{1}', '', s)

    def onConnect(self, event):

        currentClients = self.console.clients.getList()
        adminList = self._adminPlugin.getAdmins()

        c = self.console.game

        server = ''
        if c.sv_hostname:
            server = c.sv_hostname

        cid = str(event.client.id)
        player = event.client.name
        guid = str(event.client.guid)
        ip = str(event.client.ip)

        try:
            r = requests.get('https://globanlist.zwambro.pw/checkguid.php?guid=%s' %(guid), timeout=2)
            r2 = requests.get('https://globanlist.zwambro.pw/checkip.php?ip=%s' %(ip), timeout=2)
            if r.status_code == 200:
                result = r.json()
                if result["banned_guid"] == True:
                    self.debug('this player has banned guid on globanlist')
                    hostname = result['hostname'].title()
                    reason = result['reason'].title()
                    time.sleep(5)
                    if event.client not in currentClients:
                        self.debug('Player not on server, maybe have been kicked or banned by b3')
                        return             
                    elif event.client in currentClients:
                        self.debug('Player still on server')
                        #inform online admins
                        for admin in adminList:
                            admin.message('^1A suspicious player has joined server:^7 "%s", ^1check him please^7'% (player))
                        if player not in self._bannedPlayer:
                            self._bannedPlayer.append(player)                                     
                        embed = DiscordEmbed(self.url, color=1)
                        embed.set_title('Global Ban') 
                        embed.set_desc('A suspicious player has joined %s' %(self.stripColors(server)))
                        embed.textbox(name='Name', value=player + ' (@' + cid + ')', inline=True)
                        embed.textbox(name='Banned on',value=hostname,inline=True)
                        embed.textbox(name='Reason of Ban',value=reason,inline=False)
                        embed.set_footnote()
                        embed.post()
                        self.debug('Globanlist message sent to Discord.')
                        return
                    return
                return
            elif r2.status_code == 200:
                result2 = r2.json()
                if result2["banned_ip"] == True:
                    hostname2 = result2['hostname'].title()
                    reason2 = result2['reason'].title()
                    self.debug('this player has banned ip on globanlist')
                    time.sleep(5)
                    if event.client not in currentClients:
                        self.debug('Player not on server, maybe has been kicked or banned by b3')
                        return             
                    elif event.client in currentClients:
                        self.debug('Player still on server')
                        #inform online admins
                        for admin in adminList:
                            admin.message('^1A suspicious player has joined server:^7 "%s", ^1check him please^7'% (player))
                        if player not in self._bannedPlayer:
                            self._bannedPlayer.append(player)                                           
                        embed = DiscordEmbed(self.url, color=1)                    
                        embed.set_title('Global Ban')                        
                        embed.set_desc('A suspicious player has joined %s' %(self.stripColors(server)))
                        embed.textbox(name='Name', value=player + ' (@' + cid + ')', inline=True)
                        embed.textbox(name='Banned on',value=hostname2, inline=True)
                        embed.textbox(name='Reason of Ban', value=reason2, inline=False)
                        embed.set_footnote()
                        embed.post()
                        self.debug('Globanlist message sent to Discord.')
                        return
                    return
                return
        except ValueError, e:
            self.debug('error: ' + e)
            raise

    def onBan(self, event):

        admin = event.data["admin"]
        reason = event.data['reason']
        
        serverid = str(event.client.id)
        guid = str(event.client.guid)
        player = event.client.name
        ip = str(event.client.ip)

        c = self.console.game
        hostname = ''
        gamename = ''
        
        if c.sv_hostname:
            hostname = c.sv_hostname
        if c.gameName:
            if c.gameName == "cod8":
                gamename = 'TeknoMW3'
            if c.gameName == "cod6":
                gamename = 'Iw4x'
            if c.gameName == "cod4":
                gamename = 'Cod4x'
            if c.gameName == "t6":
                gamename = 'PLutoT6'
            if c.gameName == "iw5":
                gamename = 'PLutoIW5'

        spr = '%s:%s' %(guid, ip)
        token = str(uuid.uuid5(uuid.NAMESPACE_DNS, spr))

        fmt2 = "%d/%m/%Y %H:%M:%S"
        now_utc = datetime.datetime.now(timezone('UTC'))
        created = now_utc.strftime(fmt2)

        if admin == None:
            admin_name = "B3"
        else:
            admin_name = admin.name
        
        info = {
            'token': token,
            'game': gamename,
            'hostname': self.stripColors(hostname),
            'admin': self.stripColors(admin_name),
            'player': player.replace('|', ''),
            'guid': guid,
            'ip': ip,
            'reason': self.stripColors(reason.replace(',', '')),
            'duration': 'permanent',
            'serverid': '@' + serverid,
            'created': created
        }

        try:
            headers = {'Content-type': 'application/json'}
            r = requests.post('https://globanlist.zwambro.pw/addban.php', data=json.dumps(info), headers=headers)
            if r.status_code == 201:
                self.debug('Ban added perfeclty')
                return
            if player in self._bannedPlayer:
                embed = DiscordEmbed(self.url, color=1)
                embed.set_mapview('https://www.iconsdb.com/icons/download/green/checkmark-16.png') 
                embed.set_desc("%s has been Banned" % (player))
                embed.set_footnote()
                embed.post()
            self._bannedPlayer.remove(player)
        except ValueError, e:
            self.debug('error: ' + e)
            raise
            
    def onDisc(self, event):
        
        player = event.client.name
        
        if player in self._bannedPlayer:
            embed = DiscordEmbed(self.url, color=1)
            embed.set_desc("%s has left the server" % (player))
            embed.set_footnote()
            embed.post()
            self._bannedPlayer.remove(player)
            
    def cmd_zwambro(self, data, client, cmd=None):

        m = self._adminPlugin.parseUserCmd(data)
        if not m:
            client.message('^7Invalid parameters, !zwambro @id or !zw @id')
            return False

        cid = str(m[0])
        sclient = self._adminPlugin.findClientPrompt(cid, client)

        if sclient:
            guid = str(sclient.guid)
            ip = str(sclient.ip)
            
            info = {'guid': guid}
            info1 = {'ip': ip}

            try:
                headers = {'Content-type': 'application/json'}
                r = requests.post('https://globanlist.zwambro.pw/deleteguid.php', data=json.dumps(info), headers=headers)
                r1 = requests.post('https://globanlist.zwambro.pw/deleteip.php', data=json.dumps(info1), headers=headers)
                if r.status_code == 200 or r1.status_code == 200:
                    self.debug('Ban deleted completly')
                    cmd.sayLoudOrPM(client, 'Player successfully unbanned from globanlist')
                    return
            except ValueError, e:
                self.debug('error: ' + e)
                raise
        return True
