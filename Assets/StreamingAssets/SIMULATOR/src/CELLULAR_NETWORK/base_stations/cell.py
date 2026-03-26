# Class 'Cell'
# Created 20/05/2018 (version 1.0)
# Modified 03/02/2021 (version 6.0) - Jose Javier Rico Palomo

import json


class Cell:
    """
        Class Cell.
        It composes the base stations. It simulates the behaviour of a coverage cell.
        It is used to divide the scenario into regions, governed by a base station. Normally, a user is connected to a BS if it is within the coverage cell of that BS.

        Attributes
        ----------
        - CELL_id [str]: cell identifier.
        - CELL_type [str]: type of base station governing the cell.

        Methods
        -------
        - __init__: Constructor. Parametrized the object according to the entered parameters.
        - __str__: information for output by file or by screen of results.
        - to_json: it dumps (in a json file) the values of the class attributes at each time instant.
    """

    CELL_id: str = ""  # Example = "CELL_1"
    CELL_type: str = ""  # "MACRO" / "SMALL"

    def __init__(self, cell_id: str, cell_type: str):
        """
            'Init' method of the class 'Cell'.
            Constructor. Parametrized the object according to the entered parameters.

            :param cell_id: cell identifier -> Example = "CELL_1".
            :param cell_type: type of base station governing the cell -> "MACRO" / "SMALL".
        """

        self.CELL_id = cell_id
        self.CELL_type = cell_type

    def __str__(self):
        """
            'To-string' method of the class 'Cell'.
            Information for output by file or by screen of results.
        """

        l1 = " - id: " + self.CELL_id
        l2 = " - Cell type: " + self.CELL_type

        return l1 + "\n" + l2

    def to_json(self, time: float, file_path: str = "/SIMULATOR/Results/cellular_network/base_stations/cells/"):
        """
            It dumps (in a json file) the values of the class attributes at each time instant.

            :param time: time instant (in seconds).
            :param* file_path: path to the folder containing the results files of the cells. Defaults to "/SIMULATOR/Results/cellular_network/base_stations/cells/".
        """

        data_dump = dict()
        cell_data = dict()

        cell_data["type"] = self.CELL_type

        data_dump[time] = cell_data

        with open(file_path+self.CELL_id, 'a') as json_file:
            json.dump(data_dump, json_file)
