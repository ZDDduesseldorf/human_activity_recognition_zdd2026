# Recording file naming convention

Goal: every file can be assigned to exactly one trial, and every trial can be
found from its file names alone.

This convention is the target format for all files in the repository. Whatever
a device or tool exports, files are renamed to this format before they are
stored.

## 1. Trial ID

One ID per trial, i.e. one activity (HAR) or one continuous recording (EVT)
performed by one participant, recorded by one or more sensors at the same time:

`YYYYMMDD_Pxx_TYPE-activity_Txx`

| Field | Meaning | Example |
|---|---|---|
| `YYYYMMDD` | Date of the recording (ISO order) | `20261117` |
| `Pxx` | Participant pseudonym, two digits | `P03` |
| `TYPE` | `HAR` (activity recognition) or `EVT` (continuous event detection) | `HAR` |
| `activity` | Activity code (HAR) or scenario code (EVT), see section 2 | `walking` |
| `Txx` | Trial number of that participant, on that day, for that activity, two digits | `T01` |

Examples:

- `20261117_P03_HAR-walking_T01`
- `20261117_P03_HAR-jumping-jacks_T02`
- `20261117_P03_EVT-scenario01_T01`

All sensor files of the same trial share the same trial ID. Different sensors
of the same trial are told apart by device and position.

Participants are identified only by pseudonym. Real names never appear in file
names or in the repository.

## 2. Activity codes

HAR (one activity per trial):

| Code | Activity |
|---|---|
| `walking` | Gehen |
| `stairs` | Treppen steigen |
| `jumping-jacks` | Hampelmänner |
| `ball` | Ball werfen/fangen |
| `squats` | Squats |
| `door-handle` | Türgriff öffnen |
| `hand-washing` | Hände waschen |

Event detection (continuous recording with several events, so the code names
the scenario, not a single event):

| Code | Meaning |
|---|---|
| `scenario01`, `scenario02`, ... | Step-by-step scenario defined in the recording protocol |

The target events (clapping, drinking, sit/stand, handshake) are not part of
the file name. They are stored in the annotation file (section 4).

If the list of activities changes, this table is updated via pull request.

## 3. Sensor file names

`<trial ID>_<device>-<position>_<channel>_<stage>.<ext>`

| Field | Allowed values |
|---|---|
| `device` | `ax6`, `mbient` (add new devices via pull request) |
| `position` | `wrist-left`, `wrist-right`, `ankle-left`, `ankle-right`, `hip` (add new positions via pull request) |
| `channel` | `acc` (accelerometer only), `gyr` (gyroscope only), `imu` (accelerometer and gyroscope in one file) |
| `stage` | `raw` (unmodified device export), `proc` (standard format) |

The position is always the physical position (left/right). If the protocol
says "dominant wrist", the side that was used is recorded in the central log
(section 5).

If several units of the same device sit at the same position, add a number
after the position: `wrist-left2`.

Examples:

- `20261117_P03_HAR-walking_T01_mbient-ankle-left_imu_raw.csv`
- `20261117_P03_HAR-walking_T01_ax6-ankle-right_imu_raw.csv`
- `20261117_P03_HAR-walking_T01_mbient-ankle-left_acc_raw.csv`
- `20261117_P03_HAR-walking_T01_mbient-ankle-left_imu_proc.csv`

## 4. Annotation files

`<trial ID>_labels.csv`

One label file per trial (not per device), because all devices of a trial
share the same timeline. For HAR trials the whole trial has one activity; for
EVT trials the file lists the events with their times. The exact column format
is defined in the annotation issues.

Example: `20261117_P03_EVT-scenario01_T01_labels.csv`

## 5. Central log

There is one central log with one row per sensor file. It contains at least:
trial ID, activity/event, mode (HAR/EVT), participant, device type, sensor ID,
sensor position, validity status, duration and file name.

- The physical sensor ID (e.g. a serial number) is stored in the log, not in
  the file name.
- The file name column uses the names defined in this document.
- The original device file name (as exported) is noted in the log.
- A trial counts as recorded once its files have rows in the log.
- A CSV copy of the log is kept in `data/metadata/` so that it is versioned
  together with the data.

The dataset coverage tracking sheet currently serves as this log. Its columns
should follow the list above.

## 6. Files from devices and tools

Devices and recording tools name their exports in their own way. These names
are not part of the convention. After exporting:

- Copy each file into `data/raw/` and rename it according to section 3.
- Do not change the content of raw files, only the name.
- Note the original file name in the central log.
- Use the participant pseudonym, activity code and position codes from this
  document wherever a tool asks for a subject, activity or sensor label, so
  that renaming is straightforward.

## 7. Rules

- Lowercase for activity, device, position, channel and stage; uppercase `P`,
  `T` and `TYPE`.
- Only letters, digits, underscores and hyphens. No spaces, no umlauts.
- Underscore separates fields; hyphen separates words inside a field.
- Numbers are zero-padded (`P03`, not `P3`).
- Never reuse an ID. A repeated trial gets a new trial number, and the invalid
  one is marked in the log (validity status) instead of being deleted.

## 8. Complete example

One walking trial of participant 3 with a sensor on each ankle, annotated and
processed:

```text
data/
├── raw/
│   ├── 20261117_P03_HAR-walking_T01_mbient-ankle-left_imu_raw.csv
│   └── 20261117_P03_HAR-walking_T01_ax6-ankle-right_imu_raw.csv
├── processed/
│   ├── 20261117_P03_HAR-walking_T01_mbient-ankle-left_imu_proc.csv
│   └── 20261117_P03_HAR-walking_T01_ax6-ankle-right_imu_proc.csv
├── annotations/
│   └── 20261117_P03_HAR-walking_T01_labels.csv
└── metadata/
    └── (central log with two rows for this trial)
```

## 9. Rationale

- Date first: files sort chronologically in any file explorer.
- Pseudonyms: privacy, since the data are recordings of people.
- Trial ID with activity: files are readable without opening the log, and one
  trial corresponds to one activity.
- `HAR`/`EVT` in the ID: the two recording types are handled differently
  downstream.
- Trial number: a participant repeats activities, and invalid trials can be
  repeated without overwriting anything.
- `channel` field: devices differ in whether they export accelerometer and
  gyroscope together or separately.
- Same trial ID in sensor and label files: labels cannot be matched to the
  wrong recording.
- `raw`/`proc` stage: raw and processed versions can never be mixed up.
- Central log: the file name stays short, details live in one place.
- Renaming on import: the convention stays independent of any particular
  device or tool.

## 10. Changing this convention

Open an issue or a pull request that changes this file and give the reason for
the change. Files that were already stored under an older name are renamed
together with the change, and the log is updated.