import numpy as np
import pygame
import sounddevice as sd

WIDTH, HEIGHT = 1280, 720
FPS = 30
BAR_COUNT = 32
BAR_WIDTH = WIDTH // BAR_COUNT
BAR_COLORS = [
    (123, 104, 238), (186, 85, 211), (221, 160, 221), (230, 230, 250)
]

AUDIO_QUEUE = []

def find_loopback_device_id():
    devices = sd.query_devices()
    for idx, dev in enumerate(devices):
        print(idx, dev["name"])  # ekrana yazdır
        if "Loopback Audio" in dev.get("name", "") and dev.get("max_input_channels", 0) > 0:
            return idx
    return None


def audio_callback(indata, frames, time, status):
    global AUDIO_QUEUE
    # Stereo ise mono'ya çevir
    data = np.mean(indata, axis=1)
    # Hızlı Fourier Dönüşümü ile frekans barlarını çıkar
    fft_vals = np.abs(np.fft.rfft(data, n=BAR_COUNT*2))
    bars = fft_vals[:BAR_COUNT]
    if np.max(bars) > 0:
        bars = bars / np.max(bars)
    else:
        bars = np.zeros(BAR_COUNT)
    AUDIO_QUEUE.append(bars)

def main():
    device_id = find_loopback_device_id()
    if device_id is None:
        return
    print(f"Kullanılan Loopback Device ID: {device_id}")

    # Sounddevice input stream başlat
    stream = sd.InputStream(device=device_id, channels=2, callback=audio_callback, blocksize=1024)
    stream.start()

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Live System Sound Equalizer")
    clock = pygame.time.Clock()
    bars = np.zeros(BAR_COUNT)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Kuyruğa gelen son bars verisiyle güncelle
        if AUDIO_QUEUE:
            bars = AUDIO_QUEUE.pop(0)

        screen.fill((10, 10, 30))
        for i in range(BAR_COUNT):
            bar_height = int(bars[i] * (HEIGHT * 0.8))
            x = i * BAR_WIDTH
            y = HEIGHT - bar_height
            color = BAR_COLORS[i % len(BAR_COLORS)]
            pygame.draw.rect(screen, color, (x, y, BAR_WIDTH - 2, bar_height))

        pygame.display.flip()
        clock.tick(FPS)

    stream.stop()
    stream.close()
    pygame.quit()

if __name__ == "__main__":
    main()
