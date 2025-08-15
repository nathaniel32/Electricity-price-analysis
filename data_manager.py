import services.utils
import services.manage_proxy
import services.data_insert
import services.geo_insert
import services.data_transform
from services.utils import config
from database.connection import Connection
from sqlalchemy import text
import sqlparse

class DataManager:
    def __init__(self):
        self.db_connection = Connection()
        self.session = None

    def start_session(self):
        self.session = self.db_connection.get_session()

    def close_session(self):
        self.db_connection.close_session()

    def create_tables(self):
        try:
            self.db_connection.create_tables()
            print("All tables created successfully.")
        except Exception as e:
            print(f"Failed to create tables: {e}")
        
    def run_sql_file(self):
        while True:
            filepath = input("File Path (or type 'exit' to quit): ").strip().strip('"').strip("'")
            if filepath.lower() == 'exit':
                print("Exiting.")
                break
            if not filepath:
                continue

            try:
                with open(filepath, 'r', encoding='utf-8-sig') as file:
                    sql_commands = file.read()
            except FileNotFoundError:
                print("File not found!")
                continue

            statements = sqlparse.split(sql_commands)
            success_count = 0
            error_count = 0

            for stmt in statements:
                stmt = stmt.strip()
                if not stmt:
                    continue
                try:
                    self.session.execute(text(stmt))
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    print("=" * 40)
                    print("Error executing statement:")
                    print(stmt[:500])
                    print(f"🔺 Error: {str(e)[:500]}")
                    print("=" * 40)

            try:
                self.session.commit()
            except Exception as e:
                print("Commit failed. Rolling back.")
                self.session.rollback()
                print(str(e)[:500])
                continue

            print(f"\nDone. {success_count} statements executed successfully. {error_count} failed.\n")

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

        drop_tables = """
        DECLARE @sql NVARCHAR(MAX) = N'';

        SELECT @sql += 'DROP TABLE ' + QUOTENAME(s.name) + '.' + QUOTENAME(t.name) + ';' + CHAR(13)
        FROM sys.tables t
        JOIN sys.schemas s ON t.schema_id = s.schema_id;

        EXEC sp_executesql @sql;
        """

        try:
            self.session.execute(text(drop_fks))
            self.session.execute(text(drop_tables))
            self.session.commit()
            print("All tables dropped successfully.")
        except Exception as e:
            self.session.rollback()
            print(f"Failed to drop tables: {e}")

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
            country_vat=country["vat"],
            country_currency=country["currency"],
            province_header=country["province"],
            city_header=country["city"],
            additional_header=country["additional"],
            postal_code_header=country["postal"]
        )
        importer.load_and_insert()
        print(f"Geographic data for {country['name']} inserted.")

    def run(self):
        menu_items = [
            ('Check Proxy IP', lambda: services.utils.check_ip()),
            ('Change Proxy IP', lambda: (services.manage_proxy.send_signal_newnym() if config.USE_PROXY else print("Change 'USE_PROXY=true' in config.json to use this service!"))),
            ('Create Table', lambda: self.create_tables()),
            ('Drop All Table', lambda: self.drop_all_tables()),
            ('Import Data', lambda: self.run_sql_file()),
            ('Data Transform', lambda: data_transform.transform())
        ]

        self.start_session()
        data_transform = services.data_transform.DataTransform(session=self.session)
        start_auto_menu = len(menu_items)+1

        while True:
            print("\n================= MENU =================")
            for i, (label, _) in enumerate(menu_items):
                print(f"{i+1}. {label}")
            
            print("=" * 40)
            for i, country in enumerate(config.COUNTRY_CONFIG, start=start_auto_menu):
                print(f"{i}. Fetch and Save Data ({country['name']})")
            
            print("=" * 40)
            for i, country in enumerate(config.COUNTRY_CONFIG, start=len(config.COUNTRY_CONFIG) + start_auto_menu):
                print(f"{i}. Insert Geographic Data ({country['name']})")
            
            print("=" * 40)
            print(f"{start_auto_menu + 2 * len(config.COUNTRY_CONFIG)}. Exit")

            choice = input("Input: ").strip()
            print()

            if int(choice) < start_auto_menu:
                index = int(choice) - 1
                menu_items[index][1]()
            elif choice in map(str, range(start_auto_menu, start_auto_menu + len(config.COUNTRY_CONFIG))):
                index = int(choice) - start_auto_menu
                self.fetch_and_save_data(config.COUNTRY_CONFIG[index])
            elif choice in map(str, range(len(config.COUNTRY_CONFIG)+start_auto_menu, start_auto_menu + 2 * len(config.COUNTRY_CONFIG))):
                index = int(choice) - (len(config.COUNTRY_CONFIG)+start_auto_menu)
                self.load_geographic_data(config.COUNTRY_CONFIG[index])
            elif choice == str(start_auto_menu + 2 * len(config.COUNTRY_CONFIG)):
                break
            else:
                print("Invalid input!")

        self.close_session()

if __name__ == "__main__":
    app = DataManager()
    app.run()