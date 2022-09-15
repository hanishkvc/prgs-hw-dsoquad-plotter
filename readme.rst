#######################
DSOQuad/DS203 Plotter
#######################
Author: HanishKVC
Version: 20220914IST2253


Overview
##########

General
=========

Allow one to look at signal captured by the pocket oscilloscope, either
has a Dat file or Buf file.

This is tested for DSOQuad / DS203 wrt the Wildcat firmware.

Note that the sampled data is stored in these files similar to how it
would appear on the device screen, so to get enough resolution in the
captured data, ensure that the Volts/Div and Time/Div is fine enough
to capture what you are interested in.

Dat file doesnt contain meta data wrt the captured signal and also it
contains only one screen worth of data (ie around 400 samples). Other
than signal levels in terms of screen position, the only other info
it contains is the baseline wrt each channel.

In addition to the channel signal data, Buf file contains meta data like
volts/div, times/div, channel baseline levels, ...
Buf files are potentially more useful, if the oscilloscope is setup to
dump data when in the large buffer mode.


Additional
============

One can get the following additional info from / wrt buf files, when
interacting with the plot

* voltage and time wrt each position on the plot

* diff in voltage and time between the last two clicked positions.

* guess of freq wrt the data signal

* overlaying of user specified time divisions from a position specified
  by them. This also includes custom markers wrt each of these timedivs.

  It also shows a guessed binary digital data interpretation, wrt data
  signal in each of these overlaid user specified time divisions.

  Additionally 8bit hex value wrt guessed binary digital data can be
  printed, if using S(tart),0-7(BitPositions),s(top) as the markers.
  This is useful if looking at serial bus data following the template
  of Start-BitPositions-End.

The above correspond to signal data belonging to ytickschannel.


Usage
########

Cmdline arguments
===================

The needed arguments

--file <path/dso_saved_buf_file>

  the saved buf file that should be plotted

Arguments that may be used if required

--format <buf|dat|auto>

  load either the dat or the buf signal/waveform dump/save file

--channels <0|1|2|3|01|13|0123|...>

  specify which channels should be displayed as part of the plot

--dtype <b|B>

  whether to treat the sample data as signed or unsigned(default)

--ytickschannel <0|1|2|3>

  specify the channel that will be used for deciding the y ticks.
  Defaults to the 1st channel in the specified list of channels.

--filterdata <convolve|fft|"">

  filter the signal data using the specified logic and plot the
  same additionally to the original signal data.

  convolve or convolve:[w1,w2,...wN]

  fft or fft:ratioOfDataTowardsEndToClearToZero

--overlaytimedivs <time[:StringOfCharMarkers]>

  Allows a overlay of timedivs, based on the time granularity
  specified, starting from position where mouse-right button is
  clicked.

  If a StringOfCharMarkers is specified, place one char at a time
  from this string into adjacent overlay time divs.

  Also show signal data interpreted as binary digital values, wrt
  each overlaid time division, as it appears at their centers.

  Additionally 8bit hex value wrt guessed binary digital data can be
  printed, if using S(tart),0-7(BitPositions),s(top) as the markers.
  This is useful if looking at serial bus data following the template
  of Start-BitPositions-End.

  NOTE: This only works for buf files and not dat files, bcas dat
  files dont have time or voltage info in them.

  As the time/div supported by the oscilloscope need not directly
  align with the freq characteristic / bitrate of the signal being
  monitored, so one can use this option to overlay custom time/divs
  that matches what one is interested in wrt the signals.


Interactions
=============

Wrt Buf files
+++++++++++++++

* clicking a location on the plot will give its voltage and time info

* when two different locations have been clicked on the plot
  * show the difference in voltage and time btw those points
  * show the number of up/down waveform movements and a rough freq

* Clicking anywhere using right mouse button, will show a overlay of
  timedivs, with a time period specified using --overlaytimedivs.

  It will also show a set of markers wrt each time div, if user has
  specified the same as part of --overlaytimedivs.

  If markers S|s|0-7 are used, then S indicates Start marker,
  s indicates end marker and 0-7 indicates bit position of
  corresponding bit of data. Inturn the value infered/cumulated
  at the time of seeing the end marker is printed on the plot
  next to the s end marker. The Bit position indicators need not
  be in order.


Examples
==========

A example trying to look at Midi data capture, with its 32uSec bit time, 3 byte msgs of 1Start+8Data+0Parity+1Stop bits

./dso-plotter.py --file path/to/file.buf --overlaytimedivs 32e-6:S01234567sS01234567sS01234567s
./dso-plotter.py --file path/to/file.buf --overlaytimedivs 1/31250:S01234567sS01234567sS01234567s

