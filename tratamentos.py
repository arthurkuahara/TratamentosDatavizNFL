import pandas as pd
import plotly.express as px

df_scores = pd.read_csv('spreadspoke_scores.csv')
df_teams = pd.read_csv('nfl_teams.csv')
df_stadiums = pd.read_csv('nfl_stadiums.csv', encoding = 'latin-1')

df_analysis = df_scores.merge(df_stadiums, left_on = 'stadium', right_on = 'stadium_name')
df_final = df_analysis[~df_analysis['spread_favorite'].isna()].reset_index(drop = True).copy()
df_final['total'] = df_final['score_home'] + df_final['score_away']
dict_teams_corresp = dict(zip(df_teams['team_id'].to_list(), df_teams['team_name'].to_list()))
df_final['favorite'] = df_final['team_favorite_id'].map(dict_teams_corresp)

df = df_final.copy()

def categorize_outcome(row):
    if row['favorite'] == row['team_home']:
        favorite_score = row['score_home']
        underdog_score = row['score_away']
    else:
        favorite_score = row['score_away']
        underdog_score = row['score_home']

    spread_difference = favorite_score - underdog_score

    if spread_difference > 0 and spread_difference < abs(row['spread_favorite']):
        return "favorite won, but didn't cover"
    elif spread_difference >= abs(row['spread_favorite']):
        return "favorite won and covered the spread"
    else:
        return "underdog won outright"

df['outcome'] = df.apply(categorize_outcome, axis=1)

df['over_under_line'] = pd.to_numeric(df['over_under_line'], errors='coerce')

def within_7_points(row):
    if abs(row['total'] - row['over_under_line']) <= 3:
        return True
    else:
        return False

df['within_7_points'] = df.apply(within_7_points, axis=1)

def within_spread(row):
    if row['outcome'] == "favorite won and covered the spread":
        spread_difference = row['score_home'] - row['score_away'] - row['spread_favorite']
    elif row['outcome'] == "underdog won outright":
        spread_difference = row['score_away'] - row['score_home'] + row['spread_favorite']
    else:
        spread_difference = abs(row['score_home'] - row['score_away'])

    if spread_difference <= 3:
        return True
    else:
        return False

df['within_spread'] = df.apply(within_spread, axis=1)


# Assuming your DataFrame is named 'df'
grouped_season = df.groupby('schedule_season')

# Count the number of True and False values for the 'within_7_points' and 'within_spread' columns
count_within_7_points = grouped_season['within_7_points'].value_counts().unstack().fillna(0).reset_index()
count_within_7_points['ratio'] = count_within_7_points[True] / (count_within_7_points[True] + count_within_7_points[False])
count_within_7_points = count_within_7_points[count_within_7_points['schedule_season'] >= 1979]
count_within_spread = grouped_season['within_spread'].value_counts().unstack().fillna(0).reset_index()
count_within_spread['ratio'] = count_within_spread[True] / (count_within_spread[True] + count_within_spread[False])
count_within_spread = count_within_spread[count_within_spread['schedule_season'] >= 1979]

fig = px.bar(count_within_7_points, x = 'schedule_season', y = 'ratio')
fig.update_layout(title = 'Percentage of games in season where the total falls within 3 points of the projected total')
fig.layout.yaxis.tickformat = ',.0%'
fig.show()


grouped_season_outcome = df.groupby(['schedule_season', 'outcome']).size().reset_index(name='count')
grouped_season_outcome = grouped_season_outcome[grouped_season_outcome['schedule_season'] >= 1979]
grouped_season_outcome['percentage'] = grouped_season_outcome.groupby('schedule_season')['count'].apply(lambda x: 100 * x / x.sum())

fig = px.area(grouped_season_outcome, x='schedule_season', y='percentage', color='outcome', title='Percentage of Outcome by Season')
fig.layout.yaxis.tickformat = ',.0%'
fig.show()

fig = px.histogram(df, x = 'spread_favorite', nbins=100, title='Most common spreads in the NFL, 1979 - present')
fig.show()

test = df.groupby(['weather_wind_mph'])['total'].mean().reset_index()
fig = px.scatter(test, x = 'weather_wind_mph', y = 'total', title = 'Average Total Score by Wind Velocity, Miles per Hour')
fig.update_layout(yaxis_range=[22, 50])
fig.show()

favorites_per_team = df.groupby(['favorite', 'is_huge_favorite'])['is_huge_favorite'].size().reset_index(name='counts')
favorites_per_team = favorites_per_team[favorites_per_team['is_huge_favorite'] == True]
fig = px.bar(favorites_per_team, x = 'favorite', y = 'counts', title = 'Number of times each team has been favored by at least two touchdowns, 1979 - present.')
fig.show()


favorites_per_team = df.groupby(['favorite', 'is_huge_favorite'])['favorite'].size().reset_index(name='counts')
fig = px.bar(favorites_per_team, x = 'favorite', y = 'counts', title = 'Number of times each team has been the pre-match favorite, 1979 - present.', color = 'is_huge_favorite')
fig.show()
