# Image Insight - Blur Detection & Description

A web application that analyzes images to detect blurring or generates a detailed description using AI (Gemini 2.0 Flash).

## Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) must be installed and running.

## How to Run

1.  **Clone the repository** (if you haven't already).
2.  **Double-click `start_app.bat`**.
    - This will build the Docker container, start the server, and automatically open your web browser to `http://localhost:5000`.

## Manual Run (if script fails)

1.  Open a terminal in this directory.
2.  Run:
    ```bash
    docker-compose up --build
    ```
3.  Open `http://localhost:5000` in your browser.

## Features
- **Blur Detection**: Uses Laplacian variance to detect if an image is blurry.
- **AI Description**: Uses OpenRouter (Google Gemini 2.0 Flash) to describe clear images.
- **Modern UI**: Colorful, responsive, and easy to use.
