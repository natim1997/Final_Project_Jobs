const admin = require('firebase-admin');

try {
    // First try to use the local file (for local development on your PC)
    const serviceAccount = require('./serviceAccountKey.json');
    admin.initializeApp({
        credential: admin.credential.cert(serviceAccount)
    });
    console.log("Firebase initialized locally with service account file.");
} catch (error) {
    // If the file is missing (like in Cloud Run), use default Google Cloud credentials
    admin.initializeApp({
        credential: admin.credential.applicationDefault()
    });
    console.log("Firebase initialized in Cloud Run using default credentials.");
}

// Initialize Firestore
const db = admin.firestore();

module.exports = { db, admin };