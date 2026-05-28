# Use an official Node.js runtime as a parent image (lightweight alpine version)
FROM node:18-alpine

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install only production dependencies
RUN npm install --only=production

# Copy the rest of the application code
COPY . .

# Set the port environment variable to 8080
ENV PORT 8080

# Command to run the application
CMD [ "npm", "start" ]