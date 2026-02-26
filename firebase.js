import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.8.1/firebase-app.js';
import { getFirestore, doc, setDoc, onSnapshot } from 'https://www.gstatic.com/firebasejs/10.8.1/firebase-firestore.js';
import { getAuth, signInWithEmailAndPassword, signOut, onAuthStateChanged } from 'https://www.gstatic.com/firebasejs/10.8.1/firebase-auth.js';

// ==========================================
// COLOQUE AS SUAS CHAVES DO FIREBASE AQUI
// ==========================================
const firebaseConfig = {
  apiKey: "AIzaSyCKkQ26NfSwcVXxm3pRM706MZ5Goo9yg7c",
  authDomain: "kambam-equipes.firebaseapp.com",
  projectId: "kambam-equipes",
  storageBucket: "kambam-equipes.firebasestorage.app",
  messagingSenderId: "870835450124",
  appId: "1:870835450124:web:552998a893c81827d01929",
  measurementId: "G-DVXBG1BPFV"
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
