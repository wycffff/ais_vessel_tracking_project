from io import StringIO
import pandas as pd


def tracks_to_csv_buffer(rows: list[dict]) -> StringIO:
    df = pd.DataFrame(rows)
    buffer = StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    return buffer
