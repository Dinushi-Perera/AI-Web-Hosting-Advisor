FROM node:22-alpine
WORKDIR /app

COPY package*.json ./
RUN npm config set fetch-retries 5 \
    && npm config set fetch-retry-mintimeout 10000 \
    && npm config set fetch-retry-maxtimeout 120000 \
    && npm ci --include=dev --no-audit --no-fund
COPY . .

ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
ARG NEXT_PUBLIC_DEMO_MODE=false
ARG NEXT_PUBLIC_AUTH_REQUIRED=true
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL \
    NEXT_PUBLIC_DEMO_MODE=$NEXT_PUBLIC_DEMO_MODE \
    NEXT_PUBLIC_AUTH_REQUIRED=$NEXT_PUBLIC_AUTH_REQUIRED \
    NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

RUN npm run build

EXPOSE 3000
CMD ["npm","run","start","--","-H","0.0.0.0"]
