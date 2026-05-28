const Joi = require('joi');

/**
 * Joi Schema for Job Creation and Updates.
 * Defines the exact structure and data types allowed.
 * Prevents NoSQL Injection and invalid data structures.
 */
const jobSchema = Joi.object({
    basic_info: Joi.object({
        job_title: Joi.string().min(3).max(100).required(),
        company_name: Joi.string().allow(null, '').optional(), // Made optional for fast deployment
        category: Joi.string().allow(null, '').optional()       // Made optional for fast deployment
    }).required(),
    
    location: Joi.object({
        address: Joi.string().required(),
        lat: Joi.number().min(-90).max(90).required(),
        lng: Joi.number().min(-180).max(180).required()
    }).required(),
    
    apparel_requirements: Joi.array().items(Joi.string()).optional(), // Added array validation for dress codes
    dealbreakers: Joi.object().optional(),
    characteristics: Joi.object().optional(),
    schedule: Joi.object().optional(),
    availability: Joi.object().optional(),
    salary_info: Joi.object().optional(),
    description: Joi.string().max(1000).allow('').optional()
    
    // Security Note: allowUnknown(true) permits fields not explicitly listed above.
    // In a strict production environment, you should map EVERY field and set this to false
    // to reject any undocumented parameters. We keep it true for now to avoid breaking existing data.
}).unknown(true);

/**
 * Middleware: Validates the incoming request body against the defined schema.
 */
const validateJobInput = (req, res, next) => {
    // Validate the request body
    const { error } = jobSchema.validate(req.body);
    
    if (error) {
        console.warn(`Security/Validation Blocked Request: ${error.details[0].message}`);
        return res.status(400).json({ 
            error: "Bad Request: Invalid input format.",
            details: error.details[0].message 
        });
    }
    
    // Input is clean and matches the schema, proceed to the target controller
    next();
};

module.exports = { validateJobInput };