const admin = require('firebase-admin');
const serviceAccount = require('./serviceAccountKey.json');

// Initialize Firebase Admin with the database URL
admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  databaseURL: "https://jobmatcherproject-default-rtdb.firebaseio.com/"
});

const db = admin.database();

module.exports = { db, admin };