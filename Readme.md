# Logistics Management System

This README provides step-by-step instructions for setting up and running the Logistics Management System.

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)
- MySQL server

## Setup Instructions

1. Clone the repository:

   ```
   git clone https://github.com/your-username/logistics-management-system.git
   cd logistics-management-system
   ```

2. Create a virtual environment (optional but recommended):

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install required packages:

   ```
   pip install mysql-connector-python requests numpy geopy python-dotenv
   ```

4. Set up the MySQL database:

   - Create a new database in MySQL for this project.

5. Create a `.env` file in the project root directory with the following content:

   ```
   DATABASE=your_database_name
   API_OPEN_CAGE=your_opencage_api_key
   ```

   Replace `your_database_name` with the name of the database you created, and `your_opencage_api_key` with your OpenCage API key.

6. Update database connection details:
   Open the Python script and modify the `create_connection()` function with your MySQL server details:

   ```python
   def create_connection():
       return mysql.connector.connect(
           host="your_host",
           user="your_username",
           password="your_password",
           database=os.getenv("DATABASE")
       )
   ```

7. Run the script:
   ```
   python logistics_management_system.py
   ```

## Usage

After running the script, you'll be presented with the admin menu. Follow the on-screen prompts to:

- Input new package data
- Check the farthest address
- Check the heaviest package
- Calculate total shipments (Domestic and International)

## Troubleshooting

If you encounter any issues:

- Ensure all required packages are installed correctly.
- Check that your MySQL server is running and accessible.
- Verify that your `.env` file contains the correct database name and API key.
- Make sure you have an active internet connection for geocoding requests.

For any other problems, please open an issue in the GitHub repository.
