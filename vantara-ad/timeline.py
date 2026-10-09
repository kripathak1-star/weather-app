"""Shared timing for picture, music and SFX (seconds). 120 BPM -> one beat every 0.5 s."""
FPS = 60
DUR = 30.0
BPM = 120
BEAT = 60.0 / BPM

SCENES = [(0.0, 5.0), (5.0, 10.0), (10.0, 18.0), (18.0, 25.0), (25.0, 30.0)]

# scene 1
S1_STOP = 0.12
S1_SCROLL = 0.42
S1_RAMP = (3.85, 5.0)        # velocity zoom into the text
# scene 2
S2_BURST = 5.55              # particle explosion
S2_LOGO_FRONT = 6.1          # emblem finishes its 3D rotation
S2_WORDMARK = 6.3
S2_MORPH = (9.45, 10.15)     # liquid morph into scene 3
# scene 3
S3_CLICKS = [11.55, 13.55, 16.05]
S3_WHIPS = [12.75, 15.25]
# scene 4
S4_SWEEPS = [22.55, 23.55]
S4_RISER = (23.9, 25.0)
# scene 5
S5_SHOCK = 25.05
S5_TAG = 25.9
S5_URL = 26.6
