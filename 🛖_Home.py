import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import smtplib
import os
from dotenv import load_dotenv

load_dotenv()

DEPARTURE_MAIL = os.environ["DEPARTURE_MAIL"]
PASS_DEPART_MAIL = os.environ["PASS_DEPART_MAIL"]
ARRIVAL_MAIL = os.environ["ARRIVAL_MAIL"]

DATAFRAME_HEIGHT_LARGE = 320
DATAFRAME_HEIGHT_SMALL = 100
PX_HEIGHT = 400
PX_WIDTH = 700
BIN_SIZE_TEMP = 0.8
BIN_SIZE_HUM = 2

st.set_page_config(
    page_title="Where are U best",
    page_icon="🎾",
    layout="centered",
)

def all_matches(matches_data, data_type, current_weather):
    choice = st.sidebar.radio("Filter data by:", options=["General", "Players", "Winners", "Country", "H2H", "Matches Forecast"], horizontal=True, help="For some options below, new filters are available.")
    players1 = matches_data["Player 1"].unique()
    players2 = matches_data["Player 2"].unique()
    full_players_list = sorted(list(set(players1) | set(players2)))

    st.title(f"🎾 Where are U best - {choice}")

    if choice == "General":
        st.markdown(f"#### View the latest recorded `{data_type}`.")
        col01, col02, col03, col04, col05 = st.columns(5)
        col01.metric(label="Saved matches", value=len(matches_data))
        col02.metric(label="Total players", value=len(full_players_list))
        col03.metric(label="Total tournaments", value=len(matches_data["Tournament"].unique()))
        col04.metric(label="Total cities", value=len(matches_data["City"].unique()))
        col05.metric(label="Total countries", value=len(matches_data["Country"].unique()))
        st.dataframe(matches_data.tail(8), height=DATAFRAME_HEIGHT_LARGE)

    elif choice == "Players":
        player_select = st.sidebar.selectbox("Pick a player:", full_players_list)
        st.write(f"You choose **{player_select}**")
        player_df = matches_data[(matches_data['Player 1'] == player_select) | (matches_data['Player 2'] == player_select)]
        st.dataframe(player_df)

        # Wins and defeats
        wins = 0
        defeat = 0
        for winner in player_df["Winner"]:
            if player_select[-4:] in winner:
                wins += 1
            else:
                defeat += 1

        # Temperature
        mean_temp = (player_df["Temperature"]).mean()
        std_dev_temp = pd.DataFrame(player_df["Temperature"]).std()

        # Humidity
        mean_humidity = (player_df["Humidity"]).mean()
        std_dev_hum = pd.DataFrame(player_df["Humidity"]).std()

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric(label="Matches", value=player_df.shape[0])
        col2.metric(label="Wins", value=wins, delta=f"{(wins/player_df.shape[0])*100:.1f}%")
        col3.metric(label="Defeats", value=defeat, delta=f"{(defeat/player_df.shape[0])*100:.1f}%")
        col4.metric(label="Mean temperature", value=f"{mean_temp:.2f}", delta=f"{std_dev_temp.max():.2f}", help="The green value represents the standard deviation for collected values so far.")
        col5.metric(label="Mean humidity", value=f"{mean_humidity:.2f}", delta=f"{std_dev_hum.max():.2f}", help="The green value represents the standard deviation for collected values so far.")

        wins_df = (player_df[player_df["Winner"].str.contains(player_select[-4:])]).round()
        defeats_df = (player_df[player_df["Winner"].str.contains(player_select[-4:])==False]).round()

        fig = go.Figure()
        if wins_df.shape[0] == 0:
            fig.add_trace(go.Histogram(x=defeats_df["Temperature"], name="Defeats", marker_color="red"))
            fig.update_layout(title_text="Temperature - Defeats")
        elif defeats_df.shape[0] == 0:
            fig.add_trace(go.Histogram(x=wins_df["Temperature"], name="Wins", marker_color="green"))
            fig.update_layout(title_text="Temperature - Wins")
        else:
            fig.add_traces([go.Histogram(x=wins_df["Temperature"], name="Wins", marker_color="green"), go.Histogram(x=defeats_df["Temperature"], name="Defeats", marker_color="red")])
            fig.update_layout(title_text="Temperature - Wins vs. Defeats")

        fig.update_traces(
            opacity=0.75,
            xbins=dict(
                start=0,
                end=40,
                size=BIN_SIZE_TEMP),
            )
        fig.update_layout(yaxis_title="Wins",
                          xaxis_title="Temperature",
                          barmode="overlay",
                          width=PX_WIDTH,
                          height=PX_HEIGHT,
                          legend_title="Legend",
                          legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.8)
                          )
        fig.update_xaxes(range=[0, 40])
        fig.update_yaxes(range=[0, 30])
        st.plotly_chart(fig)


        fig2 = go.Figure()
        if wins_df.shape[0] == 0:
            fig2.add_trace(go.Histogram(x=defeats_df["Humidity"], name="Defeats", marker_color="red"))
            fig2.update_layout(title_text="Humidity - Defeats")
        elif defeats_df.shape[0] == 0:
            fig2.add_trace(go.Histogram(x=wins_df["Humidity"], name="Wins", marker_color="green"))
            fig2.update_layout(title_text="Humidity - Wins")
        else:
            fig2.add_traces([go.Histogram(x=wins_df["Humidity"], name="Wins", marker_color="green"), go.Histogram(x=defeats_df["Humidity"], name="Defeats", marker_color="red")])
            fig2.update_layout(title_text="Humidity - Wins vs. Defeats")

        fig2.update_traces(
            opacity=0.75,
            xbins=dict(
                start=0,
                end=100,
                size=BIN_SIZE_HUM),
            )
        fig2.update_layout(yaxis_title="Wins",
                          xaxis_title="Humidity",
                          barmode="overlay",
                          width=PX_WIDTH,
                          height=PX_HEIGHT,
                          legend_title="Legend",
                          legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.8)
                          )
        fig2.update_xaxes(range=[0, 100])
        fig2.update_yaxes(range=[0, 30])
        st.plotly_chart(fig2)

        i_will_try = st.sidebar.checkbox("Do you want to try?")
        if i_will_try:
            desired_temp = st.sidebar.slider(label='Temperature', min_value=5, max_value=50, value=(10, 40))
            desired_humid = st.sidebar.slider(label='Humidity', min_value=0, max_value=100, value=(50, 70))
            my_choice_temp = (player_df[(player_df['Temperature'] >= desired_temp[0]) & (player_df['Temperature'] <= desired_temp[1])])
            my_choice_hum = (my_choice_temp[(my_choice_temp['Humidity'] >= desired_humid[0]) & (my_choice_temp['Humidity'] <= desired_humid[1])])
            st.dataframe(my_choice_hum)

    elif choice == "Winners":
        winners = matches_data["Winner"].unique()
        winner_select = st.sidebar.selectbox("Pick a winner:", winners)
        wins = matches_data[matches_data["Winner"] == winner_select]
        st.dataframe(wins, height=DATAFRAME_HEIGHT_SMALL)

        all_wins_rounded = matches_data.round()
        wins_rounded = wins.round()

        fig = px.histogram(wins_rounded, x="Temperature", title="Wins and Temperature - Chosen Player", text_auto=True, range_x=(0, 40), range_y=(0, 30), width=PX_WIDTH, height=PX_HEIGHT)
        fig.update_layout(yaxis_title="Wins")
        fig.update_traces(
            xbins=dict(
                start=0,
                end=40,
                size=BIN_SIZE_TEMP)
            )
        st.plotly_chart(fig)

        fig2 = go.Figure()
        fig2.add_traces([go.Histogram(x=all_wins_rounded["Temperature"], name="All players", marker_color="red"), go.Histogram(x=wins_rounded["Temperature"], name=winner_select, marker_color="blue")])

        fig2.update_traces(
            opacity=0.75,
            xbins=dict(
                start=0,
                end=40,
                size=BIN_SIZE_TEMP),
            )
        fig2.update_layout(title_text="Wins and Temperature - All Players vs. Chosen Player",
                           yaxis_title="Wins",
                           xaxis_title="Temperature",
                           barmode="overlay",
                           width=PX_WIDTH,
                           height=PX_HEIGHT,
                           legend_title="Legend",
                           legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.8)
                           )
        fig2.update_xaxes(range=[0, 40])
        fig2.update_yaxes(range=[0, 30])
        st.plotly_chart(fig2)

        fig3 = px.histogram(wins_rounded, x="Humidity", title="Wins and Humidity - Chosen Player", text_auto=True, range_x=(0, 100), range_y=(0, 30), width=PX_WIDTH, height=PX_HEIGHT)
        fig3.update_layout(yaxis_title="Wins")
        fig3.update_traces(xbins=dict(
            start=0,
            end=100,
            size=BIN_SIZE_HUM
            ))
        st.plotly_chart(fig3)

        fig4 = go.Figure()
        fig4.add_trace(go.Histogram(x=all_wins_rounded["Humidity"], name="All players", marker_color="red"))
        fig4.add_trace(go.Histogram(x=wins_rounded["Humidity"], name=winner_select, marker_color="blue"))

        fig4.update_traces(
            opacity=0.75,
            xbins=dict(
                start=0,
                end=100,
                size=BIN_SIZE_HUM),
            )
        fig4.update_layout(title_text="Wins and Humidity - All Players vs. Chosen player",
                           yaxis_title="Wins",
                           xaxis_title="Humidity",
                           barmode="overlay",
                           width=PX_WIDTH,
                           height=PX_HEIGHT,
                           legend_title="Legend",
                           legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.8)
                           )
        fig4.update_xaxes(range=[0, 100])
        fig4.update_yaxes(range=[0, 30])
        st.plotly_chart(fig4)

    elif choice == "Country":
        countries = matches_data["Country"].unique()
        country_select = st.sidebar.selectbox("Pick a country:", countries)
        st.dataframe(matches_data[matches_data["Country"] == country_select], height=DATAFRAME_HEIGHT_LARGE)

    elif choice == "H2H":
        # TODO How to put small graphs into columns

        winners = matches_data["Winner"].unique()
        col1, col2 = st.columns(2)
        player1 = col1.selectbox("Player 1", winners)
        player2 = col2.selectbox("Player 2", winners)

        player1_wins = (matches_data[matches_data["Winner"] == player1]).round()
        player2_wins = (matches_data[matches_data["Winner"] == player2]).round()
        col1.metric("Wins", len(player1_wins))
        col2.metric("Wins", len(player2_wins))

        ### Humidity
        fig_hum = go.Figure()
        fig_hum.add_trace(go.Histogram(x=player1_wins["Humidity"], name=player1, marker_color="red"))
        fig_hum.add_trace(go.Histogram(x=player2_wins["Humidity"], name=player2, marker_color="blue"))

        fig_hum.update_traces(
            opacity=0.75,
            xbins=dict(
                start=0,
                end=100,
                size=BIN_SIZE_HUM),
            )
        fig_hum.update_layout(title_text=f"Humidity - Head to Head {player1} vs {player2}",
                           yaxis_title="Wins",
                           xaxis_title="Humidity",
                           barmode="overlay",
                           width=PX_WIDTH,
                           height=PX_HEIGHT,
                           legend_title="Legend",
                           legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.8)
                           )
        fig_hum.update_xaxes(range=[0, 100])
        fig_hum.update_yaxes(range=[0, 30])
        st.plotly_chart(fig_hum)

        ### Temperature
        fig_temp = go.Figure()
        fig_temp.add_traces([go.Histogram(x=player1_wins["Temperature"], name=player1, marker_color="red"), go.Histogram(x=player2_wins["Temperature"], name=player2, marker_color="blue")])

        fig_temp.update_traces(
            opacity=0.75,
            xbins=dict(
                start=0,
                end=40,
                size=.8),
            )
        fig_temp.update_layout(title_text=f"Temperature - Head to Head {player1} vs {player2}",
                           yaxis_title="Wins",
                           xaxis_title="Temperature",
                           barmode="overlay",
                           width=PX_WIDTH,
                           height=PX_HEIGHT,
                           legend_title="Legend",
                           legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.8)
                           )
        fig_temp.update_xaxes(range=[0, 40])
        fig_temp.update_yaxes(range=[0, 30])
        st.plotly_chart(fig_temp)
    elif choice == "Matches Forecast":
        df_to_predict = pd.read_pickle("ml_models/df_to_predict.pkl")
        rf_model = pd.read_pickle("ml_models/rf_model.pkl")
        player1 = st.selectbox("Choose the player 1:", df_to_predict.index)
        player2 = st.selectbox("Choose the player 2:", df_to_predict.index)
        if len(current_weather) != 0:
            city = st.selectbox("Select a city:", current_weather.index)
            st.markdown("*For best results, try it up to **two hours** before the start of the match*")
            player1_cod = df_to_predict.at[player1, "p1_cod"]
            player2_cod = df_to_predict.at[player2, "p1_cod"]
            temp = current_weather.at[city, "Temperature"]
            humid = current_weather.at[city, "Humidity"]
            matches_played_p1 = df_to_predict.at[player1, "matches_played"]
            matches_played_p2 = df_to_predict.at[player2, "matches_played"]
            win_ratio_p1 = df_to_predict.at[player1, "win_ratio"]
            win_points_p1 = df_to_predict.at[player1, "win_points"]
            win_ratio_p2 = df_to_predict.at[player2, "win_ratio"]
            win_points_p2 = df_to_predict.at[player2, "win_points"]

            predict_p1 = rf_model.predict_proba([[temp, humid, player1_cod, matches_played_p1, win_ratio_p1, win_points_p1]])
            predict_p2 = rf_model.predict_proba([[temp, humid, player2_cod, matches_played_p2, win_ratio_p2, win_points_p2]])

            p1_prob_loss = round(predict_p1[0][0], ndigits=2)
            p1_prob_win = round(predict_p1[0][1], ndigits=2)
            p2_prob_loss = round(predict_p2[0][0], ndigits=2)
            p2_prob_win = round(predict_p2[0][1], ndigits=2)

            win_proba_1 = round((p1_prob_win + p2_prob_loss) / 2, ndigits=2) * 100
            win_proba_2 = round((p2_prob_win + p1_prob_loss) / 2, ndigits=2) * 100

            dataframe = pd.DataFrame([win_proba_1, win_proba_2], index=[player1, player2], columns=["win_proba"])

            fig = px.bar(dataframe, y="win_proba", color=dataframe.index, text_auto=True)
            fig.update_layout(
                        title_text=f"Win probability - {player1} vs {player2}",
                        yaxis_title="Probability (%)",
                        xaxis_title="Players",
                        showlegend=False,
                        font={
                            "size": 20
                        }
                            )
            st.plotly_chart(fig)
        else:
            col1, col2, col3 = st.columns([45, 100, 1])

            col2.markdown("**There are no tournaments being played.**")

def all_tournaments(tournament_data, data_type):
    """
    Shows all recorded tournaments and its data.
    """
    st.title("🎾 Where are U best - Tournaments")
    # Showing recorded tournaments
    st.markdown(f"#### Recorded `{data_type}`.")
    col01, col02, col03 = st.columns(3)
    col01.metric(label="Saved Tournaments", value=len(tournament_data["Name"].unique()))
    col02.metric(label="Total Cities", value=len(tournament_data["City"].unique()))
    col03.metric(label="Total Countries", value=len(tournament_data["Country"].unique()))

    # World map with tournaments
    st.markdown("##### Hover over points for more information.")
    tournaments_coord = pd.read_pickle("tournaments_files/tournaments_coord.pkl")
    fig = px.scatter_map(data_frame=tournaments_coord, lat="lat", lon="lon", zoom=0.5, hover_name="name", hover_data=["city", "country", "surface"], labels={"city": "City", "surface": "Surface", "country": "Country", "lat": "Latitude", "lon": "Longitude"}, color=tournaments_coord["surface"], color_discrete_sequence=["blue", "chocolate", "green"])
    fig.update_layout(mapbox_style="carto-positron", margin={"r":0,"t":0,"l":0,"b":0}, legend=dict(yanchor="top", y=0.98, xanchor="left", x=0.01))
    st.plotly_chart(fig)



### Page Start ###
# st.title("🎾 Where are U best")

### Adding sidebar ###
add_sidebar = st.sidebar.radio("Select one of the options below:", ("Matches", "Tournaments"), horizontal=True)

### Loading and configuring data from pickle files ###
matches = pd.read_pickle("matches/daily.pkl")
matches.columns = ["Player 1", "Player 2", "Tournament", "City", "Country", "Winner", "Score", "Date", "Temperature", "Humidity"]
matches.index += 1
tournaments = pd.read_pickle("tournaments_files/tournaments.pkl")
tournaments.columns = ["Name", "City", "Country", "Surface", "Start", "End", "Year"]
tournaments.index += 1
weather_data = pd.read_pickle("weather_files/current_weather.pkl")
weather_data.columns = ["City", "Temperature", "Humidity"]
weather_data.set_index("City", inplace=True)

### Showing data according to selection ###
if add_sidebar == "Matches":
    all_matches(matches_data=matches, data_type=add_sidebar, current_weather=weather_data)


if add_sidebar == "Tournaments":
    all_tournaments(tournament_data=tournaments, data_type=add_sidebar)

st.sidebar.write("---")
st.sidebar.markdown("#### Cities with active tournament and current weather conditions:")
st.sidebar.dataframe(weather_data)

st.sidebar.write("---")
st.sidebar.markdown("#### 📬 Contacts")
st.sidebar.info('👨🏻‍💻 **Rodrigo Mendes** - [LinkedIn](https://www.linkedin.com/in/rodrigo-mendes-pinto/) - [Github](https://github.com/rodimendes/where_are_u_best)')

with st.sidebar.form(key="form", clear_on_submit=True):
    text = st.text_area("Feel free to give me some impressions or suggestions")
    name = st.text_input(label="Name")
    email = st.text_input(label="Email for reply, if you want.")
    submit = st.form_submit_button()
    if submit:
        st.success("Message sent successfully")
        email_message = f"Subject:Where are U best calling... 📬\n\nMessage: {text}\nName: {name}\nEmail: {email}"
        with smtplib.SMTP("smtp.gmail.com", port=587) as connection:
            connection.starttls()
            connection.login(DEPARTURE_MAIL, PASS_DEPART_MAIL)
            connection.sendmail(from_addr=DEPARTURE_MAIL, to_addrs=ARRIVAL_MAIL, msg=email_message.encode('utf-8'))
