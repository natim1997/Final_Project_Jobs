const admin = require('firebase-admin');

// Simple english comment: Load credentials safely from environment variables in production, or local file in development
let credentialData;

if (process.env.FIREBASE_SERVICE_ACCOUNT) {
  // If running in Google Cloud Run, parse the JSON string from environment variables
  credentialData = admin.credential.cert(JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT));
} else {
  // If running locally on your Lenovo, use the local file
  const serviceAccount = require('./serviceAccountKey.json');
  credentialData = admin.credential.cert(serviceAccount);
}

admin.initializeApp({
  credential: credentialData,
  databaseURL: "https://jobmatcherproject-default-rtdb.firebaseio.com/"
});

const db = admin.database();

module.exports = { db, admin };