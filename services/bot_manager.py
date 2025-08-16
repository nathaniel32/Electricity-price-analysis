from services.utils import config, confirm_action
from database.models import TCountry, TProvince, TCity, TPostalArea
import requests
import time
import random
import json
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_

class BotManager:
    def __init__(self, table_manager, session, target_url, target_country, fetch_min_delay, fetch_max_delay):
        self.table_manager = table_manager
        self.target_url = target_url
        self.target_country = target_country
        self.session = session
        self.fetch_min_delay = fetch_min_delay
        self.fetch_max_delay = fetch_max_delay
        self.proxies = config.PROXIES if config.USE_PROXY else None

    def run_bot(self):
        save_pa_data = confirm_action(message="Save JSON Data (y/n): ")
        transform_to_tabular = confirm_action(message="Transform to Tabular (y/n): ") if save_pa_data else True

        if transform_to_tabular:
            self.table_manager._tabular_transform_init()

        areas = (
            self.session.query(TPostalArea)
            .select_from(TPostalArea)
            .join(TCity, TCity.ci_id == TPostalArea.ci_id)
            .join(TProvince, TProvince.p_id == TCity.p_id)
            .join(TCountry, TCountry.c_id == TProvince.c_id)
            .filter(
                #TPostalArea.pa_data.is_(None),
                or_(
                    TPostalArea.pa_status_code != 200,
                    TPostalArea.pa_status_code.is_(None)
                ),
                TCountry.c_name == self.target_country
            )
            .all()
        )

        if areas:
            print(f"Found {len(areas)} rows to fetch!")
        else:
            print("Nothing can be done!")

        for index, area in enumerate(areas, start=1):
            print(f"\n{index}/{len(areas)}")
            pa_code = area.pa_code
            if area.pa_status_code != 400:
                try:
                    response = requests.get(f"{self.target_url}{pa_code}", proxies=self.proxies, headers=config.FETCH_HEADER)
                    
                    area.pa_status_code = response.status_code
                    
                    response.raise_for_status()

                    if save_pa_data:
                        print("Saving JSON..")
                        area.pa_data = json.dumps(response.json())

                    if transform_to_tabular:
                        print("Transforming JSON..")
                        self.table_manager._tabular_transform_tr(pa_id=area.pa_id, json_data=response.json(), log=True)

                    print("PLZ:", pa_code, "\nData: ", str(area.pa_data)[0:200]+"...")
                    self.session.commit()
                
                except IntegrityError as e:
                    # commit status code
                    self.session.commit()
                except requests.RequestException as e:
                    print("Status Code:", area.pa_status_code)
                    # commit status code
                    self.session.commit()
                except Exception as e:
                    self.session.rollback()
                    print(f"Error: {e}")

                time.sleep(random.uniform(self.fetch_min_delay, self.fetch_max_delay))
            else:
                print(pa_code, "NO DATA!")