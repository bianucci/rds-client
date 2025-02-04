from aurora_db_manager import AuroraDBManager
from db_config import DBConfiguration
import tkinter as tk
from query_mapper import QueryMapper
from database_widgets import DatabaseWidgets


class DatabaseGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Aurora Database Manager")

        # Initialize database connection
        config = DBConfiguration()
        self.db = AuroraDBManager(
            config.db_name, config.resource_arn, config.secret_arn
        )
        self.query_mapper = QueryMapper()

        # Create widgets using the new class
        self.widgets = DatabaseWidgets(self.root, self.db, self.query_mapper)


if __name__ == "__main__":
    root = tk.Tk()
    app = DatabaseGUI(root)
    root.geometry("1200x600")  # Set initial window size
    root.mainloop()
