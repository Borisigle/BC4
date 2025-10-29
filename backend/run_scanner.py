"""
Script para ejecutar el escáner de señales manualmente.
En futuro: se ejecutará cada hora automáticamente.
"""

from __future__ import annotations

from src.signals import SignalEngine


def main() -> None:
    print("🔍 Iniciando escáner de señales...\n")

    engine = SignalEngine()
    signals = engine.scan_for_signals()

    if not signals:
        print("❌ No se detectaron señales válidas en este momento.")
        print("   Razones comunes:")
        print("   - BTC en alta volatilidad o contexto desfavorable")
        print("   - No hay setups claros en ningún activo")
        print("   - Scores por debajo del umbral (< 50)")
        return

    print(f"✅ {len(signals)} señal(es) detectada(s):\n")

    for signal in signals:
        print("=" * 60)
        print(signal.to_alert_string())
        print("=" * 60)
        print()


if __name__ == "__main__":
    main()
