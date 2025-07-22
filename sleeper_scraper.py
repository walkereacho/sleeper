import requests, json, csv, os, datetime

if not os.path.isfile("sleeper_players.json"):
    players_url = "https://api.sleeper.app/v1/players/nfl"
    players_req = requests.get(players_url)
    players_json = players_req.json()
    with open(f'sleeper_players.json', 'w', newline='\n') as players_json_file:
        players_json_file.write(json.dumps(players_json, indent=2))

season = 2025
league_id = 1180283972269297664
players_json = {}
with open(f'sleeper_players.json', 'r', newline='\n') as players_json_file:
    players_json = json.load(players_json_file)

rosters_url = f"https://api.sleeper.app/v1/league/{league_id}/rosters"
rosters_req = requests.get(rosters_url)
rosters_json = rosters_req.json()
owner_id_to_roster_id_dict = {}
for roster in rosters_json:
    owner_id = roster.get("owner_id")
    roster_id = roster.get("roster_id")
    owner_id_to_roster_id_dict[owner_id] = roster_id

users_url = f"https://api.sleeper.app/v1/league/{league_id}/users"
users_req = requests.get(users_url)
users_json = users_req.json()


# Manually figured out - 
username_to_name_dict = {
    'Need more Juscz': 'Mikey',
    'Dirty Kev and the Boyz': 'Kevin',
    'Munch & The Munchkins': 'Chris',
    'Inferno F.C.': 'Thomas',
    'Aging and Bloated': 'Dave',
    "The Hardly Know 'Ers": 'Walker',
    'Aaron’s Drug Adventures': 'Liam',
    'BENchwarmers': 'Ben F',
    'J E T S NONONO': 'Justin',
    'Juju and Jujujuju': 'Alex R',
    'Baker’s Mayflowers': 'Alex W',
    'CeeDee’s Nutz': 'Mayank',
    'Call of Duty: Tank': 'Ben L',
}

roster_id_to_owner_dict = {}

for user in users_json:
    owner_id = user.get("user_id")
    name = user.get("metadata",{}).get("team_name") or user.get("display_name")
    roster_id = owner_id_to_roster_id_dict.get(owner_id)
    roster_id_to_owner_dict[roster_id] = username_to_name_dict[name] if username_to_name_dict[name] else name
 


##################
# TRADE HISTORY #
##################

week = 1
trades = {}
for week in range(0, 25):
    url = f"https://api.sleeper.app/v1/league/{league_id}/transactions/{week}"
    r = requests.get(url)
    json_array = r.json()

    filtered_transactions = [
    t for t in json_array 
        if t.get("type") == "trade" and t.get("status") == "complete"
    ]
    filtered_transactions.sort(key=lambda x: int(x.get("status_updated", 0)), reverse=False)

    for transaction in filtered_transactions:
        if transaction.get("type") != "trade":
            continue
        if transaction.get("status") != "complete": 
            continue
        time = transaction.get("status_updated") / 1000
        status_updated = datetime.datetime.fromtimestamp(int(time))
        print()
        print(status_updated.strftime("%m/%d/%Y"))
        players_added = transaction.get("adds", dict()) # Player ID --> Roster ID that added
        if (players_added is None or players_added == "None"):
            players_added = dict()
        players_dropped = transaction.get("drops", dict()) # Player ID --> Roster ID that dropped
        if (players_dropped is None or players_dropped == "None"):
            players_dropped = dict()

        trade_info = {}
        # Convert traded players info
        for player in players_added:
            roster_that_added = players_added.get(player, -1)
            if roster_that_added == -1:
                print ("Error: No roster added")

            owner = roster_id_to_owner_dict.get(roster_that_added, "null")
            player_name = players_json.get(player, {}).get("full_name", player)
            # Add to trade_info
            if roster_that_added not in trade_info:
                trade_info[roster_that_added] = []

            trade_info[roster_that_added].append({
                "player_name": player_name,
                "draft_pick": None,
                "amount": None
            })

        draft_picks = transaction.get("draft_picks", [])
        for draft_pick in draft_picks:
            new_owner_id = draft_pick.get("owner_id")
            if trade_info.get(new_owner_id) is None:
                trade_info[new_owner_id] = []
            trade_info[new_owner_id].append({
                "player_name": None,
                "draft_pick": draft_pick,
                "amount": None
            })

        waiver_transactions = transaction.get("waiver_budget", [])
        for transaction in waiver_transactions:
            receiver_id = transaction.get("receiver")
            amount = transaction.get("amount", 0)
            if trade_info.get(receiver_id) is None:
                trade_info[receiver_id] = []
            trade_info[receiver_id].append({
                "player_name": None,
                "draft_pick": None,
                "amount": amount
            })
        first_team_id = list(trade_info.keys())[0]
        second_team_id = list(trade_info.keys())[1]

    ###########
        for i in range(0, max(len(trade_info[first_team_id]), len(trade_info[second_team_id]))):
            if (i == 0): 
                first_team_name = roster_id_to_owner_dict.get(first_team_id, "Unknown Team")
                print(f"{first_team_name}", end=", ")
            else: 
                print("", end=", ")
            if (i < len(trade_info[first_team_id])):
                if trade_info[first_team_id][i].get("player_name") is not None:
                    print(trade_info[first_team_id][i].get("player_name"), end=", ")
                elif trade_info[first_team_id][i].get("draft_pick") is not None:
                    draft_pick = trade_info[first_team_id][i].get("draft_pick")
                    pick_year = draft_pick.get("season", "Unknown Year")
                    pick_round = draft_pick.get("round", "Unknown Round")
                    original_owner_id = draft_pick.get("roster_id", "Unknown Owner")
                    original_owner = roster_id_to_owner_dict.get(original_owner_id, "Unknown Owner")
                    print(f"{pick_year} Round {pick_round} ({original_owner})", end=", ")
                elif trade_info[first_team_id][i].get("amount") is not None:
                    amount = trade_info[first_team_id][i].get("amount")
                    print(f"${amount}", end=", ")
            else: 
                print("", end=", ")

            if (i == 0):
                second_team_name = roster_id_to_owner_dict.get(second_team_id, "Unknown Team")
                print(second_team_name, end=", ")
            else: 
                print("", end=", ")
            
            if (i < len(trade_info[second_team_id])):
                if trade_info[second_team_id][i].get("player_name") is not None:
                    print(trade_info[second_team_id][i].get("player_name"), end=", ")
                elif trade_info[second_team_id][i].get("draft_pick") is not None:
                    draft_pick = trade_info[second_team_id][i].get("draft_pick")
                    pick_year = draft_pick.get("season", "Unknown Year")
                    pick_round = draft_pick.get("round", "Unknown Round")
                    original_owner_id = draft_pick.get("roster_id", "Unknown Owner")
                    original_owner = roster_id_to_owner_dict.get(original_owner_id, "Unknown Owner")
                    print(f"{pick_year} Round {pick_round} ({original_owner})", end=", ")
                elif trade_info[second_team_id][i].get("amount") is not None:
                    amount = trade_info[second_team_id][i].get("amount")
                    print(f"${amount}", end=", ")
            else: 
                print("", end=", ")
            print() # Two new lines after each row of trade info


###################
# MATCHUP HISTORY #
###################

# week = 1
# for week in range(1, 18):
#     url = f"https://api.sleeper.app/v1/league/{league_id}/matchups/{week}"
#     r = requests.get(url)
#     json = r.json()
#     matchups = {}
#     for roster in json:
#         matchup_id = roster.get("matchup_id")
#         matchup = matchups.get(matchup_id, [])

#         roster_id = roster.get("roster_id")
#         final_points = roster.get("points")
#         starter_ids = roster.get("starters", [])
#         starter_points = roster.get("starters_points", [])
#         starters = []
#         for i in range(len(starter_ids)):
#             id = starter_ids[i]
#             points = starter_points[i]
#             starters.append((id, points))
#         roster_dict = {}
#         roster_dict["name"] = roster_id_to_owner_dict.get(roster_id)
#         roster_dict["starters"] = starters
#         roster_dict["points"] = final_points
#         matchup.append(roster_dict)

#         matchups[matchup_id] = matchup

#     positions = ["QB", "RB", "RB", "RB", "WR", "WR", "WR", "TE", "WR/RB/TE", "K", "D/ST"]

#     with open(f'{season}/{season}_week_{week}.csv', 'w', newline='\n') as csvfile:
#         csvwriter = csv.writer(csvfile, delimiter=',',
#                                 quotechar='|', quoting=csv.QUOTE_MINIMAL)
#         for matchup in matchups:
#             game = matchups.get(matchup, [])
#             home_team = game[0]
#             away_team = game[1]
#             game_home_name = home_team.get("name")
#             game_home_score = home_team.get("points")
#             game_away_name = away_team.get("name")
#             game_away_score = away_team.get("points")
            
#             csvwriter.writerow(
#                 [game_home_name,game_home_score,"vs.",game_away_score,game_away_name]
#             )
            
#             game_home_players = home_team.get("starters")
#             game_away_players = away_team.get("starters")

#             for i in range(len(game_home_players)):
#                 home_player, home_score = game_home_players[i]
#                 away_player, away_score = game_away_players[i]
#                 home_player_name = players_json.get(home_player, {}).get("full_name", home_player)
#                 away_player_name = players_json.get(away_player, {}).get("full_name", away_player)
#                 csvwriter.writerow(
#                     [home_player_name, home_score, positions[i], away_score, away_player_name]
#                 )
#             csvwriter.writerow([])