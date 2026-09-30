"""Well-known measurement kinds.

A kind is just a string: the device may send any kind it wants and it will be stored
as-is. These constants only exist so that the code referring to known kinds does not
rely on string literals scattered around.
"""

# Raw kinds, as sent by the device.
HEART_RATE = "heart_rate"
SPO2 = "spo2"
BREATHING_RATE = "breathing_rate"
SWEAT = "sweat"
GSR = "gsr"

# Processed kinds, produced by processors.
HEART_RATE_STATS = "heart_rate_stats"
SPO2_STATS = "spo2_stats"
