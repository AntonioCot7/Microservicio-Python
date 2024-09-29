import os
import boto3
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Inicializar FastAPI
app = FastAPI()

# Configuración de la base de datos MySQL
DATABASE_URL = "mysql+mysqlconnector://root:mysql@db:3306/ecommerce_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Configuración de AWS S3
S3_BUCKET = "imagenes-s3-productos"
S3_FOLDER = "Imagenes-Productos"

# Cliente S3
s3_client = boto3.client('s3')

# Modelo Producto
class Producto(Base):
    __tablename__ = "productos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100))
    descripcion = Column(String(255))
    precio = Column(Integer)
    stock = Column(Integer)
    imagen = Column(String(255))  # Ruta de la imagen en S3
    categoria_id = Column(Integer, ForeignKey('categorias.id'))
    categoria = relationship("Categoria", back_populates="productos")

# Modelo Categoria
class Categoria(Base):
    __tablename__ = "categorias"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100))
    productos = relationship("Producto", back_populates="categoria")

# Crear las tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Esquema Pydantic para productos
class ProductoSchema(BaseModel):
    nombre: str
    descripcion: str
    precio: int
    stock: int
    categoria_id: int

    class Config:
        from_attributes = True

# Esquema Pydantic para categorías
class CategoriaSchema(BaseModel):
    nombre: str

    class Config:
        from_attributes = True

# Dependencia para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Función para subir archivos a S3
def upload_image_to_s3(file: UploadFile):
    try:
        file_key = f"{S3_FOLDER}/{file.filename}"
        s3_client.upload_fileobj(file.file, S3_BUCKET, file_key, ExtraArgs={"ACL": "public-read"})
        file_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{file_key}"
        return file_url
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error subiendo la imagen a S3: {str(e)}")

# Ruta para crear un producto con imagen
@app.post("/productos/", response_model=ProductoSchema)
async def crear_producto(nombre: str, descripcion: str, precio: int, stock: int, categoria_id: int, imagen: UploadFile = File(...), db: SessionLocal = Depends(get_db)):
    # Subir imagen a S3
    imagen_url = upload_image_to_s3(imagen)
    
    # Crear el producto en la base de datos
    db_producto = Producto(
        nombre=nombre, 
        descripcion=descripcion, 
        precio=precio, 
        stock=stock, 
        imagen=imagen_url, 
        categoria_id=categoria_id
    )
    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    return db_producto

# Ruta para obtener todos los productos
@app.get("/productos/")
def obtener_productos(db: SessionLocal = Depends(get_db)):
    productos = db.query(Producto).all()
    return productos

# Ruta para obtener productos por categoría
@app.get("/productos/categoria/{categoria_id}")
def obtener_productos_por_categoria(categoria_id: int, db: SessionLocal = Depends(get_db)):
    productos = db.query(Producto).filter(Producto.categoria_id == categoria_id).all()
    if not productos:
        raise HTTPException(status_code=404, detail="No se encontraron productos para esta categoría.")
    return productos

# Ruta para obtener un producto específico por ID y categoría
@app.get("/productos/{categoria_id}/{producto_id}")
def obtener_producto_por_id_y_categoria(categoria_id: int, producto_id: int, db: SessionLocal = Depends(get_db)):
    producto = db.query(Producto).filter(Producto.categoria_id == categoria_id, Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado en esta categoría.")
    return producto

# Ruta para eliminar un producto
@app.delete("/productos/{producto_id}")
def eliminar_producto(producto_id: int, db: SessionLocal = Depends(get_db)):
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    db.delete(producto)
    db.commit()
    return {"detail": "Producto eliminado exitosamente"}

# Ruta para crear una categoría
@app.post("/categorias/", response_model=CategoriaSchema)
def crear_categoria(categoria: CategoriaSchema, db: SessionLocal = Depends(get_db)):
    db_categoria = Categoria(**categoria.dict())
    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)
    return db_categoria

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8005)
