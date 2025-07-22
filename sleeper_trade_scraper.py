import requests, json, csv, os

league_id_22 = 827234151739564032
league_id_24 = 1048281174080061440
league_id = league_id_24


week = 1
trades = {}
for week in range(1, 18):
    print(f"Week {week} Trades")
    url = f"https://api.sleeper.app/v1/league/{league_id}/transactions/{week}"
    r = requests.get(url)
    json = r.json()
    for transaction in json:
        if transaction.get("type") != "trade":
            continue
        if transaction.get("status") != "complete": 
            continue
        
        # Draft picks
        draft_picks = transaction.get("draft_picks", [])
        for draft_pick in draft_picks:
            round = draft_pick.get("round")
            season = draft_pick.get("season")
            previous_owner_id = draft_pick.get("previous_owner_id")
            new_owner_id = draft_pick.get("owner_id")

        #players 
        players = transaction.get("adds", {}) # Player ID --> Roster ID
        for player_id, roster_id in players.items():
            name = all_players.get(player_id, {}).get("full_name", "Unknown Player")
            roster = all_rosters[roster_id]

            print("Name: ", name)
            print("Roster: ", roster)
        

    print("\n")