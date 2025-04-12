import pickle
from dotenv import load_dotenv
import os
import requests
import pandas as pd

load_dotenv()
api_key = os.environ.get("OPENWEATHER_KEY")

try:
    try:
        os.mkdir("tournaments_files")
    except:
        with open("tournaments_files/tournaments.pkl", "rb") as file:
            tournament_data = pickle.load(file)
        tournaments_coord = tournament_data.drop(["start_date", "end_date", "year"], axis=1)

        tournaments_coord["lat"] = 0.0
        tournaments_coord["lon"] = 0.0
        
        for pos, city in tournaments_coord.iterrows():            
            coord_params = {
                        "appid": api_key,
                        "q": city.city,
                        "limit": 1,
                        }
            # Getting latitude and longitude

            coord_url = "http://api.openweathermap.org/geo/1.0/direct"
            coord_response = requests.get(coord_url, params=coord_params)
            coord_response.raise_for_status() # returns an HTTPError object if an error has occurred during the process. It is used for debugging the requests module.            
            lat = coord_response.json()[0]['lat']
            long = coord_response.json()[0]['lon']
            tournaments_coord.at[pos, "lat"] = lat
            tournaments_coord.at[pos, "lon"] = long

        with open("tournaments_files/tournaments_coord.pkl", "rb") as file:
            old_file = pickle.load(file)

        reunited_data = pd.concat([old_file, tournaments_coord], ignore_index=True)
        full_data = pd.concat([reunited_data, old_file], ignore_index=True)
        print("Dropping duplicated data")
        # new_data = full_data.drop_duplicates(subset=['name', 'city', 'country', 'year'], keep=False, ignore_index=True)
        # if new_data.shape[0] == 0:
        #     print("Nothing to save")
        keep_data = full_data.drop_duplicates(subset=['name', 'city', 'country', 'year'], keep="first", ignore_index=True)
        with open("matches/daily.pkl", "wb") as file:
            pickle.dump(keep_data, file)
except:
    with open("tournaments_files/tournaments_coord.pkl", "wb") as file:
        pickle.dump(tournaments_coord, file)
    print("Full coordenates dataset saved")



# pessoas = ["Angelo Mendes Vieira Pinto", "Olivia", "Rodrigo"]

# print(pessoas)

# >> ["Angelo", "Olivia", "Rodrigo"]

# print(pessoas[0])

# >> Angelo

# pessoas = [{"filhos": ["Angelo Mendes Vieira Pinto", "Olivia"], "pai": "Rodrigo"}]

# print(pessoas[0]["filhos"])

# >> ["Angelo Mendes Vieira Pinto", "Olivia"]

# print(pessoas[0]["filhos"][0])

# >> "Angelo Mendes Vieira Pinto"