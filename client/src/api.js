import { db } from './firebase';
import { collection, getDocs, query, where } from 'firebase/firestore';

export const fetchAllProducts = async () => {
    const productsCollection = collection(db, 'products');
    const productSnapshot = await getDocs(productsCollection);
    const productList = productSnapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
    return productList;
};

export const searchProductsByCategory = async (category) => {
    const productsCollection = collection(db, 'products');
    // Firestore doesn't have a 'contains' or 'LIKE' query, but this prefix search works for categories.
    const q = query(productsCollection, where('category', '>=', category), where('category', '<=', category + '\uf8ff'));
    const productSnapshot = await getDocs(q);
    const productList = productSnapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
    return productList;
};