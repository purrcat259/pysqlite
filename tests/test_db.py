import os
import pytest
import neopysqlite.exceptions as exception
from neopysqlite.neopysqlite import Neopysqlite


# TODO: Pass database filename and tables names via argparse to run tests against a specific database

os.system('sqlite3 test.db < fill_test_db.sql')

test_rows = [
    ('', None),
    ('apple', 'juice'),
    ('lemon', 'lime')
]


class TestNeopysqliteDB(Neopysqlite):
    def __init__(self):
        super().__init__(database_name='Test DB', db_path=test_db_path, verbose=True)

    def reset(self):
        os.system('C:\sqlite3\sqlite3.exe test.db < fill_test_db.sql')

current_directory = os.path.dirname(os.path.abspath(__file__))
test_db_path = os.path.join(current_directory, 'test.db')
db = TestNeopysqliteDB()


class TestDBAccess:
    def test_db_exists(self):
        assert os.path.isfile(test_db_path), 'Database file does not exist'

    def test_db_accessible(self):
        assert os.access(test_db_path, os.R_OK), 'Database file could not be opened'


class TestDBNotEmpty:
    def test_table_exists(self):
        db.reset()
        data = db.get_all_rows(table='sqlite_sequence')
        table_names = [field[0] for field in data]
        assert 'table_one' in table_names, 'Test table "table_one" does not exist'

    def test_db_is_not_empty(self):
        db.reset()
        data = db.get_all_rows(table='table_one')
        assert len(data) > 0, 'Test table "table_one" is empty but it should not be empty'

    def test_getting_rows_from_nonexistent_table_throws_exception(self):
        db.reset()
        with pytest.raises(exception.PysqliteTableDoesNotExist):
            data = db.get_all_rows(table='table_two')


class TestInitialiseInvalidDB:
    def test_db_does_not_exist_throws_exception(self):
        with pytest.raises(exception.PysqliteCannotAccessException):
            db = Neopysqlite(database_name='foo', db_path='odfsjiojsdf.jojiv', verbose=True)


class TestDBContents:
    def test_tables_exist(self):
        db.reset()
        test_table_names = [
            'sqlite_sequence',
            'table_one'
        ]
        actual_table_names = db.get_table_names()
        assert test_table_names == actual_table_names, 'Table names retrieved not matching test names'

    def test_row_counts(self):
        db.reset()
        data = db.get_all_rows(table='table_one')
        assert len(data) == 5, 'Test row count not as expected'


class TestDBInsert:
    def test_insert_row(self):
        db.reset()
        db.insert_row(table='table_one', row_string='(NULL, ?, ?)', row_data=('turkey', 'goose'))
        data = db.get_all_rows('table_one')
        assert data[-1][1] == 'turkey', 'Requested field 1 not as expected'
        assert data[-1][2] == 'goose', 'Requested field 2 not as expected'

    def test_insert_row_to_non_existent_table_throws_exception(self):
        db.reset()
        with pytest.raises(exception.PysqliteTableDoesNotExist):
            db.insert_row(table='oifdjgiodjf', row_string='', row_data=())


class TestDBDelete:
    def test_delete_new_inserted_row(self):
        db.reset()
        db.insert_rows(table='table_one', row_string='(NULL, ?, ?)', row_data_list=test_rows)
        db.delete_rows(table='table_one', delete_string='something_not_null = ?', delete_value=('lemon',))
        data = db.get_all_rows(table='table_one')
        assert data[-1][1] == 'apple', 'Inserted field was not properly deleted'

    def test_delete_all_rows(self):
        db.reset()
        db.delete_rows(table='table_one')
        data = db.get_all_rows('table_one')
        assert data == [], 'All the table rows were not properly deleted'


class TestDBUpdate:
    def test_update_one_row(self):
        db.reset()
        db.update_rows(table='table_one', update_string='something_not_null = ?', update_values=('test',), filter_string='something_null = \'chutney\'')
        data = db.get_specific_rows(table='table_one', filter_string='something_null = \'chutney\'')
        assert data[0][1] == 'test'


class TestDBConnection:
    def test_db_connection_open_after_initialisation(self):
        assert db.connection_open is True

    def test_db_connection_closed_after_closing(self):
        db_to_close = Neopysqlite('Testing DB Connection', db_path=test_db_path, verbose=True)
        db_to_close.close_connection()
        assert db_to_close.connection_open is False


class TestSQLStringExecution:
    def test_passing_invalid_sql_throws_exception(self):
        with pytest.raises(exception.PysqliteExecutionException):
            db.execute_sql(sql_string='DELETE * FROM table_one')

    def test_passing_valid_sql(self):
        db.execute_sql(sql_string='DROP TABLE table_one')
        assert 'table_one' not in db.get_table_names()


