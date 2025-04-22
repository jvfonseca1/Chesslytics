import requests
import pandas as pd
import re
from datetime import datetime, timedelta

from config import NOTION_API_TOKEN, CHESS_USERNAME, CHESS_DATABASE_ID

def get_notion_database():
    try:
        url = f"https://api.notion.com/v1/databases/{CHESS_DATABASE_ID}/query"
        headers = {
            "Authorization": NOTION_API_TOKEN,
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }

        print(f"Extracting Notion Database")
        response = requests.post(url, headers=headers)
        if response.status_code != 200:
            raise Exception (f"Error getting database: {response.status_code}\n{response.content}")
        
        data = response.json()
        df = data['results']
        while data['has_more']:
            payload = {
                "start_cursor": data['next_cursor']
            }
            response = requests.post(url, headers=headers, json=payload)
            data = response.json()
            df.extend(data["results"])
        
        print(f"Found {len(df)} games in the database")
        return df

    except Exception as e:
        print(e)

def extract_year_month(url):
    parts = url.split('/')
    year = int(parts[-2])
    month = int(parts[-1])
    return (year, month)

def get_chess_data(full_scan: bool = False):
    try:
        print("Extracting chess data")
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
        response = requests.get(f"https://api.chess.com/pub/player/{CHESS_USERNAME}/games/archives", headers=headers)
        if response.status_code != 200:
            raise Exception (f"Error getting archived games: {response.status_code}\n{response.content}")
        months = sorted(response.json()['archives'], key=extract_year_month, reverse=True)

        if full_scan == False:
            months = [months[0]]
        print(f"Found {len(months)} months to go through")
        
        data = {
            'uuid': str,
            'date': str,
            'opening': str,
            'opponent': str,
            'result': str,
            'type': str
        }

        inserts = []
        
        for month in months:
            print(f"Analyzing Month:\n{month}")
            response = requests.get(month, headers=headers)
            if response.status_code != 200:
                raise Exception (f"Error getting game: {response.status_code}\n{response.content}")
            games = response.json()['games']

            for game in games:
                game_date = re.search(r'\[Date\s+"(\d{4}\.\d{2}\.\d{2})"\]', game['pgn']).group(1)

                if full_scan or game_date == (datetime.now() - timedelta(days=1)).strftime('%Y.%m.%d'):
                    white_username = str(game['white']['username']).lower()
                    print(f"Exporting:\n{game}")
                    data['uuid'] = game['uuid']
                    data['date'] = game_date
                    data['opening'] = game['eco']
                    data['opponent'] = game['black' if CHESS_USERNAME == white_username else 'white']['username']
                    data['result'] = game['white' if CHESS_USERNAME == white_username else 'black']['result']
                    data['type'] = f"{game['rules']} - {game['time_class']}"

                    inserts.append(data.copy())

        return inserts
    except Exception as e:
        print(e)

def insert_games_to_notion(games_to_be_inserted):
    try:
        print("Inserting games to Notion")
        url = f"https://api.notion.com/v1/pages"
        headers = {
            "Authorization": NOTION_API_TOKEN,
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }

        for game in games_to_be_inserted:
            payload = {
                "parent": {
                    "database_id": CHESS_DATABASE_ID
                },
                "properties": {
                    "uuid": {
                        "title": [
                            {
                                "text": {
                                    "content": game['uuid']
                                }
                            }
                        ]
                    },
                    "date": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": game['date']
                                }
                            }
                        ]
                    },
                    "opening": {
                        "url": game['opening']
                    },
                    "opponent": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": game['opponent']
                                }
                            }
                        ]
                    },
                    "result": {
                        "select": {
                                "name": game['result']
                            }
                    },
                    "type": {
                        "select": {
                                "name": game['type']
                            }
                    }
                }
            }

            response = requests.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                raise Exception (f"Error inserting game: {response.status_code}\n{response.content}")
            print(f"Inserted:\n{game}")
    except Exception as e:
        print(e)


def main():
    try:
        df = get_notion_database()
        
        full_scan = False
        if len(df) == 0:
            full_scan = True
        
        games_to_be_inserted = get_chess_data(full_scan)

        insert_games_to_notion(games_to_be_inserted)
    except Exception as e:
        print(e)

main()