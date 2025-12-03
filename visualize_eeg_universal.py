#!/usr/bin/env python3
"""
Universal EEG/iEEG Data Visualizer
Supports: EDF, GDF, and other MNE-compatible formats
"""

import mne
import matplotlib.pyplot as plt
import numpy as np
import sys
import os

def visualize_eeg_file(file_path, show_events=True, duration=10, n_channels=None):
    """
    Visualize EEG/iEEG data from various file formats

    Parameters:
    -----------
    file_path : str
        Path to the data file (EDF, GDF, etc.)
    show_events : bool
        Whether to show event markers (for BCI tasks)
    duration : float
        Duration of data to show in plot (seconds)
    n_channels : int or None
        Number of channels to show (None = show all)
    """

    # Check file exists
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return

    # Determine file format
    file_ext = os.path.splitext(file_path)[1].lower()
    print(f"Detected file format: {file_ext}")

    # Load data based on format
    print(f"\nLoading data from: {file_path}")
    try:
        if file_ext == '.edf':
            raw = mne.io.read_raw_edf(file_path, preload=True)
        elif file_ext == '.gdf':
            raw = mne.io.read_raw_gdf(file_path, preload=True)
        elif file_ext == '.fif':
            raw = mne.io.read_raw_fif(file_path, preload=True)
        else:
            print(f"Trying to load as generic format...")
            raw = mne.io.read_raw(file_path, preload=True)
    except Exception as e:
        print(f"Error loading file: {e}")
        return

    # ========================================================================
    # Basic Information
    # ========================================================================
    print("\n" + "="*70)
    print("DATA FILE INFORMATION")
    print("="*70)
    print(f"File: {os.path.basename(file_path)}")
    print(f"Duration: {raw.times[-1]:.2f} seconds ({raw.times[-1]/60:.2f} minutes)")
    print(f"Sampling frequency: {raw.info['sfreq']} Hz")
    print(f"Number of channels: {len(raw.ch_names)}")
    print(f"Data shape: {raw.get_data().shape}")

    # Channel information
    ch_types = raw.get_channel_types()
    unique_types = set(ch_types)
    print(f"\nChannel types: {unique_types}")
    for ch_type in unique_types:
        count = ch_types.count(ch_type)
        print(f"  - {ch_type}: {count} channels")

    print(f"\nChannel names:")
    for i, ch in enumerate(raw.ch_names):
        ch_type = ch_types[i]
        print(f"  {i+1:2d}. {ch:20s} ({ch_type})")

    # ========================================================================
    # Event/Marker Information (important for BCI tasks!)
    # ========================================================================
    events = None
    event_id = None

    if show_events:
        try:
            # Try to find events in the data
            events = mne.find_events(raw, stim_channel='auto', verbose=False)

            if len(events) > 0:
                print("\n" + "="*70)
                print("EVENT MARKERS (BCI Task Timing)")
                print("="*70)
                print(f"Found {len(events)} events")

                # Show unique event types
                unique_events = np.unique(events[:, 2])
                print(f"\nEvent types (IDs): {unique_events}")

                # For BCI Competition IV 2b, common event IDs:
                # 768 = rejected trial
                # 769 = left hand (class 1)
                # 770 = right hand (class 2)
                # 783 = cue unknown
                # 1023 = new segment

                # Try to identify event meanings
                event_meanings = {
                    768: "Rejected trial",
                    769: "Left hand",
                    770: "Right hand",
                    771: "Foot",
                    772: "Tongue",
                    783: "Cue (unknown)",
                    1023: "New segment/run",
                    1072: "Eye movement"
                }

                print("\nEvent breakdown:")
                for event_type in unique_events:
                    count = np.sum(events[:, 2] == event_type)
                    meaning = event_meanings.get(event_type, "Unknown")
                    print(f"  ID {event_type:4d}: {count:4d} occurrences - {meaning}")

                # Create event_id dictionary for known events
                event_id = {meaning: evt_id for evt_id, meaning in event_meanings.items()
                           if evt_id in unique_events}

                # Show first few events
                print("\nFirst 10 events:")
                print("  Time(s)  | Sample | Event ID | Meaning")
                print("  " + "-"*50)
                for i in range(min(10, len(events))):
                    time = events[i, 0] / raw.info['sfreq']
                    sample = events[i, 0]
                    evt_id = events[i, 2]
                    meaning = event_meanings.get(evt_id, "Unknown")
                    print(f"  {time:7.2f}  | {sample:6d} | {evt_id:8d} | {meaning}")

        except Exception as e:
            print(f"\nNo events found or error reading events: {e}")

    # ========================================================================
    # Auto-detect data type and set appropriate channel types
    # ========================================================================
    print("\n" + "="*70)
    print("CHANNEL TYPE DETECTION")
    print("="*70)

    # Check if this looks like BCI Competition data
    is_bci_comp = any(name in ['C3', 'C4', 'Cz', 'C3-A2', 'Cz-A2', 'C4-A2']
                      for name in raw.ch_names)

    # Check if this looks like iEEG data
    is_ieeg = any('POL' in name or 'SEEG' in name.upper()
                  for name in raw.ch_names)

    if is_bci_comp:
        print("Detected: BCI Competition / Motor Imagery data")
        # Set EEG and EOG channel types
        for ch_name in raw.ch_names:
            if 'EOG' in ch_name.upper():
                raw.set_channel_types({ch_name: 'eog'})
            elif any(x in ch_name for x in ['C3', 'C4', 'Cz']):
                raw.set_channel_types({ch_name: 'eeg'})

    elif is_ieeg:
        print("Detected: iEEG (intracranial) data")
        for ch_name in raw.ch_names:
            if 'DC' in ch_name:
                raw.set_channel_types({ch_name: 'misc'})
            elif 'POL' in ch_name or 'SEEG' in ch_name.upper():
                raw.set_channel_types({ch_name: 'seeg'})

    else:
        print("Generic EEG data - using default channel types")

    print(f"Updated channel types: {set(raw.get_channel_types())}")

    # ========================================================================
    # Visualization
    # ========================================================================
    print("\n" + "="*70)
    print("GENERATING VISUALIZATIONS")
    print("="*70)

    # Determine number of channels to show
    if n_channels is None:
        n_channels = min(30, len(raw.ch_names))

    # Get picks for plotting (exclude misc channels)
    plot_picks = mne.pick_types(raw.info, meg=False, eeg=True, eog=True,
                                 seeg=True, ecog=True, exclude=[])

    if len(plot_picks) == 0:
        plot_picks = 'all'

    print(f"\n1. Interactive time-series plot")
    print("   - Use arrow keys to navigate")
    print("   - Use +/- to adjust scaling")

    # Plot raw data with events if available
    if events is not None and len(events) > 0:
        raw.plot(duration=duration, n_channels=n_channels,
                scalings='auto', events=events, event_id=event_id,
                title=f'Data Visualization: {os.path.basename(file_path)}',
                block=False)
    else:
        raw.plot(duration=duration, n_channels=n_channels,
                scalings='auto',
                title=f'Data Visualization: {os.path.basename(file_path)}',
                block=False)

    # Plot PSD
    print(f"\n2. Power Spectral Density (PSD)")
    try:
        # Different frequency ranges for different data types
        if is_ieeg:
            fmax = 200  # iEEG can have high frequency activity
        else:
            fmax = 50   # Scalp EEG typically up to 50Hz

        raw.compute_psd(fmax=fmax).plot(average=True, picks=plot_picks,
                                         amplitude=False, spatial_colors=False)
    except Exception as e:
        print(f"   Could not plot PSD: {e}")

    # If events exist, plot event-related potentials
    if events is not None and len(events) > 0 and event_id:
        print(f"\n3. Epoching data around events")
        try:
            # Create epochs around events (for motor imagery, -1 to 4 seconds)
            epochs = mne.Epochs(raw, events, event_id=event_id,
                               tmin=-1.0, tmax=4.0, baseline=(-1.0, 0.0),
                               preload=True, verbose=False)

            print(f"   Created {len(epochs)} epochs")
            print(f"   Epoch duration: {epochs.tmin} to {epochs.tmax} seconds")

            # Plot evoked responses
            evoked_dict = {}
            for event_name in event_id.keys():
                if event_name in epochs.event_id:
                    evoked = epochs[event_name].average()
                    evoked_dict[event_name] = evoked

            if evoked_dict:
                print(f"   Plotting evoked responses...")
                fig, axes = plt.subplots(len(evoked_dict), 1,
                                        figsize=(10, 4*len(evoked_dict)))
                if len(evoked_dict) == 1:
                    axes = [axes]

                for ax, (event_name, evoked) in zip(axes, evoked_dict.items()):
                    evoked.plot(axes=ax, show=False, spatial_colors=True)
                    ax.set_title(f'Evoked Response: {event_name}')

                plt.tight_layout()

        except Exception as e:
            print(f"   Could not create epochs: {e}")

    print("\n" + "="*70)
    print("Plots displayed. Close windows to exit.")
    print("="*70)

    plt.show()


if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        # Default to EDF file in edf_test
        file_path = 'BCICIV_2b_gdf copy/B0101T.gdf'

    # Optional parameters
    duration = 10  # seconds to show per screen
    n_channels = None  # None = auto-select

    visualize_eeg_file(file_path, show_events=True,
                      duration=duration, n_channels=n_channels)
