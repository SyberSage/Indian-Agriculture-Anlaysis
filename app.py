"""AgriData Explorer - Indian agriculture dashboard (ICRISAT district data, 1966-2017)."""
import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

st.set_page_config(page_title="AgriData Explorer", page_icon="🌾", layout="wide")

DATA_DIR = Path(__file__).parent / "data"

# Column prefix -> (display name, group). The OILSEEDS and SORGHUM total columns are left out on
# purpose: they would double count their component crops (and OILSEEDS is mostly 0 after 2015).
CROPS = {
    "RICE": ("Rice", "Cereals"), "WHEAT": ("Wheat", "Cereals"), "MAIZE": ("Maize", "Cereals"),
    "KHARIF_SORGHUM": ("Kharif Sorghum", "Cereals"), "RABI_SORGHUM": ("Rabi Sorghum", "Cereals"),
    "PEARL_MILLET": ("Pearl Millet", "Cereals"), "FINGER_MILLET": ("Finger Millet", "Cereals"),
    "BARLEY": ("Barley", "Cereals"),
    "CHICKPEA": ("Chickpea", "Pulses"), "PIGEONPEA": ("Pigeonpea", "Pulses"),
    "MINOR_PULSES": ("Minor Pulses", "Pulses"),
    "GROUNDNUT": ("Groundnut", "Oilseeds"), "SESAMUM": ("Sesamum", "Oilseeds"),
    "RAPESEED_AND_MUSTARD": ("Rapeseed & Mustard", "Oilseeds"), "SAFFLOWER": ("Safflower", "Oilseeds"),
    "CASTOR": ("Castor", "Oilseeds"), "LINSEED": ("Linseed", "Oilseeds"),
    "SUNFLOWER": ("Sunflower", "Oilseeds"), "SOYABEAN": ("Soyabean", "Oilseeds"),
    "SUGARCANE": ("Sugarcane", "Cash Crops"), "COTTON": ("Cotton", "Cash Crops"),
}
OIL_PARTS = ["GROUNDNUT", "SESAMUM", "RAPESEED_AND_MUSTARD", "SAFFLOWER", "CASTOR", "LINSEED",
             "SUNFLOWER", "SOYABEAN"]
ALL_OILSEEDS = "All Oilseeds (8 crops combined)"
CROP_CHOICES = ["Rice", "Wheat", "Sugarcane", "Maize", "Cotton", ALL_OILSEEDS, "Groundnut", "Soyabean",
                "Pearl Millet", "Chickpea", "Pigeonpea", "Barley", "Finger Millet", "Kharif Sorghum",
                "Rabi Sorghum", "Rapeseed & Mustard", "Sesamum", "Sunflower", "Safflower", "Castor",
                "Linseed", "Minor Pulses"]
METRICS = {"Production (1000 tons)": "PROD", "Area (1000 ha)": "AREA", "Yield (kg/ha)": "YIELD"}
COMBINED_METRICS = {"Production (1000 tons)": "PROD", "Area (1000 ha)": "AREA"}



# ----------------------------------------------------------------------------- data
def find_data_file() -> Path:
    """Look for data/clean_agri_data.xlsx (also tolerates a mistyped .xlxs, or a .csv)."""
    for ext in (".xlsx", ".xlxs", ".xls", ".csv"):
        path = DATA_DIR / f"clean_agri_data{ext}"
        if path.exists():
            return path
    st.error("Data file not found. Put clean_agri_data.xlsx inside the data/ folder.")
    st.stop()


@st.cache_data
def load_wide() -> pd.DataFrame:
    """The cleaned wide table, exactly as produced by 1_data_cleaning.ipynb (-1 already replaced by 0)."""
    path = find_data_file()
    wide = pd.read_csv(path) if path.suffix == ".csv" else pd.read_excel(path, engine="openpyxl")
    num = wide.select_dtypes("number").columns
    wide[num] = wide[num].clip(lower=0)  # same as the notebook: -1 (not available) -> 0
    wide["STATE_NAME"] = wide["STATE_NAME"].replace({"Orissa": "Odisha"})
    wide["OILSEEDS_PROD_FIXED"] = sum(wide[f"{c}_PRODUCTION_1000_TONS"] for c in OIL_PARTS)
    wide["OILSEEDS_AREA_FIXED"] = sum(wide[f"{c}_AREA_1000_HA"] for c in OIL_PARTS)
    return wide


@st.cache_data
def load_data() -> pd.DataFrame:
    """One row per district-year-crop, built from the wide table."""
    wide = load_wide()
    parts = []
    for key, (name, group) in CROPS.items():
        part = wide[["YEAR", "STATE_NAME", "DIST_NAME"]].copy()
        part["CROP"], part["GROUP"] = name, group
        part["AREA"] = wide[f"{key}_AREA_1000_HA"]
        part["PROD"] = wide[f"{key}_PRODUCTION_1000_TONS"]
        parts.append(part)
    long = pd.concat(parts, ignore_index=True)
    return long[(long["AREA"].fillna(0) > 0) | (long["PROD"].fillna(0) > 0)].reset_index(drop=True)


def summarise(df: pd.DataFrame, by) -> pd.DataFrame:
    """Sum area and production, then compute yield from the totals (never average yields)."""
    g = df.groupby(by, as_index=False)[["AREA", "PROD"]].sum(min_count=1)
    g["YIELD"] = g["PROD"] / g["AREA"].where(g["AREA"] > 0) * 1000
    return g


def pick_crop(df: pd.DataFrame, choice: str) -> pd.DataFrame:
    return df[df["GROUP"] == "Oilseeds"] if choice == ALL_OILSEEDS else df[df["CROP"] == choice]


def human(x) -> str:
    if pd.isna(x):
        return "-"
    for div, suffix in ((1e6, "M"), (1e3, "K")):
        if abs(x) >= div:
            return f"{x / div:.2f}{suffix}"
    return f"{x:,.0f}"


def top_bar(df: pd.DataFrame, y: str, col: str, label: str, title: str, n: int = 15, height: int = 420):
    d = df.dropna(subset=[col]).nlargest(n, col)
    fig = px.bar(d, x=col, y=y, orientation="h", title=title, labels={col: label},
                 color_discrete_sequence=["#2e8b57"])
    fig.update_yaxes(autorange="reversed", title=None)
    fig.update_layout(height=height, margin=dict(l=0, r=0, t=40, b=0))
    return fig


# ----------------------------------------------------------------------------- notebook analyses
def P(crop: str) -> str:
    return f"{crop}_PRODUCTION_1000_TONS"


def A(crop: str) -> str:
    return f"{crop}_AREA_1000_HA"


def bar_series(s: pd.Series, title: str, ylabel: str = "Production (1000 tons)"):
    d = pd.DataFrame({"label": s.index.astype(str), "value": s.values})
    fig = px.bar(d, x="label", y="value", title=title, labels={"label": "", "value": ylabel},
                 color_discrete_sequence=["#2e8b57"])
    fig.update_layout(height=400, margin=dict(l=0, r=0, t=50, b=0))
    return fig


def line_fig(d: pd.DataFrame, x: str, y: str, title: str, color=None, **kwargs):
    fig = px.line(d, x=x, y=y, color=color, title=title, **kwargs)
    fig.update_layout(height=420, margin=dict(l=0, r=0, t=50, b=0))
    return fig


EDA_TITLES = [
    "1. Top 7 rice-producing states",
    "2. Top 5 wheat-producing states (bar + share)",
    "3. Oilseed production, top 5 states",
    "4. Top 7 sunflower-producing states",
    "5. Sugarcane production over the years",
    "6. Rice vs wheat production over the years",
    "7. Rice production by West Bengal districts",
    "8. Top 10 wheat production years, Uttar Pradesh",
    "9. Millet production over the years",
    "10. Sorghum production by state (Kharif and Rabi)",
    "11. Top 7 states for groundnut production",
    "12. Soyabean: top 5 states and yield efficiency",
    "13. Oilseed production in major states",
    "14. Impact of area on production (rice, wheat, maize)",
    "15. Rice vs wheat yield across states",
]
EDA_NOTES = {
    2: "Oilseeds are built from their 8 component crops. The `OILSEEDS` column in the source file is "
       "mostly 0 from 2016 onward, which understates recent production.",
    11: "Yield is total production divided by total area. Averaging the yield column would weight tiny "
        "districts the same as large ones.",
    12: "Oilseeds are built from their 8 component crops (the `OILSEEDS` column is mostly 0 from 2016).",
    13: "Rows with zero area or production are left out of the scatter, since 0 means 'not recorded'.",
    14: "Yield is total production divided by total area, so states that do not grow a crop are not "
        "pulled down by zeros.",
}


def eda_figs(W: pd.DataFrame, i: int) -> list:
    by_state = lambda col: W.groupby("STATE_NAME")[col].sum()
    by_year = lambda col: W.groupby("YEAR")[col].sum()
    if i == 0:
        return [bar_series(by_state(P("RICE")).nlargest(7), "Top 7 rice-producing states")]
    if i == 1:
        s = by_state(P("WHEAT")).nlargest(5)
        pie = px.pie(values=s.values, names=s.index, title="Wheat production share (among the top 5)")
        pie.update_layout(height=400, margin=dict(l=0, r=0, t=50, b=0))
        return [bar_series(s, "Top 5 wheat-producing states"), pie]
    if i == 2:
        return [bar_series(by_state("OILSEEDS_PROD_FIXED").nlargest(5), "Top 5 oilseed-producing states")]
    if i == 3:
        return [bar_series(by_state(P("SUNFLOWER")).nlargest(7), "Top 7 sunflower-producing states")]
    if i == 4:
        d = by_year(P("SUGARCANE")).reset_index()
        return [line_fig(d, "YEAR", P("SUGARCANE"), "Sugarcane production over the years (1000 tons)")]
    if i == 5:
        d = pd.DataFrame({"Rice": by_year(P("RICE")), "Wheat": by_year(P("WHEAT"))}).reset_index()
        d = d.melt("YEAR", var_name="Crop", value_name="Production (1000 tons)")
        return [line_fig(d, "YEAR", "Production (1000 tons)", "Rice vs wheat production", color="Crop")]
    if i == 6:
        s = W[W["STATE_NAME"] == "West Bengal"].groupby("DIST_NAME")[P("RICE")].sum().nlargest(10)
        return [bar_series(s, "Rice production: top 10 West Bengal districts")]
    if i == 7:
        s = W[W["STATE_NAME"] == "Uttar Pradesh"].groupby("YEAR")[P("WHEAT")].sum().nlargest(10)
        return [bar_series(s, "Top 10 wheat production years: Uttar Pradesh")]
    if i == 8:
        d = by_year(P("PEARL_MILLET")).reset_index()
        return [line_fig(d, "YEAR", P("PEARL_MILLET"), "Pearl millet production over the years (1000 tons)")]
    if i == 9:
        s = W.groupby("STATE_NAME")[[P("KHARIF_SORGHUM"), P("RABI_SORGHUM")]].sum()
        s.columns = ["Kharif", "Rabi"]
        fig = px.bar(s.reset_index(), x="STATE_NAME", y=["Kharif", "Rabi"], barmode="stack",
                     title="Sorghum production by state (1000 tons)",
                     labels={"value": "Production (1000 tons)", "STATE_NAME": "", "variable": "Season"})
        fig.update_layout(height=420, margin=dict(l=0, r=0, t=50, b=0))
        return [fig]
    if i == 10:
        return [bar_series(by_state(P("GROUNDNUT")).nlargest(7), "Top 7 states for groundnut production")]
    if i == 11:
        g = W.groupby("STATE_NAME")[[P("SOYABEAN"), A("SOYABEAN")]].sum().nlargest(5, P("SOYABEAN"))
        yld = g[P("SOYABEAN")] / g[A("SOYABEAN")].where(g[A("SOYABEAN")] > 0) * 1000
        return [bar_series(g[P("SOYABEAN")], "Top 5 soyabean-producing states"),
                bar_series(yld, "Soyabean yield efficiency, top 5 states", "Yield (kg/ha)")]
    if i == 12:
        return [bar_series(by_state("OILSEEDS_PROD_FIXED").nlargest(10), "Oilseed production: top 10 states")]
    if i == 13:
        parts = []
        for crop in ("RICE", "WHEAT", "MAIZE"):
            d = W[(W[A(crop)] > 0) & (W[P(crop)] > 0)][[A(crop), P(crop), "DIST_NAME", "STATE_NAME", "YEAR"]]
            d.columns = ["Area (1000 ha)", "Production (1000 tons)", "DIST_NAME", "STATE_NAME", "YEAR"]
            parts.append(d.assign(Crop=crop.title()))
        fig = px.scatter(pd.concat(parts), x="Area (1000 ha)", y="Production (1000 tons)", color="Crop",
                         hover_data=["DIST_NAME", "STATE_NAME", "YEAR"], opacity=0.5,
                         title="Impact of area on production")
        fig.update_layout(height=480, margin=dict(l=0, r=0, t=50, b=0))
        return [fig]
    g = W.groupby("STATE_NAME")[[P("RICE"), A("RICE"), P("WHEAT"), A("WHEAT")]].sum()
    y = pd.DataFrame({"Rice": g[P("RICE")] / g[A("RICE")].where(g[A("RICE")] > 0) * 1000,
                      "Wheat": g[P("WHEAT")] / g[A("WHEAT")].where(g[A("WHEAT")] > 0) * 1000})
    top = y.nlargest(10, "Rice").reset_index()
    fig = px.bar(top, x="STATE_NAME", y=["Rice", "Wheat"], barmode="group",
                 title="Rice vs wheat yield, top 10 states by rice yield",
                 labels={"value": "Yield (kg/ha)", "STATE_NAME": "", "variable": "Crop"})
    fig.update_layout(height=420, margin=dict(l=0, r=0, t=50, b=0))
    return [fig]


def district_corr(W: pd.DataFrame, crop: str, min_years: int = 10) -> pd.DataFrame:
    d = W[(W[A(crop)] > 0) & (W[P(crop)] > 0)]
    rows = []
    for (dist, state), g in d.groupby(["DIST_NAME", "STATE_NAME"]):
        if len(g) >= min_years:
            rows.append((dist, state, g[A(crop)].corr(g[P(crop)])))
    return pd.DataFrame(rows, columns=["district", "state", f"{crop.lower()}_corr"])


SQL_NOTES = {
    2: "Oilseeds are built from the 8 component crops. The raw `OILSEEDS` column is 0 in 2016-2017, which "
       "made states like Chhattisgarh and Telangana show a false -100% growth.",
    3: "Only districts with at least 10 years of data are included (fewer if you select a shorter year range).",
    8: "Only districts with at least 10 years of data are included (fewer if you select a shorter year range).",
    7: "Oilseed area is built from the 8 component crops, because the raw `OILSEEDS` area column is 0 in "
       "2016-2017 (that left the latest-year column empty).",
}


def sql_results(W: pd.DataFrame, i: int) -> dict:
    """Pandas version of each SQL question in 3_SQL.ipynb (same logic, same filters)."""
    if W.empty:
        return {"empty": "No data in this year range."}
    latest = int(W["YEAR"].max())
    n_years = int(W["YEAR"].nunique())
    min_years = min(10, n_years)  # districts need 10 years of data (fewer if a shorter range is selected)
    needs_prior = f"Widen the year range so it includes {latest - 5}: this question compares {latest} with {latest - 5}."
    if i in (1, 2) and latest - 5 < int(W["YEAR"].min()):
        return {"empty": needs_prior}
    if i == 3 and n_years < 3:
        return {"empty": "Select at least 3 years to compute correlations."}
    if i == 0:
        top3 = W.groupby("STATE_NAME")[P("RICE")].sum().nlargest(3).index
        d = (W[W["STATE_NAME"].isin(top3)].groupby(["YEAR", "STATE_NAME"], as_index=False)[P("RICE")].sum()
             .rename(columns={"YEAR": "year", "STATE_NAME": "state", P("RICE"): "rice_production"})
             .sort_values(["year", "rice_production"], ascending=[True, False]))
        return {"table": d, "figs": [line_fig(d, "year", "rice_production",
                                              "Rice production (1000 tons): top 3 states", color="state")]}
    if i == 1:
        ycol = "WHEAT_YIELD_KG_PER_HA"
        end = W[W["YEAR"] == latest][["DIST_CODE", "DIST_NAME", "STATE_NAME", ycol]].rename(
            columns={ycol: "end_yield", "DIST_NAME": "district", "STATE_NAME": "state"})
        start = W[W["YEAR"] == latest - 5][["DIST_CODE", ycol]].rename(columns={ycol: "start_yield"})
        m = end.merge(start, on="DIST_CODE")
        m = m[(m["end_yield"] > 0) & (m["start_yield"] > 0)]
        m["yield_increase"] = m["end_yield"] - m["start_yield"]
        d = m.nlargest(5, "yield_increase")[["district", "state", "start_yield", "end_yield", "yield_increase"]]
        fig = px.bar(d, x="district", y="yield_increase", color="state",
                     title=f"Wheat yield increase (kg/ha), {latest - 5} to {latest}")
        fig.update_layout(height=400, margin=dict(l=0, r=0, t=50, b=0))
        return {"table": d, "figs": [fig]}
    if i == 2:
        g = W[W["YEAR"].isin([latest, latest - 5])].pivot_table(
            index="STATE_NAME", columns="YEAR", values="OILSEEDS_PROD_FIXED", aggfunc="sum")
        d = pd.DataFrame({"recent_prod": g[latest], "old_prod": g[latest - 5]})
        d = d[d["old_prod"] > 0]
        d["growth_rate_pct"] = ((d["recent_prod"] - d["old_prod"]) / d["old_prod"] * 100).round(2)
        d = d.sort_values("growth_rate_pct", ascending=False).reset_index().rename(columns={"STATE_NAME": "state"})
        fig = px.bar(d, x="state", y="growth_rate_pct", title="Oilseed production growth (%), 5-year",
                     color="growth_rate_pct", color_continuous_scale="RdYlGn", color_continuous_midpoint=0)
        fig.update_layout(height=400, margin=dict(l=0, r=0, t=50, b=0))
        return {"table": d, "figs": [fig]}
    if i == 3:
        d = (district_corr(W, "RICE", min_years).merge(district_corr(W, "WHEAT", min_years), on=["district", "state"], how="outer")
             .merge(district_corr(W, "MAIZE", min_years), on=["district", "state"], how="outer").round(3))
        long = d.melt(id_vars=["district", "state"], var_name="crop", value_name="correlation").dropna()
        fig = px.box(long, x="crop", y="correlation", points="all", hover_data=["district", "state"],
                     title="District-wise correlation between area and production")
        fig.update_layout(height=450, margin=dict(l=0, r=0, t=50, b=0))
        return {"table": d, "figs": [fig], "extra": d[["rice_corr", "wheat_corr", "maize_corr"]].describe().round(3)}
    if i == 4:
        top5 = W.groupby("STATE_NAME")[P("COTTON")].sum().nlargest(5).index
        y = (W[W["STATE_NAME"].isin(top5)].groupby(["STATE_NAME", "YEAR"], as_index=False)[P("COTTON")].sum()
             .rename(columns={"STATE_NAME": "state", "YEAR": "year", P("COTTON"): "cotton_production"})
             .sort_values(["state", "year"]))
        prev = y.groupby("state")["cotton_production"].shift()
        y["yoy_growth_pct"] = ((y["cotton_production"] - prev) / prev.where(prev != 0) * 100).round(2)
        return {"table": y, "figs": [line_fig(y, "year", "yoy_growth_pct",
                                              "Cotton production: year-over-year growth (%)", color="state")]}
    if i == 5:
        d = (W[(W["YEAR"] == latest) & (W[P("GROUNDNUT")] > 0)]
             .groupby(["DIST_NAME", "STATE_NAME"], as_index=False)[P("GROUNDNUT")].sum()
             .nlargest(10, P("GROUNDNUT"))
             .rename(columns={"DIST_NAME": "district", "STATE_NAME": "state", P("GROUNDNUT"): "groundnut_production"}))
        fig = px.bar(d, x="district", y="groundnut_production", color="state",
                     title=f"Top 10 districts by groundnut production ({latest})")
        fig.update_layout(height=400, margin=dict(l=0, r=0, t=50, b=0))
        return {"table": d, "figs": [fig]}
    if i == 6:
        m = W[(W[A("MAIZE")] > 0) & (W[P("MAIZE")] > 0)]
        by_sy = m.groupby(["YEAR", "STATE_NAME"], as_index=False)[[P("MAIZE"), A("MAIZE")]].sum()
        by_sy["maize_yield_kg_per_ha"] = (by_sy[P("MAIZE")] / by_sy[A("MAIZE")] * 1000).round(2)
        by_sy = by_sy.rename(columns={"YEAR": "year", "STATE_NAME": "state"})[["year", "state", "maize_yield_kg_per_ha"]]
        india = m.groupby("YEAR", as_index=False)[[P("MAIZE"), A("MAIZE")]].sum()
        india["india_maize_yield_kg_per_ha"] = (india[P("MAIZE")] / india[A("MAIZE")] * 1000).round(2)
        india = india.rename(columns={"YEAR": "year"})
        return {"table": by_sy, "figs": [
            line_fig(india, "year", "india_maize_yield_kg_per_ha", "All-India maize yield (kg/ha)"),
            line_fig(by_sy, "year", "maize_yield_kg_per_ha", "Maize yield by state (kg/ha)", color="state")]}
    if i == 7:
        sy = W[W["OILSEEDS_AREA_FIXED"] > 0].groupby(["STATE_NAME", "YEAR"], as_index=False)["OILSEEDS_AREA_FIXED"].sum()
        avg = sy.groupby("STATE_NAME")["OILSEEDS_AREA_FIXED"].mean().round(2)
        last = sy[sy["YEAR"] == latest].set_index("STATE_NAME")["OILSEEDS_AREA_FIXED"].round(2)
        d = (pd.DataFrame({"avg_annual_area_1000ha": avg, "latest_year_area_1000ha": last})
             .sort_values("avg_annual_area_1000ha", ascending=False).reset_index()
             .rename(columns={"STATE_NAME": "state"}))
        fig = px.bar(d, x="state", y="avg_annual_area_1000ha",
                     title="Average annual oilseed area (1000 ha) by state", color_discrete_sequence=["#2e8b57"])
        fig.update_layout(height=400, margin=dict(l=0, r=0, t=50, b=0))
        return {"table": d, "figs": [fig]}
    if i == 8:
        g = (W[W["RICE_YIELD_KG_PER_HA"] > 0].groupby(["DIST_NAME", "STATE_NAME"])["RICE_YIELD_KG_PER_HA"]
             .agg(avg_rice_yield="mean", years_recorded="count").reset_index())
        d = (g[g["years_recorded"] >= min_years].nlargest(10, "avg_rice_yield").round(2)
             .rename(columns={"DIST_NAME": "district", "STATE_NAME": "state"}))
        fig = px.bar(d, x="district", y="avg_rice_yield", color="state",
                     title="Top 10 districts by average rice yield (kg/ha)")
        fig.update_layout(height=400, margin=dict(l=0, r=0, t=50, b=0))
        return {"table": d, "figs": [fig]}
    r = W[W["YEAR"] >= latest - 9]
    top5 = (r.groupby("STATE_NAME")[P("RICE")].sum() + r.groupby("STATE_NAME")[P("WHEAT")].sum()).nlargest(5).index
    d = (r[r["STATE_NAME"].isin(top5)].groupby(["YEAR", "STATE_NAME"], as_index=False)[[P("RICE"), P("WHEAT")]].sum()
         .rename(columns={"YEAR": "year", "STATE_NAME": "state", P("RICE"): "rice_production",
                          P("WHEAT"): "wheat_production"}))
    long = d.melt(id_vars=["year", "state"], var_name="crop", value_name="production")
    fig = px.line(long, x="year", y="production", color="state", line_dash="crop",
                  title="Rice vs wheat production (1000 tons), top 5 states, last 10 years")
    fig.update_layout(height=450, margin=dict(l=0, r=0, t=50, b=0))
    return {"table": d, "figs": [fig]}


SQL_TITLES = ['1.Year-wise Trend of Rice Production Across States (Top 3)', '2.Top 5 Districts by Wheat Yield Increase Over the Last 5 Years', '3. States with the Highest Growth in Oilseed Production (5-Year Growth Rate)', '4.District-wise Correlation Between Area and Production for Rice, Wheat, Maize', '5. Yearly Production Growth of Cotton in Top 5 Cotton Producing States', '6. Districts with the Highest Groundnut Production in the Latest Year', '7. Annual Average Maize Yield Across All States', '8. Total Area Cultivated for Oilseeds in Each State', '9. Districts with the Highest Rice Yield', '10. Compare Production of Wheat and Rice for Top 5 States Over 10 Years']


# ----------------------------------------------------------------------------- pages
def page_all_crops():
    st.header("📊 All Crops")
    st.caption("All 21 individual crops combined. Fruits, vegetables, potatoes, onion and fodder have "
               "area only, so they are not included. Production in tons mixes sugarcane (raw cane "
               "weight) with grains, so area is the fairer combined comparison.")
    if filtered.empty:
        st.warning("No data for this selection.")
        return
    tot = summarise(filtered.assign(_k=1), "_k").iloc[0]
    by_state_all = summarise(filtered, "STATE_NAME")
    top_state = by_state_all.nlargest(1, "PROD")["STATE_NAME"].iloc[0]
    k1, k2, k3 = st.columns(3)
    k1.metric("Total production (1000 tons)", human(tot["PROD"]))
    k2.metric("Total area (1000 ha)", human(tot["AREA"]))
    k3.metric("Top state by production", top_state)

    m_label = st.radio("Metric", list(COMBINED_METRICS), horizontal=True, key="all_metric")
    m = COMBINED_METRICS[m_label]

    left, right = st.columns(2)
    by_year_all = summarise(filtered, "YEAR")
    combo = make_subplots(specs=[[{"secondary_y": True}]])
    combo.add_bar(x=by_year_all["YEAR"], y=by_year_all["AREA"], name="Area (1000 ha)",
                  marker_color="#a8d5a2")
    combo.add_trace(go.Scatter(x=by_year_all["YEAR"], y=by_year_all["PROD"], name="Production (1000 tons)",
                               line=dict(color="#1b5e20")), secondary_y=True)
    combo.update_layout(title="Area and production by year", height=440, margin=dict(l=0, r=0, t=40, b=0),
                        legend=dict(orientation="h", y=-0.2))
    left.plotly_chart(combo, width="stretch")
    right.plotly_chart(top_bar(by_state_all, "STATE_NAME", m, m_label, f"Top states by {m_label}", 10,
                               height=440), width="stretch")

    a, b = st.columns(2)
    by_crop = summarise(filtered, "CROP")
    a.plotly_chart(top_bar(by_crop, "CROP", m, m_label, f"{m_label} by crop", 21, height=480), width="stretch")
    by_group_year = summarise(filtered, ["YEAR", "GROUP"])
    grp = px.area(by_group_year, x="YEAR", y=m, color="GROUP", labels={m: m_label},
                  title=f"{m_label} by crop group over time")
    grp.update_layout(height=480, margin=dict(l=0, r=0, t=40, b=0))
    b.plotly_chart(grp, width="stretch")
    tree_data = by_crop.dropna(subset=["AREA"]).merge(
        pd.DataFrame([(n, g) for n, g in CROPS.values()], columns=["CROP", "GROUP"]), on="CROP")
    st.plotly_chart(px.treemap(tree_data[tree_data["AREA"] > 0], path=["GROUP", "CROP"], values="AREA",
                               title="Share of cropped area (1000 ha)"), width="stretch")


def page_crop_explorer():
    st.header("🌱 Crop Explorer")
    c1, c2 = st.columns([2, 3])
    crop_choice = c1.selectbox("Crop", CROP_CHOICES)
    metric_label = c2.radio("Metric", list(METRICS), horizontal=True)
    metric = METRICS[metric_label]

    sel = pick_crop(filtered, crop_choice)
    if sel.empty:
        st.warning("No data for this selection.")
        return
    by_state = summarise(sel, "STATE_NAME")
    total = summarise(sel.assign(_k=1), "_k").iloc[0]
    best = by_state.dropna(subset=[metric]).nlargest(1, metric)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Production (1000 tons)", human(total["PROD"]))
    k2.metric("Area (1000 ha)", human(total["AREA"]))
    k3.metric("Yield (kg/ha)", human(total["YIELD"]))
    k4.metric(f"Top state ({metric_label.split(' (')[0].lower()})",
              best["STATE_NAME"].iloc[0] if not best.empty else "-")
    st.caption("This page shows one crop at a time, so its top state can differ from the All Crops page. "
               "Production and area are summed over the selected years, so area counts the same land once "
               "per year. Yield is production divided by area, so it is not affected.")

    left, right = st.columns(2)
    by_year = summarise(sel, "YEAR")
    trend = px.area(by_year, x="YEAR", y=metric, labels={metric: metric_label},
                    title=f"{crop_choice}: {metric_label} by year", color_discrete_sequence=["#2e8b57"])
    trend.update_layout(height=460, margin=dict(l=0, r=0, t=40, b=0))
    left.plotly_chart(trend, width="stretch")
    right.plotly_chart(top_bar(by_state, "STATE_NAME", metric, metric_label,
                               f"Top states by {metric_label}", 12, height=460), width="stretch")


def page_eda():
    st.header("🔎 EDA", anchor="eda-top")
    st.caption("The 15 analyses from 2_EDA.ipynb, one after another. They use the year range at the top of "
               "the page (the state filter does not apply).")
    st.markdown("**Jump to:** " + " · ".join(f"[{i + 1}](#eda-{i + 1})" for i in range(len(EDA_TITLES))))
    for i, title in enumerate(EDA_TITLES):
        st.subheader(title, anchor=f"eda-{i + 1}", divider="green")
        for j, fig in enumerate(run_eda(i, year_from, year_to)):
            st.plotly_chart(fig, width="stretch", key=f"eda_{i}_{j}")
        if i in EDA_NOTES:
            st.info(EDA_NOTES[i])
        st.markdown("[↑ Back to top](#eda-top)")


def page_sql():
    st.header("🧮 SQL Questions", anchor="sql-top")
    st.caption("The 10 questions from 3_SQL.ipynb, one after another. Each result is computed here with the "
               "same logic as the MySQL query (a hosted app cannot reach a local database), and it uses the "
               "year range at the top of the page.")
    st.markdown("**Jump to:** " + " · ".join(f"[Q{i + 1}](#sql-{i + 1})" for i in range(len(SQL_TITLES))))
    for i, title in enumerate(SQL_TITLES):
        st.subheader(clean_title(title), anchor=f"sql-{i + 1}", divider="green")
        result = run_sql(i, year_from, year_to)
        if "empty" in result:
            st.info(result["empty"])
        else:
            for j, fig in enumerate(result["figs"]):
                st.plotly_chart(fig, width="stretch", key=f"sql_{i}_{j}")
            if i in SQL_NOTES:
                st.info(SQL_NOTES[i])
            st.dataframe(result["table"], width="stretch", hide_index=True, key=f"sql_tbl_{i}")
            if "extra" in result:
                st.caption("Summary of the district correlations")
                st.dataframe(result["extra"], width="stretch", key=f"sql_extra_{i}")
        st.markdown("[↑ Back to top](#sql-top)")


def page_about():
    st.header("ℹ️ About the project")
    st.markdown(
        """
**AgriData Explorer: Understanding Indian agriculture with EDA**

India's agriculture data is complex, fragmented and hard to access, which makes it difficult for farmers,
policymakers and researchers to make informed decisions. This project brings district-level data from
20 states (1966-2017) into one place, so crop **production, yield and area under cultivation** are easy to
explore, and trends, gaps and regional differences stand out.

**Who it helps**
- **Farmers:** see how crops have performed over time and where regional productivity can improve.
- **Policymakers:** find low-productivity regions and crops with fluctuating yields, for subsidies and insurance planning.
- **Researchers:** study agricultural trends and spot areas for innovation.

**How the project was built**
Data cleaning (Python) -> 15 exploratory analyses (EDA) -> 10 business questions answered with SQL (MySQL)
-> interactive Power BI report -> this Streamlit dashboard.

**Data:** ICRISAT district-level data. Area is in 1000 hectares, production in 1000 tons and yield in kg per
hectare. The data ends in 2017, so "latest year" means the last year of the selected range.

The year range at the top applies to every page. The state filter applies to All Crops and Crop Explorer.
        """
    )
    with st.expander("Preview the reshaped data"):
        st.dataframe(filtered.head(500), width="stretch")


# ----------------------------------------------------------------------------- cached runners
@st.cache_data(show_spinner=False)
def year_slice(y0: int, y1: int) -> pd.DataFrame:
    w = load_wide()
    return w[w["YEAR"].between(y0, y1)]


@st.cache_data(show_spinner=False)
def run_eda(i: int, y0: int, y1: int) -> list:
    return eda_figs(year_slice(y0, y1), i)


@st.cache_data(show_spinner=False)
def run_sql(i: int, y0: int, y1: int) -> dict:
    return sql_results(year_slice(y0, y1), i)


def clean_title(t: str) -> str:
    return re.sub(r"^(\d+)\.\s*", r"Q\1. ", t)


# ----------------------------------------------------------------------------- global layout + filters
data = load_data()
y_min, y_max = int(data["YEAR"].min()), int(data["YEAR"].max())

st.markdown(
    """
    <style>
    .st-key-yearbar {
        position: sticky; top: 3.5rem; z-index: 999;
        background: #faf6e6; color: #1f2d1f;
        padding: 0.5rem 1.25rem 0.1rem 1.25rem;
        border: 1px solid #d9d2b6; border-radius: 0.6rem;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.15);
    }
    [data-testid="stSidebar"] {
    min-width: 240px !important;
    max-width: 240px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

pg = st.navigation(
    [
        st.Page(page_all_crops, title="All Crops", icon="📊", url_path="all-crops", default=True),
        st.Page(page_crop_explorer, title="Crop Explorer", icon="🌱", url_path="crop-explorer"),
        st.Page(page_eda, title="EDA", icon="🔎", url_path="eda"),
        st.Page(page_sql, title="SQL Questions", icon="🧮", url_path="sql"),
        st.Page(page_about, title="About", icon="ℹ️", url_path="about"),
    ],
    position="sidebar",
)

st.title("🌾 AgriData Explorer")
with st.container(key="yearbar"):
    year_from, year_to = st.slider("📅 Year range (applies to every page)", y_min, y_max, (y_min, y_max),
                                   key="year_range")

chosen_states = st.sidebar.multiselect("State(s)", sorted(data["STATE_NAME"].unique()),
                                       placeholder="All states", key="state_filter")
st.sidebar.caption("The state filter applies to All Crops and Crop Explorer. The year range applies everywhere.")
st.sidebar.caption("Source: ICRISAT district-level data, 20 states, 1966-2017.")

scope = data if not chosen_states else data[data["STATE_NAME"].isin(chosen_states)]
filtered = scope[scope["YEAR"].between(year_from, year_to)]

pg.run()
