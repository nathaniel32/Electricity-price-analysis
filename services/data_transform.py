from database.models import TPostalArea, TValue, TDate, THour, TComponent
from services.utils import config
import json

class DataTransform:
    def __init__(self, session):
        self.session = session

    def transform(self):
        areas = (
            self.session.query(TPostalArea.pa_code)
            .outerjoin(TValue, TValue.pa_id == TPostalArea.pa_id)
            .filter(TPostalArea.pa_data.isnot(None), TValue.pa_id.is_(None))
            .all()
        )

        if areas:
            print(f"Found {len(areas)} rows!")
        else:
            print("Nothing can be done!")

        for area in areas:
            print(area.pa_code)
            json_string_data = self.session.query(TPostalArea.pa_data).filter(TPostalArea.pa_code == area.pa_code).first()
            json_data = json.loads(json_string_data[0])

            for date_component_config in config.DATE_COMPONENTS_CONFIG:
                hours_json = json_data["energy"][date_component_config]
                for hour_json in hours_json:
                    date = hour_json["date"]
                    hour = hour_json["hour"]
                    print()
                    print(date)
                    print(hour)
                    for price_component in hour_json["priceComponents"]:
                        for price_conponent_config in config.PRICE_COMPONENTS_CONFIG:
                            if price_component["type"] in price_conponent_config["alias"]:
                                print(price_conponent_config["name"] ," -> ", price_component["priceExcludingVat"])

            
            break