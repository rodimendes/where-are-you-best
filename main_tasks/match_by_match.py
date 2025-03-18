from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.core.utils import ChromeType
from selenium.webdriver.common.by import By
import time
import datetime as dt
import os
import requests
from dotenv import load_dotenv
import pandas as pd
import pickle
import mysql.connector

load_dotenv()
api_key = os.environ.get("OPENWEATHER_KEY")

def get_source_code(url):
    """
    Gets the source code and saves it for further verifications.
    The function returns the path to 'html' file and the player name.
    """
    try:
        # Firefox web browser
        print("\033[44m\033[37mFirefox Attempt\033[0m")
        firefox_options = Options()
        firefox_options.add_argument("-headless")
        driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=firefox_options)
    except:
        print("\033[41m\033[37mFirefox Attempt FAILED\033[0m")
        time.sleep(2)
        print("\033[44m\033[37mChrome Attempt\033[0m")
        # Chrome web browser
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless') #### Without window
        driver = webdriver.Chrome(service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()), options=chrome_options)
        return

    driver.get(url)

    while True:
        driver.execute_script("window.scrollBy(0, 1000)")
        time.sleep(3)
        if driver.execute_script("return window.innerHeight + window.pageYOffset >= document.body.offsetHeight"):
            break
        with open(f"matches_source_code/{dt.date.today()}.html", "w") as file:
            file.write(driver.page_source)

    driver.quit()
    return f"matches_source_code/{dt.date.today()}.html"


def get_matches_info_to_dict(source_code):
    """
    It takes source code as html file and gets 'player1', 'player2', 'tournament', 'city', 'country', 'winner', 'score', 'date', 'temperature', 'humidity' from last completed matches, returning a dictionary.
    """
    today = dt.date.today()
    with open(source_code, "r") as file_to_read:
        soup = BeautifulSoup(file_to_read, 'html.parser')
    raw_data = soup.find("article")
    if raw_data != None:
        raw_tournament_data = raw_data.find_all("div", class_="tournament-wrapper") # Prints a list with all matches info per tournament
        tournament_name_list = []
        city_list = []
        country_list = []
        player1 = []
        player2 = []
        score = []
        winner = []
        temperature = []
        humidity = []
        for tournament in raw_tournament_data:
            tournament_matches = tournament.find(attrs={"data-status":"COMPLETE"})
            name = tournament["data-ui-title"]
            raw_city = tournament["data-ui-subtitle"]
            city_and_country = raw_city.split(",")
            city = city_and_country[0].strip().title()
            country = city_and_country[-1].strip().title()
            players = tournament_matches.find_all("a", class_="match-table__player match-table__player--link")
            if len(players) == 0:
                players = tournament_matches.find_all("span", class_="match-table__player-fullname")
                for pos, player in enumerate(players):
                    fname = player.find("span", class_="match-table__player-fname").text
                    lname = player.find("span", class_="match-table__player-lname").text
                    full_name = f"{fname} {lname}"
                    if pos % 2 == 0:
                        player1.append(full_name)
                        tournament_name_list.append(name)
                        city_list.append(city)
                        country_list.append(country)
                    else:
                        player2.append(full_name)
            else:
                for pos, player in enumerate(players):
                    player_name = player["href"].split("/")[-1].replace("-", " ").title()
                    if pos % 2 == 0:
                        player1.append(player_name)
                        tournament_name_list.append(name)
                        city_list.append(city)
                        country_list.append(country)
                    else:
                        player2.append(player_name)
            raw_score = tournament_matches.find_all("a", class_="tennis-match__match-link")
            score_data = []
            for result in raw_score:
                try:
                    score_data.append(result['title'])
                except:
                    score_data.append("UNKNOWN")
            for match in score_data:
                if "/" in match:
                    raw_winner = match.split(" d ")[0].strip().split(" /")[0].strip()
                    winner.append(raw_winner)
                    try:
                        score.append(match.split("/")[-1].strip())
                    except:
                        score.append("UNKNOWN")
                else:
                    raw_winner = match.split(" d ")[0].strip()
                    if "]" in raw_winner:
                        winner.append(raw_winner.split("]")[1].strip())
                    else:
                        winner.append(raw_winner.strip())
                    try:
                        score.append(match.split(" ")[-1])
                    except:
                        score.append("UNKNOWN")

        if len(player1) != 0:
            for city in city_list:
                coord_params = {
                    "appid": api_key,
                    "q": city,
                    "limit": 1,
                    }
                    # Getting latitude and longitude
                coord_url = f"http://api.openweathermap.org/geo/1.0/direct"
                coord_response = requests.get(coord_url, params=coord_params)
                coord_response.raise_for_status() # returns an HTTPError object if an error has occurred during the process. It is used for debugging the requests module.
                lat = coord_response.json()[0]['lat']
                long = coord_response.json()[0]['lon']

                # Getting current temperature and humidity
                parameters = {
                        "appid": api_key,
                        "units": "metric",
                        "lat": lat,
                        "lon": long,
                        }

                endpoint = f"https://api.openweathermap.org/data/2.5/weather"

                response = requests.get(endpoint, params=parameters)
                response.raise_for_status
                weather_data = response.json()
                temperature.append(weather_data['main']['feels_like'])
                humidity.append(weather_data['main']['humidity'])
        else:
            print("No one match completed so far.")
    
        match_dict = {
            "player1": player1,
            "player2": player2,
            "tournament": tournament_name_list,
            "city": city_list,
            "country": country_list,
            "winner": winner,
            "score": score,
            "date": today,
            "temperature": temperature,
            "humidity": humidity,
        }

        return match_dict
    
    else:
        print('Sorry, no matches played to be recorded.')

def to_dataframe(player_matches: dict):
    """
    Saves the dictionary as dataframe.
    """
    if len(player_matches["player1"]) == 0:
        matches_df = pd.DataFrame(player_matches, columns=[column for column in player_matches.keys()])
        return matches_df

    else:
        matches_df = pd.DataFrame(player_matches, columns=[column for column in player_matches.keys()])
        try:
            try:
                os.mkdir("matches")
            except:
                with open("matches/daily.pkl", "rb") as file:
                    old_data = pickle.load(file)
                reunited_data = pd.concat([old_data, matches_df], ignore_index=True)
                reunited_data = sanitizing(reunited_data)
                full_data = pd.concat([reunited_data, old_data], ignore_index=True)
                full_data = sanitizing(full_data)
                new_data = full_data.drop_duplicates(subset=['player1', 'player2', 'city'], keep=False, ignore_index=True)
                if new_data.shape[0] == 0:
                    print("Nothing to save")
                keep_data = full_data.drop_duplicates(subset=['player1', 'player2', 'city'], keep="first", ignore_index=True)
                with open(f"matches/daily.pkl", "wb") as file:
                    pickle.dump(keep_data, file)
            return new_data

        except:
            with open(f"matches/daily.pkl", "wb") as file:
                    pickle.dump(matches_df, file)
            print("Full dataset saved")
            return matches_df


def to_database(dataframe: pd.DataFrame):
    """
    Checks the dataframe for new data and, if so, loads it into database for further analysis.
    """
    # connection = mysql.connector.connect(
    #     user = os.environ.get("PYANY_USERNAME"), # nome usuário principal
    #     password = os.environ.get("PYANY_PWD"),
    #     host = os.environ.get("PYANY_HOST"), # endpoint
    #     port = 3306,
    #     database = os.environ.get("PYANY_DATABASE") # nome do db
    # )

    connection = mysql.connector.connect(
        user = 'root',
        password = os.environ.get("LOCALPASSWORD"),
        host = 'localhost',
        database = os.environ.get("LOCAL_DATABASE")
    )

    if dataframe.shape[0] == 0:
        print("No data to load.")
    else:
        with connection.cursor() as cursor:
            for index, row in dataframe.iterrows():
                player1 = row["player1"]
                player2 = row["player2"]
                tournament = row["tournament"]
                city = row["city"]
                country = row["country"]
                winner = row["winner"]
                score = row["score"]
                date = row["date"]
                temperature = row["temperature"]
                humidity = row["humidity"]

                command = f"INSERT INTO matches (player1, player2, tournament, city, country, winner, score, date, temperature, humidity) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                cursor.execute(command, (player1, player2, tournament, city, country, winner,  score, date, temperature, humidity))
                connection.commit()
        print("Data uploaded successfully")


def sanitizing(dataframe: pd.DataFrame):
    without_dot = [player for player in dataframe['player1'].unique() if "." not in player]

    without_dot2 = [player for player in dataframe['player2'].unique() if "." not in player]

    without_dot.extend(without_dot2)

    without_dot = list(set(without_dot))

    for pos, to_replace in enumerate(dataframe['player1']):
        if '.' in to_replace:
            for player in without_dot:
                if to_replace.split()[-1] == player.split()[-1] and to_replace[0] == player[0]:
                    dataframe.at[pos, 'player1'] = player

    for pos, to_replace in enumerate(dataframe['player2']):
        if '.' in to_replace:
            for player in without_dot:
                if to_replace.split()[-1] == player.split()[-1] and to_replace[0] == player[0]:
                    dataframe.at[pos, 'player2'] = player

    for pos, to_replace in enumerate(dataframe['winner']):
        if '.' in to_replace:
            for player in without_dot:
                if to_replace.split()[-1] == player.split()[-1] and to_replace[0] == player[0]:
                    dataframe.at[pos, 'winner'] = player

    return dataframe
