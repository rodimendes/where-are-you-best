# 🎾 Where are U best? 🥇
### Project to find out where and under what weather conditions tennis players win.

## Description
`Where are U best` is a project that seeks to identify the degree of influence of the playing surface, temperature and humidity on female tennis players.

For this the python script gets data from the official webpage of female tennis players, that is, [Women's Tennis Association - WTA](https://www.wtatennis.com/) and gathers weather forecast data as temperature and humidity, collected by using API from [OpenWeather](https://openweathermap.org/).

On this first approach we've collected the following information:
- players,
- score,
- tournament,
- city,
- country,
- winner,
- score,
- date,
- temperature, and
- humidity.

## Files and main functions
The scripts are inside the `main_tasks` folder and collect different data.

### `match_by_match.py`

- `def get_source_code(url):`

  Gets the source code and saves it for further verifications. The function returns the path to 'html' file.

- `def get_matches_info_to_dict(source_code):`

  It takes source code as html file and gets 'player1', 'player2', 'tournament', 'city', 'country', 'winner', 'score', 'date', 'temperature', 'humidity' from last matches completed, returning a dictionary.

  If there are no complete new matches, it returns an empty dictionary.

- `def to_dataframe(player_matches: dict):`

  Checks whether the received dictionary has any match records.
  If the dictionary is empty, it returns an empty dataframe.If it has data, it updates the existing dataframe (pickle file) for further analysis and returns only new entries as dataframe.

- `def to_database(dataframe: pd.DataFrame):`

  Checks the dataframe for new data and, if so, loads it into the database for further analysis. Otherwise, it closes the application without connecting to the database.

### `tournaments.py`

- `def get_data_source(url):`

  Gets the source code and saves it for further     verifications. The function returns the path to 'html' file and the player name.

- `def get_tournaments_info_to_dict(html_file):`

  Receives the source code as html file and gets 'name', 'city', 'country', 'surface', 'start_date', 'end_date' and 'year' from last tournaments, returning a dictionary.

- `def to_dataframe(tournaments: dict):`

  Receives a dictionary, saving for dataframe format.
  The tournaments considered are those of the current month.

- `def to_database(tournaments: pd.DataFrame):`

  Checks the dataframe for new data and, if so, loads it into the database for further analysis. Otherwise, it closes the application without connecting to the database.

- `def get_data_from_db():`

  Runs a query for all records in the table.

### `weather.py`

- `def weather_data():`

  It checks the city hosting a current tournament, locates its latitude and longitude, and then collects the temperature and humidity for the next seven days. Returns a dictionary with the name of the city, forecast date, temperature and humidity.

- `def to_dataframe(weather_dict: dict):`

  Saves the dictionary as dataframe.

- `def to_database(weather: pd.DataFrame):`

  Loads the data into database for further analysis.

# ✍️ UNDER CONSTRUCTION 👨🏻‍💻
