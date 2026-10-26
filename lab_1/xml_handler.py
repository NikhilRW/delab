import pandas as pd

df = pd.read_xml("data.xml")

# print("Printing json in the split method : ", df.to_json(orient="split"))
# print("Printing json in the index method : ", df.to_json(orient="index"))
# print("Head of the file : ", df.head(), end="\n\n")
# print("Tail of the file : ", df.tail(), end="\n\n")
# print("Shape of the file : ", df.shape, end="\n\n")
# print("Description of the file : ", df.describe(), end="\n\n")
# print("columns types : ", df.dtypes, end="\n\n")

is_exit = False


def modify_value():
    row_num = input("Enter row number to change : ")
    column_name = input("Enter column name of the row : ")
    new_value = input("Enter new value : ")
    df.loc[int(row_num), column_name] = new_value


def delete_row():
    row_num = input("Enter row number to delete : ")
    df.drop(index=int(row_num), inplace=True)


def add_row():
    new_index = len(df)
    for column in df.columns:
        new_value = input(f"Enter value for column '{column}' : ")
        if df[column].dtype.name.__contains__("int"):
            df.loc[new_index, column] = int(new_value)
        elif df[column].dtype.name.__contains__("float"):
            df.loc[new_index, column] = float(new_value)
        else:
            df.loc[new_index, column] = new_value


def add_column():
    new_column_name = input("Enter new column name : ")
    df.insert(df.columns.__len__(), new_column_name, "", allow_duplicates=True)
    data_type = input("Enter data type of the column (string,number,boolean) : ")
    df[new_column_name] = None
    match data_type:
        case "string":
            df[new_column_name] = df[new_column_name].astype(str)
        case "number":
            df[new_column_name] = df[new_column_name].astype(float)
        case "boolean":
            df[new_column_name] = df[new_column_name].astype(bool)
        case _:
            df[new_column_name] = df[new_column_name].astype(str)


def do_action_based_on_option_selected(option):
    match option:
        case "1":
            modify_value()
        case "2":
            delete_row()
        case "3":
            add_row()
        case "4":
            add_column()
        case "5":
            global is_exit
            is_exit = True


while is_exit != True:
    option_selected = input(
        "Enter 1.Modify value 2.Delete Row 3.Add Row 4.Add Column 5.Exit : "
    )
    do_action_based_on_option_selected(option_selected)

df.to_xml("data.xml")
