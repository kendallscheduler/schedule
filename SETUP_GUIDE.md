# How to Run Kendall Scheduler on Another Computer

You can run this application on any Mac. There are two main ways to get the code onto the new computer:

## Option 1: Copy the Folder (Easiest)
1.  **Copy** the entire `Master Schedule` folder from your SSD to the new computer (e.g., to the Desktop).
2.  **Delete old environment files** to avoid path errors:
    *   Delete the folder `webapp/backend/venv`
    *   Delete the folder `webapp/frontend/node_modules`
3.  Proceed to the "First Time Setup" section below.

## Option 2: Clone from GitHub (Developer Way)
1.  Open Terminal on the new computer.
2.  Run:
    ```bash
    git clone https://github.com/kendallscheduler/schedule.git
    cd schedule
    ```
3.  Proceed to the "First Time Setup" section below.

---

## First Time Setup

Before running the scheduler, ensure the new computer has the necessary tools installed.

### 1. Install Prerequisites
Open the **Terminal** app (Command+Space, type "Terminal") and run these commands to check if you have the tools.

*   **Check Python** (Must be version 3.9 or higher):
    ```bash
    python3 --version
    ```
    *If not found, download and install from [python.org](https://www.python.org/downloads/)*

*   **Check Node.js** (Must be version 18 or higher):
    ```bash
    node --version
    ```
    *If not found, download and install from [nodejs.org](https://nodejs.org/)*

### 2. Run the Application
Once the tools are installed and the code is on the computer:

1.  Open **Terminal**.
2.  Navigate to the folder:
    ```bash
    cd /path/to/Master\ Schedule
    ```
    *(Tip: You can type `cd`, press space, and drag the folder from Finder into the Terminal window)*
3.  Run the start script:
    ```bash
    ./start_app.sh
    ```
4.  The script will:
    *   Set up the Python environment (install backend tools).
    *   Set up the Node environment (install frontend tools).
    *   Launch the website automatically.

### 3. Access the Scheduler
Open your web browser (Chrome/Safari) and go to:
[http://localhost:3000](http://localhost:3000)

## Troubleshooting
*   **"Permission denied"**: Run `chmod +x start_app.sh` to make the script executable.
*   **"Address already in use"**: The script tries to clear this automatically, but if it fails, restart the computer to clear stuck processes.
