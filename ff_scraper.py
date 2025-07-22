import requests, csv

league_id = 327013
season = 2021

for week in range(1, 18):
    url = f"https://www.fleaflicker.com/api/FetchLeagueScoreboard?sport=NFL&league_id={league_id}&season={season}&scoring_period={week}"
    r = requests.get(url)
    json = r.json()
    games = json.get("games", [])
    week_game_ids = []
    for game in games:
        game_id = game.get("id")
        if game_id is not None:
            week_game_ids.append(game.get("id"))

    with open(f'{season}/{season}_week_{week}.csv', 'w', newline='\n') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=',',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)


        for game_id in week_game_ids:
            game_url = f"https://www.fleaflicker.com/api/FetchLeagueBoxscore?sport=NFL&league_id={league_id}&fantasy_game_id={game_id}"
            game_req = requests.get(game_url)
            game = game_req.json()
            game_meta = game.get("game",{})
            game_home_name = game_meta.get("home", {}).get("name")
            game_home_score = game_meta.get("homeScore",{}).get("score", {}).get("formatted")

            game_away_name = game_meta.get("away", {}).get("name")
            game_away_score = game_meta.get("awayScore",{}).get("score", {}).get("formatted")

            csvwriter.writerow(
                [game_home_name,game_home_score,"vs.",game_away_score,game_away_name]
            )
            lineups = game.get("lineups", [])
            slots = []
            for lineup in lineups: 
                if lineup.get("group") != "START":
                    continue
                slots = lineup.get("slots", [])
            
            for slot in slots: 
                postion = slot.get("position", {}).get("label")
                away_player = slot.get("away", {}).get("proPlayer", {}).get("nameFull")
                away_score = slot.get("away", {}).get("viewingActualPoints", {}).get("formatted")
                home_player = slot.get("home", {}).get("proPlayer", {}).get("nameFull")
                home_score = slot.get("home", {}).get("viewingActualPoints", {}).get("formatted")
                csvwriter.writerow(
                    [home_player, home_score, postion, away_score, away_player]
                )
            csvwriter.writerow([])