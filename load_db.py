from main_tasks.match_by_match import to_database
import pickle


with open("matches/daily.pkl", "rb") as file:
    old_data = pickle.load(file)

# print(old_data.head())
# print(old_data.shape)

to_database(old_data)