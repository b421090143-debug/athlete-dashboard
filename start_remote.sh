#!/bin/bash

# Kill any existing streamlit processes
pkill -f streamlit

# Start streamlit with remote access configuration
streamlit run app.py \
    --server.port 8080 \
    --server.address 0.0.0.0 \
    --server.enableCORS false \
    --server.enableXsrfProtection false \
    --server.headless true

echo "Streamlit starting on port 8080..."
echo "Local access: http://localhost:8080"
echo "Network access: http://$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}'):8080"
