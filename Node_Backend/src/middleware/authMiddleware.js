const { admin } = require('../config/firebase');

/**
 * Middleware 1: Authentication (AuthN)
 * Verifies the Firebase JWT token to ensure the user is authenticated.
 */
const verifyToken = async (req, res, next) => {
    try {
        const authHeader = req.headers.authorization;

        // Check if the Authorization header exists and follows the Bearer format
        if (!authHeader || !authHeader.startsWith('Bearer ')) {
            return res.status(401).json({ error: "Unauthorized: Missing or invalid token format." });
        }

        // Extract the raw token string
        const token = authHeader.split('Bearer ')[1];

        // Verify the token's validity and signature using Firebase Admin SDK
        const decodedToken = await admin.auth().verifyIdToken(token);

        // Inject the decoded user payload (UID, email, custom claims) into the request
        req.user = decodedToken; 

        // Token is valid, proceed to the next middleware or controller
        next(); 

    } catch (error) {
        console.error("Token verification failed:", error.message);
        // Return 403 Forbidden if the token is expired, revoked, or tampered with
        return res.status(403).json({ error: "Forbidden: Invalid or expired token." });
    }
};

/**
 * Middleware 2: Authorization (AuthZ) - RBAC
 * Verifies that the authenticated user possesses the required role.
 * Note: Must be called AFTER verifyToken.
 */
const requireRole = (requiredRole) => {
    return (req, res, next) => {
        // Check if the user object exists and if the role claim matches the requirement
        if (!req.user || req.user.role !== requiredRole) {
            console.warn(`Access Denied: User ${req.user?.uid} attempted to access a ${requiredRole} route.`);
            return res.status(403).json({ 
                error: `Forbidden: This action requires '${requiredRole}' privileges.` 
            });
        }
        
        // Role is verified, proceed to the target controller
        next(); 
    };
};

module.exports = { verifyToken, requireRole };