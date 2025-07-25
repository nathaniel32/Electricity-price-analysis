import services.data_insert
import services.geo_insert
import services.manage_proxy
import services.utils

def main():
    while True:
        print("\n==== MENU ====")
        print("1. Check Proxy IP")
        print("2. Change Proxy IP")
        print("=" * 40)
        print("3. Fetch and Input Data (Deutschland)")
        print("4. Fetch and Input Data (Niederlande)")
        print("5. Fetch and Input Data (Schweden)")
        print("6. Fetch and Input Data (Norwegen)")
        print("=" * 40)
        print("7. Input Geographic Data (Deutschland)")
        print("8. Input Geographic Data (Niederlande)")
        print("9. Input Geographic Data (Schweden)")
        print("10. Input Geographic Data (Norwegen)")
        print("=" * 40)
        print("11. Drop All Tables")
        print("12. Exit")
        choice = input("Input: ")
        print()
        if choice == '1':
            services.utils.check_ip()
        elif choice == '2':
            services.manage_proxy.send_signal_newnym()
        elif choice == '3':
            data_importer = services.data_insert.DataImporter(target_url='https://tibber.com/de/api/lookup/price-overview?postalCode=', target_country='Deutschland', fetch_min_delay=0, fetch_max_delay=0)
            data_importer.fetch_and_insert()
            data_importer.close()
        elif choice == '4':
            data_importer = services.data_insert.DataImporter(target_url='https://tibber.com/nl/api/lookup/price-overview?postalCode=', target_country='Niederlande', fetch_min_delay=0, fetch_max_delay=0)
            data_importer.fetch_and_insert()
            data_importer.close()
        elif choice == '5':
            data_importer = services.data_insert.DataImporter(target_url='https://tibber.com/se/api/lookup/price-overview?postalCode=', target_country='Schweden', fetch_min_delay=0, fetch_max_delay=0)
            data_importer.fetch_and_insert()
            data_importer.close()
        elif choice == '6':
            data_importer = services.data_insert.DataImporter(target_url='https://tibber.com/no/api/lookup/price-overview?postalCode=', target_country='Norwegen', fetch_min_delay=0, fetch_max_delay=0)
            data_importer.fetch_and_insert()
            data_importer.close()
        elif choice == '7':
            geo_importer = services.geo_insert.GeoImporter(csv_path='data/csv/deutschland.csv', sep=';', country_name='Deutschland', province_header='Bundesland', city_header='Ort', additional_header='Zusatz', postal_code_header='Plz')
            geo_importer.load_and_insert()
            geo_importer.close()
        elif choice == '8':
            geo_importer = services.geo_insert.GeoImporter(csv_path='data/csv/niederlande.csv', sep=',', country_name='Niederlande', province_header='state', city_header='place', additional_header=None, postal_code_header='zipcode')
            geo_importer.load_and_insert()
            geo_importer.close()
        elif choice == '9':
            geo_importer = services.geo_insert.GeoImporter(csv_path='data/csv/schweden.csv', sep=',', country_name='Schweden', province_header='state', city_header='place', additional_header=None, postal_code_header='zipcode')
            geo_importer.load_and_insert()
            geo_importer.close()
        elif choice == '10':
            geo_importer = services.geo_insert.GeoImporter(csv_path='data/csv/norwegen.csv', sep=',', country_name='Norwegen', province_header='state', city_header='place', additional_header=None, postal_code_header='zipcode')
            geo_importer.load_and_insert()
            geo_importer.close()
        elif choice == '11':
            confirm = input("Are you sure you want to DROP ALL TABLES? This cannot be undone! (yes/no): ").lower()
            if confirm == 'yes':
                geo_importer.drop_all_table()
                geo_importer.close()
                print("All tables dropped successfully.")
                break
            else:
                print("Drop cancelled.")
        elif choice == '12':
            break
        else:
            print("Invalid selection!")

if __name__ == "__main__":
    main()