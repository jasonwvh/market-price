import React from 'react';

const ProductCard = ({ product }) => {
    return (
        <div className="product-card">
            <div className="product-image-container">
                {product.image_url && <img src={product.image_url} alt={product.name} className="product-image" />}
            </div>
            <div className="product-info">
                <h3 className="product-name">{product.name}</h3>
                <p><strong>Brand:</strong> {product.brand}</p>
                <p><strong>Category:</strong> {product.category}</p>
                <p className="product-price"><strong>Price:</strong> {product.currency}{product.price}</p>
                <p><strong>Pack Size:</strong> {product.pack_size_quantity} {product.pack_size_unit}</p>
            </div>
        </div>
    );
};

export default ProductCard;
