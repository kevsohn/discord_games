Discord Bot: 
    
    python3 discord_games/bot/main.py

Backend Server (Flask): 
    
    python3 discord_games/server.py

Postgresql (psycopg2): 
    
    Start:
        brew services start postgresql    
    
    Create DB + User:
        sudo -i -u postgres
        psql
        
        CREATE DATABASE <db;
        CREATE USER <user> WITH PASSWORD '<pwd>';
        GRANT ALL PRIVILEGES ON DATABASE <db> TO <user>;

        psql -U <user> -d <db> -h localhost -W

    Check Location of Data:
        sudo -i -u postgres
        psql
        
        SHOW data_directory;


Possible Improvements:
    
    1) Use Django instead of Flask if production focussed, espcially with the ORM feature making it easier to swap the DB without having to rewrite DB-specific code.

    2) Use Redis (use redislite?) + some DB to have quicker access to real-time stats like leaderboards since Redis is a RAM-based key-value store that can be deployed on a remote machine (unlike a dict local to the program), and the DB provides the backup/permanent storage.
    
    3) Think about either dockerizing the setup and deploying on a VM or offloading the DB+Redis combo to a cloud provider
