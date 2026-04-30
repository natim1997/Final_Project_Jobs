const winston = require('winston');

/**
 * Winston Logger Configuration
 * Log Levels: error (0), warn (1), info (2), http (3), verbose (4), debug (5), silly (6)
 */
const logger = winston.createLogger({
    level: 'info',
    format: winston.format.combine(
        winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
        winston.format.json() // Logs are saved in JSON format for easy analysis
    ),
    transports: [
        // 1. Write all logs with level 'error' and below to 'error.log'
        new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
        // 2. Write all logs with level 'info' and below to 'combined.log'
        new winston.transports.File({ filename: 'logs/combined.log' }),
    ],
});

// If we're not in production, also log to the console with pretty colors
if (process.env.NODE_ENV !== 'production') {
    logger.add(new winston.transports.Console({
        format: winston.format.combine(
            winston.format.colorize(),
            winston.format.simple()
        ),
    }));
}

module.exports = logger;