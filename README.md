# clashapi

You can see api.py for full example.

```
token = """
YOUR TOKEN
""".replace("\n", "")

clan_id = "#CLANID".replace("#", "%23")

api = clashapi.EVEAPIConnection()

auth = api.auth(token=token)                            # provide your auth bearer token

result = auth.clans(name="string to search")            # requests /clans?name="string to search"
result = auth.clan(clan_id)()                           # requests /clans/{clanTag}
result = auth.clan(clan_id).members()                   # requests /clans/{clanTag}/members

result = auth.locations()                               # requests /locations/
result = auth.location("32000087")()                    # requests /locations/{locationId}
result = auth.location("32000087").rankings.players()   # requests /locations/{locationId}/ranking/{rankingId}

result = auth.leagues()                                 # requests /leagues

print(result)                                           # content is json
```
