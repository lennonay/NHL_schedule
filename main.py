import pandas as pd
import numpy as np
import sys 

def get_team_abrv(schedule, team):
    team_lst = np.array(np.sort(schedule['Home'].unique()))
    abrv_lst = np.array(np.sort(team['name'].unique()))
    
    abrv_lst[5], abrv_lst[4]  = abrv_lst[4], abrv_lst[5]
    abrv_lst[8], abrv_lst[4]  = abrv_lst[4], abrv_lst[8]
    abrv_lst[7], abrv_lst[4]  = abrv_lst[4], abrv_lst[7]
    abrv_lst[6], abrv_lst[4]  = abrv_lst[4], abrv_lst[6]
    abrv_lst[17], abrv_lst[16]  = abrv_lst[16], abrv_lst[17]
    abrv_lst[24], abrv_lst[23]  = abrv_lst[23], abrv_lst[24]
    abrv_lst[31], abrv_lst[30]  = abrv_lst[30], abrv_lst[31]
    
    team_abrv = pd.DataFrame({'Team':team_lst,'Abrv':abrv_lst})
    
    return team_abrv

def get_full_schedule(schedule, team_abrv):
    ver1 = schedule.copy()
    ver2 = schedule.copy()

    ver1 = ver1.merge(team_abrv, left_on='Away', right_on= 'Team')
    ver1 = ver1[['Date', 'Home', 'Abrv']]
    ver1 = ver1.rename(columns={'Home':'Team1','Abrv':'Team2'})
    ver1['Team2'] = '@ ' + ver1['Team2']

    ver2 = ver2.merge(team_abrv, left_on='Home', right_on= 'Team')
    ver2 = ver2[['Date','Away', 'Abrv']]
    ver2 = ver2.rename(columns={'Away':'Team1','Abrv':'Team2'})
    ver2['Team2'] = 'vs ' + ver2['Team2']
    ver2.head()

    full_schedule = pd.concat([ver1,ver2],ignore_index=True)
    full_schedule['Date'] = pd.to_datetime(full_schedule['Date']).dt.date

    return full_schedule

def get_week_schedule(full_schedule, week_num):
    date_start = pd.date_range(full_schedule['Date'].min(), full_schedule['Date'].max(), freq='W-MON')
    
    if (week_num > len(date_start) or week_num < 1):
        sys.exit("Week number should be in range 1 and {}".format(len(date_start)))  
    
    current_week = date_start[week_num]
    current_week_end = date_start[week_num + 1]

    mask = (full_schedule['Date'] >= current_week) & (full_schedule['Date'] < current_week_end)

    week_mask = full_schedule[mask]

    week_table = week_mask.pivot_table(index = 'Team1', columns= 'Date', values = 'Team2', aggfunc='first')

    return week_table

def get_schedule_strength(week_table, team):
    week_table['game_count']=week_table.count(axis = 1)
    week_table = week_table.reset_index()
    week_table['Opponent_Score'] = 0

    team_all = team[team['situation'] == 'all']
    team_all['xGoalsPercentage'] = team_all['xGoalsFor']/(team_all['xGoalsAgainst'] + team_all['xGoalsFor'])
    team_all = team_all[['team','xGoalsPercentage']]

    for i in range(1, 8):
        week_table['opp'] = week_table[week_table.columns[i]].str.split(' ').str[1]
        week_table = week_table.merge(team_all, left_on= 'opp', right_on= 'team', how = 'left')
        week_table['xGoalsPercentage'] = week_table['xGoalsPercentage'].fillna(1)
        week_table['xGoalsPercentage'] = 1 - week_table['xGoalsPercentage']
        week_table['Opponent_Score'] = week_table['Opponent_Score'] + week_table['xGoalsPercentage'] 
        week_table = week_table.drop(columns=['team','xGoalsPercentage','opp'])
    
    return week_table


if __name__ == "__main__":
    schedule = pd.read_csv('data/2022_2023_NHL_Schedule.csv', names=['Date','Time','Home','Away'])
    schedule = schedule[['Date', 'Home','Away']]
    team = pd.read_csv('data/teams.csv')
    
    week_num = 23

    team_abrv = get_team_abrv(schedule, team)

    full_schedule = get_full_schedule(schedule, team_abrv)

    week_schedule = get_week_schedule(full_schedule, week_num)

    week_strength_schedule = get_schedule_strength(week_schedule, team)

    week_strength_schedule= week_strength_schedule.sort_values('Opponent_Score',ascending=False)

    week_strength_schedule.style.background_gradient(axis = None, subset = ['Opponent_Score']).to_html('week_strength_schedule.html')

    print(week_strength_schedule)