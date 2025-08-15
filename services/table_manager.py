from database.models import TPostalArea, TValue, TDate, THour, TComponent
import services.utils
import json
from sqlalchemy import text
import sqlparse

class TableManager:
    def __init__(self, session, db_connection):
        self.session = session
        self.db_connection = db_connection

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

    def tabular_transform(self):
        existing_dates = set()
        existing_hours = set()
        existing_components = set()

        """Load ID"""
        existing_date_ids = self.session.query(TDate.d_id).all()
        existing_dates = {date_id[0] for date_id in existing_date_ids}
        
        # hours
        existing_hour_ids = self.session.query(THour.h_id).all()
        existing_hours = {hour_id[0] for hour_id in existing_hour_ids}
        
        # components
        existing_component_ids = self.session.query(TComponent.co_id).all()
        existing_components = {comp_id[0] for comp_id in existing_component_ids}
        
        print(f"Cache initialized: {len(existing_dates)} dates, {len(existing_hours)} hours, {len(existing_components)} components")

        
        areas = (
            self.session.query(TPostalArea.pa_id, TPostalArea.pa_code)
            .filter(TPostalArea.pa_data.isnot(None))
            .all()
        )

        if areas:
            print(f"Found {len(areas)} rows!")
        else:
            print("Nothing can be done!")
            return

        for area in areas:
            try:
                print(area.pa_id)
                
                t_postal_area = (
                    self.session.query(TPostalArea.pa_id, TPostalArea.pa_data)
                    .filter(TPostalArea.pa_id == area.pa_id)
                    .first()
                )
                
                postal_json_data = json.loads(t_postal_area.pa_data)

                if "energy" not in postal_json_data:
                    print(f"Invalid JSON structure for {area.pa_code}")
                    continue

                for date_component_config in services.utils.config.DATE_COMPONENTS_CONFIG:
                    hours_json = postal_json_data["energy"][date_component_config]
                    
                    for hour_json in hours_json:
                        date = hour_json["date"]
                        hour = hour_json["hour"]

                        # Generate unique IDs
                        date_id = services.utils.md5_hash(date)
                        hour_id = services.utils.md5_hash(str(hour))

                        # Check cache
                        if date_id not in existing_dates:
                            t_date = TDate(d_id=date_id, d_date=date)
                            self.session.add(t_date)
                            # Add to cache
                            existing_dates.add(date_id)
                            self.session.flush()

                        # Check cache
                        if hour_id not in existing_hours:
                            t_hour = THour(h_id=hour_id, h_hour=hour)
                            self.session.add(t_hour)
                            # Add to cache
                            existing_hours.add(hour_id)
                            self.session.flush()
                        
                        for price_component in hour_json["priceComponents"]:
                            for price_component_config in services.utils.config.PRICE_COMPONENTS_CONFIG:
                                if price_component["type"] in price_component_config["alias"]:
                                    #print(price_component_config["name"], " -> ", price_component["priceExcludingVat"])
                                    
                                    # Check cache
                                    component_id = services.utils.md5_hash(price_component_config["name"])
                                    if component_id not in existing_components:
                                        t_component = TComponent(
                                            co_id=component_id, 
                                            co_name=price_component_config["name"]
                                        )
                                        self.session.add(t_component)
                                        # Add to cache
                                        existing_components.add(component_id)
                                        self.session.flush()

                                    # Create TValue record
                                    t_value = TValue(
                                        pa_id=t_postal_area.pa_id,
                                        d_id=date_id,
                                        h_id=hour_id,
                                        co_id=component_id, 
                                        v_value=price_component["priceExcludingVat"]
                                    )
                                    self.session.add(t_value)

                self.session.commit()
                print(f"Successfully processed postal area: {area.pa_code}")
                
            except Exception as e:
                print(f"Error processing postal area {area.pa_code}: {str(e)[:100]}")
                self.session.rollback()
                continue

        print("Data transformation completed!")