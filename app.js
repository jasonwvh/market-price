// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyAcbN8OsOTq932Y43KJrQuwLG611XJ7zlU",
  authDomain: "groceries-41bbb.firebaseapp.com",
  projectId: "groceries-41bbb",
  storageBucket: "groceries-41bbb.firebasestorage.app",
  messagingSenderId: "980431215696",
  appId: "1:980431215696:web:09abc5b669dea811b98555",
  measurementId: "G-K2VLW8T7X1"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);