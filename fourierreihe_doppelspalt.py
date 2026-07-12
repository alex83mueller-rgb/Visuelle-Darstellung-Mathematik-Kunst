#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QUANTUM TIME CRYSTAL - FOURIER SCHWELLEN-ANALYSATOR v2.0
======================================================
Visualisiert die diskreten Quantenzustände und Schwellenübergänge (Phasensprünge)
eines getriebenen Raumzeit-Kristalls mittels Fourier-Synthese.

Textobjekt -> Quanten-Spin-Frequenzen -> Floquet-Fourier-Synthese -> Phasenraum-Matrix
"""

import math
import time
import os
from typing import List, Tuple

# SYSTEM-KONFIGURATION
TERMINAL_WIDTH = 80
CRYSTAL_HEIGHT = 20
FPS = 14
DURATION = 8.0  # Sekunden pro Quantensimulation

# PHYSIKALISCHE PHASENGRENZEN (Schwellenwerte der Wellenfunktion)
THRESHOLD_GROUND = 0.20  # Grundzustand / Vakuumfluktuation (Dunkelblau)
THRESHOLD_THERMAL = 0.45 # Thermische Phase / Symmetrische Ordnung (Grün)
THRESHOLD_CRYSTAL = 0.72 # Zeitkristalline Phase / Symmetriebrechung (Cyan)
THRESHOLD_ENTANGLED = 0.90 # Kritische Verschränkung / Peak-Zustand (Neon-Magenta)

def clear_terminal():
    """Löscht den Terminal-Bildschirm."""
    os.system('cls' if os.name == 'nt' else 'clear')

def text_zu_eigenfrequenzen(text: str) -> List[float]:
    """
    Wandelt das Textobjekt in deterministische Eigenfrequenzen des Kristalls um.
    Nutzt den Goldenen Schnitt (1.6180339) für die Quanten-Kopplungskonstanten.
    """
    GOLDEN_RATIO = 1.618033988749895
    eigenfrequenzen = []
    
    for i, char in enumerate(text):
        char_wert = ord(char)
        # Berechne diskrete Spin-Energien des Gitters
        freq = ((char_wert * (i + 1)) % 50) / 50.0 * GOLDEN_RATIO
        if freq == 0:
            freq = 0.5
        eigenfrequenzen.append(freq)
        
    # Sicherstellen, dass wir genug Oberschwingungen für die Reihe haben
    while len(eigenfrequenzen) < 4:
        eigenfrequenzen.append(len(eigenfrequenzen) * GOLDEN_RATIO + 0.77)
        
    return eigenfrequenzen[:6]  # Limit auf die 6 dominantesten Quanten-Moden

def floquet_fourier_synthese(space_x: float, space_y: float, t: float, moden: List[float]) -> float:
    """
    Berechnet die Wahrscheinlichkeitsamplitude des Kristalls an der Koordinate (x,y) zum Zeitpunkt t.
    Nutzt eine Fourierreihe zur Überlagerung der zeitlichen und räumlichen Oberschwingungen.
    """
    psi_amplitude = 0.0
    gesamt_koeffizient = 0.0
    
    # Fourier-Synthese über die Quantenmoden (n = Harmonische)
    for n, ω_base in enumerate(moden, start=1):
        # Höhere Harmonische (n) repräsentieren höhere Energieniveaus
        ω_n = ω_base * n * 0.15          # Zeitliche Frequenz
        k_n = (2.0 * math.pi / n) * 0.08  # Räumliche Wellenzahl (K-Vektor)
        
        # Amplituden-Koeffizient sinkt quantenmechanisch mit 1/n (Fourier-Dämpfung)
        c_n = 1.0 / n
        
        # Quantenmechanische Phasen-Kopplung (Verschränkungssimulation im Raum)
        phase_x = math.sin(k_n * space_x + t * ω_n)
        phase_y = math.cos(k_n * space_y - t * ω_n * 0.5)
        
        # Aufaddieren zur Fourierreihe
        psi_amplitude += c_n * (phase_x * phase_y)
        gesamt_koeffizient += c_n
        
    # Normalisierter Zustandwert im Intervall [-1.0, 1.0]
    return psi_amplitude / gesamt_koeffizient if gesamt_koeffizient > 0 else 0.0

def hole_kristall_zustand_und_farbe(amplitude: float) -> Tuple[str, str]:
    """
    Ordnet der normalisierten Quanten-Intensität [0..1] eine Farbe und 
    Zustandsglyphe zu. Macht die Schwellenübergänge der Kristallphasen sichtbar.
    """
    # ANSI 256-Farbcodes für Quantenphasen
    ANSI_VAKUUM    = "\033[38;5;235m"  # Grau (Inaktiv / Vakuum)
    ANSI_GROUND    = "\033[38;5;27m"   # Dunkelblau (Grundzustand)
    ANSI_THERMAL   = "\033[38;5;40m"   # Tiefgrün (Thermische Phase)
    ANSI_CRYSTAL   = "\033[38;5;45m"   # Helles Cyan (Zeitkristall-Ordnung)
    ANSI_ENTANGLED = "\033[38;5;201m"  # Neon-Pink/Magenta (Maximale Verschränkung)
    
    if amplitude >= THRESHOLD_ENTANGLED:
        return ANSI_ENTANGLED, "⚛"  # Peak-Verschränkungssprung
    elif amplitude >= THRESHOLD_CRYSTAL:
        return ANSI_CRYSTAL, "█"     # Zeitkristalline Symmetriebrechung
    elif amplitude >= THRESHOLD_THERMAL:
        return ANSI_THERMAL, "▓"     # Thermischer Übergangsbereich
    elif amplitude >= THRESHOLD_GROUND:
        return ANSI_GROUND, "▒"      # Grundzustand / Niedrige Erregung
    else:
        return ANSI_VAKUUM, "░"      # Quantenrauschen

def rendere_kristall_gitter(t: float, moden: List[float]):
    """Generiert das zweidimensionale Quantenfeld des Zeitkristalls im Terminal."""
    gitter_zeilen = []
    
    for y in range(CRYSTAL_HEIGHT):
        zeile_str = ""
        aktuelle_farbe = ""
        
        for x in range(TERMINAL_WIDTH):
            # Berechne die lokale Wellenamplitude mittels Fourierreihe
            raw_psi = floquet_fourier_synthese(float(x), float(y), t, moden)
            
            # Normalisieren auf den Bereich [0.0, 1.0]
            norm_psi = (raw_psi + 1.0) * 0.5
            
            # Phase bestimmen anhand der Schwellenübergänge
            farbe, glyphe = hole_kristall_zustand_und_farbe(norm_psi)
            
            # Farbwechsel-Optimierung für flüssiges Rendering im Terminal
            if farbe != aktuelle_farbe:
                zeile_str += farbe + glyphe
                aktuelle_farbe = farbe
            else:
                zeile_str += glyphe
                
        if aktuelle_farbe:
            zeile_str += "\033[0m"
        gitter_zeilen.append(zeile_str)
        
    for zeile in gitter_zeilen:
        print(zeile)

def zeige_eigenzustand_spektrum(moden: List[float]):
    """Visualisiert das diskrete Energiespektrum der Fourier-Komponenten nach dem Lauf."""
    print("\n\033[1;35mDISCRETES ENERGIESPEKTRUM DES KRISTALLS (Fourier-Moden):\033[0m")
    for n, freq in enumerate(moden, start=1):
        gewicht = 1.0 / n
        balken = "■" * int(gewicht * 35)
        print(f"  Eigenzustand |ψ_{n}⟩ (E = {freq:5.2f} eV): \033[38;5;39m{balken:<35}\033[0m Gewicht: {gewicht:.2f}")

def starte_kristall_simulation(text_objekt: str):
    """Führt die evolutionäre Zeitschleife des Zeitkristalls aus."""
    moden = text_zu_eigenfrequenzen(text_objekt)
    total_frames = int(DURATION * FPS)
    delay = 1.0 / FPS
    
    t = 0.0
    for frame in range(total_frames):
        clear_terminal()
        print(f"\033[1;35m=== QUANTUM TIME CRYSTAL SPEKTRAL-ANALYSATOR v2.0 ===\033[0m")
        print(f"Gitter-Initialisierung über: [\033[1;33m{text_objekt}\033[0m] | Fourier-Zeitevolution läuft...")
        print("-" * TERMINAL_WIDTH)
        
        # Das Kristallgitter rendern
        rendere_kristall_gitter(t, moden)
        
        print("-" * TERMINAL_WIDTH)
        # Farbliche Schwellen-Legende der Kristallphasen
        print("Kristall-Phasen: "
              f"\033[38;5;235m░ Rauschen\033[0m  "
              f"\033[38;5;27m▒ Grundzustand (>{THRESHOLD_GROUND:.2f})\033[0m  "
              f"\033[38;5;40m▓ Thermisch (>{THRESHOLD_THERMAL:.2f})\033[0m  "
              f"\033[38;5;45m█ Zeitkristall (>{THRESHOLD_CRYSTAL:.2f})\033[0m  "
              f"\033[38;5;201m⚛ Verschränkt (>{THRESHOLD_ENTANGLED:.2f})\033[0m")
        print(f"Evolutionszeit τ: {t:.2f} \t| Frame: {frame+1}/{total_frames}")
        
        # Nicht-linearer Zeitsprung zur Simulation quantenmechanischer Fluktuationen
        t += 0.14 + 0.03 * math.sin(t * 0.5)
        time.sleep(delay)
        
    # Am Ende das diskrete Spektrum ausgeben
    zeige_eigenzustand_spektrum(moden)

def main():
    try:
        while True:
            clear_terminal()
            print("=" * 80)
            print("             FOURIER QUANTUM TIME CRYSTAL - PHASEN-ANALYSATOR")
            print("=" * 80)
            print("Dieses System nutzt Fourierreihen, um die Oberschwingungen der Wellenfunktion")
            print("eines Zeitkristalls zu berechnen. Wenn die Harmonischen konstruktiv")
            print("interferieren, durchbrechen sie Schwellenwerte und wechseln die Phase.")
            print("Geben Sie Quantenzustände (z.B. '1/2', '55/144') oder Textketten ein.")
            print("Tippen Sie 'exit' zum Verlassen.")
            print("-" * 80)
            
            user_input = input("\nQuanten-Eingabeobjekt: ").strip()
            if not user_input:
                continue
            if user_input.lower() == 'exit':
                print("\nQuanten-Prüfstand heruntergefahren. Symmetrie wiederhergestellt!")
                break
                
            print("\nBerechne Schrödinger-Eigenwerte und koppele Fourier-Moden...")
            time.sleep(0.6)
            starte_kristall_simulation(user_input)
            input("\n[ENTER] drücken für das nächste Quantenobjekt...")
            
    except KeyboardInterrupt:
        print("\nSimulation durch Benutzer unterbrochen.")

if __name__ == "__main__":
    main()
