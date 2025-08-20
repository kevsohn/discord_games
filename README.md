Activate Virtual Env:

source <venv>/bin/activate


Discord Bot: 
    
    python3 discord_games/bot.py

Backend Server (Flask): 
    
    python3 discord_games/server.py

Postgresql (psycopg2): 
    
    Start:
        brew services start postgresql    
        pg_isready -h localhost -p 5432  -> to check if accepting connections
    
    Create DB:
        psql -U $(whoami) -h localhost -d postgres
        
        CREATE DATABASE <db>;
        \q
        
        psql -U $(whoami) -h localhost -d <db>

    List All DBs:
        \l

    Check All Tables:
        \c <db>     -> to make sure we're in the right db
        \dt         -> list tables
        \d <table>  -> inspect table

    Create User (optional):
        CREATE USER <user> WITH PASSWORD '<pwd>';
        GRANT ALL PRIVILEGES ON DATABASE <db> TO <user>;
        \q

        psql -U <user> -d <db> -h localhost -W

    Check Data Storage Location:
        psql -U $(whoami) -h localhost -d postgres
        
        SHOW data_directory;


Possible Improvements:
    
    1) Use Django instead of Flask if production focussed, espcially with the ORM feature making it easier to swap the DB without having to rewrite DB-specific code.

    2) Use Redis (use redislite?) + some DB to have quicker access to real-time stats like leaderboards since Redis is a RAM-based key-value store that can be deployed on a remote machine (unlike a dict local to the program), and the DB provides the backup/permanent storage.
    
    3) Think about either dockerizing the setup and deploying on a VM or offloading the DB+Redis combo to a cloud provider
