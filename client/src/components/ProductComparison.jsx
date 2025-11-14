import React from 'react';

const ProductComparison = ({ productsToCompare }) => {
    if (productsToCompare.length === 0) {
        return null;
    }

    return (
        <div style={styles.comparisonContainer}>
            <h2>Product Comparison</h2>
            <div style={styles.comparisonGrid}>
                {productsToCompare.map(product => (
                    <div key={product.id} style={styles.comparisonCard}>
                        {product.image_url && <img src={product.image_url} alt={product.name} style={styles.productImage} />}
                        <h3>{product.name}</h3>
                        <p><strong>Brand:</strong> {product.brand}</p>
                        <p><strong>Price:</strong> {product.currency}{product.price}</p>
                        <p><strong>Pack Size:</strong> {product.pack_size_quantity} {product.pack_size_unit}</p>
                    </div>
                ))}
            </div>
        </div>
    );
};

const styles = {
    comparisonContainer: {
        marginTop: '40px',
        padding: '20px',
        borderTop: '1px solid #eee',
        textAlign: 'center',
    },
    comparisonGrid: {
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'center',
        gap: '20px',
    },
    comparisonCard: {
        border: '1px solid #007bff',
        borderRadius: '8px',
        padding: '16px',
        width: '280px',
        boxShadow: '0 4px 8px rgba(0,123,255,0.2)',
        backgroundColor: '#e9f5ff',
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

export default ProductComparison;
