from main_tasks import cities_coord, match_by_match, tournaments, weather
import datetime as dt
from time import sleep
import smtplib
import os


DEPARTURE_MAIL = os.environ.get("DEPARTURE_MAIL")
PASS_DEPART_MAIL = os.environ.get("PASS_DEPART_MAIL")
ARRIVAL_MAIL = os.environ.get("ARRIVAL_MAIL")

today = dt.datetime.today()
hour = dt.datetime.now().time()

def updating_matches():
    # get_source_code = match_by_match.get_source_code("/Users/rodimendes/Documents/my_projects/where_are_you_best/matches_source_code/2025-04-13.html")
    get_source_code = match_by_match.get_source_code("https://www.wtatennis.com/scores")
    matches_dict = match_by_match.get_matches_info_to_dict(get_source_code)
    matches_df = match_by_match.to_dataframe(matches_dict)
    # match_by_match.to_database(matches_df)
    weather.current_weather()
    print("\033[92mMatches have been updated!\033[0m")


if (today.weekday() == 6) and ("12:00" < str(hour)):# < "14:00"):
    try:
        tournaments_url = "https://www.wtatennis.com/tournaments"
        tournament_source_file = tournaments.get_data_source(tournaments_url)
        tournament_dict = tournaments.get_tournaments_info_to_dict(tournament_source_file)
        
        print(f"Tournament dict - {tournament_dict}")
        
        tournament_df = tournaments.to_dataframe(tournament_dict)
        # tournaments.to_database(tournament_df)
        print("\033[92mTournaments module works well\033[0m")
    except:
        print("\033[91mTournaments not working.\033[0m")
    try:
        weather_dict = weather.weather_data()
        weather_df = weather.to_dataframe(weather_dict)
        # weather.to_database(weather_df)
        print("\033[92mweather module works well\033[0m")
    except:
            print("\033[91mweather not working.\033[0m")
    try:
        cities_coord
        print("\033[92mcities_coord module works well\033[0m")
    except:
        print("\033[91mcities_coord not working.\033[0m")

try:
    updating_matches()
except Exception as e:
    print("\033[91mUpdate did not work properly.\033[0m")
    print(f'Matches not updated. Error message: {e}')
    sleep(20)
    print("\033[93mTrying to update one more time\033[0m")
    try:
        updating_matches()
    except:
        email_message = f"Subject:🚨The update process is not working well.🚨\n\nCheck the update process as soon as posible to fix bugs.\n{e}"
        with smtplib.SMTP("smtp.gmail.com", port=587) as connection:
            connection.starttls()
            connection.login(DEPARTURE_MAIL, PASS_DEPART_MAIL)
            connection.sendmail(from_addr=DEPARTURE_MAIL, to_addrs=ARRIVAL_MAIL, msg=email_message.encode('utf-8'))
