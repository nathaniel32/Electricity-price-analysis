import services.utils
import services.manage_proxy
import services.data_insert
import services.geo_insert
from services.utils import config
from database.connection import Connection
from sqlalchemy import text

class DataManager:
    def __init__(self):
        self.db_connection = Connection()
        self.session = None

    def start_session(self):
        self.session = self.db_connection.get_session()

    def close_session(self):
        self.db_connection.close_session()

    def create_tables(self):
        self.db_connection.create_tables()

    def run_sql_file(self):
        filepath = input("File Path: ").strip()
        print()

        try:
            with open(filepath, 'r') as file:
                sql_commands = file.read()
        except FileNotFoundError:
            print("File not found!")
            return
        
        try:
            self.session.execute(text(sql_commands))
            self.session.commit()
            print("SQL file executed successfully.")
        except Exception as e:
            self.session.rollback()
            print(f"Error: {e}")

    def drop_all_tables(self):
        drop_fks = """
        DECLARE @sql NVARCHAR(MAX) = N'';

        SELECT @sql += 'ALTER TABLE ' + QUOTENAME(s.name) + '.' + QUOTENAME(t.name) 
            + ' DROP CONSTRAINT ' + QUOTENAME(fk.name) + ';' + CHAR(13)
        FROM sys.foreign_keys fk
        JOIN sys.tables t ON fk.parent_object_id = t.object_id
        JOIN sys.schemas s ON t.schema_id = s.schema_id;

        EXEC sp_executesql @sql;
        """

        # Drop all tabel
        drop_tables = """
        DECLARE @sql NVARCHAR(MAX) = N'';

        SELECT @sql += 'DROP TABLE ' + QUOTENAME(s.name) + '.' + QUOTENAME(t.name) + ';' + CHAR(13)
        FROM sys.tables t
        JOIN sys.schemas s ON t.schema_id = s.schema_id;

        EXEC sp_executesql @sql;
        """

        self.session.execute(text(drop_fks))
        self.session.execute(text(drop_tables))
        self.session.commit()

    def fetch_and_save_data(self, country):
        importer = services.data_insert.DataImporter(
            session=self.session,
            target_url=country["url"],
            target_country=country["name"],
            fetch_min_delay=config.FETCH_MIN_DELAY,
            fetch_max_delay=config.FETCH_MAX_DELAY
        )
        importer.fetch_and_insert()
        print(f"Data for {country['name']} inserted.")

    def load_geographic_data(self, country):
        importer = services.geo_insert.GeoImporter(
            session=self.session,
            csv_path=country["csv"],
            sep=country["sep"],
            country_name=country["name"],
            province_header=country["province"],
            city_header=country["city"],
            additional_header=country["additional"],
            postal_code_header=country["postal"]
        )
        importer.load_and_insert()
        print(f"Geographic data for {country['name']} inserted.")

    def run(self):
        self.start_session()
        while True:
            print("\n================= MENU =================")
            print("1. Check Proxy IP")
            print("2. Change Proxy IP")
            print("2a. Create Table")
            print("2b. Drop All Table")
            print("2c. Import Data")
            print("=" * 40)
            for i, country in enumerate(config.COUNTRY_CONFIG, start=3):
                print(f"{i}. Fetch and Save Data ({country['name']})")
            print("=" * 40)
            for i, country in enumerate(config.COUNTRY_CONFIG, start=7):
                print(f"{i}. Insert Geographic Data ({country['name']})")
            print("=" * 40)
            print(f"{7 + len(config.COUNTRY_CONFIG)}. Exit")

            choice = input("Input: ").strip()
            print()

            if choice == '1':
                services.utils.check_ip()
            elif choice == '2':
                if config.USE_PROXY:
                    services.manage_proxy.send_signal_newnym()
                else:
                    print("Change 'USE_PROXY=true' in config.json to use this service!")
            elif choice == '2a':
                self.create_tables()
            elif choice == '2b':
                self.drop_all_tables()
            elif choice == '2c':
                self.run_sql_file()
            elif choice in map(str, range(3, 3 + len(config.COUNTRY_CONFIG))):
                index = int(choice) - 3
                self.fetch_and_save_data(config.COUNTRY_CONFIG[index])
            elif choice in map(str, range(7, 7 + len(config.COUNTRY_CONFIG))):
                index = int(choice) - 7
                self.load_geographic_data(config.COUNTRY_CONFIG[index])
            elif choice == str(7 + len(config.COUNTRY_CONFIG)):
                break
            else:
                print("Invalid input!")

        self.close_session()

if __name__ == "__main__":
    app = DataManager()
    app.run()