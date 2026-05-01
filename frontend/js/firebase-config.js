import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.1/firebase-app.js";
import { getAuth, GoogleAuthProvider } from "https://www.gstatic.com/firebasejs/10.8.1/firebase-auth.js";

const firebaseConfig = {
    apiKey: "AIzaSyBffsnhQmA8X_AIrhDF7wW6IYUMDH_szPk",
    authDomain: "show-ranker-project.firebaseapp.com",
    projectId: "show-ranker-project",
    storageBucket: "show-ranker-project.firebasestorage.app",
    messagingSenderId: "10037187822",
    appId: "1:10037187822:web:5e36fbb62dabe0e2ac8fff",
    measurementId: "G-675E716Y2L"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const provider = new GoogleAuthProvider();
