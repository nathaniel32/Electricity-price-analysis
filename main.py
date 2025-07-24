import services.data_insert
import services.geo_insert
import services.manage_proxy
import services.utils

def main():
    geo_importer = services.geo_insert.GeoImporter(
        country_name='Deutschland',
        csv_path='data/deutschland.csv',
        province_header='Bundesland',
        city_header='Ort',
        additional_header='Zusatz',
        postal_code_header='Plz'
    )
    while True:
        print("\n==== MENU ====")
        print("1. Check Proxy IP")
        print("2. Change Proxy IP")
        print("3. Fetch and Input Data")
        print("4. Input Geographic Data")
        print("5. Drop All Tables")
        print("5. Exit")
        choice = input("Input: ")

        if choice == '1':
            services.utils.check_ip()
        elif choice == '2':
            services.manage_proxy.send_signal_newnym()
        elif choice == '3':
            data_importer = services.data_insert.DataImporter(target_url='https://tibber.com/de/api/lookup/price-overview?postalCode=', target_country='Deutschland', fetch_delay=2)
            data_importer.fetch_and_insert()
            data_importer.close()
        elif choice == '4':
            geo_importer.load_and_insert()
            geo_importer.close()
        elif choice == '5':
            confirm = input("Are you sure you want to DROP ALL TABLES? This cannot be undone! (yes/no): ").lower()
            if confirm == 'yes':
                geo_importer.drop_all_table()
                geo_importer.close()
                print("All tables dropped successfully.")
                break
            else:
                print("Drop cancelled.")
        elif choice == '6':
            break
        else:
            print("Invalid selection!")

if __name__ == "__main__":
    main()