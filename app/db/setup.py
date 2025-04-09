import asyncio
import logging
from typing import Optional
import typer
import asyncpg
from app.core.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Typer app
cli = typer.Typer(help="Database management CLI")
settings = get_settings()


async def create_database(database_name: str) -> None:
    """Create PostgreSQL database if it doesn't exist."""
    # Parse connection parameters from URL
    conn_params = asyncpg.URLParser.parse(settings.DATABASE_URL)
    
    # Create connection URL without specific database
    base_url = f"postgresql://{conn_params['user']}:{conn_params['password']}@{conn_params['host']}:{conn_params['port']}/postgres"
    
    try:
        # Connect to default postgres database
        conn = await asyncpg.connect(base_url)
        
        # Check if database exists
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            database_name
        )
        
        if not exists:
            # Create database if it doesn't exist
            await conn.execute(f'CREATE DATABASE "{database_name}"')
            logger.info(f"Created database: {database_name}")
        else:
            logger.info(f"Database already exists: {database_name}")
            
    except Exception as e:
        logger.error(f"Error creating database: {str(e)}")
        raise
    finally:
        await conn.close()


async def setup_database(drop_existing: bool = False) -> None:
    """Set up the database and run migrations."""
    try:
        # Parse database name from URL
        db_name = asyncpg.URLParser.parse(settings.DATABASE_URL)["database"]
        
        if drop_existing:
            # Connect to postgres database to drop existing database
            conn_params = asyncpg.URLParser.parse(settings.DATABASE_URL)
            base_url = f"postgresql://{conn_params['user']}:{conn_params['password']}@{conn_params['host']}:{conn_params['port']}/postgres"
            conn = await asyncpg.connect(base_url)
            
            # Terminate existing connections
            await conn.execute(f'''
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{db_name}'
                AND pid <> pg_backend_pid()
            ''')
            
            # Drop database if it exists
            await conn.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
            await conn.close()
            logger.info(f"Dropped existing database: {db_name}")
        
        # Create fresh database
        await create_database(db_name)
        
        # Run alembic migrations
        from alembic.config import Config
        from alembic import command
        
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        logger.info("Successfully applied all migrations")
        
    except Exception as e:
        logger.error(f"Error setting up database: {str(e)}")
        raise


@cli.command()
def init(
    drop_existing: bool = typer.Option(
        False,
        "--drop-existing",
        "-d",
        help="Drop existing database before creating new one"
    )
) -> None:
    """Initialize the database and run migrations."""
    try:
        asyncio.run(setup_database(drop_existing))
        logger.info("Database setup completed successfully")
    except Exception as e:
        logger.error(f"Database setup failed: {str(e)}")
        raise typer.Exit(1)


@cli.command()
def verify() -> None:
    """Verify database connection and schema."""
    async def _verify() -> None:
        try:
            conn = await asyncpg.connect(settings.DATABASE_URL)
            
            # Check if tables exist
            tables = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            
            logger.info("Connected to database successfully")
            logger.info("Found tables: %s", ", ".join(t["table_name"] for t in tables))
            
            await conn.close()
        except Exception as e:
            logger.error(f"Database verification failed: {str(e)}")
            raise
    
    try:
        asyncio.run(_verify())
    except Exception:
        raise typer.Exit(1)


if __name__ == "__main__":
    cli()
