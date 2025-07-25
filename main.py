import services.utils
import services.manage_proxy
import services.data_insert
import services.geo_insert
from services.utils import config

def fetch_and_save_data(country):
    importer = services.data_insert.DataImporter(
        target_url=country["url"],
        target_country=country["name"],
        fetch_min_delay=config.FETCH_MIN_DELAY,
        fetch_max_delay=config.FETCH_MAX_DELAY
    )
    importer.fetch_and_insert()
    importer.close()
    print(f"Data for {country['name']} inserted.")

def load_geographic_data(country):
    importer = services.geo_insert.GeoImporter(
        csv_path=country["csv"],
        sep=country["sep"],
        country_name=country["name"],
        province_header=country["province"],
        city_header=country["city"],
        additional_header=country["additional"],
        postal_code_header=country["postal"]
    )
    importer.load_and_insert()
    importer.close()
    print(f"Geographic data for {country['name']} inserted.")

def main():
    while True:
        print("\n================= MENU =================")
        print("1. Check Proxy IP")
        print("2. Change Proxy IP")
        print("=" * 40)
        for i, country in enumerate(config.COUNTRY_CONFIG, start=3):
            print(f"{i}. Fetch and Save Data ({country['name']})")
        print("=" * 40)
        for i, country in enumerate(config.COUNTRY_CONFIG, start=7):
            print(f"{i}. Insert Geographic Data ({country['name']})")
        print("=" * 40)
        print(f"{7 + len(config.COUNTRY_CONFIG)}. Exit")

        choice = input("Input: ").strip()

        if choice == '1':
            services.utils.check_ip()
        elif choice == '2':
            services.manage_proxy.send_signal_newnym()
        elif choice in map(str, range(3, 3 + len(config.COUNTRY_CONFIG))):
            index = int(choice) - 3
            fetch_and_save_data(config.COUNTRY_CONFIG[index])
        elif choice in map(str, range(7, 7 + len(config.COUNTRY_CONFIG))):
            index = int(choice) - 7
            load_geographic_data(config.COUNTRY_CONFIG[index])
        elif choice == str(7 + len(config.COUNTRY_CONFIG)):
            break
        else:
            print("Invalid input!")

if __name__ == "__main__":
    main()