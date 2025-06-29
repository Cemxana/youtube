import queue
import numpy as np
import pygame
import sounddevice as sd

WIDTH, HEIGHT = 1280, 720
FPS = 30
BAR_COUNT = 32  # Equalizer bar sayısı
BAR_WIDTH = WIDTH // BAR_COUNT
BAR_COLORS = [
    (123, 104, 238), (186, 85, 211), (221, 160, 221), (230, 230, 250)
]

AUDIO_QUEUE = queue.Queue()

def find_input_device_id():
    """Varsa BlackHole, yoksa default input device ID döner."""
    devices = sd.query_devices()
    for idx, dev in enumerate(devices):
        if "BlackHole" in dev.get("name", "") and dev.get("max_input_channels", 0) > 0:
            return idx
    # Eğer BlackHole yoksa, default input:
    return sd.default.device[0]

def audio_callback(indata, frames, time, status):
    """Ses örneğini kuyruğa yollar."""
    if status:
        print(status, flush=True)
    # FFT ile frekans barları
    # Mono yap:
    samples = np.mean(indata, axis=1)
    # Hızlı Fourier Transform (magnitude):
    fft_vals = np.abs(np.fft.rfft(samples, n=BAR_COUNT*2))
    bars = fft_vals[:BAR_COUNT]
    bars = np.clip(bars / np.max(bars), 0, 1) if np.max(bars) > 0 else bars
    try:
        AUDIO_QUEUE.put_nowait(bars)
    except queue.Full:
        pass

def draw_equalizer(screen, bars):
    """Barlar çizilir."""
    for i in range(BAR_COUNT):
        bar_height = int(bars[i] * (HEIGHT * 0.8))
        x = i * BAR_WIDTH
        y = HEIGHT - bar_height
        color = BAR_COLORS[i % len(BAR_COLORS)]
        pygame.draw.rect(screen, color, (x, y, BAR_WIDTH - 2, bar_height))

def main():
    device_id = find_input_device_id()
    print(f"Using input device ID: {device_id}")

    stream = sd.InputStream(device=device_id, channels=2, callback=audio_callback, blocksize=1024)
    stream.start()

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    bars = np.zeros(BAR_COUNT)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        while not AUDIO_QUEUE.empty():
            bars = AUDIO_QUEUE.get()

        screen.fill((10, 10, 30))
        draw_equalizer(screen, bars)

        pygame.display.flip()
        clock.tick(FPS)

    stream.stop()
    stream.close()
    pygame.quit()

if __name__ == "__main__":
    main()
