# VoiceProject

Clone Voice and Reproduce Text while the sentiment analysis is calculated at the same time.

## Quick Start

1. Install [PostgreSQL](https://www.postgresql.org/download/) and create the database (see [Database Setup](#database-setup)).
2. Copy `.env.example` to `.env` and fill in your API keys and `DB_PASSWORD`.
3. Install dependencies: `pip install -r requirements.txt`
4. Run the server: `python app.py`
5. Open `http://localhost:5000` — you'll be redirected to the login page.

## Database Setup

See the detailed guide in [`docs/arquitectura.md`](docs/arquitectura.md#6-base-de-datos--postgresql) or follow the quick steps:

```bash
# 1. Install PostgreSQL (if not already installed)
#    Windows: https://www.postgresql.org/download/windows/
#    macOS:   brew install postgresql@16
#    Linux:   sudo apt install postgresql

# 2. Create the database and user
psql -U postgres -c "CREATE USER edcastr WITH PASSWORD '12345aB.';"
psql -U postgres -c "CREATE DATABASE \"VoiceProject\" OWNER edcastr;"
psql -U postgres -d VoiceProject -c "GRANT ALL ON SCHEMA public TO edcastr;"

# 3. Create the tables
psql -U edcastr -d VoiceProject -f sql/create_tables.sql

# 4. Add DB_PASSWORD to your .env file
echo DB_PASSWORD=12345aB. >> .env
```

## Documentation

- **[`docs/arquitectura.md`](docs/arquitectura.md)** — System architecture, database schema, components, data flows.
- **[`docs/apis_y_paginas.md`](docs/apis_y_paginas.md)** — API reference, page guides, environment variables.
