const { db } = require('../config/firebase');

/**
 * Adds a review and updates the target's average rating.
 */
const addReview = async (req, res) => {
    try {
        const { from_id, to_id, type, rating, review_text } = req.body;

        if (!from_id || !to_id || !rating) {
            return res.status(400).json({ error: "Missing required fields" });
        }

        // 1. Save the full review to the 'reviews' node
        const newReviewRef = db.ref('reviews').push();
        const reviewData = {
            from_id,
            to_id,
            type, // 'candidate_to_job' or 'job_to_candidate'
            rating: Number(rating),
            review_text,
            timestamp: Date.now()
        };
        await newReviewRef.set(reviewData);

        // 2. Update the summarized rating in the target's profile
        // Determine the path: is it a job or a candidate being rated?
        const targetPath = type === 'candidate_to_job' ? `jobs/${to_id}` : `candidates/${to_id}`;
        const targetRef = db.ref(`${targetPath}/rating_summary`);

        // Fetch current summary
        const snapshot = await targetRef.once('value');
        let { average_rating = 0, total_reviews = 0 } = snapshot.val() || {};

        // Calculate new average
        const newTotal = total_reviews + 1;
        const newAverage = ((average_rating * total_reviews) + rating) / newTotal;

        // Save updated summary
        await targetRef.update({
            average_rating: Number(newAverage.toFixed(1)),
            total_reviews: newTotal,
            last_updated: Date.now()
        });

        res.status(200).json({ 
            status: "success", 
            message: "Review added and rating updated!",
            new_average: newAverage.toFixed(1)
        });

    } catch (error) {
        console.error(" Error adding review:", error);
        res.status(500).json({ error: "Internal Server Error" });
    }
};

module.exports = { addReview };