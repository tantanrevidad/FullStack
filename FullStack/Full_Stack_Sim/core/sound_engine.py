import pygame
import math
import random
import array

class SoundGenerator:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.max_amp = 20000

    def _make_buffer(self, data):
        return pygame.mixer.Sound(buffer=data)

    def generate_wave(self, freq, duration, wave_type='sine', volume=0.5):
        n_samples = int(self.sample_rate * duration)
        buf = array.array('h', [0] * n_samples)
        attack = int(n_samples * 0.1)
        decay = int(n_samples * 0.8)
        
        for i in range(n_samples):
            t = float(i) / self.sample_rate
            if wave_type == 'sine':
                val = math.sin(2.0 * math.pi * freq * t)
            elif wave_type == 'square':
                val = 1.0 if math.sin(2.0 * math.pi * freq * t) > 0 else -1.0
            elif wave_type == 'saw':
                val = 2.0 * (t * freq - math.floor(t * freq + 0.5))
            elif wave_type == 'noise':
                val = random.uniform(-1, 1)
            else:
                val = 0
            
            env = 1.0
            if i < attack: env = i / attack
            elif i > decay: env = 1.0 - ((i - decay) / (n_samples - decay))
            
            buf[i] = int(val * self.max_amp * volume * env)
        return self._make_buffer(buf)

class MusicSequencer:
    def __init__(self):
        self.gen = SoundGenerator()
        self.is_playing = False
        self.current_scene = "MENU"
        
        # Sound Bank
        base_freqs = {'C': 130.81, 'C#': 138.59, 'D': 146.83, 'Eb': 155.56, 'E': 164.81, 'F': 174.61, 'F#': 185.00, 'G': 196.00, 'Ab': 207.65, 'A': 220.00, 'Bb': 233.08, 'B': 246.94}
        self.sound_bank = {}
        for note, freq in base_freqs.items():
            self.sound_bank[f"bass_{note}"] = self.gen.generate_wave(freq / 2, 0.4, 'square', 0.3)
            self.sound_bank[f"pad_{note}"] = self.gen.generate_wave(freq, 1.0, 'sine', 0.15)
            self.sound_bank[f"high_{note}"] = self.gen.generate_wave(freq * 2, 0.6, 'sine', 0.1)
        self.sound_bank['kick'] = self.gen.generate_wave(60, 0.1, 'sine', 0.8)
        self.sound_bank['hat'] = self.gen.generate_wave(0, 0.05, 'noise', 0.15)
        self.sound_bank['glitch'] = self.gen.generate_wave(800, 0.05, 'saw', 0.05)

        # Themes
        self.themes = {
            "MENU":  {"bpm": 90, "scale": ["C", "Eb", "G", "Bb"], "bass_pattern": [1,0,0,0, 0,0,1,0, 1,0,0,0, 0,0,0,0], "prob_pad": 0.2, "prob_glitch": 0.05},
            "HEAVY": {"bpm": 80, "scale": ["F", "Ab", "C", "Eb"], "bass_pattern": [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,1,0,0], "prob_pad": 0.1, "prob_glitch": 0.01},
            "TECH":  {"bpm": 110, "scale": ["Eb", "G", "Bb", "D"], "bass_pattern": [1,0,0,0, 0,0,1,0, 0,0,1,0, 0,1,0,1], "prob_pad": 0.4, "prob_glitch": 0.2},
            "DATA":  {"bpm": 105, "scale": ["G", "Bb", "D", "F"], "bass_pattern": [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], "prob_pad": 0.1, "prob_glitch": 0.1}
        }
        self.active_theme = self.themes["MENU"]
        self.step_interval = 60000 / self.active_theme["bpm"] / 4
        self.last_step_time = 0
        self.current_step = 0
        self.total_steps = 16

    def start(self):
        self.is_playing = True
        self.last_step_time = pygame.time.get_ticks()

    def set_theme(self, scene_name):
        if scene_name == "MENU": target = "MENU"
        elif scene_name in ["STACK", "QUEUE"]: target = "HEAVY"
        elif scene_name in ["TREE", "EXPR_TREE", "RECURSION"]: target = "TECH"
        else: target = "DATA"
        self.active_theme = self.themes[target]
        self.step_interval = 60000 / self.active_theme["bpm"] / 4

    def update(self):
        if not self.is_playing: return
        now = pygame.time.get_ticks()
        if now - self.last_step_time >= self.step_interval:
            self.last_step_time = now
            self._play_step(self.current_step)
            self.current_step = (self.current_step + 1) % self.total_steps

    def _play_step(self, step):
        theme = self.active_theme
        scale = theme["scale"]
        if theme["bass_pattern"][step]:
            if random.random() > 0.5: self.sound_bank['kick'].play()
            else: self.sound_bank[f"bass_{scale[0]}"].play()
        if step % 4 == 0 or random.random() < 0.1: self.sound_bank['hat'].play()
        if random.random() < theme["prob_pad"]:
            note = random.choice(scale)
            prefix = "pad_" if random.random() > 0.4 else "high_"
            self.sound_bank[f"{prefix}{note}"].play()
        if random.random() < theme["prob_glitch"]: self.sound_bank['glitch'].play()