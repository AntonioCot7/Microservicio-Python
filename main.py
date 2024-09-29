from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configuración de la base de datos
DATABASE_URL = "mysql+mysqlconnector://root:mysql@db:3306/ecommerce_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Definición del modelo de Producto
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    description = Column(String(255))
    price = Column(Integer)

# Creación de la base de datos
Base.metadata.create_all(bind=engine)

# Inicia FastAPI
app = FastAPI()

# Clase para manejar la creación de productos
class ProductCreate(BaseModel):
    name: str
    description: str
    price: int

# Ruta para crear un producto
@app.post("/products/")
def create_product(product: ProductCreate):
    db = SessionLocal()
    db_product = Product(name=product.name, description=product.description, price=product.price)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    db.close()
    return db_product

# Ruta para obtener todos los productos
@app.get("/products/")
def get_products():
    db = SessionLocal()
    products = db.query(Product).all()
    db.close()
    return products
