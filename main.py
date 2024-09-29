from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Inicializar FastAPI
app = FastAPI()

# Configuración de la base de datos MySQL
DATABASE_URL = "mysql+mysqlconnector://root:password@3.217.247.83:3306/ecommerce_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelo Producto
class Producto(Base):
    __tablename__ = "productos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100))
    descripcion = Column(String(255))
    precio = Column(Integer)
    stock = Column(Integer)

# Crear las tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Esquema Pydantic para los productos
class ProductoSchema(BaseModel):
    nombre: str
    descripcion: str
    precio: int
    stock: int

    class Config:
        orm_mode = True

# Ruta para crear un producto
@app.post("/productos/", response_model=ProductoSchema)
def crear_producto(producto: ProductoSchema):
    db = SessionLocal()
    db_producto = Producto(**producto.dict())
    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    return db_producto

# Ruta para obtener todos los productos
@app.get("/productos/")
def obtener_productos():
    db = SessionLocal()
    productos = db.query(Producto).all()
    return productos
