#!/usr/bin/env python3
"""
Visualize XDF file with MNE (interactive viewer like GDF)
"""

import mne
import pyxdf
import numpy as np
import matplotlib.pyplot as plt

# Load XDF file
xdf_file = 'block_Default.xdf'
print(f"Loading XDF file: {xdf_file}\n")

data, header = pyxdf.load_xdf(xdf_file)

# Identify EEG and marker streams
eeg_stream = None
marker_stream = None

for stream in data:
    stream_type = stream['info']['type'][0]
    if stream_type.lower() == 'eeg':
        eeg_stream = stream
    elif stream_type.lower() == 'markers':
        marker_stream = stream

if eeg_stream is None:
    print("Error: No EEG stream found!")
    exit(1)

# Extract EEG data
eeg_data = eeg_stream['time_series'].T  # MNE expects (channels, samples)
eeg_timestamps = eeg_stream['time_stamps']
sfreq = float(eeg_stream['info']['nominal_srate'][0])

# Check data range to determine units
data_max = np.abs(eeg_data).max()
print(f"\nData range: {eeg_data.min():.2f} to {eeg_data.max():.2f}")
print(f"Maximum absolute value: {data_max:.2f}")

# Convert to Volts if data is in microvolts
# MNE expects data in Volts, and will display in µV automatically
if data_max > 1:  # Data is likely in microvolts
    print("→ Data appears to be in microvolts (µV)")
    print("→ Converting to Volts for MNE...")
    eeg_data = eeg_data * 1e-6  # Convert µV to V
else:
    print("→ Data appears to be in Volts")

print(f"\nEEG data shape: {eeg_data.shape}")
print(f"Sampling rate: {sfreq} Hz")
print(f"Duration: {eeg_timestamps[-1] - eeg_timestamps[0]:.2f} seconds")

# Create channel names (try to get from metadata, or use defaults)
n_channels = eeg_data.shape[0]
ch_names = [f'Ch{i+1}' for i in range(n_channels)]

# Try to get real channel names if available
try:
    if 'desc' in eeg_stream['info'] and eeg_stream['info']['desc']:
        desc = eeg_stream['info']['desc'][0]
        if desc is not None and 'channels' in desc:
            channels = desc['channels'][0]['channel']
            ch_names = [ch['label'][0] for ch in channels]
except:
    pass

print(f"Channels: {ch_names}")

# Create MNE info object
info = mne.create_info(
    ch_names=ch_names,
    sfreq=sfreq,
    ch_types='eeg'
)

# Create MNE Raw object
raw = mne.io.RawArray(eeg_data, info)

# Set the first timestamp as the start time
raw.set_meas_date(eeg_timestamps[0])

# Select only Ch2, Ch3, Ch4 for analysis
channels_to_keep = ['Ch2', 'Ch3', 'Ch4']
available_channels = [ch for ch in channels_to_keep if ch in raw.ch_names]

if len(available_channels) == 3:
    print(f"\n✓ Selecting channels: {available_channels}")
    raw.pick_channels(available_channels)
else:
    print(f"\n⚠ Warning: Could not find all requested channels")
    print(f"  Requested: {channels_to_keep}")
    print(f"  Available: {raw.ch_names}")
    print(f"  Found: {available_channels}")

print("\n" + "="*70)
print("EXTRACTING MARKERS")
print("="*70)

# Extract markers and create MNE events
events = []
event_id = {}

if marker_stream is not None:
    marker_data = marker_stream['time_series']
    marker_timestamps = marker_stream['time_stamps']

    print(f"\nFound {len(marker_timestamps)} markers")

    # Map marker timestamps to sample indices
    for marker, timestamp in zip(marker_data, marker_timestamps):
        # Get marker string
        marker_str = str(marker[0]) if isinstance(marker, (list, np.ndarray)) else str(marker)

        # Convert timestamp to sample index
        # Find the closest sample to this timestamp
        time_diff = timestamp - eeg_timestamps[0]
        sample_idx = int(time_diff * sfreq)

        # Make sure sample is within bounds
        if 0 <= sample_idx < eeg_data.shape[1]:
            # MNE events format: [sample_idx, 0, event_id]
            # Use the marker value as event_id
            try:
                marker_int = int(marker_str)
            except:
                marker_int = hash(marker_str) % 10000  # Fallback for non-integer markers

            events.append([sample_idx, 0, marker_int])

            # Track event types
            if marker_str not in event_id:
                event_id[marker_str] = marker_int

    events = np.array(events)

    print(f"\nEvent types found:")
    for name, evt_id in sorted(event_id.items(), key=lambda x: x[1]):
        count = np.sum(events[:, 2] == evt_id)
        print(f"  '{name}' (ID {evt_id}): {count} occurrences")

    # Create event descriptions for BCI Competition format
    event_descriptions = {
        '768': 'Trial Start',
        '769': 'Left Hand Cue',
        '770': 'Right Hand Cue'
    }

    print("\nEvent meanings:")
    for name, evt_id in event_id.items():
        desc = event_descriptions.get(name, 'Unknown')
        print(f"  {name} = {desc}")

else:
    print("\nNo marker stream found!")
    events = None
    event_id = None

print("\n" + "="*70)
print("POWER SPECTRAL DENSITY (PSD)")
print("="*70)

# Compute and plot PSD
print("\nComputing Power Spectral Density...")
try:
    # For EEG data, typically interested in frequencies up to 50 Hz
    # (includes delta, theta, alpha, beta, and low gamma bands)
    fmax = 50  # Hz

    # Compute PSD using Welch's method
    psd = raw.compute_psd(fmax=fmax)

    # Plot average PSD across all channels
    fig_psd = psd.plot(average=True, picks='eeg',
                       amplitude=False, spatial_colors=False,
                       show=False)
    fig_psd.suptitle(f'Power Spectral Density: {xdf_file}', fontsize=12, fontweight='bold')

    # Also plot PSD for each channel separately
    fig_psd_channels = psd.plot(average=False, picks='eeg',
                                amplitude=False, spatial_colors=True,
                                show=False)
    fig_psd_channels.suptitle(f'PSD by Channel: {xdf_file}', fontsize=12, fontweight='bold')

    print("✓ PSD computed successfully")
    print(f"  Frequency range: 0-{fmax} Hz")
    print(f"  Number of channels: {len(ch_names)}")

except Exception as e:
    print(f"⚠ Could not compute PSD: {e}")

print("\n" + "="*70)
print("OPENING INTERACTIVE VIEWER")
print("="*70)
print("""
Controls:
  - Left/Right arrows: Navigate through time
  - Up/Down arrows: Adjust scaling
  - +/- keys: Zoom in/out
  - Click on channel name: Hide/show channel
  - Click and drag: Scroll through data

Event colors:
  - Green: 768 (Trial Start)
  - Blue: 769 (Left Hand Cue)
  - Red: 770 (Right Hand Cue)
""")

# Create custom event colors
event_color = {}
if event_id:
    for name, evt_id in event_id.items():
        if name == '768':
            event_color[evt_id] = 'green'
        elif name == '769':
            event_color[evt_id] = 'blue'
        elif name == '770':
            event_color[evt_id] = 'red'
        else:
            event_color[evt_id] = 'purple'

# Plot with events
if events is not None and len(events) > 0:
    raw.plot(
        duration=10,  # Show 10 seconds at a time
        n_channels=3,  # Show 3 channels (Ch2, Ch3, Ch4)
        scalings='auto',
        events=events,
        event_id=event_id,
        event_color=event_color,
        title=f'XDF Data (Ch2, Ch3, Ch4): {xdf_file}',
        block=False  # Don't block so PSD windows are also visible
    )
else:
    raw.plot(
        duration=10,
        n_channels=3,
        scalings='auto',
        title=f'XDF Data (Ch2, Ch3, Ch4): {xdf_file}',
        block=False
    )

# Show all plots (PSD + interactive viewer)
print("\n" + "="*70)
print("All plots displayed. Close windows to exit.")
print("="*70)
plt.show()
