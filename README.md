# S-Parameter Web Analyzer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A web-based tool built with Streamlit and Scikit-RF to analyze and visualize S-parameter (.s2p) files. Upload multiple Touchstone files, select a specific S-parameter (e.g., S21), view the frequency response plot (dB vs. Frequency), and download the combined data in an Excel file.

---

## ✨ Features

* **Multi-File Upload:** Upload and process multiple `.s2p` (Touchstone v1.0) files simultaneously.
* **Parameter Selection:** Choose the S-parameter (S11, S12, S21, S22) you want to analyze and plot.
* **Format Handling:** Leverages Scikit-RF to handle various Touchstone data formats (DB/Angle, Magnitude/Angle, Real/Imaginary).
* **Interactive Plotting:** Displays an interactive plot using Matplotlib showing the selected S-parameter magnitude in dB versus frequency. Frequency axis units (Hz, kHz, MHz, GHz) are automatically adjusted.
* **Frequency Point Handling:** Uses the frequency points from the first uploaded file as a reference. Files with different frequency points will trigger a warning, and their data might be excluded from the combined output if inconsistent.
* **Data Export:** Download the extracted S-parameter data for all processed files as a single Excel (.xlsx) file.
* **Plot Export:** Download the generated plot as a high-resolution PNG image.
* **User-Friendly Interface:** Simple web interface built with Streamlit.
* **Multi-OS Font Support:** Includes logic to automatically find and use appropriate Japanese fonts for graph labels on macOS, Windows, and Linux (requires fonts like Hiragino Sans, Meiryo UI, or Noto Sans CJK JP to be installed).

## 🛠️ Technology Stack

* **Python 3.x**
* **Streamlit:** Web application framework
* **Scikit-RF (skrf):** Core library for RF/Microwave engineering, S-parameter file parsing and handling
* **Pandas:** Data manipulation and Excel export
* **NumPy:** Numerical computations
* **Matplotlib:** Data visualization and plotting
* **Openpyxl:** Engine for writing .xlsx files

## 🚀 Setup and Installation

Follow these steps to set up and run the application locally:

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/your-username/your-repository-name.git](https://github.com/your-username/your-repository-name.git)
    cd your-repository-name
    ```
    (Replace `your-username/your-repository-name` with your actual GitHub username and repository name)

2.  **Create and Activate a Virtual Environment:** (Recommended)
    ```bash
    # Create venv
    python3 -m venv venv

    # Activate venv
    # On macOS/Linux:
    source venv/bin/activate
    # On Windows:
    .\venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    Make sure you have a `requirements.txt` file in the repository root. If not, create one from your working virtual environment using `pip freeze > requirements.txt`.
    ```bash
    pip install -r requirements.txt
    ```
    The `requirements.txt` should contain at least:
    ```
    streamlit
    scikit-rf
    pandas
    numpy
    matplotlib
    openpyxl
    # watchdog (optional, recommended by Streamlit)
    ```

## ▶️ Usage

1.  **Activate the virtual environment** (if not already active):
    ```bash
    # On macOS/Linux:
    source venv/bin/activate
    # On Windows:
    .\venv\Scripts\activate
    ```

2.  **Run the Streamlit App:**
    ```bash
    streamlit run s2p_webapp.py
    ```
    (Replace `s2p_webapp.py` with the actual name of your Python script file)

3.  **Access the App:** The application should automatically open in your default web browser, usually at `http://localhost:8501`.

4.  **Using the App:**
    * Click the "Browse files" button or drag and drop your `.s2p` files onto the file uploader.
    * Select the desired S-parameter from the dropdown menu.
    * Click the "解析実行" (Analyze Run) button.
    * The plot and data table will be displayed.
    * Use the download buttons below the plot and data table to save the results.

5.  **(Optional) Network Access:** To allow other computers on your local network to access the app (use with caution, ensure your firewall allows the port):
    ```bash
    streamlit run s2p_webapp.py --server.address=0.0.0.0 --server.port=8501
    ```
    Then access it using `http://<your-ip-address>:8501`.

## 📄 Input File Format

* The application expects **Touchstone v1.0 `.s2p` files**.
* It relies on Scikit-RF for parsing, which supports common formats (DB/Angle, Magnitude/Angle, Real/Imaginary) and frequency units (Hz, kHz, MHz, GHz).
* Ensure your files have a standard Touchstone header (e.g., `# HZ S MA R 50`).

## ❓ Troubleshooting

* **Japanese Font Issues / 文字化け:** If graph labels appear as squares (□□□), ensure you have a suitable Japanese font installed on your system (e.g., Hiragino Sans on macOS, Meiryo UI or Yu Gothic UI on Windows, Noto Sans CJK JP on Linux). The script attempts to find one automatically. Clearing the Matplotlib font cache might help after installing new fonts (run `python -c "import matplotlib; print(matplotlib.get_cachedir())"` to find the cache location, then delete the directory contents).
* **Dependency Errors:** Make sure all packages listed in `requirements.txt` are correctly installed within your activated virtual environment (`pip install -r requirements.txt`).
* **Performance:** Processing a large number of files or files with a very high number of frequency points may take time and consume significant memory, depending on your hardware.

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
