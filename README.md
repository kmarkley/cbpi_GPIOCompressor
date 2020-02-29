# GPIOCompressor for CraftBeerPi

This plugin adds Actors for controlling compressors (like refrigerators/freezers). To prevent damage to the compressor, you should not turn the compressor on and off repeatedly. It's best to have a delay between cycles. This actor allows for that delay.

There are two types of compressor
- GPIOCompressor: A standard GPIO output compressor
- RelayCompressor: A GPIO compressor with inverted output

Both accept a number of minutes to delay before allowing turning the compressor back on again. The switch will display as though it is on, but the GPIO will not trigger unless enough time has elapsed.

Additionally, a duty cycle may be set to prevent the compressor from running continuously when executing large temperature changes.  Set the number of minutes the compressor should run and rest each cycle. As with the delay, CBPI will show the actor as on even when the compressor is off during the rest portion of the duty cycle.
