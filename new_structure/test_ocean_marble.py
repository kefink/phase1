#!/usr/bin/env python3
"""
Simple test app to showcase the Ocean Marble Glassmorphism design
"""
from flask import Flask, render_template_string

app = Flask(__name__)

# Simple HTML template to showcase the ocean marble design
TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ocean Marble Glassmorphism - Kirima Primary School</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
    <div class="background">
        <div class="container">
            <h1>Kirima Primary School</h1>
            <h2>Ocean Marble Glassmorphism Design</h2>
            <p>Experience the beautiful ocean marble aesthetic with flowing glassmorphism effects.</p>
            
            <div class="login-form">
                <div class="form-group">
                    <label for="username">Username</label>
                    <input type="text" id="username" name="username" placeholder="Enter your username">
                </div>
                
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" placeholder="Enter your password">
                </div>
                
                <div class="login-buttons">
                    <a href="#" class="btn">Login as Admin</a>
                    <a href="#" class="btn btn-secondary">Login as Teacher</a>
                    <a href="#" class="btn btn-outline">Login as Class Teacher</a>
                </div>
            </div>
        </div>
    </div>
    
    <div style="margin: 2rem auto; max-width: 90%;">
        <div class="dashboard-card">
            <div class="card-header">
                <h3>Ocean Marble Dashboard Card</h3>
            </div>
            <p>This card showcases the beautiful ocean marble glassmorphism effect with flowing colors inspired by natural marble patterns.</p>
            <ul>
                <li><strong>Cream (#EEE8B2):</strong> Soft, warm base tone</li>
                <li><strong>Gold (#C18D52):</strong> Rich accent color</li>
                <li><strong>Dark Teal (#081B1B):</strong> Deep, mysterious depth</li>
                <li><strong>Deep Teal (#203B37):</strong> Ocean-like richness</li>
                <li><strong>Sage Green (#5A8F76):</strong> Natural, calming tone</li>
                <li><strong>Mint (#96CDB0):</strong> Fresh, light accent</li>
            </ul>
        </div>
        
        <div class="dashboard-card">
            <div class="card-header">
                <h3>Interactive Elements</h3>
            </div>
            <p>All elements feature smooth transitions and hover effects that enhance the marble aesthetic.</p>
            <div class="login-buttons">
                <a href="#" class="btn">Primary Button</a>
                <a href="#" class="btn btn-outline">Outline Button</a>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(TEMPLATE)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
