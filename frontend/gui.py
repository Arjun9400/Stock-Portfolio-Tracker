import sys
import datetime
import pickle
import pandas as pd
from PySide6.QtWidgets import  QLineEdit, QApplication, QMainWindow,QDialog,QTableWidgetItem,  QVBoxLayout, QHBoxLayout, QGridLayout, QWidget, QPushButton, QTableView, QHeaderView, QTabWidget, QMessageBox, QLabel, QCheckBox
from PySide6.QtGui import QStandardItemModel, QStandardItem, QFont, QColor
from PySide6.QtCore import Qt, QSortFilterProxyModel
import webbrowser
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import backend.stockhandle as sh
import threading
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk


class CustomSortFilterProxyModel(QSortFilterProxyModel):
    def lessThan(self, left, right):
        left_data = self.sourceModel().data(left)
        right_data = self.sourceModel().data(right)

        # Convert to float if possible, otherwise keep as string
        try:
            left_value = float(left_data)
        except ValueError:
            left_value = left_data

        try:
            right_value = float(right_data)
        except ValueError:
            right_value = right_data

        # Ensure both values are of the same type for comparison
        if isinstance(left_value, float) and isinstance(right_value, float):
            return left_value < right_value
        else:
            return str(left_value) < str(right_value)


class CSVViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        maincsv = pd.read_csv('data/main.csv')
        holdingscsv = pd.read_csv('data/holdings.csv')

        self.setWindowTitle("Stock Viewer")
        self.setGeometry(100, 100, 800, 600)  # Set initial geometry
        self.setWindowState(Qt.WindowMaximized)  # Maximize the window

        # Central widget 
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Layout
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Tab widget
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)

        # First tab
        self.tab1 = QWidget()
        self.tab_widget.addTab(self.tab1, "Stock Viewer")

        # Layout for the first tab
        self.tab1_layout = QVBoxLayout(self.tab1)

        # Table view
        self.table_view = QTableView()
        self.tab1_layout.addWidget(self.table_view)


        # Enable sorting
        self.table_view.setSortingEnabled(True)
        # Enable column resizing
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        
        self.hide_none_checkbox = QCheckBox("Show Owned")
        self.tab1_layout.addWidget(self.hide_none_checkbox)
        self.hide_none_checkbox.stateChanged.connect(self.toggle_none_rows)
        
        self.switch_button = QPushButton("Switch to Second Tab")
        self.switch_button.clicked.connect(self.switch_to_second_tab)
        self.tab1_layout.addWidget(self.switch_button)
        
        update_layout = QHBoxLayout()
        self.update_button = QPushButton("Update Full")
        self.update_button.clicked.connect(self.update_full)
        self.update_current_button = QPushButton("Update Current Price")
        update_layout.addWidget(self.update_button)
        self.last_update_label_full = QLabel("Last Update:")
        update_layout.addWidget(self.last_update_label_full)
        with open("data/full.pkl", "rb") as file:
            # Deserialize the list from the file
            time_full = pickle.load(file)
            self.last_update_label_full.setText(f'Last Updated: {time_full[0]}')

        
        
        self.update_info_label = QLabel(self.tab1)
        update_layout.addWidget(self.update_info_label)
        
        self.update_current_button.clicked.connect(self.update_current)
        update_layout.addWidget(self.update_current_button)
        
        self.last_update_label_current = QLabel("Last Update:")
        update_layout.addWidget(self.last_update_label_current)
        with open("data/current.pkl", "rb") as file:
            # Deserialize the list from the file
            time_current = pickle.load(file)
            self.last_update_label_current.setText(f'Last Updated: {time_current[0]}')


        self.tab1_layout.addLayout(update_layout)

        # Second tab
        self.tab2 = QWidget()
        self.tab_widget.addTab(self.tab2, "Stock Info")
        
        # Layout for the second tab
        self.tab2_layout = QVBoxLayout(self.tab2)
        
        # Table view for the second tab
        self.table_view_2 = QTableView()
        self.tab2_layout.addWidget(self.table_view_2)
        
        # Horizontal layout for buttons
        self.tab2_button_layout = QHBoxLayout()
        
        # Add buttons to the horizontal layout
        self.search_graph_button = QPushButton("Search Graph")
        self.search_graph_button.clicked.connect(self.search_graph)
        self.tab2_button_layout.addWidget(self.search_graph_button)
        
        self.financial_button = QPushButton("Search Financials")
        self.financial_button.clicked.connect(self.open_financials)
        self.tab2_button_layout.addWidget(self.financial_button)
        
        # Add the horizontal button layout to the main vertical layout
        self.tab2_layout.addLayout(self.tab2_button_layout)
    
        
        

        # Third tab
        self.tab3 = QWidget()
        self.tab_widget.addTab(self.tab3, "Holdings")

        # Layout for the third tab
        self.tab3_layout = QGridLayout(self.tab3)
        
        # Get the last two rows of the DataFrame
        last_two_rows = holdingscsv.tail(2)
        
        # Extract the 'Total Amt' values from the last two rows
        #last_amt = last_two_rows.iloc[-1]['Total Amt']
        last_amt = maincsv['Total Amount'].sum()
        second_last_amt = last_two_rows.iloc[-2]['Total Amt']
        total_amt_sum = round(maincsv['Total Amount'].sum())
        suffix_amount = last_amt-second_last_amt
        suffix_percent = sh.ssround((suffix_amount/second_last_amt)*100)
        
        
        if suffix_amount > 0:
            self.sum_label = QLabel(f"Your Current Holdings are: {sh.commafy(total_amt_sum)}  ▲{suffix_percent}% ({sh.commafy(suffix_amount)})")
            self.sum_label.setStyleSheet("color: rgb(0, 175, 0);")
        elif suffix_amount < 0:
            self.sum_label = QLabel(f"Your Current Holdings are: {sh.commafy(total_amt_sum)}  ▼{suffix_percent}% ({sh.commafy(suffix_amount)})")
            self.sum_label.setStyleSheet("color: rgb(255, 70,70 );")

        # Create QLabel for the total amount
        
        self.sum_label.setAlignment(Qt.AlignCenter)

        # Increase font size
        font = QFont()
        font.setPointSize(36)  # Set the font size you want
        self.sum_label.setFont(font)
        #self.sum_label.setStyleSheet("color: rgb(0, 175, 0);")

        # Add QLabel to the grid layout
        self.tab3_layout.addWidget(self.sum_label, 0, 0, 1, 2, Qt.AlignCenter)

        # Table view for the third tab
        self.table_view_3 = QTableView()
        self.tab3_layout.addWidget(self.table_view_3, 1, 0, 1, 2)

        self.table_view_3.setSortingEnabled(True)
        
        # Button to switch to second tab
        # Create a button in tab 3
        self.plot_button = QPushButton("Plot Data")
        self.plot_button.clicked.connect(lambda state, df=holdingscsv, x_column='Date', y_column='Total Amt': self.plot_data(df, x_column, y_column))
        self.tab3_layout.addWidget(self.plot_button,2,0,1,2)
        
        self.tab4 = QWidget()
        self.tab_widget.addTab(self.tab4, "Add Tickers")

        # Layout for the fourth tab
        self.tab4_layout = QVBoxLayout(self.tab4)

        self.value_input = QLineEdit(self)
        self.value_input.setPlaceholderText("Enter a value here...")

        self.submit_button = QPushButton("Submit", self)
        self.submit_button.clicked.connect(self.store_value)

        self.display_label = QLabel("NA")

        # Add widgets to layout
        self.tab4_layout.addWidget(self.value_input)
        self.tab4_layout.addWidget(self.submit_button)
        self.tab4_layout.addWidget(self.display_label) 
        
        self.display_csv('main.csv')
        self.display_holdings_csv('holdings.csv')

    def store_value(self):
        # Get the value from the input field
        value = self.value_input.text()
        
        if value:
            # Store the value in the list
            
            
            # Update the display label with the list of entered values
            self.display_label.setText(f"Entered Values: {value}")
        
        # Clear the input field for the next value
        self.value_input.clear()
        
        


        
        

    
    def display_csv(self, file_name):
        df = pd.read_csv(file_name)
        
        model = QStandardItemModel()
    
        # Set header
        model.setHorizontalHeaderLabels(df.columns)
    
        # Set rows
        for row_idx, row in enumerate(df.itertuples(index=False)):
            items = [QStandardItem("" if pd.isna(item) else str(item)) for item in row]
    
            model.appendRow(items)
    
        # Apply the custom sort filter proxy model
        proxy_model = CustomSortFilterProxyModel()
        proxy_model.setSourceModel(model)
        self.table_view.setModel(proxy_model)
        # Resize columns to fit content initially
        self.table_view.resizeColumnsToContents()

    def display_holdings_csv(self, file_name):
        df = pd.read_csv(file_name)
        model = QStandardItemModel()

        # Set header
        model.setHorizontalHeaderLabels(df.columns)

        # Set rows
        for row in df.itertuples(index=False):
            items = []
            for i, item in enumerate(row):
                item_str = "" if pd.isna(item) else str(item)
                if i == 0:
                    item_str = item_str[:10]  # Truncate to 10 characters if it's the first column
                items.append(QStandardItem(item_str))
            model.appendRow(items)

        self.table_view_3.setModel(model)
        self.table_view_3.resizeColumnsToContents()
        self.table_view_3.sortByColumn(0, Qt.DescendingOrder)

    def switch_to_second_tab(self):
        selected_indexes = self.table_view.selectionModel().selectedIndexes()
        if not selected_indexes:
            QMessageBox.warning(self, "No selection", "Please select a cell to view the respective row in the second tab.")
            return

        selected_row_index = selected_indexes[0].row()
        proxy_model = self.table_view.model()
        model = proxy_model.sourceModel()

        row_data = []
        for col in range(model.columnCount()):
            item = model.item(proxy_model.mapToSource(selected_indexes[0]).row(), col)
            if item is not None:
                row_data.append(item.text())
            else:
                row_data.append("")

        new_model = QStandardItemModel(1, model.columnCount())
        for col, data in enumerate(row_data):
            qitem = QStandardItem(data)
            new_model.setItem(0, col, qitem)
            new_model.setHorizontalHeaderItem(col, model.horizontalHeaderItem(col).clone())

        self.table_view_2.setModel(new_model)
        self.table_view_2.resizeColumnsToContents()

        self.tab_widget.setCurrentIndex(1)
        
    def update_current(self):
        # Instead of directly executing the updater script, run it in a separate thread
        updater_thread = threading.Thread(target=self.run_updater)
        updater_thread.start()
        

    def run_updater(self):
        counter = 0
        current_list = []
        datacsv = pd.read_csv('main.csv')
        for index, row in datacsv.iterrows():
            stock_id = row['Stock ID']
            current_price = sh.get_currentprice(stock_id)
            datacsv.at[index, 'Current Price'] = current_price
            self.update_info_label.setText(f'Updating Current Price: {counter}/565')
            counter+=1
        datacsv.to_csv('main.csv', index=False)
        
        current_time = datetime.datetime.now()
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M")
        # Define the list you want to save
        current_list.append(formatted_time)
        
        # Open a file in binary write mode ('wb')
        with open("current.pkl", "wb") as file:
            file.write(b"")
            # Serialize the list and save it to the file
            pickle.dump(current_list, file)
        
        
        # Open the file in binary read mode ('rb')
        with open("current.pkl", "rb") as file:
            # Deserialize the list from the file
            time_current = pickle.load(file)
            self.last_update_label_current.setText(f'Last Updated: {time_current[0]}')
        self.update_info_label.setText('Done Current!')
        
    def update_full(self):
        updater_thread_2 = threading.Thread(target=self.run_updater_2)
        updater_thread_2.start()
    
    def run_updater_2(self):
        #self.update_current()
        full_list = []
        counter = 0
        datacsv = pd.read_csv('main.csv')
        self.update_info_label.setText('Updating Stock History...')
        #sh.update_csv("5d")
        for index, row in datacsv.iterrows():
            stock_id = row['Stock ID']
            current_price_2 = sh.get_currentprice(stock_id)
            datacsv.at[index, 'Current Price'] = current_price_2
            current_price = row['Current Price']
            percent = sh.get_percent(stock_id, current_price, 0, 0, 0, 2)
            datacsv.at[index, '1 Day'] = percent
            percent = sh.get_percent(stock_id, current_price, 0, 0, 1, 0)
            datacsv.at[index, '1 Week'] = percent
            percent = sh.get_percent(stock_id, current_price, 0, 1, 0, 0)
            datacsv.at[index, '1 Month'] = percent
            percent = sh.get_percent(stock_id, current_price, 0, 6, 0, 0)
            datacsv.at[index, '6 Month'] = percent
            percent = sh.get_percent(stock_id, current_price, 1, 0, 0, 0)
            datacsv.at[index, '1 Year'] = percent
            percent = sh.get_percent(stock_id, current_price, 5, 0, 0, 0)
            datacsv.at[index, '5 Year'] = percent
            counter +=1            
            self.update_info_label.setText(f'Updating Full: {counter}/565')
            

        self.update_info_label.setText('Finishing...')
        sh.calculate_total_holdings(-5)
        datacsv.to_csv('main.csv', index=False)
        current_time = datetime.datetime.now()
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M")
        # Define the list you want to save
        full_list.append(formatted_time)
        
        # Open a file in binary write mode ('wb')
        with open("full.pkl", "wb") as file:
            file.write(b"")
            # Serialize the list and save it to the file
            pickle.dump(full_list, file)
        
        
        # Open the file in binary read mode ('rb')
        with open("full.pkl", "rb") as file:
            # Deserialize the list from the file
            time_full = pickle.load(file)
            self.last_update_label_full.setText(f'Last Updated: {time_full[0]}')
        self.update_info_label.setText('Done Full!')
        pass
            
        
        
        
    def toggle_none_rows(self, state):
  
        if state == 2:  # Checked
            for row in range(self.table_view.model().rowCount()):
                index = self.table_view.model().index(row, 10)  # Check column 9
                value = index.data()
                if value == '':
                    self.table_view.setRowHidden(row, True)

        else:
            for row in range(self.table_view.model().rowCount()):
                self.table_view.setRowHidden(row, False)
                
    def plot_data(self, df, x_column, y_column):
        # Extract x and y columns for plotting
        x_data = df[x_column]
        y_data = df[y_column]

        # Create a figure
        fig = Figure()
        ax = fig.add_subplot(111)
        ax.plot(x_data, y_data)
        ax.set_xlabel(x_column)
        ax.set_ylabel(y_column)
        ax.set_title('Data Plot')


        # Create a canvas
        canvas = FigureCanvas(fig)
        canvas.show()
                
    def search_graph(self):
        model = self.table_view_2.model()

        # Since the second tab table has only 1 row, directly access the 2nd column (index 1)
        if model.rowCount() > 0 and model.columnCount() > 1:
            third_column_value = model.item(0, 2).text()
            webbrowser.open(f"https://www.google.com/search?q={third_column_value}+share+price+nse")
        else:
            QMessageBox.warning(self, "No data", "The table does not have sufficient columns.")
            
    def open_financials(self):
        model = self.table_view_2.model()

        # Since the second tab table has only 1 row, directly access the 2nd column (index 1)
        if model.rowCount() > 0 and model.columnCount() > 1:
            second_column_value = model.item(0, 1).text()
            webbrowser.open(f"https://finance.yahoo.com/quote/{second_column_value}/financials/")
        else:
            QMessageBox.warning(self, "No data", "The table does not have sufficient columns.")
    
    

    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = CSVViewer()
    viewer.show()
    sys.exit(app.exec())

