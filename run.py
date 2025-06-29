import os
import queue
import numpy as np
import pygame
import sounddevice as sd

WIDTH, HEIGHT = 1280, 720
FPS = 30
RING_COUNT = 8
COLORS = [
    (75, 0, 130),  # indigo
    (72, 61, 139),
    (106, 90, 205),
    (123, 104, 238),
    (147, 112, 219),
    (186, 85, 211),
    (221, 160, 221),
    (230, 230, 250),
]

AUDIO_QUEUE = queue.Queue()
volume_level = 0.0


def find_blackhole_device_id():
    """Return the input device ID for BlackHole or None."""
    devices = sd.query_devices()
    for idx, dev in enumerate(devices):
        if "BlackHole" in dev.get("name", "") and dev.get("max_input_channels", 0) > 0:
            return idx
    return None


def audio_callback(indata, frames, time, status):
    global volume_level
    if status:
        print(status, flush=True)
    rms = float(np.sqrt(np.mean(indata**2)))
    try:
        AUDIO_QUEUE.put_nowait(rms)
    except queue.Full:
        pass


def draw_visualizer(screen, center, base_radius, volume):
    for i in range(RING_COUNT):
        growth = volume * 300  # scale volume to pixel growth
        radius = base_radius + i * 20 + growth
        pygame.draw.circle(screen, COLORS[i % len(COLORS)], center, int(radius), 2)


def main():
    device_id = find_blackhole_device_id()
    if device_id is None:
        print("BlackHole input device not found. Available devices:")
        print(sd.query_devices())
        return
    print(f"Using BlackHole device ID: {device_id}")

    stream = sd.InputStream(device=device_id, channels=2, callback=audio_callback)
    stream.start()

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    ear_path = os.path.join(os.path.dirname(__file__), "images", "kulak.png")
    ear_img = pygame.image.load(ear_path).convert_alpha()
    ear_rect = ear_img.get_rect(center=(WIDTH // 2, HEIGHT // 2))

    base_radius = 80
    running = True
    volume = 0.0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        while not AUDIO_QUEUE.empty():
            volume = AUDIO_QUEUE.get()

        screen.fill((10, 10, 30))
        screen.blit(ear_img, ear_rect)
        draw_visualizer(screen, ear_rect.center, base_radius, volume)

        pygame.display.flip()
        clock.tick(FPS)

    stream.stop()
    stream.close()
    pygame.quit()


if __name__ == "__main__":
    main()