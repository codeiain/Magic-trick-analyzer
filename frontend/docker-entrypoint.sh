#!/bin/sh
set -e

# Replace API_URL placeholder in built files if environment variable is set
if [ -n "$API_URL" ]; then
    echo "Configuring API URL to: $API_URL"
    find /usr/share/nginx/html -name "*.js" -exec sed -i "s|http://localhost:8084/api|$API_URL|g" {} \;
fi

# Replace VITE_API_URL in built files
if [ -n "$VITE_API_URL" ]; then
    echo "Configuring VITE API URL to: $VITE_API_URL"
    find /usr/share/nginx/html -name "*.js" -exec sed -i "s|http://localhost:8084|$VITE_API_URL|g" {} \;
fi

# Start nginx
exec "$@"
