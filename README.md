
## Electricity-price-analysis

### Setup

This project uses a PostgreSQL database.

Create a `config.json` file in the root of your project with your database credentials:

```json
{
    "DB_USERNAME": "your_db_username",
    "DB_PASSWORD": "your_db_password",
    "DB_DATABASE": "your_database_name"
}
```

* **`geo_insert.py`** — inserts location data from CSV into your database
* **`data_insert.py`** — fetches electricity price data and updates your database


### Database Schema
![Database Schema](data/schema.png)