from database.models import TPostalArea, TValue, TDate, THour, TComponent
import services.utils
import json

class DataTransform:
    def __init__(self, session):
        self.session = session
        self.existing_dates = set()
        self.existing_hours = set()
        self.existing_components = set()
    
    def _load_existing_data(self):
        """Load existing IDs into cache"""
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
    
    def transform(self):
        self._load_existing_data()
        
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
                        if date_id not in self.existing_dates:
                            t_date = TDate(d_id=date_id, d_date=date)
                            self.session.add(t_date)
                            # Add to cache
                            self.existing_dates.add(date_id)
                            self.session.flush()

                        # Check cache
                        if hour_id not in self.existing_hours:
                            t_hour = THour(h_id=hour_id, h_hour=hour)
                            self.session.add(t_hour)
                            # Add to cache
                            self.existing_hours.add(hour_id)
                            self.session.flush()
                        
                        #print()
                        #print(date)
                        #print(hour)
                        
                        for price_component in hour_json["priceComponents"]:
                            for price_component_config in services.utils.config.PRICE_COMPONENTS_CONFIG:
                                if price_component["type"] in price_component_config["alias"]:
                                    #print(price_component_config["name"], " -> ", price_component["priceExcludingVat"])
                                    
                                    # Check cache
                                    component_id = services.utils.md5_hash(price_component_config["name"])
                                    if component_id not in self.existing_components:
                                        t_component = TComponent(
                                            co_id=component_id, 
                                            co_name=price_component_config["name"]
                                        )
                                        self.session.add(t_component)
                                        # Add to cache
                                        self.existing_components.add(component_id)
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
                print(f"Error processing postal area {area.pa_code}: {e}")
                self.session.rollback()
                self._load_existing_data()
                continue

        print("Data transformation completed!")