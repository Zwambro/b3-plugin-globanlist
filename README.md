# ![BigBrotherBot](http://i.imgur.com/7sljo4G.png) B3-plugin-globanlist
 B3 plugin for share ban list between clans by sending a war on discord if a banned player joined your server

- !zwambro &lt;@playerid&gt; - Unban the banned player from globanlist

---------
### Requirements
- `requests` and `pytz` modules required
  - install with `pip install requests`
  - install with `pip install pytz`
---------
### Installation

1. Create a Discord webhook in your Discord channel.
2. Paste the webhook on discord.xml in b3/extplugins/conf.
3. Add plugin to b3.xml: 
`
<plugin name="globanlist" config="@b3/extplugins/conf/globanlist.xml"/>
`


