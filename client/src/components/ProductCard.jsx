import React from 'react';

const ProductCard = ({ product }) => {
    return (
        <div style={styles.card}>
            {product.image_url && <img src={product.image_url} alt={product.name} style={styles.productImage} />}
            <h3>{product.name}</h3>
            <p><strong>Brand:</strong> {product.brand}</p>
            <p><strong>Category:</strong> {product.category}</p>
            <p><strong>Price:</strong> {product.currency}{product.price}</p>
            <p><strong>Pack Size:</strong> {product.pack_size_quantity} {product.pack_size_unit}</p>
        </div>
    );
};

const styles = {
    card: {
        border: '1px solid #ddd',
        borderRadius: '8px',
        padding: '16px',
        margin: '16px',
        width: '250px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
    },
    productImage: {
        width: '100%',
        height: '150px',
        objectFit: 'contain',
        marginBottom: '10px',
    },
};

export default ProductCard;
