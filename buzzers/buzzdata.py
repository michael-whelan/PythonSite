
from data.raw_data import flights

from enum import Enum


class buzzer(Enum):
	pilot = 0
	team = 1
	crew = 2

def data_for(buzztype):
	""" Based on the value of buzztype, perform the necessary data manipulation
		on the raw_data, then return the manipulated results as a tuple of tuples.
	"""


	raw_data = []
	if buzztype == buzzer.pilot:
		for dest, times in sorted( { d: [ t for t in flights if flights[t] == d ]
										for d in set(flights.values()) }.items()):
			raw_data.append((dest, sorted(times)))
	elif buzztype == buzzer.team:
		for time, destination in sorted(flights.items()):
			raw_data.append((time, destination))
	elif buzztype == buzzer.crew:
		for time in sorted(flights, key=lambda k: (flights[k], k)):
			raw_data.append((flights[time], time))
	else:
		raise TypeError("Only buzzer.pilot, buzzer.team, or buzzer.crew supported.")
	return tuple(raw_data)


