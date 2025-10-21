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

# ---- Dependency installation (cached layer) ----
# Copy only dependency manifests first for caching
COPY --chown=appuser:appgroup package.json yarn.lock ./

# Install dependencies (will cache unless package files change)
RUN yarn install --frozen-lockfile

# Copy rest of the source code with correct ownership
COPY --chown=appuser:appgroup . .

# Build production files
RUN yarn run build

# Stage 2: Serve with nginx (already non-root user)
FROM cgr.dev/chainguard/nginx

# Switch to root (Chainguard Nginx runs as non-root by default later)
USER root

# Copy built static files from the build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Expose default HTTP port
EXPOSE 80

# No CMD needed - Chainguard's nginx image provides it by default
