#!/usr/bin/python3
#-----------------------------------------------------------------------------
# clashapi - Clash of Clan API access
#
# Copyright (c)2016 Julien "Sablier" Christophe <sablier@zendikar.fr>
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE
#
#-----------------------------------------------------------------------------

# Based on eveapi - EVE Online API access (https://github.com/ntt/eveapi)
# Copyright (c)2007-2014 Jamie "Entity" van den Berge <jamie@hlekkir.com>

# for ssl error : http://stackoverflow.com/questions/31649390/python-requests-ssl-handshake-failure

import clashapi
from cachehandler import CacheHandler

token = """

""".replace("\n", "")

scheme = "https"
server = "api.clashofclans.com/v1"
base_url = scheme+"://"+server

clan_id = "#9Y00CGGV".replace("#", "%23")

clashapi.set_user_agent("clashapi.py/0.9")

api = clashapi.EVEAPIConnection(url=base_url,cacheHandler=CacheHandler())

auth = api.auth(token=token)

# result = auth.clans(name="le Nakano")
# result = auth.clan(clan_id)()
# result = auth.clan(clan_id).members()

# result = auth.locations()
# result = auth.location("32000087")()
# result = auth.location("32000087").rankings.players()

result = auth.leagues()

print(result)
