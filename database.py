import psycopg2

def connect_to_database(host: str, user: str, database: str, password: str):
    try:
        conn = psycopg2.connect(
            host=host,
            user=user,
            database=database,
            password=password
        )

        return conn
    except Exception as e:
        print(f"Error while getting DB connection: {e}")

def check_existing_table(conn: psycopg2.extensions.connection, table_name: str) -> bool:
    try:
        print(f"Checking if table {table_name} exists")
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT EXISTS(
                SELECT * FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name  = %s
            )
        """, (table_name,))
        exists = cursor.fetchone()[0]
        
        return exists
    except Exception as e:
        print(f"Error while checking existing table: {e}")
    finally:
        cursor.close()