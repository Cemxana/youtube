import numpy as np
import pygame
import time
import os
import urllib.parse

WIDTH, HEIGHT = 1280, 720
FPS = 30
BAR_COUNT = 32
BAR_WIDTH = WIDTH // BAR_COUNT
BAR_COLORS = [
    (123, 104, 238), (186, 85, 211), (221, 160, 221), (230, 230, 250)
]

def read_playlist(m3u_path):
    """M3U dosyasından dosya yollarını döndürür (decode ederek ve Cemxana'dan başlatarak)."""
    tracks = []
    cemxana_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Cemxana'))
    with open(m3u_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                decoded_line = urllib.parse.unquote(line)
                full_path = os.path.join(cemxana_dir, decoded_line)
                tracks.append(full_path)
    return tracks

def load_wav_samples(filename):
    """WAV dosyasını numpy array olarak okur (mono)."""
    import wave
    import struct
    wf = wave.open(filename, 'rb')
    n_frames = wf.getnframes()
    frames = wf.readframes(n_frames)
    wf.close()
    channels = wf.getnchannels()
    samples = np.array(struct.unpack("%dh" % (n_frames * channels), frames), dtype=np.float32)
    if channels > 1:
        samples = samples.reshape(-1, channels)
        samples = samples.mean(axis=1)
    samples /= np.max(np.abs(samples))
    return samples, wf.getframerate()

def play_wav(filename):
    """pygame ile wav dosyasını çalar."""
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()

def animate_equalizer(samples, sample_rate):
    """Equalizer animasyonu."""
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Playlist Equalizer")
    clock = pygame.time.Clock()
    hop = int(sample_rate / FPS)  # her frame'de bu kadar örnek kullan
    idx = 0
    playing = True
    running = True
    while running and pygame.mixer.music.get_busy():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # O anki örnekleri al
        window = samples[idx:idx + hop]
        idx += hop
        if len(window) < hop:
            window = np.pad(window, (0, hop - len(window)))
        # FFT
        fft_vals = np.abs(np.fft.rfft(window, n=BAR_COUNT*2))
        bars = fft_vals[:BAR_COUNT]
        bars = np.clip(bars / np.max(bars) if np.max(bars) > 0 else bars, 0, 1)
        # Çiz
        screen.fill((10, 10, 30))
        for i in range(BAR_COUNT):
            bar_height = int(bars[i] * (HEIGHT * 0.8))
            x = i * BAR_WIDTH
            y = HEIGHT - bar_height
            color = BAR_COLORS[i % len(BAR_COLORS)]
            pygame.draw.rect(screen, color, (x, y, BAR_WIDTH - 2, bar_height))
        pygame.display.flip()
        clock.tick(FPS)

        # Eğer şarkı bitti ise
        if idx + hop >= len(samples):
            break

    pygame.display.quit()

def main():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    playlist_path = os.path.join(BASE_DIR, '..', 'Cemxana', 'playlist.m3u')
    playlist = read_playlist(playlist_path)
    pygame.mixer.init()
    for track in playlist:
        if not os.path.exists(track):
            print("Dosya bulunamadı:", track)
            continue
        print("Çalınıyor:", track)
        samples, sample_rate = load_wav_samples(track)
        play_wav(track)
        animate_equalizer(samples, sample_rate)
        time.sleep(1)  # Şarkılar arası kısa bir duraklama

    pygame.quit()

if __name__ == "__main__":
    main()
