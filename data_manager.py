import services.utils
import services.bot_manager
import services.csv_manager
from services.table_manager import TableManager
from services.utils import config
from database.connection import Connection
from services.proxy_manager import ProxyManager

class DataManager:
    def __init__(self):
        self.session = None
        self.db_connection = Connection()

    def start_session(self):
        self.session = self.db_connection.get_session()

    def close_session(self):
        self.db_connection.close_session()

    def run_bot(self, country):
        importer = services.bot_manager.BotManager(
            session=self.session,
            target_url=country["url"],
            target_country=country["name"],
            fetch_min_delay=config.FETCH_MIN_DELAY,
            fetch_max_delay=config.FETCH_MAX_DELAY
        )
        importer.run_bot()
        print(f"Data for {country['name']} inserted.")

    def import_geo(self, country):
        importer = services.csv_manager.GeoImporter(
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

    def menu(self):
        proxy_manager = ProxyManager()
        table_manager = TableManager(session=self.session, db_connection=self.db_connection)
        
        menu_items = [
            ('Check Proxy IP', lambda: proxy_manager.check_ip()),
            ('Change Proxy IP', lambda: (proxy_manager.send_signal_newnym() if config.USE_PROXY else print("Change 'USE_PROXY=true' in config.json to use this service!"))),
            ('Create Table', lambda: table_manager.create_tables()),
            ('Drop All Table', lambda: table_manager.drop_all_tables()),
            ('Import SQL File', lambda: table_manager.import_sql_file()),
            ('Bot Data Tabular Transform', lambda: table_manager.tabular_transform()),
            ('Clear Bot Data Session', lambda: table_manager.clear_bot_data_session())
        ]
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