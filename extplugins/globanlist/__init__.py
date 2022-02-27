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
#  15.05.2020 - v1.0 - Zwambro
#  - first release
#
#  27.02.2021 - v1.1 - Zwambro
#  - update ban/check/unban urls
#  - add an internal db token
#
#  27.02.2022 - v1.2 - Zwambro
#  - add Ban Credibility
#  - clean discord embed syntax
#

__version__ = '1.2'
__author__ = 'Zwambro'

import b3
import b3.events
import b3.plugin
import requests
import json
import datetime
import time
import re

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
        self.apiKey = str(self.config.get('settings', 'api'))

    def stripColors(self, s):
        return re.sub('\^[0-9]{1}', '', s)

    def onConnect(self, event):

        currentClients = self.console.clients.getList()
        adminList = self._adminPlugin.getAdmins()

        c = self.console.game

        hostname = ''
        if c.sv_hostname:
            hostname = c.sv_hostname

        cid = str(event.client.id)
        player = event.client.name
        guid = str(event.client.guid)
        ip = str(event.client.ip)

        try:
            r = requests.get('https://zwambro.pw/globanlist/checktheban?guid=%s&ip=%s' %(guid, ip), headers={'Authorization': 'Token ' + self.apiKey + ''}, timeout=2)
            if r.status_code == 200:
                result = r.json()
                if result["banned"] == True:
                    self.debug("Found entry in globanlist")

                    time.sleep(5)

                    if event.client in currentClients:
                        self.debug('Player still on server')

                        #inform online admins
                        for admin in adminList:
                            admin.message('%s ^1is a suspicious player, check him'% (player))

                        embed = DiscordEmbed(self.url, color=1)
                        embed.set_title('Global Ban') 
                        embed.set_desc('A suspicious player has joined %s' %(self.stripColors(hostname)))
                        embed.textbox(name='Name', value=player, inline=True)
                        embed.textbox(name='PlayerID', value=' (@' + cid + ')', inline=True)
                        embed.textbox(name='Ban Credibility', value=result["banCredibility"], inline=False)
                        embed.set_footnote()
                        embed.post()
                        self.debug('Globanlist message sent to Discord')
                        return
                    else:
                        self.debug('Player not on server, maybe have been kicked or banned by b3')
                    return
                else:
                    self.debug('No ban found on globanlist for this player')

        except Exception as e:
            self.debug('error: ' + str(e))

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

        if admin == None:
            admin_name = "B3"
        else:
            admin_name = admin.name

        info = {
            'game': gamename,
            'server': self.stripColors(hostname),
            'adminname': self.stripColors(admin_name),
            'hackername': player.replace('|', ''),
            'guid': guid,
            'ip': ip,
            'reason': self.stripColors(reason.replace(',', '')),
            'bantype': 'Permban',
            'gameid': '@' + serverid,
        }
        try:
            headers = {'Content-type': 'application/json', 'Authorization': 'Token ' + self.apiKey + ''}
            r = requests.post('https://zwambro.pw/globanlist/addban', data=json.dumps(info), headers=headers)
            if r.status_code == 201:
                self.debug('Ban added perfectly')
        except Exception as e:
            self.debug('error: ' + str(e))

    def cmd_zwambro(self, data, client, cmd=None):

        m = self._adminPlugin.parseUserCmd(data)
        if not m:
            client.message('^7Invalid parameters, !zwambro @id')
            return False

        cid = str(m[0])
        sclient = self._adminPlugin.findClientPrompt(cid, client)
        if sclient:
            guid = str(sclient.guid)
            ip = str(sclient.ip)

            info = {'guid': guid, 'ip': ip}

            try:
                headers = {'Content-type': 'application/json', 'Authorization': 'Token ' + self.apiKey + ''}
                r = requests.post('https://zwambro.pw/globanlist/unban', data=json.dumps(info), headers=headers)
                if r.status_code == 200:
                    result = r.json()
                    if result["active_ban"] == True and result["unbanned"] == True:
                        self.debug('Ban deleted completly')
                        cmd.sayLoudOrPM(client, 'Player successfully unbanned from globanlist')
                        return
                    else:
                        client.message('No ban exists')
            except Exception as e:
                self.debug('error: ' + str(e))
