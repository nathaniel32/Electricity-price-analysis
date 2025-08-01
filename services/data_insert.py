from services.utils import config
from database.connection import Connection
from database.models import TCountry, TProvince, TCity, TPostalArea
import requests
from datetime import datetime
import pytz
import time
import random
import json

class DataImporter:
    def __init__(self, target_url, target_country, fetch_min_delay, fetch_max_delay):
        self.target_url = target_url
        self.target_country = target_country
        self.session = Connection().get_session()
        self.fetch_min_delay = fetch_min_delay
        self.fetch_max_delay = fetch_max_delay
        self.proxies = config.PROXIES if config.USE_PROXY else None

    def fetch_and_insert(self):
        areas = (
            self.session.query(TPostalArea)
            .select_from(TPostalArea)
            .join(TCity, TCity.ci_id == TPostalArea.ci_id)
            .join(TProvince, TProvince.p_id == TCity.p_id)
            .join(TCountry, TCountry.c_id == TProvince.c_id)
            .filter(
                TPostalArea.pa_data == None,
                TCountry.c_name == self.target_country
            )
            .all()
        )

        if areas:
            print(f"Found {len(areas)} rows to fetch!")
        else:
            print("Nothing can be done!")

        for area in areas:
            pa_code = area.pa_code
            if area.pa_status_code != 400:
                try:
                    response = requests.get(f"{self.target_url}{pa_code}", proxies=self.proxies, headers=config.FETCH_HEADER)
                    
                    area.pa_status_code = response.status_code
                    
                    response.raise_for_status()

                    area.pa_data = json.dumps(response.json())
                    area.pa_updated_at = datetime.now(pytz.utc)

                    print("\nPLZ:", pa_code, "\nTime: ", area.pa_updated_at, "\nData: ", str(area.pa_data)[0:200]+"...")
                    self.session.commit()
                except requests.RequestException as e:
                    print("\nStatus Code:", area.pa_status_code)
                    print(f"Failed to fetch data for {pa_code}: {e}")
                except ValueError:
                    print("\nStatus Code:", area.pa_status_code)
                    print(f"The response from the API is not valid JSON for {pa_code}")

                self.session.commit()
                time.sleep(random.uniform(self.fetch_min_delay, self.fetch_max_delay))
            else:
                print(pa_code, "NO DATA!")

    def close(self):
        self.session.close()