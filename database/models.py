from sqlalchemy import Column, Text, ForeignKey
from sqlalchemy.dialects.postgresql import VARCHAR, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

model_base = declarative_base()

class TCountry(model_base):
    __tablename__ = 't_country'

    c_id = Column(VARCHAR(32), primary_key=True)
    c_name = Column(Text, nullable=False)

    provinces = relationship("TProvince", back_populates="country")


class TProvince(model_base):
    __tablename__ = 't_province'

    p_id = Column(VARCHAR(32), primary_key=True)
    p_name = Column(Text, nullable=False)
    c_id = Column(VARCHAR(32), ForeignKey('t_country.c_id'))

    country = relationship("TCountry", back_populates="provinces")
    cities = relationship("TCity", back_populates="province")


class TCity(model_base):
    __tablename__ = 't_city'

    ci_id = Column(VARCHAR(32), primary_key=True)
    ci_name = Column(Text, nullable=False)
    p_id = Column(VARCHAR(32), ForeignKey('t_province.p_id'))

    province = relationship("TProvince", back_populates="cities")
    postal_areas = relationship("TPostalArea", back_populates="city")


class TPostalArea(model_base):
    __tablename__ = 't_postal_area'

    pa_id = Column(VARCHAR(32), primary_key=True)
    pa_name = Column(Text)
    pa_code = Column(Text, nullable=False)
    pa_data = Column(JSONB)
    ci_id = Column(VARCHAR(32), ForeignKey('t_city.ci_id'))

    city = relationship("TCity", back_populates="postal_areas")