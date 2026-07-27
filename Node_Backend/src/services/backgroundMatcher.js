const { getMatchesForCandidate } = require('../controllers/matchController');
const { db } = require('../config/firebase');
const logger = require('../config/logger');

// ==========================================
// Background Match Engine
// ==========================================

// Run match for a single candidate (When candidate signs up/updates profile)
// NOTE: This is now an async function that returns a Promise instead of using
// setTimeout. Cloud Run may freeze the container's event loop once the HTTP
// response has been sent, which meant a deferred setTimeout callback could
// simply never run (or run late, on an unrelated future request). The caller
// (createCandidate) now does `await triggerSingleCandidateMatch(userId)`
// BEFORE sending its response, so this always finishes while the container
// is guaranteed to be active.
const triggerSingleCandidateMatch = async (candidateId) => {
    logger.info(`[MATCH] Triggering match engine for candidate: ${candidateId}`);

    // Empty query since we want to check all jobs for this candidate
    const mockReq = { params: { candidateId: candidateId }, query: {} };

    // We still need to "mock" res because getMatchesForCandidate is written
    // as an Express controller (it calls res.status().json() internally).
    // We capture what it would have sent, in case we want to inspect/log it.
    let capturedResult = null;
    const mockRes = {
        status: (code) => ({
            json: (payload) => {
                capturedResult = { code, payload };
            }
        })
    };

    await getMatchesForCandidate(mockReq, mockRes);

    if (capturedResult && capturedResult.code >= 400) {
        logger.error(`[MATCH] getMatchesForCandidate returned an error for ${candidateId}: ${JSON.stringify(capturedResult.payload)}`);
    } else {
        logger.info(`[MATCH] Finished matching for candidate: ${candidateId}`);
    }

    return capturedResult;
};

// Run match for ALL candidates (When an employer creates/updates a specific job)
// Kept as fire-and-forget on purpose: this can involve many candidates and is
// triggered from the job-creation endpoint, which shouldn't block its response
// on a potentially long full-scan match run. If you need this to also be
// reliable, apply the same "await before responding" pattern used for
// triggerSingleCandidateMatch in the caller.
const triggerAllCandidatesMatch = async (jobId) => {
    logger.info(`[MATCH] Job ${jobId} changed! Checking matches for this specific job...`);
    try {
        const candidatesSnapshot = await db.collection('candidates').get();

        const matchPromises = candidatesSnapshot.docs.map((doc) => {
            const candidateId = doc.id;
            // Pass the jobId in the query so the controller knows to filter
            const mockReq = { params: { candidateId }, query: { jobId: jobId } };
            const mockRes = { status: () => ({ json: () => {} }) };

            return getMatchesForCandidate(mockReq, mockRes).catch((err) => {
                logger.error(`[MATCH] Error matching candidate ${candidateId} for job ${jobId}: ${err.message}`);
            });
        });

        await Promise.all(matchPromises);
        logger.info(`[MATCH] Finished matching all candidates for job ${jobId}`);
    } catch (error) {
        logger.error(`[MATCH] Error triggering all candidates: ${error.message}`);
    }
};

module.exports = { triggerSingleCandidateMatch, triggerAllCandidatesMatch };