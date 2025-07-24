from utils import config
from database.connection import session_local
from database.models import TCountry, TProvince, TCity, TPostalArea
import requests

class DataImporter:
    def __init__(self, target_url, target_country):
        self.target_url = target_url
        self.target_country = target_country
        self.session = session_local()

    def fetch_and_insert(self):
        #postal_areas = self.session.query(TPostalArea).filter_by(pa_data=None).all()

        areas = (
            self.session.query(TPostalArea.pa_code)
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

        for area in areas:
            pa_code = area.pa_code

            print(pa_code)

            """ try:
                response = requests.get(f"{self.target_url}{pa_code}")
                response.raise_for_status()

                data = response.json()

                # Update field JSONB
                area.pa_data = data

            except requests.RequestException as e:
                print(f"Failed to fetch data for {pa_code}: {e}")
            except ValueError:
                print(f"The response from the API is not valid JSON for {pa_code}")
            break; """

        self.session.commit()

    def close(self):
        self.session.close()


if __name__ == "__main__":
    importer = DataImporter(target_url='', target_country='Deutschland', )
    importer.fetch_and_insert()
    importer.close()