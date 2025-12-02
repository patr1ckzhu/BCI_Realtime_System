#!/usr/bin/env python3
"""
Visualize iEEG EDF file using MNE
"""

import mne
import matplotlib.pyplot as plt

# Read the EDF file
edf_file = 'edf_test/sub-007_ses-1_task-picture_ieeg.edf'
raw = mne.io.read_raw_edf(edf_file, preload=True)

# Set channel types to iEEG (SEEG or ECoG)
# This helps MNE understand this is intracranial data
raw.set_channel_types({ch: 'seeg' for ch in raw.ch_names if not ch.startswith('POL DC')})
# DC channels might be auxiliary channels
if 'POL DC01' in raw.ch_names:
    raw.set_channel_types({ch: 'misc' for ch in raw.ch_names if ch.startswith('POL DC')})

# Print basic information
print("=" * 50)
print("iEEG EDF File Information")
print("=" * 50)
print(f"Duration: {raw.times[-1]:.2f} seconds")
print(f"Sampling frequency: {raw.info['sfreq']} Hz")
print(f"Number of channels: {len(raw.ch_names)}")
print(f"Channel types: {set(raw.get_channel_types())}")
print("\nFirst 10 channel names:")
for i, ch in enumerate(raw.ch_names[:10]):
    print(f"  {i+1}. {ch}")
print(f"  ... and {len(raw.ch_names) - 10} more channels")
print("=" * 50)

# Plot the raw data
# For iEEG, we might need different scalings than scalp EEG
# This will open an interactive window where you can scroll through the data
print("\nOpening interactive plot window...")
print("Use left/right arrow keys to navigate through time")
print("Use +/- keys to adjust scaling")
raw.plot(duration=10, n_channels=30, scalings='auto',
         title='iEEG Data Visualization', block=False)

# Plot the power spectral density
print("\nGenerating power spectral density plot...")
raw.compute_psd(fmax=100).plot(average=True, picks='seeg',
                                amplitude=False, spatial_colors=False)

# Keep the plots open
print("\nPlots are displayed. Close the plot windows to exit.")
plt.show()