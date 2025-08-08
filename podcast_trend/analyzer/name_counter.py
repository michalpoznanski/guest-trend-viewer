import pandas as pd
from .name_extractor import extract_names_from_title

def build_ranking(df:pd.DataFrame)->pd.DataFrame:
    rows = []
    for _, r in df.iterrows():
        names = extract_names_from_title(str(r.get("Title","")))
        for n in names:
            rows.append({"name": n, "views": int(r.get("View_Count",0))})
    if not rows:
        return pd.DataFrame(columns=["name","views"])
    agg = pd.DataFrame(rows).groupby("name", as_index=False)["views"].sum().sort_values("views", ascending=False)
    return agg
