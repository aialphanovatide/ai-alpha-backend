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
- We use Alembic for database migrations. Follow these steps to manage database schema changes:

```bash
alembic init alembic
```

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