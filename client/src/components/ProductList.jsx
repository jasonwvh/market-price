import React, { useState, useEffect } from 'react';
import ProductCard from './ProductCard';
import { fetchAllProducts, searchProductsByCategory } from '../api';

const ProductList = () => {
    const [products, setProducts] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        loadProducts();
    }, []);

    const loadProducts = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await fetchAllProducts();
            setProducts(data);
        } catch (err) {
            setError('Failed to fetch products.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleSearch = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            const data = await searchProductsByCategory(searchTerm);
            setProducts(data);
        } catch (err) {
            setError('Failed to search products.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <h2>Available Products</h2>
            <form onSubmit={handleSearch} style={styles.searchForm}>
                <input
                    type="text"
                    placeholder="Search by product category..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    style={styles.searchInput}
                />
                <button type="submit" style={styles.searchButton}>Search</button>
                <button type="button" onClick={loadProducts} style={styles.resetButton}>Show All</button>
            </form>

            {loading && <p>Loading products...</p>}
            {error && <p style={{ color: 'red' }}>{error}</p>}

            <div style={styles.productList}>
                {products.length > 0 ? (
                    products.map(product => (
                        <ProductCard key={product.id} product={product} />
                    ))
                ) : (
                    !loading && <p>No products found.</p>
                )}
            </div>
        </div>
    );
};

const styles = {
    searchForm: {
        display: 'flex',
        gap: '8px',
        marginBottom: '20px',
        justifyContent: 'center',
    },
    searchInput: {
        padding: '8px',
        borderRadius: '4px',
        border: '1px solid #ccc',
        width: '300px',
    },
    searchButton: {
        padding: '8px 16px',
        borderRadius: '4px',
        border: 'none',
        backgroundColor: '#007bff',
        color: 'white',
        cursor: 'pointer',
    },
    resetButton: {
        padding: '8px 16px',
        borderRadius: '4px',
        border: '1px solid #007bff',
        backgroundColor: '#fff',
        color: '#007bff',
        cursor: 'pointer',
    },
    productList: {
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'center',
    },
};

export default ProductList;
