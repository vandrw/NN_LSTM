# Code fetched from mathigatti/midi2img

from music21 import converter, instrument, note, chord
import json
import sys
import numpy as np
from imageio import imwrite
import os


def extractNote(element):
    return int(element.pitch.ps)


def extractDuration(element):
    return element.duration.quarterLength


def get_notes(notes_to_parse):
    """ Get all the notes and chords from the midi files in the ./midi_songs directory """
    durations = []
    notes = []
    start = []

    for element in notes_to_parse:
        if isinstance(element, note.Note):
            if element.isRest:
                continue

            start.append(element.offset)
            notes.append(extractNote(element))
            durations.append(extractDuration(element))

        elif isinstance(element, chord.Chord):
            if element.isRest:
                continue
            for chord_note in element.notes:
                start.append(element.offset)
                durations.append(extractDuration(element))
                notes.append(extractNote(chord_note))

    return {"start": start, "pitch": notes, "dur": durations}


def midi2image(midi_path):
    # print("[INFO] Checking " + midi_path.split(os.sep)[-1].split(".")[0] + f"_Piano_0.png")
    # if (os.path.exists("midi_imgs2" + os.sep + midi_path.split(os.sep)[-1].split(".")[0] + f"_Piano_0.png")):
    #     print("[SKIP] Already exists!")
    #     return

    mid = converter.parse(midi_path)

    instruments = instrument.partitionByInstrument(mid)

    data = {}

    try:
        i = 0
        for instrument_i in instruments.parts:
            if instrument_i.partName != "Piano":
                continue

            notes_to_parse = instrument_i.recurse()

            if instrument_i.partName is None:
                data["instrument_{}".format(i)] = get_notes(notes_to_parse)
                i += 1
            else:
                data[instrument_i.partName] = get_notes(notes_to_parse)

        # data["Piano"] = get_notes(instruments.parts["Piano"].recurse())

    except Exception as e:
        # print("[ERR] Failed! " + str(e))
        # return
        notes_to_parse = mid.flat.notes
        data["instrument_0".format(i)] = get_notes(notes_to_parse)

    resolution = 0.25

    for instrument_name, values in data.items():
        # https://en.wikipedia.org/wiki/Scientific_pitch_notation#Similar_systems

        upperBoundNote = 127
        lowerBoundNote = 21
        maxSongLength = 106

        index = 0
        prev_index = 0
        repetitions = 0
        while repetitions < 1:
            if prev_index >= len(values["pitch"]):
                break

            matrix = np.zeros((upperBoundNote-lowerBoundNote,
                               maxSongLength), dtype=np.uint8)

            pitchs = values["pitch"]
            durs = values["dur"]
            starts = values["start"]

            for i in range(prev_index, len(pitchs)):
                pitch = pitchs[i]

                dur = int(durs[i]/resolution)
                start = int(starts[i]/resolution)

                if dur+start - index*maxSongLength < maxSongLength:
                    for j in range(start, start+dur):
                        if j - index*maxSongLength >= 0:
                            matrix[pitch-lowerBoundNote, j -
                                   index*maxSongLength] = 255
                else:
                    prev_index = i
                    break
            
            if (np.sum(matrix) == 0):
                print("[WARNING] Empty image! Skipping!")
                index += 1
                repetitions += 1
                continue

            imwrite("midi_imgs2" + os.sep + midi_path.split(
                "/")[-1].replace(".mid", f"_{instrument_name}_{index}.png"), matrix)
            index += 1
            repetitions += 1


if __name__ == "__main__":
    import sys
    midi_path = sys.argv[1]
    midi2image(midi_path)
