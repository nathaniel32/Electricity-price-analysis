from services.utils import config
from database.connection import session_local
from database.models import TCountry, TProvince, TCity, TPostalArea
import requests
from datetime import datetime
import pytz
import time

class DataImporter:
    def __init__(self, target_url, target_country, fetch_delay):
        self.target_url = target_url
        self.target_country = target_country
        self.session = session_local()
        self.fetch_delay = fetch_delay

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
            
            try:
                response = requests.get(f"{self.target_url}{pa_code}", proxies=config.PROXIES)
                response.raise_for_status()

                area.pa_data = response.json()
                area.pa_updated_at = datetime.now(pytz.utc)

                print("PLZ:", pa_code, "\nTime: ", area.pa_updated_at, "\nData: ", str(area.pa_data)[0:200]+"...")
                self.session.commit()
            except requests.RequestException as e:
                print(f"Failed to fetch data for {pa_code}: {e}")
            except ValueError:
                print(f"The response from the API is not valid JSON for {pa_code}")
            
            time.sleep(self.fetch_delay)

    def close(self):
        self.session.close()