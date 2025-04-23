import sqlite3

class Interface():
    def __init__(self,table_name,parameters:list):
        """
        Parameters must be of form : "column_name type"
        """
        self.name = table_name

        self.db = sqlite3.connect("interface.db", check_same_thread=False)
        self.cursor = self.db.cursor()
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({", ".join(parameters)})")

    def read(self,parameters=[]):
        """
        Parameters must be of form : "column_name value"
        """
        if parameters == []:
            self.cursor.execute(f"SELECT * FROM {self.name}")
            return self.cursor.fetchall()
        else:
            self.cursor.execute(f"SELECT * FROM {self.name} WHERE {" AND ".join([f"{arg[0]}='{arg[1]}'" for arg in parameters])}")
            return self.cursor.fetchall()

    def write(self,values:list):
        """
        Values must be a list of values in order of the columns
        """
        try:
            self.cursor.execute(f"INSERT INTO {self.name} VALUES ({",".join(["?"]*len(values))})",values)
        except sqlite3.OperationalError:
            raise UserWarning("The number of values does not match the number of columns")

        self.db.commit()

    def update(self, markers: list, new_values: list):
        """
        Markers are the differentiating values that allow to locate the row in the form : "column_name value"
        New values are a list of values to be set like so : "column_name value"
        """
        set_clause = ', '.join([
            f"{arg.split(' ', maxsplit=1)[0]}='{arg.split(' ', maxsplit=1)[1]}'" 
            for arg in new_values
        ])
        where_clause = ' AND '.join([
            f"{arg.split(' ', maxsplit=1)[0]}='{arg.split(' ', maxsplit=1)[1]}'"
            for arg in markers
        ])
        self.cursor.execute(f"UPDATE {self.name} SET {set_clause} WHERE {where_clause}")
        self.db.commit()

    def close(self):
        try:
            self.db.close()
        except:
            pass

    