import services.utils
import services.bot
import services.geo_insert
import services.data_transform
from services.utils import config
from database.connection import Connection
from sqlalchemy import text
import sqlparse
import database.models

class DataManager:
    def __init__(self):
        self.session = None
        self.db_connection = Connection()
        self.menu_items = [
            ('Check Proxy IP', lambda: services.utils.check_ip()),
            ('Change Proxy IP', lambda: (services.utils.send_signal_newnym() if config.USE_PROXY else print("Change 'USE_PROXY=true' in config.json to use this service!"))),
            ('Create Table', lambda: self.create_tables()),
            ('Drop All Table', lambda: self.drop_all_tables()),
            ('Import Data', lambda: self.import_sql()),
            ('Data Transform', lambda: self.tranform_data()),
            ('Clean pa_data', lambda: self.bot_data_session_init())
        ]

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
        
    def import_sql(self):
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

    def bot_data_session_init(self):
        print("Cleaning up pa_data...")
        """ for obj in self.session.query(database.models.TPostalArea).all():
            obj.pa_data = None
            obj.pa_status_code = None """
        try:
            query = """
                UPDATE t_postal_area
                SET pa_status_code = NULL,
                    pa_data = NULL;
            """
            self.session.execute(text(query))
            self.session.commit()
            print("pa_data cleanup complete.")
        except Exception as e:
            self.session.rollback()
            print(f"Cleanup failed: {e}")
            raise

    def run_bot(self, country):
        importer = services.bot.BotManager(
            session=self.session,
            target_url=country["url"],
            target_country=country["name"],
            fetch_min_delay=config.FETCH_MIN_DELAY,
            fetch_max_delay=config.FETCH_MAX_DELAY
        )
        importer.run_bot()
        print(f"Data for {country['name']} inserted.")

    def import_geo(self, country):
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
        importer.import_geo()
        print(f"Geographic data for {country['name']} inserted.")

    def tranform_data(self):
        data_transform = services.data_transform.DataTransform(session=self.session)
        data_transform.transform()

    def menu(self):
        start_auto_menu = len(self.menu_items)+1

        while True:
            print("\n================= MENU =================")
            for i, (label, _) in enumerate(self.menu_items):
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
                self.menu_items[index][1]()
            elif choice in map(str, range(start_auto_menu, start_auto_menu + len(config.COUNTRY_CONFIG))):
                index = int(choice) - start_auto_menu
                self.run_bot(config.COUNTRY_CONFIG[index])
            elif choice in map(str, range(len(config.COUNTRY_CONFIG)+start_auto_menu, start_auto_menu + 2 * len(config.COUNTRY_CONFIG))):
                index = int(choice) - (len(config.COUNTRY_CONFIG)+start_auto_menu)
                self.import_geo(config.COUNTRY_CONFIG[index])
            elif choice == str(start_auto_menu + 2 * len(config.COUNTRY_CONFIG)):
                break
            else:
                print("Invalid input!")

if __name__ == "__main__":
    app = DataManager()
    app.start_session()
    app.menu()
    app.close_session()