# Stage 1: Build the React Application
FROM node:20-alpine AS builder

WORKDIR /frontend

# Copy dependency configs
COPY package.json package-lock.json* ./

# Install packages
RUN npm install

# Copy source code and build production bundle
COPY . .
RUN npm run build

# Stage 2: Serve using Nginx
FROM nginx:1.25-alpine

# Copy custom nginx routing configs (proxies REST & WS to backend)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy build files from builder stage to nginx static server directory
COPY --from=builder /frontend/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
