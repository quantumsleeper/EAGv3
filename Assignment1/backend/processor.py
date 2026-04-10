import os
import subprocess
from pedalboard import Pedalboard, PitchShift
from pedalboard.io import AudioFile

def process_karaoke(url: str, pitch_shift: int, work_dir: str) -> str:
    """
    Core pipeline:
    1. yt-dlp to download audio as mp3
    2. spleeter to separate vocals from accompaniment
    3. pedalboard to handle pitch shift (if > 0 or < 0)
    4. ffmpeg to convert final WAV back to MP3
    """
    input_file = os.path.join(work_dir, "input.mp3")

    # Step 1: Download
    print(f"\n[{work_dir}] >> Downloading audio from {url}...")
    download_cmd = [
        "yt-dlp",
        "--cookies-from-browser", "chrome",
        "-x", "--audio-format", "mp3",
        "-o", input_file,
        url
    ]
    subprocess.run(download_cmd, check=True)
    
    if not os.path.exists(input_file):
        raise FileNotFoundError("Download failed or file not found")

    # Step 2: Vocal Separation
    print(f"\n[{work_dir}] >> Separating vocals with Demucs...")
    demucs_output_dir = os.path.join(work_dir, "demucs_out")
    # Using demucs with two-stems will output 'vocals' and 'no_vocals'
    demucs_cmd = [
        "demucs", "--two-stems", "vocals",
        "--out", demucs_output_dir,
        input_file
    ]
    subprocess.run(demucs_cmd, check=True)

    # Demucs creates a folder based on the model (htdemucs) and base filename (input)
    accompaniment_path = os.path.join(demucs_output_dir, "htdemucs", "input", "no_vocals.wav")
    if not os.path.exists(accompaniment_path):
        raise FileNotFoundError(f"Demucs extraction failed, could not find {accompaniment_path}")

    # Step 3: Pitch Shift
    final_output_path = os.path.join(work_dir, "final_karaoke.mp3")
    
    if pitch_shift != 0:
        print(f"\n[{work_dir}] >> Applying pitch shift of {pitch_shift} semitones...")
        shifted_wav_path = os.path.join(work_dir, "shifted_accompaniment.wav")
        
        with AudioFile(accompaniment_path, 'r') as f:
            audio = f.read(f.frames)
            samplerate = f.samplerate
            
        board = Pedalboard([PitchShift(semitones=pitch_shift)])
        effected = board(audio, samplerate)
        
        with AudioFile(shifted_wav_path, 'w', samplerate, effected.shape[0]) as f:
            f.write(effected)
            
        source_for_ffmpeg = shifted_wav_path
    else:
        print(f"\n[{work_dir}] >> No pitch shift requested.")
        source_for_ffmpeg = accompaniment_path

    # Step 4: Convert back to MP3
    print(f"\n[{work_dir}] >> Encoding back to MP3...")
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-i", source_for_ffmpeg,
        "-codec:a", "libmp3lame",
        "-qscale:a", "2",
        final_output_path
    ]
    subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    print(f"\n[{work_dir}] >> Processing complete.")
    return final_output_path
