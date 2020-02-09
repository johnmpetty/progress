# Progress

A chord progression generator and trainer for musicians written by John Petty
and licensed under the GPLv3.

# Using Progress

Progress is a command-line Python utility that helps a musician practice playing
along with a chord progression.

Each time Progress generates a progression it will print a description in this
format:

```
Scale: G♯ Minor
Progression: i (G♯ Minor), VI (F Major), ii° (A♯ Minor Diminished), v (D♯ Minor)
BPM: 120 (press enter to generate a new progression)
```

After an initial delay so you can read the result, a pre-roll starts with a
countdown from 4 and metronome clicks.

Progress will now cycle through the chords as the metronome continues with prints
like these to show what the current chord is:

```
I (B Major) next is vii° (A Minor Diminished)
```

Play along as they transition whether by root notes, chords, arpeggios, or melodic
motifs.

When you have mastered a progression press ENTER to generate a new one and repeat.
Use CTRL-C to exit Progress.

## Options

### Only Common Progressions

Starting with `--only-use-common-progressions` causes progress to pull from a list
of common simple progressions instead of generating its own.

This is mutually exclusive with starting on non roots as no generation happens when
this option is used.

### Starting Notes

Starting with `--start-on-non-root` allows generated progressions to start on any degree.
This leads to more unusual progressions than those only starting on the root note but is
helpful for more difficult practice.

## The Metronome

You can replace the metronome sound by replacing metronome.wav with a short sound of your
choice. The default sound is an Elektron Machine Drum triangle tone sampled by me which you
may use for any purpose.

# Development

## Notes

Progress was written using Python 3.8.

The `simpleaudio` package is the only non-standard dependency.

It's linted with `pylint` and I wrap lines and just over 80 characters per personal
preference for two tab development.

## Todo

Planned features:
* Playing the specific chords as an alternative to a metronome tone so you know you're
  playing the right notes
* A GUI or more mature TUI that doesn't write new lines
* Altered chord suggestions (add, sus, slash, etc)
* Multiple time signatures
* Suggestions for style of what to play (e.g. 8 notes, syncopated, arpegiated, etc)
* Break out generation vs the trainer

Planned improvements:
* Remove repetition that can occur when generating progressions (e.g. I IV V I IV)
* Implement breaking for a new progression less hacky
* Tests
* Packaging
