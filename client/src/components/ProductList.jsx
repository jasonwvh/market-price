import React, { useState, useEffect } from 'react';
import ProductCard from './ProductCard';
import { fetchAllProducts } from '../api';

const ProductList = () => {
    const [allProducts, setAllProducts] = useState([]);
    const [filteredProducts, setFilteredProducts] = useState([]);
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
            setAllProducts(data);
            setFilteredProducts(data);
        } catch (err) {
            setError('Failed to fetch products.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleSearch = (e) => {
        e.preventDefault();
        if (!searchTerm) {
            setFilteredProducts(allProducts);
            return;
        }
        const lowercasedTerm = searchTerm.toLowerCase();
        const results = allProducts.filter(product => {
            const nameMatch = product.name && product.name.toLowerCase().includes(lowercasedTerm);
            const categoryMatch = product.category && product.category.toLowerCase().includes(lowercasedTerm);
            return nameMatch || categoryMatch;
        });
        setFilteredProducts(results);
    };

    const handleReset = () => {
        setSearchTerm('');
        setFilteredProducts(allProducts);
    };

    return (
        <div className="product-list-container">
            <h2>Available Products</h2>
            <form onSubmit={handleSearch} className="search-form">
                <input
                    type="text"
                    placeholder="Search by product category..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="search-input"
                />
                <button type="submit" className="search-button">Search</button>
                <button type="button" onClick={handleReset} className="reset-button">Show All</button>
            </form>

            {loading && <div className="loader"></div>}
            {error && <p className="error-message">{error}</p>}

            <div className="product-list">
                {filteredProducts.length > 0 ? (
                    filteredProducts.map(product => (
                        <ProductCard key={product.id} product={product} />
                    ))
                ) : (
                    !loading && <div className="no-products-found">
                        <p>No products found.</p>
                        <p>Try adjusting your search terms or view all available products.</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ProductList;
