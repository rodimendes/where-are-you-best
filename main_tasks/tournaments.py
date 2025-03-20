from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from webdriver_manager.core.utils import ChromeType
import mysql.connector
import pandas as pd
import pickle
import os
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.options import Options


def get_data_source(url):
    """
    Gets the source code and saves it for further verifications.
    The function returns the path to 'html' file and the player name.
    """
    # Firefox web browser
    firefox_options = Options()
    firefox_options.add_argument("-headless")
    driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=firefox_options)

    # # Chrome web browser
    # chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument('--headless')
    # service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
    # driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.get(url)
    with open(f"tournaments_files/tournaments_list.html", "w") as file:
        file.write(driver.page_source)
    return "tournaments_files/tournaments_list.html"


def get_tournaments_info_to_dict(html_file):
    """
    Receives the source code as html file and returns 'name', 'city', 'country', 'surface', 'start_date', 'end_date' and 'year' from last tournaments, as a dictionary.
    """
    with open(html_file, 'r') as raw_file:
        soup = BeautifulSoup(raw_file, 'html.parser')
    active_tournaments = soup.find_all('div', class_='is-active-month')
    for tournament in active_tournaments:
        raw_names = tournament.find_all('h3', class_='tournament-thumbnail__title')
        names = [name.text.strip() for name in raw_names]
        raw_dates = tournament.find_all('time')
        start_date = [date.text.strip() for pos, date in enumerate(raw_dates) if pos % 2 == 0]
        end_date = [date.text.split(',')[0].strip() for pos, date in enumerate(raw_dates) if pos % 2 == 1]
        year = [date.text.split(',')[1].strip() for pos, date in enumerate(raw_dates) if pos % 2 == 1]
        raw_location = tournament.find_all('span', class_='tournament-thumbnail__location')
        cities = [city.text.split(',')[0].strip().title() for city in raw_location]
        countries = [country.text.split(',')[-1].strip().title() for country in raw_location]
        raw_surface = tournament.find_all('span', class_='tournament-tag')
        surfaces = [surface.text.strip() for surface in raw_surface]

    tournaments_dict = {
        'name': names,
        'city': cities,
        'country': countries,
        'surface': surfaces,
        'start_date': start_date,
        'end_date': end_date,
        'year': year
    }

    return tournaments_dict


def to_dataframe(tournaments: dict):
    """
    Receives a dictionary, saving for dataframe format.
    The tournaments considered are those of the current month.
    """
    tournaments_df = pd.DataFrame(tournaments, columns=[column for column in tournaments.keys()])
    try:
        with open(f"tournaments_files/tournaments.pkl", "rb") as old_file:
            old_data = pickle.load(old_file)
        reunited_data = pd.concat([old_data, tournaments_df], ignore_index=True)
        full_data = pd.concat([reunited_data, old_data], ignore_index=True)
        print("Dropping duplicated data")
        uptodate_tournaments = full_data.drop_duplicates(subset=["name", "year"], keep="first", ignore_index=True)
        new_data = full_data.drop_duplicates(subset=["name", "year"], keep=False, ignore_index=True)
        if new_data.shape[0] == 0:
            print("Nothing to save")
        with open("tournaments_files/tournaments.pkl", "wb") as file:
            pickle.dump(uptodate_tournaments, file)

        return new_data

    except:
        print("Saving full data")
        with open("tournaments_files/tournaments.pkl", "wb") as file:
            pickle.dump(tournaments_df, file)
        
        return tournaments_df


def to_database(tournaments: pd.DataFrame):
    """
    Loads the data into database for further analysis.
    """
    connection = mysql.connector.connect(
        user = 'root',
        password = os.environ.get("LOCALPASSWORD"),
        host = 'localhost',
        database = os.environ.get("LOCAL_DATABASE")
    )

    if tournaments.shape[0] == 0:
        print("Database up to date. No data to load.")
    else:
        with connection.cursor() as cursor:
            for index, row in tournaments.iterrows():
                name = row["name"]
                city = row["city"]
                country = row["country"]
                surface = row["surface"]
                start_date = row["start_date"]
                end_date = row["end_date"]
                year = row["year"]
                command = f"INSERT INTO tournaments (name, city, country, surface, start_date, end_date, year) VALUES (%s, %s, %s, %s, %s, %s, %s);"
                cursor.execute(command, (name, city, country, surface, start_date, end_date, year))
                connection.commit()
        print("Data uploaded successfully")
    return


def get_data_from_db():
    """
    Runs a query for all records in the table.
    """
    connection = mysql.connector.connect(
        user = 'root',
        password = os.environ.get("LOCALPASSWORD"),
        host = 'localhost',
        database = os.environ.get("LOCAL_DATABASE")
    )

    with connection.cursor() as cursor:
        query = "SELECT * FROM tournaments"
        cursor.execute(query)
        content = cursor.fetchall()

    return content


tournaments_dict = get_tournaments_info_to_dict("tournaments_files/tournaments_list.html")
to_dataframe(tournaments_dict)
