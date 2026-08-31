# Frontend build Dockerfile
FROM node:22-alpine AS builder

# Set working directory
WORKDIR /app

# Declare build arguments
ARG VITE_AUTH0_DOMAIN
ARG VITE_AUTH0_CLIENT_ID
ARG VITE_API_URL
ARG VITE_HASURA_ENDPOINT

# Copy package files
COPY package*.json ./

# Install all dependencies
RUN npm ci

# Copy source code
COPY . .

# Build frontend (set environment variables so Vite can read them)
RUN VITE_AUTH0_DOMAIN=$VITE_AUTH0_DOMAIN \
    VITE_AUTH0_CLIENT_ID=$VITE_AUTH0_CLIENT_ID \
    VITE_API_URL=$VITE_API_URL \
    VITE_HASURA_ENDPOINT=$VITE_HASURA_ENDPOINT \
    npm run build

# Production stage - use nginx to serve static files
FROM nginx:alpine AS production

# Install curl for health check
RUN apk add --no-cache curl

# Copy build output to nginx directory
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port 3000
EXPOSE 3000

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
