import sys
import os
import subprocess
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return '''
    <html>
        <head>
            <title>Athlete Analytics Dashboard</title>
            <meta http-equiv="refresh" content="0; url=/api/streamlit">
        </head>
        <body>
            <h1>Redirecting to Athlete Dashboard...</h1>
        </body>
    </html>
    '''

@app.route('/api/streamlit')
def streamlit_proxy():
    try:
        # This is a workaround - Vercel isn't ideal for Streamlit
        return jsonify({
            "message": "Streamlit dashboard requires a persistent server. Consider using Streamlit Cloud instead.",
            "alternative": "https://share.streamlit.io/",
            "repo": "b421090143-debug/athlete-dashboard"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
