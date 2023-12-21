from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Barang(Base):
    __tablename__ = 'barang'
    id_barang = Column(Integer, primary_key=True)
    product_name = Column(String(255))
    price = Column(Integer)
    quality = Column(Integer)
    durability = Column(Integer)
    weight = Column(Integer)
    size = Column(Integer)
    
    def __repr__(self) -> str:
        return f"Ponsel(id={self.id!r}, harga={self.price!r}, quality={self.quality!r}, durability={self.durability!r}, weight={self.weight!r}, size={self.size!r})"
