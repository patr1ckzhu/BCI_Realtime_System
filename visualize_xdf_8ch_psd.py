#!/usr/bin/env python3
"""
Visualize XDF file - 8 channels with average PSD only
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

print(f"All channels: {ch_names}")

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

# Select first 8 channels (Ch1-Ch8)
channels_to_keep = [f'Ch{i+1}' for i in range(8)]
available_channels = [ch for ch in channels_to_keep if ch in raw.ch_names]

if len(available_channels) == 8:
    print(f"\n✓ Selecting 8 channels: {available_channels}")
    raw.pick_channels(available_channels)
else:
    print(f"\n⚠ Warning: Could not find all 8 channels")
    print(f"  Requested: {channels_to_keep}")
    print(f"  Available: {raw.ch_names}")
    print(f"  Found: {available_channels}")

print("\n" + "="*70)
print("POWER SPECTRAL DENSITY (PSD) - Average across 8 channels")
print("="*70)

# Compute and plot PSD
print("\nComputing Power Spectral Density...")
try:
    # For EEG data, typically interested in frequencies up to 50 Hz
    # (includes delta, theta, alpha, beta, and low gamma bands)
    fmax = 50  # Hz

    # Compute PSD using Welch's method
    psd = raw.compute_psd(fmax=fmax)

    # Plot ONLY average PSD across all 8 channels
    fig_psd = psd.plot(average=True, picks='eeg',
                       amplitude=False, spatial_colors=False,
                       show=False)
    fig_psd.suptitle(f'Average PSD (8 channels): {xdf_file}',
                     fontsize=14, fontweight='bold')

    print("✓ PSD computed successfully")
    print(f"  Frequency range: 0-{fmax} Hz")
    print(f"  Number of channels: 8")
    print(f"  Channels used: Ch1-Ch8")

except Exception as e:
    print(f"⚠ Could not compute PSD: {e}")

# Show plot
print("\n" + "="*70)
print("PSD plot displayed. Close window to exit.")
print("="*70)
plt.show()