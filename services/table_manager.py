from database.models import TPostalArea, TValue, TDate, THour, TComponent
import services.utils
import json
from sqlalchemy import text
import sqlparse
from sqlalchemy.exc import IntegrityError

class TableManager:
    def __init__(self, session, db_connection):
        self.session = session
        self.db_connection = db_connection
        self.existing_dates = None
        self.existing_hours = None
        self.existing_components = None

    def create_tables(self):
        try:
            self.db_connection.create_tables()
            print("All tables created successfully.")
        except Exception as e:
            print(f"Failed to create tables: {e}")

    def import_sql_file(self):
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

    def clear_bot_data_session(self):
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

    def _tabular_transform_init(self):
        self.existing_dates = set()
        self.existing_hours = set()
        self.existing_components = set()
        
        """Load ID"""
        # Load dates
        existing_date_ids = self.session.query(TDate.d_id).all()
        self.existing_dates = {date_id[0] for date_id in existing_date_ids}
        
        # Load hours
        existing_hour_ids = self.session.query(THour.h_id).all()
        self.existing_hours = {hour_id[0] for hour_id in existing_hour_ids}
        
        # Load components
        existing_component_ids = self.session.query(TComponent.co_id).all()
        self.existing_components = {comp_id[0] for comp_id in existing_component_ids}
        
        print(f"Cache initialized: {len(self.existing_dates)} dates, {len(self.existing_hours)} hours, {len(self.existing_components)} components")

    def _tabular_transform_tr(self, pa_id, json_data, log=False):
        try:
            if "energy" not in json_data:
                raise ValueError(f"Invalid JSON structure for postal area {pa_id}")

            for date_component_config in services.utils.config.DATE_COMPONENTS_CONFIG:
                hours_json = json_data["energy"][date_component_config]
                
                for hour_json in hours_json:
                    date = hour_json["date"]
                    hour = hour_json["hour"]

                    # Generate unique IDs
                    date_id = services.utils.md5_hash(date)
                    hour_id = services.utils.md5_hash(str(hour))

                    # Check cache
                    if date_id not in self.existing_dates:
                        t_date = TDate(d_id=date_id, d_date=date)
                        self.session.add(t_date)
                        self.existing_dates.add(date_id)
                        self.session.flush()

                    if hour_id not in self.existing_hours:
                        t_hour = THour(h_id=hour_id, h_hour=hour)
                        self.session.add(t_hour)
                        self.existing_hours.add(hour_id)
                        self.session.flush()
                    
                    for price_component in hour_json["priceComponents"]:
                        for price_component_config in services.utils.config.PRICE_COMPONENTS_CONFIG:
                            if price_component["type"] in price_component_config["alias"]:
                                component_id = services.utils.md5_hash(price_component_config["name"])
                                if component_id not in self.existing_components:
                                    t_component = TComponent(
                                        co_id=component_id, 
                                        co_name=price_component_config["name"]
                                    )
                                    self.session.add(t_component)
                                    self.existing_components.add(component_id)
                                    self.session.flush()

                                t_value = TValue(
                                    pa_id=pa_id,
                                    d_id=date_id,
                                    h_id=hour_id,
                                    co_id=component_id, 
                                    v_value=price_component["priceExcludingVat"]
                                )
                                self.session.add(t_value)

            self.session.commit()
            if log:
                print(f"Data successfully transformed into tabular: {pa_id}")

        except IntegrityError as e:
            self.session.rollback()
            #print(f"Primary key violation for postal area {pa_id}: {e.orig}")
            raise
        except Exception as e:
            self.session.rollback()
            print(f"Error processing postal area {pa_id}: {str(e)}")
            raise

    def tabular_transform(self):
        self._tabular_transform_init()
        
        areas = (
            self.session.query(TPostalArea.pa_id)
            .filter(TPostalArea.pa_data.isnot(None))
            .all()
        )

        if areas:
            print(f"Found {len(areas)} rows!")
        else:
            print("Nothing can be done!")
            return

        input_data = 0
        for index, area in enumerate(areas, start=1):
            try:
                t_postal_area = (
                    self.session.query(TPostalArea.pa_data)
                    .filter(TPostalArea.pa_id == area.pa_id)
                    .first()
                )

                if not t_postal_area:
                    print(f"Postal area {area.pa_id} not found")
                    continue
                
                postal_json_data = json.loads(t_postal_area.pa_data)
                
                self._tabular_transform_tr(area.pa_id, postal_json_data)

                input_data += 1
            except IntegrityError as e:
                pass
            except Exception as e:
                print(f"\nError processing postal area {area.pa_id}: {e}")
                continue

            if index % 10 == 0 or index == len(areas):
                print(f"\r{index}/{len(areas)} | New Tabular Data: {input_data} ", end='', flush=True)

        print("\nData transformation completed!")