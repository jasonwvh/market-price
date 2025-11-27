import React from 'react';
import ProductList from './components/ProductList';
import './App.css'; // Assuming you have some global styles or will add them here

function App() {
    return (
        <div className="App">
            <header className="App-header">
                <h1>Grocery Prices</h1>
            </header>
            <main>
                <ProductList />
            </main>
        </div>
    );
}

export default App;