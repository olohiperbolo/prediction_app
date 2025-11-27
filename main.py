import pandas as pd

#create script to read csv file and print 5 rows

def read_and_print_csv(file_path):
    # Read the CSV file
    df = pd.read_csv(file_path)
    
    # Print the first 5 rows
    print(df.head())

if __name__ == "__main__":
    file_path = 'data.csv'
    read_and_print_csv(file_path)