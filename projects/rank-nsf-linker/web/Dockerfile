# Stage 1: Build the app
FROM cgr.dev/chainguard/node AS build

# Create app directory and set working dir
WORKDIR /app

# Switch to root to add user/group and fix ownership
USER root

# Install yarn globally
RUN npm install -g yarn

# Create a non-root user and group
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Change ownership of /app so the non-root user can write there
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Copy package.json AND package-lock.json first for caching
COPY --chown=appuser:appgroup package.json yarn.lock node_modules ./

# Install dependencies (will cache unless package files change)
RUN yarn

# Copy rest of the source code with correct ownership
COPY --chown=appuser:appgroup . .

# Build production files
RUN yarn run build

# Stage 2: Serve with nginx (already non-root user)
FROM cgr.dev/chainguard/nginx

# Clean default nginx files (running as root in build time)
USER root

# Copy built static files from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx config
COPY conf/nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Run nginx
CMD ["nginx", "-g", "daemon off;"]
