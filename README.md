
## Electricity-price-analysis

### Setup

This project uses a PostgreSQL database.

Create a `config.json` file in the root of your project with your database credentials:

```json
{
    "DB_USERNAME": "",
    "DB_PASSWORD": "",
    "DB_DATABASE": "",
    "PROXIES": {
        "http": "socks5h://127.0.1.0:9050",
        "https": "socks5h://127.0.1.0:9050"
    },
    "PROXY_SETTING_IP": "127.0.1.0",
    "PROXY_SETTING_PORT": 9051,
    "FETCH_HEADER": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
}
```

* **`geo_insert.py`** — inserts location data from CSV into your database
* **`data_insert.py`** — fetches electricity price data and updates your database


### Database Schema
![Database Schema](data/schema.png)