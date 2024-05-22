from .Pan_Tompkins import Pan_Tompkins_QRS, heart_rate
import numpy as np
import pandas as pd
import operator
import pywt
# from scipy import signal
from sklearn.preprocessing import StandardScaler
from skimage.restoration import denoise_wavelet

size_RR_max = 90 # window for correcting r position
winL = 90 # window left
winR = 90 # window right

def preprocess(ecg, remove_baseline = True):
    from scipy.signal import medfilt

    ecg = denoise_wavelet(ecg, method='VisuShrink', mode='soft', wavelet_levels=10, wavelet='db8', rescale_sigma='True')
    
    if remove_baseline:
        # median_filter1D
        baseline = medfilt(ecg, 71)
        baseline = medfilt(baseline, 215)

        # Remove Baseline
        for i in range(0, len(ecg)):
            ecg[i] = ecg[i] - baseline[i]

    scaler = StandardScaler()
    ecg = scaler.fit_transform(ecg.reshape(-1, 1)).reshape(-1)
    return ecg


def windowing(MLII, r_peak_index, raw_MLII = None):
    
    beat = []
    new_r_peak_index = []
    
    # correct r peak index
    for i in range(len(r_peak_index)):
        pos = int(r_peak_index[i])
        if pos > size_RR_max and pos < (len(MLII) - size_RR_max):
            index, value = max(enumerate(MLII[pos - size_RR_max : pos + size_RR_max]), key=operator.itemgetter(1))
            pos = (pos - size_RR_max) + index

        # windowing
        if(pos > winL and pos < (len(MLII) - winR)):
            if raw_MLII is None:
                beat.append(MLII[pos - winL : pos + winR])
            else:
                beat.append(raw_MLII[pos - winL : pos + winR])
            new_r_peak_index.append(pos)
    
    new_r_peak_index = np.array(new_r_peak_index)
    return beat, new_r_peak_index

def calc_rri(r_peak_index):

    # Initialize feature arrays
    ds = {
        'RR0': [],
        'RR-1': [],
        'RR+1': [],
        'RR0/avgRR': [],
        'tRR0': [],
        'RR-1/avgRR': [],
        'RR-1/RR0': [],
        'RR+1/avgRR': [],
        'RR+1/RR0': [],
    }

    # Calculate RR intervals
    rr_intervals = np.diff(r_peak_index)

    for i in range(len(rr_intervals)):
        if i < 42 or i == len(rr_intervals) - 1:
            continue
        RR0 = rr_intervals[i]
        RR_minus_1 = rr_intervals[i-1]
        RR_plus_1 = rr_intervals[i+1]
        avgRR = np.mean(rr_intervals[i-42:i+1])
        stddevRR = np.std(rr_intervals[i-42:i+1])
        RR0_avgRR = RR0 / avgRR
        tRR0 = (RR0 - avgRR) / stddevRR
        RR_minus_1_avgRR = RR_minus_1 / avgRR
        RR_minus_1_RR0 = RR_minus_1 / RR0
        RR_plus_1_avgRR = RR_plus_1 / avgRR
        RR_plus_1_RR0 = RR_plus_1 / RR0

        # Append features to arrays
        ds['RR0'].append(RR0)
        ds['RR-1'].append(RR_minus_1)
        ds['RR+1'].append(RR_plus_1)
        ds['RR0/avgRR'].append(RR0_avgRR)
        ds['tRR0'].append(tRR0)
        ds['RR-1/avgRR'].append(RR_minus_1_avgRR)
        ds['RR-1/RR0'].append(RR_minus_1_RR0)
        ds['RR+1/avgRR'].append(RR_plus_1_avgRR)
        ds['RR+1/RR0'].append(RR_plus_1_RR0)

    # Convert ds to DataFrame
    ds_df = pd.DataFrame(ds)
    return ds_df

def pan_tompkins(record, fs = 360):
    # Pan-Tompkins
    QRS_detector = Pan_Tompkins_QRS(fs)
    ecg = pd.DataFrame(np.array([list(range(len(record))),record]).T,columns=['TimeStamp','ecg'])
    # output_signal = QRS_detector.solve(ecg)
    mwin, bpass = QRS_detector.solve(ecg)

    # Find the R peak locations
    signal = ecg.iloc[:,1].to_numpy()
    hr = heart_rate(signal, fs, mwin, bpass)
    result = hr.find_r_peaks()
    result = np.array(result)

    # Clip the x locations less than 0 (Learning Phase)
    result = result[result > 0]

    # delete alocated memory global variable
    # del QRS_detector
    # del ecg
    # del signal
    # del hr
    # del mwin
    # del bpass

    return result

# Compute the wavelet descriptor for a beat
def compute_wavelet_descriptor(beat, family, level):
    wave_family = pywt.Wavelet(family)
    coeffs = pywt.wavedec(beat, wave_family, level=level)
    return coeffs[0]

def to_wavelet(windowed_beats):

    f_wav = np.empty((0, 23 * 1))

    for p in range(len(windowed_beats)):
        b = windowed_beats[p]
        f_wav_lead = np.empty([])
        f_wav_lead =  compute_wavelet_descriptor(b, 'db1', 3)
        f_wav = np.vstack((f_wav, f_wav_lead))

    return f_wav

