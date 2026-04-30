const { db } = require('../config/firebase');

/**
 * Sends a new message in a chat between a candidate and a job (employer).
 */
const sendMessage = async (req, res) => {
    try {
        const { candidateId, jobId, senderRole, text } = req.body;

        if (!candidateId || !jobId || !senderRole || !text) {
            return res.status(400).json({ error: "Missing required chat fields." });
        }

        // Generate a unique Chat ID combining both participants
        const chatId = `${candidateId}_${jobId}`;
        const timestamp = Date.now();

        // 1. Create the new message object
        const newMessage = {
            senderRole, // 'candidate' or 'employer'
            text,
            timestamp
        };

        // 2. Push the message to the 'messages' list inside the specific chat
        const chatRef = db.ref(`chats/${chatId}`);
        await chatRef.child('messages').push(newMessage);

        // 3. Update the chat's metadata (so we can easily sort active chats later)
        await chatRef.update({
            participants: { [candidateId]: true, [jobId]: true },
            last_updated: timestamp
        });

        res.status(200).json({ status: "success", message: "Message sent!" });

    } catch (error) {
        console.error("❌ Error sending message:", error);
        res.status(500).json({ error: "Internal Server Error" });
    }
};

/**
 * Fetches the chat history, strictly limited to the last 50 messages to save memory.
 */
const getMessages = async (req, res) => {
    try {
        const { candidateId, jobId } = req.params;
        const chatId = `${candidateId}_${jobId}`;

        // 🔥 MEMORY OPTIMIZATION: Only fetch the last 50 messages
        const messagesSnapshot = await db.ref(`chats/${chatId}/messages`)
            .orderByChild('timestamp')
            .limitToLast(50) 
            .once('value');

        if (!messagesSnapshot.exists()) {
            return res.status(200).json({ status: "success", messages: [] });
        }

        // Convert the Firebase object into an array for the Android app
        const messagesData = messagesSnapshot.val();
        const messagesArray = Object.keys(messagesData).map(key => ({
            messageId: key,
            ...messagesData[key]
        }));

        res.status(200).json({ 
            status: "success", 
            total_returned: messagesArray.length,
            messages: messagesArray 
        });

    } catch (error) {
        console.error("❌ Error fetching messages:", error);
        res.status(500).json({ error: "Internal Server Error" });
    }
};

module.exports = { sendMessage, getMessages };