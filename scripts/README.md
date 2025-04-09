# Database Setup Scripts

This directory contains scripts for database management and setup.

## Setup Database

The `setup_db.py` script provides commands to initialize and verify the database:

### Initialize Database

```bash
# Create new database and run migrations
python scripts/setup_db.py init

# Drop existing database, create new one, and run migrations
python scripts/setup_db.py init --drop-existing
```

### Verify Database

```bash
# Verify database connection and check existing tables
python scripts/setup_db.py verify
```

## Environment Variables

Make sure to set up your `.env` file with the correct database URL:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/rag_db
```

## Error Handling

The script will:
1. Create the database if it doesn't exist
2. Run all migrations
3. Verify the database schema
4. Provide detailed error messages if anything fails
