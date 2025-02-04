class QueryMapper:
    def format_query_results(self, results):
        if not isinstance(results, dict) or "records" not in results:
            return str(results)

        if not results["records"]:
            return "No records found"

        # Extract column names and types from metadata
        headers = []
        if "columnMetadata" in results:
            headers = [
                f"{col['name']} ({col['typeName']})"
                for col in results["columnMetadata"]
            ]
        else:
            num_columns = len(results["records"][0])
            headers = [f"Column {i+1}" for i in range(num_columns)]

        # Calculate column widths
        col_widths = [len(h) for h in headers]
        for row in results["records"]:
            for i, col in enumerate(row):
                value = str(list(col.values())[0])
                col_widths[i] = max(col_widths[i], len(value))

        # Create header
        header_row = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
        separator = "-" * len(header_row)

        # Format table
        table_lines = [header_row, separator]

        # Add data rows
        for row in results["records"]:
            values = []
            for i, col in enumerate(row):
                value = str(list(col.values())[0])
                values.append(value.ljust(col_widths[i]))
            table_lines.append(" | ".join(values))

        return "\n".join(table_lines)
