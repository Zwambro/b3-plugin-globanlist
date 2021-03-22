# ![BigBrotherBot](http://i.imgur.com/7sljo4G.png) B3-plugin-globanlist
 B3 plugin for share ban list between clans by sending a warn on discord if a banned player joined another clan's server.

- !zwambro &lt;@playerid&gt; - to unban banned player from globanlist.

---------
### Requirements
- `requests` modules required
  - install with `pip install requests`
  - `Zwambro API token`, if you want to use this plugin on your servers, you need first to contact me to create an identification token for your clan (to make things more secure), contact me on discord `Zwambro#8854`.
---------
### Installation

1. Create a Discord webhook in your Discord channel.
2. Contact me to create API token for you
3. Paste the webhook on globanlist.xml in b3/extplugins/conf.
4. Paste the API Token that I sent you on globanlist.xml in b3/extplugins/conf.
3. Add plugin to b3.xml: 

`
<plugin name="globanlist" config="@b3/extplugins/conf/globanlist.xml"/>
`