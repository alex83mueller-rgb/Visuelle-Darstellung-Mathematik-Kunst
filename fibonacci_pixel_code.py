#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIBONACCI-PIXEL CODEC — echter Hin- und Rückweg
=================================================
Text -> Bits -> Fibonacci-Blöcke -> RGB-Pixel -> Anzeige -> zurück zu Bits -> Text.

WICHTIGER UNTERSCHIED zum "Quantum Crystal"-Skript:
Dort wurde die Eingabe nur zur Modulation einer Fourier-Animation genutzt
(Sinus/Kosinus + Rundung + Zufalls-Jitter + Farbschwellen) — das ist absichtlich
verlustbehaftet, für den visuellen Effekt. Ein Rückweg (Pixel -> Text) war dort
nicht möglich, weil bei jedem Schritt Information vernichtet wurde.

Hier ist es umgekehrt: JEDER Schritt ist bewusst verlustfrei gestaltet, damit
am Ende exakt wieder der Originaltext rauskommt. Das Preis dafür: die Anzeige
ist weniger "organisch", dafür ehrlich überprüfbar.

WARUM ES FUNKTIONIERT:
- Jeder Fibonacci-Block wird als ganze Zahl direkt in ein 24-Bit-RGB-Pixel
  gepackt (R = Bits 16-23, G = Bits 8-15, B = Bits 0-7). Keine Rundung nötig,
  weil Blockbreiten auf max. 24 Bit begrenzt sind (passt exakt in 3 Bytes).
- Die Blockbreite selbst wird separat mitgespeichert (als Metadatum neben
  dem Pixel) — ohne sie wüssten wir nicht, ob eine "5" aus "101" (3 Bit) oder
  "00101" (5 Bit) entstanden ist. Das ist kein Trick, sondern genau das,
  was auch echte Dateiformate tun (z.B. Bildbreite/-höhe im Header speichern).

EINSCHRÄNKUNG: Funktioniert zuverlässig für Zeichen mit Codepoint <= 255
(ASCII + deutsche Umlaute/ß). Für Emojis oder andere Unicode-Bereiche
bräuchte man mehr als 8 Bit pro Zeichen — das müsste man extra behandeln.
"""

import sys
import os
import time

# Nur Fibonacci-Zahlen bis 24 werden verwendet, damit jeder Block
# garantiert in ein einzelnes 24-Bit-RGB-Pixel passt (kein Rundungsverlust).
def fibonacci_bis(max_wert):
    folge = [1, 1]
    while True:
        naechste = folge[-1] + folge[-2]
        if naechste > max_wert:
            break
        folge.append(naechste)
    return folge

FIB_SEQ = fibonacci_bis(24)  # [1, 1, 2, 3, 5, 8, 13, 21]


def text_zu_bits(text: str) -> str:
    return "".join(format(ord(c), "08b") for c in text)


def bits_zu_text(bits: str) -> str:
    zeichen = []
    for i in range(0, len(bits), 8):
        byte = bits[i:i + 8]
        zeichen.append(chr(int(byte, 2)))
    return "".join(zeichen)


def in_fibonacci_bloecke(bits: str):
    bloecke = []
    index, fib_pos, n = 0, 0, len(bits)
    while index < n:
        breite = FIB_SEQ[fib_pos % len(FIB_SEQ)]
        rest = n - index
        if breite > rest:
            breite = rest  # letzter Block nimmt exakt den Rest
        bloecke.append(bits[index:index + breite])
        index += breite
        fib_pos += 1
    return bloecke


def block_zu_pixel(block_bits: str):
    wert = int(block_bits, 2) if block_bits else 0
    r = (wert >> 16) & 0xFF
    g = (wert >> 8) & 0xFF
    b = wert & 0xFF
    return (r, g, b)


def pixel_zu_block(pixel, breite: int) -> str:
    r, g, b = pixel
    wert = (r << 16) | (g << 8) | b
    return format(wert, f"0{breite}b")


def berechne_wasserzeichen(text: str):
    """
    Einfache XOR-Prüfsumme über den gesamten Bitstrom, als eigenes RGB-Pixel kodiert.
    WICHTIG zur Einordnung: Das ist ein Integritätsmerkmal, KEINE Kryptografie.
    Es hat keinen geheimen Schlüssel — jeder, der den Algorithmus kennt, kann ein
    passendes Wasserzeichen selbst berechnen. Es erkennt zufällige Verfälschung
    (z.B. ein falsch übertragenes Pixel), schützt aber nicht vor einem Angreifer,
    der bewusst und informiert fälschen will.
    """
    bits = text_zu_bits(text)
    summe = 0
    for i in range(0, len(bits), 24):
        stueck = bits[i:i + 24].ljust(24, "0")
        summe ^= int(stueck, 2)
    r = (summe >> 16) & 0xFF
    g = (summe >> 8) & 0xFF
    b = summe & 0xFF
    return (r, g, b)


def pruefe_wasserzeichen(text: str, wasserzeichen_pixel) -> bool:
    return berechne_wasserzeichen(text) == wasserzeichen_pixel


def extrahiere_wasserzeichen(pixel_daten):
    for eintrag in pixel_daten:
        if eintrag.get("wasserzeichen"):
            return eintrag["pixel"]
    return None


def encode(text: str):
    """Text -> Liste von {"pixel": (r,g,b), "breite": int}, plus 1 Wasserzeichen-Pixel am Ende."""
    bits = text_zu_bits(text)
    bloecke = in_fibonacci_bloecke(bits)
    pixel_daten = [{"pixel": block_zu_pixel(bl), "breite": len(bl), "wasserzeichen": False} for bl in bloecke]
    pixel_daten.append({"pixel": berechne_wasserzeichen(text), "breite": 0, "wasserzeichen": True})
    return pixel_daten


def decode(pixel_daten) -> str:
    """Liste von Pixel-Einträgen -> Original-Text (Wasserzeichen-Pixel wird übersprungen)"""
    bits = "".join(
        pixel_zu_block(e["pixel"], e["breite"])
        for e in pixel_daten
        if not e.get("wasserzeichen")
    )
    return bits_zu_text(bits)


GRID_BREITE = 16  # Pixel pro Zeile in der Anzeige


def clear_terminal():
    os.system("cls" if os.name == "nt" else "clear")


def render(pixel_daten):
    """Statische, unanimierte Ausgabe (z.B. für Skript-Import/Tests)."""
    zeile = ""
    for eintrag in pixel_daten:
        r, g, b = eintrag["pixel"]
        zeile += f"\033[48;2;{r};{g};{b}m  \033[0m"
    print(zeile)


def render_animiert(pixel_daten, text):
    """Zeigt live, wie jeder Block zu genau einem Pixel wird — Schritt für Schritt."""
    echte_bloecke = [e for e in pixel_daten if not e.get("wasserzeichen")]
    wasserzeichen = next(e for e in pixel_daten if e.get("wasserzeichen"))

    delay = min(0.15, 1.8 / max(1, len(echte_bloecke)))
    zeilen, aktuelle_zeile = [], ""
    for i, eintrag in enumerate(echte_bloecke):
        r, g, b = eintrag["pixel"]
        aktuelle_zeile += f"\033[48;2;{r};{g};{b}m  \033[0m"
        anzeige_zeilen = zeilen + [aktuelle_zeile]
        if (i + 1) % GRID_BREITE == 0:
            zeilen.append(aktuelle_zeile)
            aktuelle_zeile = ""

        clear_terminal()
        print(f"=== KODIERE: '{text}' ===")
        print(f"Block {i + 1}/{len(echte_bloecke)}  |  {eintrag['breite']} Bit  ->  RGB{eintrag['pixel']}")
        print("-" * 40)
        for z in anzeige_zeilen:
            print(z)
        time.sleep(delay)

    if aktuelle_zeile:
        zeilen.append(aktuelle_zeile)

    r, g, b = wasserzeichen["pixel"]
    wz_zeile = f"\033[48;2;{r};{g};{b}m  \033[0m"
    print(f"\n{len(echte_bloecke)} Pixel fertig kodiert.")
    print(f"Wasserzeichen (Prüfsumme): {wz_zeile} RGB{wasserzeichen['pixel']}\n")
    return zeilen


def decode_animiert(pixel_daten):
    """Liest die Pixel nacheinander zurück und baut den Text live vor den Augen auf."""
    echte_bloecke = [e for e in pixel_daten if not e.get("wasserzeichen")]
    delay = min(0.15, 1.8 / max(1, len(echte_bloecke)))
    bits_puffer, text_bisher = "", ""
    for i, eintrag in enumerate(echte_bloecke):
        block_bits = pixel_zu_block(eintrag["pixel"], eintrag["breite"])
        bits_puffer += block_bits
        while len(bits_puffer) >= 8:
            byte, bits_puffer = bits_puffer[:8], bits_puffer[8:]
            text_bisher += chr(int(byte, 2))

        clear_terminal()
        print(f"=== DEKODIERE Pixel {i + 1}/{len(echte_bloecke)} ===")
        print(f"RGB{eintrag['pixel']}  ->  {eintrag['breite']} Bit: {block_bits}")
        print("-" * 40)
        print(f"Bisher entschlüsselt: {text_bisher}\u2588")
        time.sleep(delay)

    print(f"\nFertig dekodiert: {text_bisher}\n")
    return text_bisher


def selbsttest():
    """Prüft den Rundweg UND das Wasserzeichen automatisch mit mehreren Beispielwörtern."""
    tests = ["Hi", "Test123", "Grüße", "##########", "hh#hh#hh#"]
    alle_ok = True
    print("Selbsttest läuft ...")
    for wort in tests:
        pd = encode(wort)
        zurueck = decode(pd)
        wz = extrahiere_wasserzeichen(pd)
        wz_ok = pruefe_wasserzeichen(zurueck, wz)
        ok = (zurueck == wort) and wz_ok
        alle_ok = alle_ok and ok
        status = "OK " if ok else "FEHLER"
        print(f"  [{status}] {wort!r} -> {len(pd) - 1} Pixel -> {zurueck!r}  (Wasserzeichen: {'gültig' if wz_ok else 'ungültig'})")

    # Zusätzlich: zeigen, dass eine Verfälschung tatsächlich auffliegt
    pd = encode("Test123")
    r, g, b = pd[0]["pixel"]
    pd[0]["pixel"] = ((r + 1) % 256, g, b)  # ein Pixel absichtlich verändern
    verfaelscht = decode(pd)
    wz = extrahiere_wasserzeichen(pd)
    erkannt = not pruefe_wasserzeichen(verfaelscht, wz)
    print(f"  [{'OK ' if erkannt else 'FEHLER'}] Verfälschungstest -> Wasserzeichen erkennt Manipulation: {erkannt}")
    alle_ok = alle_ok and erkannt

    print("Selbsttest bestanden.\n" if alle_ok else "Selbsttest FEHLGESCHLAGEN.\n")
    return alle_ok


def main():
    print("=" * 60)
    print("  FIBONACCI-PIXEL CODEC — Hin- und Rückweg")
    print("=" * 60)
    if not selbsttest():
        print("Abbruch: Selbsttest fehlgeschlagen, Programm ist fehlerhaft.")
        sys.exit(1)

    while True:
        wort = input("Text eingeben (oder 'exit'): ").strip()
        if wort.lower() == "exit":
            break
        if not wort:
            continue

        pixel_daten = encode(wort)
        render_animiert(pixel_daten, wort)
        input("[ENTER] zum Dekodieren ...")
        zurueck = decode_animiert(pixel_daten)

        # Konsistenzcheck gegen die geprüfte, unanimierte Kernlogik
        erwartet = decode(pixel_daten)
        wz_pixel = extrahiere_wasserzeichen(pixel_daten)
        wz_gueltig = pruefe_wasserzeichen(zurueck, wz_pixel)
        status = "IDENTISCH" if zurueck == wort == erwartet else "ABWEICHUNG"
        print(f"Original     : {wort}")
        print(f"Dekodiert    : {zurueck}")
        print(f"Status       : {status}")
        print(f"Wasserzeichen: {'gültig ✓' if wz_gueltig else 'UNGÜLTIG ✗ (Daten wurden verändert!)'}\n")
        input("[ENTER] für nächsten Lauf ...")


if __name__ == "__main__":
    main()
