import requests
# import os
# import json
# import csv

# players_path = "sleeper/players.json"
# adp_path = "sleeper/adp.csv"
# if not os.path.exists(players_path):
#     request = requests.get("https://api.sleeper.app/v1/players/nfl")
#     data = json.loads(request.text)
#     players = json.dumps(data, indent=2)
#     with open(players_path, "w") as outfile:
#         outfile.write(players)

# players_dict = {}
# with open(players_path, "r") as player_file:
#     players_dict = json.loads(player_file.read())

# for player_id, player in players_dict.items():
#     firstname = player.get("first_name", "")
#     lastname = player.get("last_name", "")
#     name = f"{firstname} {lastname}"
#     players_dict[player_id] = player

league_id = 827234151739564032 # 864406845564039168

users_data = requests.get(f"https://api.sleeper.app/v1/league/{str(league_id)}/users")
roster_data = requests.get(f"https://api.sleeper.app/v1/league/{str(league_id)}/rosters")

users = users_data.json()
user_id_to_username = {}
for user in users:
    user_id_to_username[user.get("user_id")] = user.get("display_name")
print(user_id_to_username)
user_id_to_division = {
    '827235750625013760': 'South',
    '828329553251401728': 'South',
    '829434461149073408': 'South',
    '830492808384212992': 'South',
    '685924233787813888': 'North',
    '827227431084617728': 'North',
    '827265646562738176': 'North',
    '828329748768878592': 'North',
    '827227350528831488': 'RTP',
    '459368824110575616': 'RTP',
    '829250312975015936': 'RTP',
    '828712890029686784': 'RTP',
    # '467946841384677376':'Monday Night',
    # '685924233787813888':'Creature Comforts',
    # '734980057679978496':'Sweetwater',
    # '827227350528831488':'Monday Night',
    # '827265646562738176':'Monday Night',
    # '829250312975015936':'Creature Comforts',
    # '829434461149073408':'Monday Night',
    # '846926731855122432':'Creature Comforts',
    # '864410047093010432':'Sweetwater',
    # '864977226238664704':'Sweetwater',
    # '867533512176181248':'Creature Comforts',
    # '867920814329208832':'Sweetwater',
}

class Roster:
    name: str
    win_percentage: float
    points_for: float
    division: str

    def __init__(self, owner_id: int, wins: int, losses: int, points_for: float):
        self.points_for = points_for
        self.win_percentage = wins / (wins + losses)
        self.name = user_id_to_username.get(owner_id)
        self.division = user_id_to_division.get(owner_id)

    def __repr__(self):
        return f"{self.name} | {self.division} | {self.win_percentage} | {self.points_for}"

rosters = roster_data.json()
rosterObjects = []
for roster in rosters:
    settings = roster.get('settings', {})
    pf = settings.get('fpts', 0) + (settings.get('fpts_decimal', 0) / 100.0)
    rosterObjects.append(Roster(roster.get('owner_id'), settings.get('wins'), settings.get('losses'), pf))

byWins = sorted(rosterObjects, key=lambda roster: [roster.win_percentage, roster.points_for], reverse=True)
byPF = sorted(rosterObjects, key=lambda roster: [roster.points_for, roster.win_percentage], reverse=True)

division_winners_dict = {}
for roster in byWins:
    division = roster.division
    if (division_winners_dict.get(division, None) == None):
        division_winners_dict[division] = roster

division_winners = sorted(list(division_winners_dict.values()), key=lambda roster: [roster.win_percentage, roster.points_for], reverse=True)
standings = division_winners
for roster in byWins:
    if len(standings) > 4:
        break
    if roster not in standings:
        standings.append(roster)

for roster in byPF:
    if roster not in standings:
        standings.append(roster)

for roster in standings:
    print(roster)
