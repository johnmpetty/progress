#!/usr/bin/env python3

""" Chord trainer and the progression generator + progression representation
to use it. """

import random
import sys
import time
import threading

import simpleaudio

class Progression:
    """ Representation of a progression. """
    def __init__(self, note, scale, progression, bpm):
        self.note = note
        self.scale = scale
        self.progression = progression
        self.bpm = bpm
        self._current_chord = 0

    def __str__(self):
        progression_string = ", ".join(self.progression)
        return (f"Scale: {self.note} {self.scale}\n"
                + f"Progression: {progression_string}\n"
                + f"BPM: {self.bpm}")

    def _next_chord_index(self):
        return (self._current_chord + 1) % len(self.progression)

    def quarter_note_seconds(self):
        """ Return the fraction of a second per quarter note at this BPM. """
        return 60 / self.bpm

    def current_chord(self):
        """ Return the current chord. """
        return self.progression[self._current_chord]

    def next_chord(self):
        """ Return the next chord. """
        return self.progression[self._next_chord_index()]

    def advance_chord(self):
        """ Continue to the next chord. """
        self._current_chord = self._next_chord_index()

class ProgressionGenerator:
    """ Random chord progression generator. """

    # The different notes including their enharmonic alternatives.
    NOTES = [["A"],
             ["A♯", "B♭"],
             ["B"],
             ["C"],
             ["C♯", "D♭"],
             ["D"],
             ["D♯", "E♭"],
             ["E"],
             ["F"],
             ["F♯", "G♭"],
             ["G"],
             ["G♯", "A♭"]]

    # The two scales we support.
    SCALES = ["Minor", "Major"]

    # The chords that make up each scale for picking the first in a
    # generated progression when not forcing the root.
    CHORDS = {"Major": ["I", "ii", "iii", "IV", "V", "iv", "vii°"],
              "Minor": ["i", "ii°", "III", "iv", "v", "VI", "VII"]}

    # Which chords can follow others when generating a progression.
    CHORD_FOLLOWING = {"I":    ["ii", "iii", "IV", "V", "vi", "vii°"],
                       "i":    ["ii°", "III", "iv", "v", "VI", "VII"],
                       "ii":   ["IV", "V", "vii°"],
                       "ii°":  ["i", "v"],
                       "III":  ["iv", "VI"],
                       "iii":  ["ii", "IV", "vi"],
                       "IV":   ["I", "iii", "V", "vii°"],
                       "iv":   ["i", "ii°", "v"],
                       "V":    ["I"],
                       "v":    ["i", "VI"],
                       "vi":   ["ii", "IV", "V", "I"],
                       "VI":   ["ii°", "iv"],
                       "VII":  ["iii"],
                       "vii°": ["I", "iii"]}

    # Integer offset to the note of a particular scale degree.
    ROMAN_TO_OFFSET = {"I": 0,
                       "i": 0,
                       "ii": 2,
                       "ii°": 2,
                       "III": 4,
                       "iii": 3,
                       "IV": 5,
                       "iv": 5,
                       "V": 7,
                       "v": 7,
                       "vi": 9,
                       "VI": 9,
                       "VII": 11,
                       "vii°": 10}

    # Common progressions to draw from when not dynamically generating.
    COMMON_PROGRESSIONS = {"Major": [["I", "IV", "V"],
                                     ["ii", "V", "I"],
                                     ["I", "ii", "IV"],
                                     ["I", "IV", "I", "V"],
                                     ["I", "IV", "V", "IV"],
                                     ["I", "V", "vi", "IV"],
                                     ["I", "ii", "IV", "V"],
                                     ["I", "vi", "ii", "V"]],
                           "Minor": [["i", "iv", "v"],
                                     ["i", "VI", "VII"],
                                     ["ii", "v", "i"],
                                     ["i", "iv", "VII"],
                                     ["i", "iv", "i", "v"],
                                     ["i", "iv", "v", "iv"],
                                     ["i", "VI", "III", "VII"]]}

    # Minimum BPM used.
    BPM_MIN = 80
    # Maximum BPM used.
    BPM_MAX = 160
    # Minimum difference in BPMs used.
    BPM_STEP = 10

    # Minimum number of chords in a generated progression.
    PROGRESSION_LENGTH_MIN = 3
    # Maximum number of chords in a generated progression.
    PROGRESSION_LENGTH_MAX = 5

    def __init__(self):
        self.shuffled_notes = []
        self.shuffled_scales = []
        self.shuffled_bpms = []
        self.shuffled_progressions = []
        # Whether to start progressions only on the tonic for easy and more
        # conventional sounds or start on any chord randomly for a challenge
        # at the expense of musicality.
        self.start_on_non_root = False
        # Whether to draw from the most common progressions instead of
        # generating arbitrary ones dynamically with chord leading.
        self.only_use_common_progressions = False

    def _roman_to_chord(self, root, roman):
        """ Convert roman notation to the written form.

        For example with a root value of "A" and a roman of "iv" return
        "D Minor" as we're converting to the minor 4th degree.
        """
        if "I" in roman or "V" in roman:
            scale = "Major"
        else:
            scale = "Minor"

        root_index = self._note_to_index(root)
        chord_offset = self.ROMAN_TO_OFFSET[roman]
        chord_note_index = (root_index + chord_offset) % len(self.NOTES)

        # If the chord note is an accidental we want to makes sure it matches the
        # style of the root. If it's not an accidental there's only one choice.
        note_possibilities = self.NOTES[chord_note_index]
        if len(note_possibilities) == 2:
            if "♯" in root or "♭" not in root:
                note = note_possibilities[0]
            else:
                note = note_possibilities[1]
        else:
            note = note_possibilities[0]

        qualifier = ""
        if "°" in roman:
            qualifier += " Diminished"

        return f"{note} {scale}{qualifier}"

    def _note_to_index(self, note):
        """ Get the index of a note in the notes structure.

        This is necessary so that we can name non-roman chords based on the
        degree. """
        for i in range(len(self.NOTES)):
            if note in self.NOTES[i]:
                return i

    def new_progression(self):
        """ Return a new progression. """
        if not self.shuffled_notes:
            self.shuffled_notes = random.sample(self.NOTES, k=len(self.NOTES))
        # Make one final choice as we may need to choose between a sharp and flat.
        note = random.choice(self.shuffled_notes.pop())

        if not self.shuffled_scales:
            self.shuffled_scales = random.sample(self.SCALES, k=len(self.SCALES))
        scale = self.shuffled_scales.pop()

        if self.only_use_common_progressions:
            if not self.shuffled_progressions:
                progressions = self.COMMON_PROGRESSIONS[scale]
                self.shuffled_progressions = random.sample(progressions,
                                                           k=len(progressions))
            progression = self.shuffled_progressions.pop()
        else:
            if self.start_on_non_root:
                sequence = [random.choice(self.CHORDS[scale])]
            else:
                # Take advantage of consistency in ordering to assign I or i.
                sequence = [self.CHORDS[scale][0]]
            goal_length = random.randint(self.PROGRESSION_LENGTH_MIN,
                                         self.PROGRESSION_LENGTH_MAX)
            while len(sequence) < goal_length:
                current_chord = sequence[-1]
                next_chord = random.choice(self.CHORD_FOLLOWING[current_chord])
                sequence.append(next_chord)
            progression = sequence

        if not self.shuffled_bpms:
            bpms = range(self.BPM_MIN, self.BPM_MAX, self.BPM_STEP)
            self.shuffled_bpms = random.sample(bpms, k=len(bpms))
        bpm = self.shuffled_bpms.pop()

        progression = [f"{r} ({self._roman_to_chord(note, r)})" for r in progression]

        return Progression(note, scale, progression, bpm)


class Metronome:
    """ Simple metronome player. """
    METRONOME_FILE = "metronome.wav"

    def __init__(self, interval_seconds):
        self.interval_seconds = interval_seconds
        self.player = simpleaudio.WaveObject.from_wave_file(self.METRONOME_FILE)

    def play(self):
        """ Play the metronome sound. """
        self.player.play()

class Trainer:
    """ Presentation of the generated progressions. """
    NOTES_PER_MEASURE = 8
    # How long to wait before beginning the preroll.
    INITIAL_DELAY_SEC = 3
    # How many metronome sounds before starting.
    PREROLL_COUNT = 4

    def __init__(self):
        self.generator = ProgressionGenerator()
        self.current_note = 0
        self._keep_playing = True

    def _breakable_wait(self, seconds):
        for _ in range(seconds * 10):
            time.sleep(0.1)
            if not self._keep_playing:
                break

    def _play(self):
        self._keep_playing = True
        progression = self.generator.new_progression()
        print(progression, "(press enter to generate a new progression)")
        metronome = Metronome(progression.quarter_note_seconds())
        sys.stdout.flush()
        sys.stdout.write("(Waiting for the inital delay)\r")
        self._breakable_wait(self.INITIAL_DELAY_SEC)
        for countdown in range(self.PREROLL_COUNT, 0, -1):
            if not self._keep_playing:
                break
            sys.stdout.flush()
            sys.stdout.write(f"Preroll counting down from: {countdown}  \r")
            metronome.play()
            time.sleep(progression.quarter_note_seconds())
        note = 0
        while self._keep_playing:
            metronome.play()
            sys.stdout.flush()
            # Add some white space at the end to ensure that differing character
            # counts in chord names are still overwritten.
            sys.stdout.write(progression.current_chord() + " next is "
                             + progression.next_chord() + "                 \r")
            time.sleep(progression.quarter_note_seconds())
            note += 1
            if note == self.NOTES_PER_MEASURE:
                progression.advance_chord()
                note = 0

    def train(self):
        """ Main training loop. """
        while True:
            play_thread = threading.Thread(target=self._play)
            play_thread.daemon = True
            play_thread.start()
            input("")
            self._keep_playing = False
            play_thread.join()
            print("\n\n")

ONLY_COMMON = "--only-use-common-progressions"
START_ON_NON_ROOT = "--start-on-non-root"

USAGE = """progress - A chord progression training tool

Play along with the current chord in a progression.

Usage: progress [OPTIONS]

Options:
    --start-on-non-root Start progressions on any degree
    --only-use-common-progressions Only use fixed common progressions
"""

def main():
    """ Start the trainer with any options. """
    args = sys.argv[1:]
    if "help" in args or "--help" in args or "-h" in args:
        print(USAGE)
        sys.exit(0)
    trainer = Trainer()
    if ONLY_COMMON in args and START_ON_NON_ROOT in args:
        print("Can't specify start on non root when using common progressions")
        sys.exit(1)
    if ONLY_COMMON in args:
        trainer.generator.only_use_common_progressions = True
        args = [arg for arg in args if arg != ONLY_COMMON]
    if START_ON_NON_ROOT in args:
        trainer.generator.start_on_non_root = True
        args = [arg for arg in args if arg != START_ON_NON_ROOT]
    if len(args) != 0:
        bad_args = " ".join(args)
        print(f"Unexpected arguments: {bad_args}")
        sys.exit(1)
    trainer.train()

if __name__ == "__main__":
    main()
