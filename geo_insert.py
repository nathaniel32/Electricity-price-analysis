import pandas as pd
import hashlib
from utils import config
from database.connection import session_local
from database.models import TCountry, TProvince, TCity, TPostalArea

class GeoDataImporter:
    def __init__(
        self,
        country_name,
        csv_path,
        province_header,
        city_header,
        additional_header,
        postal_code_header,
    ):
        self.country_name = country_name
        self.csv_path = csv_path
        self.province_header = province_header
        self.city_header = city_header
        self.additional_header = additional_header
        self.postal_code_header = postal_code_header
        self.session = session_local()

    def md5_hash(self, text):
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    def safe_lower(self, val):
        if pd.notna(val):
            return str(val).strip().lower()
        return ""

    def load_and_insert(self):
        df = pd.read_csv(self.csv_path, sep=';', dtype={self.postal_code_header: str})

        print("0% [Country]")
        country_key = self.safe_lower(self.country_name)
        c_id = self.md5_hash(country_key)
        country = self.session.query(TCountry).filter_by(c_id=c_id).first()
        if not country:
            country = TCountry(c_id=c_id, c_name=self.country_name)
            self.session.add(country)
            self.session.commit()

        print("25% [Province]")
        province_count = 0
        provinces_seen = set()
        for province_name in df[self.province_header].dropna().unique():
            province_key = self.safe_lower(province_name)
            p_id = self.md5_hash(country_key + province_key)
            if p_id not in provinces_seen:
                provinces_seen.add(p_id)
                if not self.session.query(TProvince).filter_by(p_id=p_id).first():
                    province = TProvince(p_id=p_id, p_name=province_name, c_id=c_id)
                    self.session.add(province)
                    province_count += 1
        self.session.commit()

        print("50% [City]")
        city_count = 0
        cities_seen = set()
        for _, row in df.iterrows():
            city_name = row.get(self.city_header)
            province_name = row.get(self.province_header)
            if pd.notna(city_name) and pd.notna(province_name):
                city_key = self.safe_lower(city_name)
                province_key = self.safe_lower(province_name)
                ci_id = self.md5_hash(country_key + province_key + city_key)
                if ci_id not in cities_seen:
                    cities_seen.add(ci_id)
                    p_id = self.md5_hash(country_key + province_key)
                    if not self.session.query(TCity).filter_by(ci_id=ci_id).first():
                        city = TCity(ci_id=ci_id, ci_name=city_name, p_id=p_id)
                        self.session.add(city)
                        city_count += 1
        self.session.commit()

        print("75% [Postal Area]")
        postal_count = 0
        postal_seen = set()
        for _, row in df.iterrows():
            city_name = row.get(self.city_header)
            province_name = row.get(self.province_header)
            additional = row.get(self.additional_header) if self.additional_header in row else None
            postal_code = row.get(self.postal_code_header)

            if pd.notna(city_name) and pd.notna(province_name) and pd.notna(postal_code):
                city_key = self.safe_lower(city_name)
                province_key = self.safe_lower(province_name)
                postal_key = self.safe_lower(postal_code)
                pa_id = self.md5_hash(country_key + province_key + city_key + postal_key)

                if pa_id not in postal_seen:
                    postal_seen.add(pa_id)
                    pa_name = None
                    if pd.notna(additional) and str(additional).strip():
                        pa_name = str(additional).strip()

                    ci_id = self.md5_hash(country_key + province_key + city_key)
                    if not self.session.query(TPostalArea).filter_by(pa_id=pa_id).first():
                        postal_area = TPostalArea(
                            pa_id=pa_id,
                            pa_name=pa_name,
                            pa_code=postal_code,
                            ci_id=ci_id
                        )
                        self.session.add(postal_area)
                        postal_count += 1
        self.session.commit()

        print("100% [Done]")
        print(f"\nImport Summary:")
        print(f"➤  Country             : {self.country_name}")
        print(f"➤  Provinces added     : {province_count}")
        print(f"➤  Cities added        : {city_count}")
        print(f"➤  Postal Areas added  : {postal_count}")

    def close(self):
        self.session.close()


if __name__ == "__main__":
    importer = GeoDataImporter(
        country_name='Deutschland',
        csv_path='data/deutschland.csv',
        province_header='Bundesland',
        city_header='Ort',
        additional_header='Zusatz',
        postal_code_header='Plz'
    )
    importer.load_and_insert()
    importer.close()