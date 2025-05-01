import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values
import requests
import re

def extract_year_month(url):
    parts = url.split('/')
    year = int(parts[-2])
    month = int(parts[-1])
    return (year, month)

def populate_chess_games_database(conn: psycopg2.extensions.connection, exists: bool, chess_username: str, chess_database_name: str):
    try: 
        cur = conn.cursor()
        if not exists:
            cur.execute("""
                CREATE TABLE %s (
                    uuid VARCHAR(255) PRIMARY KEY,
                    date DATE NOT NULL,
                    opening VARCHAR(255),
                    opponent VARCHAR(255) NOT NULL,
                    result VARCHAR(255) NOT NULL,
                    type VARCHAR(255) NOT NULL,
                    color VARCHAR(255) NOT NULL
                )
            """, chess_database_name)
            conn.commit()
            print("Table created successfully!")
        
        print("Extracting chess data")
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
        response = requests.get(f"https://api.chess.com/pub/player/{chess_username}/games/archives", headers=headers)
        if response.status_code != 200:
            raise Exception (f"Error getting archived games: {response.status_code}\n{response.content}")
        months = sorted(response.json()['archives'], key=extract_year_month, reverse=True)

        if exists:
            months = [months[0]]
        print(f"Found {len(months)} months to go through")
        
        data = {
            'uuid': str,
            'date': str,
            'opening': str,
            'opponent': str,
            'result': str,
            'type': str,
            'color': str
        }

        inserts = []
        
        for month in months:
            print(f"Analyzing Month:\n{month}")
            response = requests.get(month, headers=headers)
            if response.status_code != 200:
                raise Exception (f"Error getting game: {response.status_code}\n{response.content}")
            games = response.json()['games']

            for game in games:
                print(f"Exporting:\n{game}")
                white_username = str(game['white']['username']).lower()
                eco = re.search(r'(?<=\[ECOUrl\s").*?(?=")', game['pgn'])
                
                data['uuid'] = game['uuid']
                data['date'] = re.search(r'\[Date\s+"(\d{4}\.\d{2}\.\d{2})"\]', game['pgn']).group(1)
                data['opening'] = eco.group(0) if eco else None
                data['opponent'] = game['black' if chess_username == white_username else 'white']['username']
                data['result'] = game['white' if chess_username == white_username else 'black']['result']
                data['type'] = f"{game['rules']} - {game['time_class']}"
                data['color'] = 'white' if chess_username == white_username else 'black'

                inserts.append(data.copy())
            
        insert_sql = """
            INSERT INTO {} (uuid, date, opening, opponent, result, type, color)
            VALUES %s
            ON CONFLICT (uuid) DO NOTHING
        """.format(chess_database_name)
        values = [(i['uuid'], i['date'], i['opening'], i['opponent'], i['result'], i['type'], i['color']) for i in inserts]

        execute_values(cur, insert_sql, values)
        conn.commit()

    except Exception as e:
        print(f"Error while populating chess games database: \n{e}")
        conn.rollback()
    finally:
        cur.close()