from config import CHESS_USERNAME, CHESS_DATABASE_NAME, POSTGRES_DB_CONN
from database import connect_to_database, check_existing_table
from tasks.chesscom import populate_chess_games_database

def main():
    try:
        conn = connect_to_database(
            host= POSTGRES_DB_CONN['HOST'],
            database= POSTGRES_DB_CONN['DB'],
            user= POSTGRES_DB_CONN['USER'],
            password= POSTGRES_DB_CONN['PASSWORD']
        )

        exists = check_existing_table(conn, CHESS_DATABASE_NAME)

        populate_chess_games_database(conn, exists, CHESS_USERNAME, CHESS_DATABASE_NAME)

    except Exception as e:
        print(e)
    finally:
        conn.close()

if __name__ == "__main__":
    main()