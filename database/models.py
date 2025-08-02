from sqlalchemy import (
    Column, String, Text, ForeignKey, Date, DateTime, Integer, Numeric,
    PrimaryKeyConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

model_base = declarative_base()

class TCountry(model_base):
    __tablename__ = 't_country'

    c_id = Column(String(32), primary_key=True)
    c_name = Column(String(255), nullable=False)

    provinces = relationship("TProvince", back_populates="country")


class TProvince(model_base):
    __tablename__ = 't_province'

    p_id = Column(String(32), primary_key=True)
    p_name = Column(String(255), nullable=False)
    c_id = Column(String(32), ForeignKey('t_country.c_id'))

    country = relationship("TCountry", back_populates="provinces")
    cities = relationship("TCity", back_populates="province")


class TCity(model_base):
    __tablename__ = 't_city'

    ci_id = Column(String(32), primary_key=True)
    ci_name = Column(String(255), nullable=False)
    p_id = Column(String(32), ForeignKey('t_province.p_id'))

    province = relationship("TProvince", back_populates="cities")
    postal_areas = relationship("TPostalArea", back_populates="city")


class TPostalArea(model_base):
    __tablename__ = 't_postal_area'

    pa_id = Column(String(32), primary_key=True)
    pa_name = Column(String(255))
    pa_code = Column(String(50), nullable=False)
    pa_data = Column(Text)  # JSON
    pa_updated_at = Column(DateTime, nullable=True)
    pa_status_code = Column(Integer)
    ci_id = Column(String(32), ForeignKey('t_city.ci_id'))

    city = relationship("TCity", back_populates="postal_areas")
    prices = relationship("TPrice", back_populates="postal_area")


class TDate(model_base):
    __tablename__ = 't_date'

    d_id = Column(String(32), primary_key=True)
    d_date = Column(Date, nullable=False)

    prices = relationship("TPrice", back_populates="date")


class TCategory(model_base):
    __tablename__ = 't_category'

    ca_id = Column(String(32), primary_key=True)
    ca_name = Column(String(255), nullable=False)

    prices = relationship("TPrice", back_populates="category")


class TPrice(model_base):
    __tablename__ = 't_price'

    pa_id = Column(String(32), ForeignKey('t_postal_area.pa_id'))
    d_id = Column(String(32), ForeignKey('t_date.d_id'))
    ca_id = Column(String(32), ForeignKey('t_category.ca_id'))
    p_value = Column(Numeric(19, 4))

    __table_args__ = (
        PrimaryKeyConstraint('pa_id', 'd_id', 'ca_id', name='pk_t_price'),
    )

    postal_area = relationship("TPostalArea", back_populates="prices")
    date = relationship("TDate", back_populates="prices")
    category = relationship("TCategory", back_populates="prices")