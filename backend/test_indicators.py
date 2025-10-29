"""Standalone script to inspect indicators over stored OHLCV data."""

from __future__ import annotations

from src.config import settings
from src.data.data_storage import DataStorage
from src.indicators.market_structure import MarketStructure
from src.indicators.technical_indicators import TechnicalIndicators


def main() -> None:
    storage = DataStorage(settings.DB_PATH)
    df = storage.get_ohlcv("BTC/USDT", "4h", limit=200)

    if df.empty:
        print("⚠️ No hay datos OHLCV almacenados para BTC/USDT 4h.")
        return

    ti = TechnicalIndicators()
    df = ti.add_all_indicators(df)

    ms = MarketStructure()
    df = ms.detect_swing_points(df)
    sr = ms.identify_support_resistance(df)
    trend = ms.determine_trend(df)

    print("\n📊 BTC/USDT 4H - Últimas 5 velas con indicadores:")
    columns = ["datetime", "close", "ema_20", "ema_50", "atr", "adx", "rsi"]
    available = [col for col in columns if col in df.columns]
    display_df = df[available].tail().copy()
    if "datetime" in display_df.columns:
        display_df["datetime"] = display_df["datetime"].dt.strftime("%Y-%m-%d %H:%M")
    print(display_df.to_string(index=False))

    print(f"\n📈 Tendencia: {trend['trend']}")
    print(f"   Fuerza: {trend['trend_strength']:.1f}")
    print(f"   ADX: {trend['adx_value']:.2f}")

    print("\n🔴 Resistencias detectadas:")
    if sr["resistances"]:
        for resistance in sr["resistances"][:3]:
            print(
                f"   ${resistance['price']:,.2f} ({resistance['strength']}, {resistance['touches']} toques)"
            )
    else:
        print("   Ninguna resistencia detectada")

    print("\n🟢 Soportes detectados:")
    if sr["supports"]:
        for support in sr["supports"][:3]:
            print(f"   ${support['price']:,.2f} ({support['strength']}, {support['touches']} toques)")
    else:
        print("   Ningún soporte detectado")


if __name__ == "__main__":
    main()
