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

## License

[MIT](https://choosealicense.com/licenses/mit/)