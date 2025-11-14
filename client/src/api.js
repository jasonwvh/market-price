const API_BASE_URL = 'http://localhost:8000'; // Assuming your FastAPI runs on this address

export const fetchAllProducts = async () => {
    const response = await fetch(`${API_BASE_URL}/products`);
    console.log(response)
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
};

export const searchProductsByCategory = async (category) => {
    const response = await fetch(`${API_BASE_URL}/products/category?category=${encodeURIComponent(category)}`);
    if (!response.ok) {
        if (response.status === 404) {
            return [];
        }
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
};
