import sys
import random
import mysql.connector
import pandas as pd
from datetime import datetime
from faker import Faker
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox, QTableWidget, QTableWidgetItem, QHBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

# Initialize Faker
fake = Faker()

# Database Connection
conn = mysql.connector.connect(
    host="localhost",  # Change if MySQL is hosted on a different server
    user="root",  # Replace with their MySQL username
    password="1234",  # Replace with their MySQL password
    database="soil_health"  # Ensure the database name matches the one created
)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS soil_health (
        id INT AUTO_INCREMENT PRIMARY KEY,
        farm_location VARCHAR(255),
        test_date DATE,
        nitrogen FLOAT,
        phosphorus FLOAT,
        potassium FLOAT,
        pH FLOAT,
        moisture FLOAT
    )
''')
conn.commit()

# Function to Generate Random Soil Data
def generate_soil_data():
    return (
        fake.city(),
        datetime.strftime(fake.date_between(start_date="-2y", end_date="today"), "%Y-%m-%d"),
        round(random.uniform(0.1, 5.0), 2),
        round(random.uniform(0.1, 5.0), 2),
        round(random.uniform(0.1, 5.0), 2),
        round(random.uniform(4.5, 8.5), 2),
        round(random.uniform(5.0, 50.0), 2)
    )

# Function to Insert Data into Database
def insert_random_data(batch_size=100):
    data_batch = [generate_soil_data() for _ in range(batch_size)]
    cursor.executemany('''
        INSERT INTO soil_health (farm_location, test_date, nitrogen, phosphorus, potassium, pH, moisture)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    ''', data_batch)
    conn.commit()
    return batch_size

# Function to Fetch Data
def fetch_data():
    cursor.execute("SELECT id, farm_location, test_date, nitrogen, phosphorus, potassium, pH, moisture FROM soil_health ORDER BY test_date")
    return cursor.fetchall()

# Function to Delete Data
def delete_selected_data(record_id):
    cursor.execute("DELETE FROM soil_health WHERE id = %s", (record_id,))
    conn.commit()

# Function to Delete All Data
def delete_all_data():
    cursor.execute("DELETE FROM soil_health")
    conn.commit()

# GUI Class
class SoilHealthApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Soil Health Data Manager")
        self.setGeometry(100, 100, 800, 600)
        
        main_layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        
        self.insert_button = QPushButton("Insert Random Data")
        self.insert_button.clicked.connect(self.insert_data)
        button_layout.addWidget(self.insert_button)

        self.export_button = QPushButton("Export Data as CSV")
        self.export_button.clicked.connect(self.export_csv)
        button_layout.addWidget(self.export_button)

        self.graph_button = QPushButton("Show Graph")
        self.graph_button.clicked.connect(self.update_graph)
        button_layout.addWidget(self.graph_button)
        
        self.refresh_button = QPushButton("Refresh Data")
        self.refresh_button.clicked.connect(self.load_data)
        button_layout.addWidget(self.refresh_button)
        
        self.delete_button = QPushButton("Delete Selected Data")
        self.delete_button.clicked.connect(self.delete_data)
        button_layout.addWidget(self.delete_button)

        self.delete_all_button = QPushButton("Delete All Records")
        self.delete_all_button.clicked.connect(self.delete_all_data)
        button_layout.addWidget(self.delete_all_button)
        
        main_layout.addLayout(button_layout)

        self.data_table = QTableWidget()
        self.data_table.setColumnCount(8)
        self.data_table.setHorizontalHeaderLabels(["ID", "Farm Location", "Test Date", "Nitrogen", "Phosphorus", "Potassium", "pH", "Moisture"])
        main_layout.addWidget(self.data_table)

        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        main_layout.addWidget(self.canvas)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
        self.load_data()

    def insert_data(self):
        inserted = insert_random_data()
        QMessageBox.information(self, "Insertion Successful", f"{inserted} records inserted successfully!")
        self.load_data()
    
    def load_data(self):
        data = fetch_data()
        self.data_table.setRowCount(len(data))
        for row_idx, row_data in enumerate(data):
            for col_idx, col_data in enumerate(row_data):
                self.data_table.setItem(row_idx, col_idx, QTableWidgetItem(str(col_data)))
    
    def export_csv(self):
        data = fetch_data()
        df = pd.DataFrame(data, columns=["ID", "Farm Location", "Test Date", "Nitrogen", "Phosphorus", "Potassium", "pH", "Moisture"])
        df.to_csv("soil_health_data.csv", index=False)
        QMessageBox.information(self, "Export Successful", "Data exported as CSV successfully!")

    def update_graph(self):
        data = fetch_data()
        if not data:
            QMessageBox.warning(self, "No Data", "No data available to display!")
            return
        
        df = pd.DataFrame(data, columns=["ID", "Farm Location", "Test Date", "Nitrogen", "Phosphorus", "Potassium", "pH", "Moisture"])
        df["Test Date"] = pd.to_datetime(df["Test Date"])
        
        self.ax.clear()
        self.ax.plot(df["Test Date"], df["Nitrogen"], label="Nitrogen", marker='o')
        self.ax.plot(df["Test Date"], df["Phosphorus"], label="Phosphorus", marker='s')
        self.ax.plot(df["Test Date"], df["Potassium"], label="Potassium", marker='^')
        
        self.ax.set_xlabel("Test Date")
        self.ax.set_ylabel("Nutrient Levels")
        self.ax.set_title("Soil Nutrient Trends")
        self.ax.legend()
        self.ax.grid()
        self.canvas.draw()
    
    def delete_data(self):
        selected_row = self.data_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "No Selection", "Please select a row to delete.")
            return
        
        record_id = self.data_table.item(selected_row, 0).text()
        delete_selected_data(record_id)
        QMessageBox.information(self, "Deletion Successful", "Selected record deleted successfully!")
        self.load_data()
    
    def delete_all_data(self):
        reply = QMessageBox.question(self, 'Delete All Records', 'Are you sure you want to delete all records?', 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            delete_all_data()
            QMessageBox.information(self, "Deletion Successful", "All records have been deleted successfully!")
            self.load_data()

# Main Execution
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SoilHealthApp()
    window.show()
    sys.exit(app.exec())