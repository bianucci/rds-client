import boto3


class AuroraDBManager:
    def __init__(self, database_name, resource_arn, secret_arn):
        self.client = boto3.client("rds-data")
        self.database_name = database_name
        self.resource_arn = resource_arn
        self.secret_arn = secret_arn

    def execute_query(self, sql_query):
        """Execute a SQL query and return the response"""
        try:
            response = self.client.execute_statement(
                resourceArn=self.resource_arn,
                secretArn=self.secret_arn,
                database=self.database_name,
                sql=sql_query,
                includeResultMetadata=True,
            )
            return response
        except self.client.exceptions.BadRequestException as e:
            print(f"Error executing query: {e}")
            return None

    def list_tables(self):
        """List all tables in the database"""
        sql_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER by table_name asc
        """

        response = self.execute_query(sql_query)
        if response and "records" in response:
            tables = [record[0]["stringValue"] for record in response["records"]]
            return tables
        return []
