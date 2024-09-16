# AI Alpha

Full rest API for AI Alpha

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to iniciate the project.

1. Clone the repository.
2. Create a virtual environment and activate it:

- Windows:

```bash
python -m venv venv
```

- macOS:

```bash
python3 -m venv venv
```

3. Install project dependencies:

```bash
pip install -r requirements.txt
```

### Database Migrations
- Create a new migration:

```bash
alembic revision --autogenerate -m "Description of changes"
```

- Apply upgrades:

```bash
alembic upgrade head
```

- Perform downgrades:

```bash
alembic downgrade -1
```

## Database Migration Workflow

To manage database schema changes. Follow these steps to handle migrations effectively:

```bash
# Before starting work
git pull
alembic upgrade head

# After making model changes
alembic revision --autogenerate -m "description of changes"

# Before committing
git pull
alembic heads  # Check for multiple heads

# If multiple heads exist:
alembic merge -m "merge heads: a simple description of the revisions" <revision1> <revision2>
alembic upgrade head

# Test your changes
git add .
git commit -m "Database changes with merge"
git push
```

### WebSocket Events

- Event : subscribe_to_ohlc_data
- Description: Subscribes to OHLC (Open, High, Low, Close) data for a specified cryptocurrency. This event allows you to receive real-time updates on the OHLC data for the selected cryptocurrency.
- Parameters:

```bash
"coin": "bitcoin",
"vs_currency": "usd",
"interval": "1h",
"precision": 2
```

- Event : subscribe_to_top_movers
- Description: Subscribes to real-time updates for the top 10 gainers and top 10 losers based on specified criteria. This event provides information about the top-performing and worst-performing cryptocurrencies.
- Parameters:

```bash
"vs_currency": "usd",
"order": "market_cap_desc",
"precision": 2
```

## License

[MIT](https://choosealicense.com/licenses/mit/)