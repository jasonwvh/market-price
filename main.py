from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import sqlite3
from scrapers.base import Product
from datetime import datetime
import uvicorn

app = FastAPI()

# Configure CORS
origins = [
    "http://localhost",
    "http://localhost:5173",  # Assuming your React app runs on this port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProductResponse(Product):
    id: int


# Dependency to get the database connection
def get_db():
    conn = sqlite3.connect('scrapers/products.db')
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def map_row_to_product(row: sqlite3.Row) -> ProductResponse:
    """Maps a database row to a Product dataclass object with type conversions."""
    # Convert sqlite3.Row to a dictionary
    product_data = dict(row)

    # Perform type conversions for 'in_stock' and 'scraped_at'
    if 'in_stock' in product_data:
        product_data['in_stock'] = bool(product_data['in_stock'])
    if 'scraped_at' in product_data and isinstance(product_data['scraped_at'], str):
        product_data['scraped_at'] = datetime.fromisoformat(product_data['scraped_at'])

    return ProductResponse(**product_data)


@app.get("/products", response_model=List[ProductResponse])
def list_all_products(db: sqlite3.Connection = Depends(get_db)):
    products_rows = db.execute('SELECT * FROM products').fetchall()
    return [map_row_to_product(row) for row in products_rows]


@app.get("/products/search", response_model=List[ProductResponse])
def find_products_by_name(name: str, db: sqlite3.Connection = Depends(get_db)):
    products_rows = db.execute('SELECT * FROM products WHERE name LIKE ?', ('%' + name + '%',)).fetchall()
    if not products_rows:
        raise HTTPException(status_code=404, detail="Product not found")
    return [map_row_to_product(row) for row in products_rows]


@app.get("/products/category", response_model=List[ProductResponse])
def find_products_by_category(category: str, db: sqlite3.Connection = Depends(get_db)):
    products_rows = db.execute('SELECT * FROM products WHERE category LIKE ?', ('%' + category + '%',)).fetchall()
    if not products_rows:
        raise HTTPException(status_code=404, detail="No products found in this category")
    return [map_row_to_product(row) for row in products_rows]


if __name__ == "__main__":
    uvicorn.run(app)
