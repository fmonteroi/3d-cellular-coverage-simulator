# Class 'Event'
# Created 17/02/2020 (version 3.0)
# Modified 09/02/2021 (version 6.0) - Jose Javier Rico Palomo

class Event:
    """
        Abstract class Event.
        Events are the actions in which the dummy variable information is updated.
        The event can be of type 'MN_Event', 'BS_Event' or 'Network_Event'.

        Attributes
        ----------
        - EVENT_id [str]: event identifier.
        - EVENT_time [float]: time instant at which event occurs.

        Methods
        -------
        - __str__: information for output by file or by screen of results.
        - to_dict: it creates a dictionary with the values of the object to be used by the subclass to dump the values into a json file.
    """

    EVENT_id: str = ""  # Example = "STEP_1"
    EVENT_time: float = 0.0  # s

    def __str__(self):
        """
            'To-string' method of the abstract class 'Event'.
            Information for output by file or by screen of results.
        """

        l1 = " - id: " + self.EVENT_id
        l2 = " - Time: " + str(self.EVENT_time) + " s"

        return l1 + "\n" + l2

    def to_dict(self):
        """
            It creates a dictionary with the values of the object to be used by the subclass to dump the values into a json file.
        """

        event_data = dict()

        event_data["time"] = self.EVENT_time

        return event_data
