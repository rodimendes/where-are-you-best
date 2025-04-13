import requests
import pickle
import os
from dotenv import load_dotenv
import mysql.connector
import datetime as dt
import pandas as pd

load_dotenv()
api_key = os.environ.get("OPENWEATHER_KEY")


def current_weather():
    with open("tournaments_files/tournaments.pkl", 'rb') as file:
        lista = pickle.load(file)

    today = dt.datetime.today().date()
    full_start_dt = lista.start_date + ' ' + lista.year
    full_end_dt = lista.end_date + ' ' + lista.year

    cities = []
    current_temperature = []
    current_humidity = []
    for pos, row in lista.iterrows():
        end_date = dt.datetime.strptime(full_end_dt[pos], '%b %d %Y')
        start_date = dt.datetime.strptime(full_start_dt[pos], '%b %d %Y')
        if start_date.date() <= today and end_date.date() >= today:
        # Look at the tournament official starting date
            if row.city == "Buchareest":
                row.city = "Bucharest"
            cities.append(row.city)
            coord_params = {
                    "appid": api_key,
                    "q": row.city,
                    "limit": 1,
                    }
                    # Getting latitude and longitude
            coord_url = "http://api.openweathermap.org/geo/1.0/direct"
            coord_response = requests.get(coord_url, params=coord_params)
            coord_response.raise_for_status() # returns an HTTPError object if an error has occurred during the process. It is used for debugging the requests module.
            try:
                lat = coord_response.json()[0]['lat']
                long = coord_response.json()[0]['lon']
            except:
                print(f"A city {row.city} doesn't work properly.")
                lat = 0
                long = 0
            # Getting current temperature and humidity
            parameters = {
                    "appid": api_key,
                    "units": "metric",
                    "lat": lat,
                    "lon": long
                    }

            endpoint = "https://api.openweathermap.org/data/2.5/weather"

            response = requests.get(endpoint, params=parameters)
            response.raise_for_status
            weather_data = response.json()
            current_temperature.append(weather_data['main']['feels_like'])
            current_humidity.append(weather_data['main']['humidity'])

    current_weather_dict = {
        "city": cities,
        "temperature": current_temperature,
        "humidity": current_humidity
    }

    current_weather_df = pd.DataFrame(current_weather_dict, columns=[column for column in current_weather_dict.keys()])

    with open("weather_files/current_weather.pkl", 'wb') as file:
            pickle.dump(current_weather_df, file)

def weather_data():
    """
    It checks the city hosting a current tournament, locates its latitude and longitude, and then collects the temperature and humidity for the next seven days. Returns a dictionary with the name of the city, forecast date, temperature and humidity.
    """
    with open("tournaments_files/tournaments.pkl", 'rb') as file:
        lista = pickle.load(file)

    full_start_dt = lista.start_date + ' ' + lista.year
    full_end_dt = lista.end_date + ' ' + lista.year
    today = dt.datetime.today()
    city = []
    week_dates = []
    week_temperature = []
    week_humidity = []
    for pos, start in enumerate(full_start_dt):
        start_date = dt.datetime.strptime(start, '%b %d %Y')
        end_date = dt.datetime.strptime(full_end_dt[pos], '%b %d %Y')
        if (start_date - today).days >= 0 and (today <= end_date):
            city_name = lista['city'][pos]
            
            print(f'Getting data from {city_name} tournament.')

            coord_params = {
            "appid": api_key,
            "q": city_name,
            "limit": 1,
            }

            # Get latitude and longitude
            coord_url = "http://api.openweathermap.org/geo/1.0/direct"
            coord_response = requests.get(coord_url, params=coord_params)
            coord_response.raise_for_status() # returns an HTTPError object if an error has occurred during the process. It is used for debugging the requests module.
            lat = coord_response.json()[0]['lat']
            long = coord_response.json()[0]['lon']

            # Get next days temperature and humidity
            parameters = {
                    "appid": api_key,
                    "units": "metric",
                    "lat": lat,
                    "lon": long
                }

            endpoint = "https://api.openweathermap.org/data/2.5/forecast"

            response = requests.get(endpoint, params=parameters)
            response.raise_for_status
            weather_data = response.json()
            remaining_days = (end_date - today).days
            print(f'Remaining days: {remaining_days}')
            print(f'Length: {len(weather_data["list"][:5])}')
            if remaining_days < 5:
                next_days = weather_data['list']
                for day in next_days:
                    if day['dt_txt'].split()[-1] == '00:00:00':
                        week_temperature.append(day['main']['feels_like'])
                        week_humidity.append(day['main']['humidity'])
                        week_dates.append(day['dt_txt'].split()[0])
                        city.append(city_name)
            else:
                next_days = weather_data['list'][:5]
                for day in next_days:
                    if day['dt_txt'].split()[-1] == '00:00:00':
                        week_temperature.append(day['main']['feels_like'])
                        week_humidity.append(day['main']['humidity'])
                        week_dates.append(day['dt_txt'].split()[0])
                        city.append(city_name)

    weather_forecast = {
        'name': city,
        "dates": week_dates,
        "temperature": week_temperature,
        "humidity": week_humidity
        }

    return weather_forecast


def to_dataframe(weather_dict: dict):
    """
    Saves the dictionary as dataframe.
    """
    weather_df = pd.DataFrame(weather_dict, columns=[column for column in weather_dict.keys()])
    try:
        last_weather_forecast = "weather_files/climate_forecast.pkl"
        with open(last_weather_forecast, "rb") as file:
            last_forecast = pickle.load(file)
        reunited_data = pd.concat([last_forecast, weather_df], ignore_index=True)
        full_forecast = pd.concat([reunited_data, last_forecast], ignore_index=True)
        uptodate_forecast = full_forecast.drop_duplicates(subset=['name', 'dates'], keep="first", ignore_index=True)
        cleaned_forecast = full_forecast.drop_duplicates(subset=['name', 'dates'], keep=False, ignore_index=True)
        if cleaned_forecast.shape[0] == 0:
            print("Nothing to save")
        with open("weather_files/climate_forecast.pkl", "wb") as file:
            pickle.dump(uptodate_forecast, file)
        return cleaned_forecast

    except:
        print("Saving full data")
        with open("weather_files/climate_forecast.pkl", 'wb') as file:
            pickle.dump(weather_df, file)
        return weather_df


def to_database(weather: pd.DataFrame):
    """
    Loads the data into database for further analysis.
    """
    connection = mysql.connector.connect(
        user = 'root',
        password = os.environ.get("LOCALPASSWORD"),
        host = 'localhost',
        database = os.environ.get("LOCAL_DATABASE")
    )

    if weather.shape[0] == 0:
        print("Database up to date. No data to load.")
    else:
        with connection.cursor() as cursor:
            for index, row in weather.iterrows():
                city = row["name"]
                date = row["dates"]
                temperature = row["temperature"]
                humidity = row["humidity"]
                command = "INSERT INTO weather_forecast (city, date, temperature, humidity) VALUES (%s, %s, %s, %s);"
                cursor.execute(command, (city, date, temperature, humidity))
                connection.commit()
        print("Weather data uploaded successfully")
    return

current_weather()
