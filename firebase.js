import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.8.1/firebase-app.js';
import { getFirestore, doc, setDoc, onSnapshot } from 'https://www.gstatic.com/firebasejs/10.8.1/firebase-firestore.js';
import { getAuth, signInWithEmailAndPassword, signOut, onAuthStateChanged } from 'https://www.gstatic.com/firebasejs/10.8.1/firebase-auth.js';

// ==========================================
// COLOQUE AS SUAS CHAVES DO FIREBASE AQUI
// ==========================================
export const firebaseConfig = {
    apiKey: "SUA_API_KEY",
    authDomain: "SEU_PROJETO.firebaseapp.com",
    projectId: "SEU_PROJETO",
    storageBucket: "SEU_PROJETO.appspot.com",
    messagingSenderId: "SEU_ID",
    appId: "SEU_APP_ID"
};

let firestoreDocRef = null;
let auth = null;

if (firebaseConfig.apiKey !== "SUA_API_KEY") {
    const app = initializeApp(firebaseConfig);
    const firestore = getFirestore(app);
    auth = getAuth(app);
    firestoreDocRef = doc(firestore, 'kambam_db', 'escala_principal');
} else {
    console.warn("Firebase não configurado.");
}

export { firestoreDocRef, auth, setDoc, onSnapshot, signInWithEmailAndPassword, signOut, onAuthStateChanged };
