import tkinter as tk
from tkinter import ttk
import time
from query_history import QueryHistory
from idlelib.colorizer import ColorDelegator
from idlelib.percolator import Percolator
import re


class DatabaseWidgets:
    def __init__(self, parent, db, query_mapper):
        self.parent = parent
        self.db = db
        self.query_mapper = query_mapper
        self.query_text = None
        self.results_text = None
        self.query_history = QueryHistory()
        self.workspace_file = "workspace.sql"  # Define workspace file path
        self.create_widgets()
        self.create_context_menu()

    def create_widgets(self):
        """Create main layout and initialize all widgets"""
        # Left panel - Table List
        left_frame = self.create_table_list_panel()

        # Right panel with tabs and results
        right_frame = ttk.Frame(self.parent)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Upper section with notebook (tabs)
        self.create_tabbed_interface(right_frame)

        # Results area (always visible)
        self.create_results_area(right_frame)

    def create_table_list_panel(self):
        """Create the left panel with table list"""
        left_frame = ttk.Frame(self.parent, width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.Y)
        left_frame.pack_propagate(False)  # Maintain fixed width

        # Create frame for table list and scrollbar
        table_frame = ttk.Frame(left_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        # Create scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Table list with scrollbar configuration
        table_list = tk.Listbox(table_frame, yscrollcommand=scrollbar.set)
        table_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configure scrollbar to work with table_list
        scrollbar.config(command=table_list.yview)

        # Add double-click binding
        table_list.bind("<Double-1>", self.show_table_preview)

        # Populate table list
        tables = self.db.list_tables()
        for table in tables:
            table_list.insert(tk.END, table)

        # Store reference to table_list
        self.table_list = table_list

        return left_frame

    def create_tabbed_interface(self, parent):
        """Create notebook with Query Editor and History tabs"""
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Create the two tabs
        self.create_query_editor_tab(notebook)
        self.create_history_tab(notebook)

    def create_query_editor_tab(self, notebook):
        """Create the Query Editor tab"""
        query_tab = ttk.Frame(notebook)
        notebook.add(query_tab, text="Query Editor")

        query_frame = ttk.Frame(query_tab)
        query_frame.pack(fill=tk.BOTH, expand=True)

        query_label = ttk.Label(query_frame, text="Query Editor")
        query_label.pack(anchor=tk.W)

        self.query_text = tk.Text(query_frame, height=10)
        self.query_text.pack(fill=tk.BOTH, expand=True)

        # Load saved content
        self.load_workspace()

        # Bind text changes to save workspace
        self.query_text.bind("<<Modified>>", self.save_workspace)

        # Add syntax highlighting
        color_delegator = ColorDelegator()
        # Remove background colors from syntax highlighting
        color_delegator.tagdefs["KEYWORD"] = {
            "foreground": "#007F7F",
            "background": None,
        }
        color_delegator.tagdefs["STRING"] = {
            "foreground": "#B366B3",
            "background": None,
        }  # Lighter purple
        color_delegator.prog = re.compile(
            r"""(?P<KEYWORD>SELECT|FROM|WHERE|INSERT|UPDATE|DELETE|JOIN|GROUP|BY|HAVING|ORDER|LIMIT|AND|OR|IN|LIKE|IS|NULL|CREATE|TABLE|DROP|ALTER|INDEX|UNIQUE|PRIMARY|KEY|FOREIGN|REFERENCES|CASCADE|SET|VALUES)\b|
            (?P<STRING>(?:'[^']*')|(?:"[^"]*"))""",
            re.IGNORECASE | re.VERBOSE,
        )
        Percolator(self.query_text).insertfilter(color_delegator)

        # Add Command+Return binding for Mac and Ctrl+Return for Windows/Linux
        self.query_text.bind(
            "<Command-Return>", lambda e: self.execute_query() or "break"
        )
        self.query_text.bind(
            "<Control-Return>", lambda e: self.execute_query() or "break"
        )

        execute_button = ttk.Button(
            query_frame, text="Execute Query", command=self.execute_query
        )
        execute_button.pack(pady=5)

    def create_history_tab(self, notebook):
        """Create the Query History tab"""
        history_tab = ttk.Frame(notebook)
        notebook.add(history_tab, text="Query History")

        history_frame = ttk.Frame(history_tab)
        history_frame.pack(fill=tk.BOTH, expand=True)

        # Create and configure the treeview
        columns = ("Query", "Time", "Duration", "Status")
        self.history_tree = ttk.Treeview(
            history_frame, columns=columns, show="headings"
        )

        self.configure_history_tree_columns()
        self.add_history_tree_scrollbar(history_frame)

        # Bind double-click event
        self.history_tree.bind("<Double-1>", self.load_query_from_history)

        # Load initial history
        self.refresh_history()

    def configure_history_tree_columns(self):
        """Configure the columns of the history treeview"""
        # Configure headings
        self.history_tree.heading("Query", text="Query")
        self.history_tree.heading("Time", text="Execution Time")
        self.history_tree.heading("Duration", text="Duration (s)")
        self.history_tree.heading("Status", text="Status")

        # Configure column widths
        self.history_tree.column("Query", width=300)
        self.history_tree.column("Time", width=150)
        self.history_tree.column("Duration", width=100)
        self.history_tree.column("Status", width=100)

    def add_history_tree_scrollbar(self, parent):
        """Add scrollbar to history treeview"""
        scrollbar = ttk.Scrollbar(
            parent, orient=tk.VERTICAL, command=self.history_tree.yview
        )
        self.history_tree.configure(yscrollcommand=scrollbar.set)

        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_results_area(self, parent):
        """Create the results area"""
        results_frame = ttk.Frame(parent)
        results_frame.pack(fill=tk.BOTH, expand=True)

        results_label = ttk.Label(results_frame, text="Query Results")
        results_label.pack(anchor=tk.W)

        # Create a frame to hold the text widget and scrollbars
        text_frame = ttk.Frame(results_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        # Create scrollbars
        y_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL)
        x_scrollbar = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL)

        # Create text widget with scrollbar configuration
        self.results_text = tk.Text(
            text_frame,
            height=10,
            wrap=tk.NONE,  # Disable line wrapping
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set,
        )

        # Configure scrollbars
        y_scrollbar.config(command=self.results_text.yview)
        x_scrollbar.config(command=self.results_text.xview)

        # Pack everything
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def create_context_menu(self):
        """Create right-click context menu for history tree"""
        self.context_menu = tk.Menu(self.parent, tearoff=0)
        self.context_menu.add_command(label="Copy Query", command=self.copy_query)

        # Bind right-click to show context menu
        self.history_tree.bind("<Button-3>", self.show_context_menu)

        # Bind left-click anywhere else to hide the menu
        self.parent.bind("<Button-1>", lambda e: self.context_menu.unpost())

    def show_context_menu(self, event):
        """Show context menu at mouse position"""
        # Select the item under cursor
        item = self.history_tree.identify_row(event.y)
        if item:
            self.history_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def copy_query(self):
        """Copy selected query to clipboard"""
        selected_items = self.history_tree.selection()
        if not selected_items:
            return

        selected_item = selected_items[0]
        query = self.history_tree.item(selected_item)["values"][0]

        # If the query was truncated, get the full query
        if query.endswith("..."):
            full_query = self.query_history.get_full_query(query[:-3])
            if full_query:
                query = full_query

        # Copy to clipboard
        self.parent.clipboard_clear()
        self.parent.clipboard_append(query)
        self.parent.update()  # Required to finalize clipboard update

    def execute_query(self):
        """Execute the query that contains the cursor, bounded by semicolons"""
        # Get full text and cursor position
        text = self.query_text.get("1.0", tk.END)

        # Convert text to character index
        cursor_index = len(self.query_text.get("1.0", "insert"))

        # Find the semicolon positions
        semicolon_positions = [i for i, char in enumerate(text) if char == ";"]

        # Find the query boundaries around the cursor
        query_start = 0
        query_end = len(text)

        # Find the last semicolon before the cursor
        for pos in semicolon_positions:
            if pos < cursor_index:
                query_start = pos + 1
            else:
                query_end = pos
                break

        # Extract and clean the query
        selected_query = text[query_start:query_end].strip()

        if selected_query:
            self.execute_single_query(selected_query)

    def execute_single_query(self, query):
        start_time = time.time()
        success = True

        try:
            results = self.db.execute_query(query)
            # Clear previous results
            self.results_text.delete("1.0", tk.END)

            # Format and display results using QueryMapper
            formatted_results = self.query_mapper.format_query_results(results)
            self.results_text.insert("1.0", formatted_results)

        except Exception as e:
            self.results_text.delete("1.0", tk.END)
            self.results_text.insert("1.0", f"Error: {str(e)}")
            success = False

        duration = time.time() - start_time
        self.query_history.add_query(query, duration, success)
        self.refresh_history()

    def refresh_history(self):
        """Refresh the history tree with latest queries"""
        # Clear existing items
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        # Load history from database
        history = self.query_history.get_query_history()
        for query, time, duration, success in history:
            status = "Success" if success else "Failed"
            self.history_tree.insert(
                "",
                0,
                values=(
                    query[:50] + "..." if len(query) > 50 else query,
                    time,
                    f"{duration:.2f}",
                    status,
                ),
            )

    def load_query_from_history(self, event):
        """Load and execute selected query from history"""
        selected_item = self.history_tree.selection()[0]
        query = self.history_tree.item(selected_item)["values"][0]

        # If the query was truncated, get the full query from the database
        if query.endswith("..."):
            # Get the full query from the history database
            history = self.query_history.get_query_history()
            for full_query, _, _, _ in history:
                if full_query.startswith(query[:-3]):
                    query = full_query
                    break

        # Load query into editor
        self.query_text.delete("1.0", tk.END)
        self.query_text.insert("1.0", query)

        # Execute the query
        self.execute_query()

    def show_table_preview(self, event):
        """Show first 50 entries of the selected table"""
        selection = self.table_list.curselection()
        if not selection:
            return

        table_name = self.table_list.get(selection[0])
        query = f'SELECT * FROM public."{table_name}" LIMIT 50;'

        # Append the query on a new line and place cursor at the end
        current_text = self.query_text.get("1.0", tk.END).rstrip()
        if current_text:
            query = f"\n{query}"  # Add newline only if there's existing text
        self.query_text.insert(tk.END, query)
        self.query_text.see(tk.END)  # Scroll to the end
        # Place cursor right before the semicolon
        self.query_text.mark_set(
            tk.INSERT, f"{tk.END}-2c"
        )  # -2c means 2 characters from end

        # Execute the query
        self.execute_single_query(query.rstrip(";"))  # Remove semicolon for execution

    def load_workspace(self):
        """Load query content from workspace file"""
        try:
            with open(self.workspace_file, "r") as f:
                content = f.read()
                self.query_text.delete("1.0", tk.END)
                self.query_text.insert("1.0", content)
        except FileNotFoundError:
            pass  # Ignore if file doesn't exist yet

    def save_workspace(self, event=None):
        """Save query content to workspace file"""
        if self.query_text.edit_modified():  # Check if text was modified
            content = self.query_text.get("1.0", tk.END).strip()
            with open(self.workspace_file, "w") as f:
                f.write(content)
            self.query_text.edit_modified(False)  # Reset modified flag
