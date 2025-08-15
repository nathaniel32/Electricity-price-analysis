
## Electricity-price-analysis

### Setup

This project uses a MSSQL database.

Create a `config.json` and `.env` files in the root of your project with your database credentials:

```json
{
    "USE_PROXY": false,
    "PROXIES": {
        "http": "socks5h://127.0.1.0:9050",
        "https": "socks5h://127.0.1.0:9050"
    },
    "IP_CHECK_URL": "http://httpbin.org/ip",
    "PROXY_SETTING_IP": "127.0.1.0",
    "PROXY_SETTING_PORT": 9051,
    "FETCH_HEADER": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Accept": "application/json"
    },
    "FETCH_MIN_DELAY": 0,
    "FETCH_MAX_DELAY": 0,
    "COUNTRY_CONFIG": [
        {
            "name": "Deutschland",
            "vat": 0.19,
            "currency": 1,
            "url": "https://example.com/de/api/lookup/price-overview?postalCode=",
            "csv": "data/csv/deutschland.csv",
            "sep": ";",
            "province": "Bundesland",
            "city": "Ort",
            "additional": "Zusatz",
            "postal": "Plz"
        },
        {
            "name": "Niederlande",
            "vat": 0.21,
            "currency": 1,
            "url": "https://example.com/nl/api/lookup/price-overview?postalCode=",
            "csv": "data/csv/niederlande.csv",
            "sep": ",",
            "province": "state",
            "city": "place",
            "additional": null,
            "postal": "zipcode"
        },
        {
            "name": "Schweden",
            "vat": 0.25,
            "currency": 0.090,
            "url": "https://example.com/se/api/lookup/price-overview?postalCode=",
            "csv": "data/csv/schweden.csv",
            "sep": ",",
            "province": "state",
            "city": "place",
            "additional": null,
            "postal": "zipcode"
        },
        {
            "name": "Norwegen",
            "vat": 0.25,
            "currency": 0.084,
            "url": "https://example.com/no/api/lookup/price-overview?postalCode=",
            "csv": "data/csv/norwegen.csv",
            "sep": ",",
            "province": "state",
            "city": "place",
            "additional": null,
            "postal": "zipcode"
        }
    ],
    "DATE_COMPONENTS_CONFIG": [
        "yesterdayHours", "todayHours"
    ],
    "PRICE_COMPONENTS_CONFIG": [
        {
            "name": "energy taxes",
            "alias": ["taxes", "energy tax"]
        },
        {
            "name": "power",
            "alias": ["power"]
        },
        {
            "name": "grid",
            "alias": ["grid"]

        },
        {
            "name": "certificate",
            "alias": ["energy certificate"]

        }
    ]
}
```

```
DB_USERNAME=sa
DB_PASSWORD=XXXXXX
DB_DATABASE=strom_db
DB_HOSTNAME=localhost
DB_PORT=1433
```

* OBBC: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server?view=sql-server-ver17
* Download data: https://drive.google.com/file/d/1iC9gfp8QR5jIfHB3BdzIk3jx-BzsmfTq/view?usp=sharing

### Run
1. docker-compose up -d
2. py data_manager.py

### Database Schema
![Database Schema](data/img/schema.png)