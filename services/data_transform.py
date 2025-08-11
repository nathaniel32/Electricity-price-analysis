from database.models import TPostalArea, TValue, TDate, THour, TComponent
import services.utils
import json

class DataTransform:
    def __init__(self, session):
        self.session = session
    
    def transform(self):
        areas = (
            self.session.query(TPostalArea.pa_id, TPostalArea.pa_code)
            .outerjoin(TValue, TValue.pa_id == TPostalArea.pa_id)
            .filter(TPostalArea.pa_data.isnot(None), TValue.pa_id.is_(None))
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
                
                # Fix: Use dot notation instead of dictionary access
                postal_json_data = json.loads(t_postal_area.pa_data)

                for date_component_config in services.utils.config.DATE_COMPONENTS_CONFIG:
                    hours_json = postal_json_data["energy"][date_component_config]
                    
                    for hour_json in hours_json:
                        date = hour_json["date"]
                        hour = hour_json["hour"]

                        # Generate unique IDs
                        date_id = services.utils.md5_hash(date)
                        hour_id = services.utils.md5_hash(f"{date}_{hour}")  # Make hour ID unique per date

                        # Check if TDate already exists, if not create it
                        existing_date = self.session.query(TDate).filter(TDate.d_id == date_id).first()
                        if not existing_date:
                            t_date = TDate(d_id=date_id, d_date=date)
                            self.session.add(t_date)
                            # Flush to ensure the date is available for the hour relationship
                            self.session.flush()

                        # Check if THour already exists, if not create it
                        existing_hour = self.session.query(THour).filter(THour.h_id == hour_id).first()
                        if not existing_hour:
                            # Fix: Use d_id instead of d_date for foreign key
                            t_hour = THour(h_id=hour_id, d_id=date_id, h_hour=hour)
                            self.session.add(t_hour)
                            self.session.flush()
                        
                        #print()
                        #print(date)
                        #print(hour)
                        
                        for price_component in hour_json["priceComponents"]:
                            for price_component_config in services.utils.config.PRICE_COMPONENTS_CONFIG:
                                if price_component["type"] in price_component_config["alias"]:
                                    #print(price_component_config["name"], " -> ", price_component["priceExcludingVat"])
                                    
                                    # Check if TComponent already exists, if not create it
                                    component_id = services.utils.md5_hash(price_component_config["name"])
                                    existing_component = self.session.query(TComponent).filter(TComponent.co_id == component_id).first()
                                    if not existing_component:
                                        t_component = TComponent(
                                            co_id=component_id, 
                                            co_name=price_component_config["name"]
                                        )
                                        self.session.add(t_component)
                                        self.session.flush()

                                    # Create TValue record
                                    # Fix: Use proper attribute access and correct IDs
                                    t_value = TValue(
                                        pa_id=t_postal_area.pa_id, 
                                        h_id=hour_id, 
                                        co_id=component_id, 
                                        v_value=price_component["priceExcludingVat"]
                                    )
                                    self.session.add(t_value)

                # Commit changes for this postal area
                self.session.commit()
                print(f"Successfully processed postal area: {area.pa_code}")
                
            except Exception as e:
                print(f"Error processing postal area {area.pa_code}: {e}")
                self.session.rollback()
                # Continue with next area instead of stopping
                continue

        print("Data transformation completed!")