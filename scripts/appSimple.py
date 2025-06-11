import streamlit as st
import altair as alt
from pydsstools.heclib.dss import HecDss
import pandas as pd
from collections import namedtuple
print(alt.__version__)

st.set_page_config(layout="wide")
def getDssData(dssFile, path, variable, window):

    with HecDss.Open(dssFile) as fid:
        ts = fid.read_ts(path, window=window )
        values = ts.values.copy()
        times = ts.pytimes
        df = pd.DataFrame(index = pd.DatetimeIndex(times), data = {variable: values})
    return df

def create_zone_rules(minDate, maxDate, zones, elevRange):
    
    def create_zone_df(label, value, minDate, maxDate):
        return pd.DataFrame({
            "date": [minDate, maxDate],
            "value": [value, value],
            "label": [label, label]
        })


    tmpFC = create_zone_df("Flood Control", zones.flood_control, minDate, maxDate)
    tmpTC = create_zone_df("Top of Conservation", zones.top_conservation, minDate, maxDate)
    tmpS = create_zone_df("Surcharge", zones.surcharge, minDate, maxDate)
    tmpTD = create_zone_df("Top of Dam", zones.top_of_dam, minDate, maxDate)

    baseFC = alt.Chart(tmpFC).mark_line(color='black').encode(
    x="date:T",
    y=alt.Y("value:Q").scale(domain=elevRange)
    )

    textFC = baseFC.mark_text(align="left", dx=5, dy=-5).encode(
    text="label:N",
    x=alt.X('date:T', aggregate='min'),
    y=alt.Y('value:Q', aggregate={'argmin': 'date'}).scale(domain=elevRange),
    )

    baseTC = alt.Chart(tmpTC).mark_line(color='black').encode(
    x="date:T",
    y=alt.Y("value:Q").scale(domain=elevRange)
    )

    textTC = baseTC.mark_text(align="left", dx=5, dy=-5).encode(
    text="label:N",
    x=alt.X('date:T', aggregate='min'),
    y=alt.Y('value:Q', aggregate={'argmin': 'date'}).scale(domain=elevRange),
    )

    baseS = alt.Chart(tmpS).mark_line(color='black').encode(
    x="date:T",
    y=alt.Y("value:Q").scale(domain=elevRange)
    )

    textS = baseS.mark_text(align="left", dx=5, dy=-5).encode(
    text="label:N",
    x=alt.X('date:T', aggregate='min'),
    y=alt.Y('value:Q', aggregate={'argmin': 'date'}).scale(domain=elevRange),
    )

    baseTD = alt.Chart(tmpTD).mark_line(color='black').encode(
    x="date:T",
    y=alt.Y("value:Q").scale(domain=elevRange)
    )

    textTD = baseTD.mark_text(align="left", dx=5, dy=-5).encode(
    text="label:N",
    x=alt.X('date:T', aggregate='min'),
    y=alt.Y('value:Q', aggregate={'argmin': 'date'}).scale(domain=elevRange),
    )

    allZones = baseFC + textFC + baseTC + textTC + baseS + textS + baseTD + textTD
        
    return allZones

def process_paths(dss_file, paths, window):
    output_df = pd.DataFrame()
    for variable, path in paths.items():
        df = getDssData(dss_file, path, variable, window)
        output_df = pd.concat([output_df, df], axis=1)
    output_df = output_df.stack().reset_index()
    output_df.columns = ['date', 'variable', 'value']
    return output_df

def getDssData(dssFile, path, variable, window):

    with HecDss.Open(dssFile) as fid:
        ts = fid.read_ts(path, window=window )
        values = ts.values.copy()
        times = ts.pytimes
        df = pd.DataFrame(index = pd.DatetimeIndex(times), data = {variable: values})
    return df


flowRangeLookup = {
    "ORO": (0,350000),
    "NBB": (0, 200000)
}

elevRangeLookup = {
    "ORO": (800, 930),
    "NBB": (1870, 1970)
}

windowLookup = {
    '1997':['18 Dec 1996 1200', '09 Jan 1997 1200'],
    '1986':['04 Feb 1986 1200', '26 Feb 1986 1200'],
}

estDssFileLookup = {
    '1997': "SS-1997_results.dss",
    '1986': "SS-1986_results.dss"
}

scaleFactorLookup = {
    '1986':[100,102,104,106,108,110,112,114,116,118,120,130,140,150],
    '1997':[84,86,88,90,92,94,96,98,100,102,104,106,108,110,120,130]
}

# Define the options for the dropdowns

# Define the options for the dropdowns
pattern_year_options = [1986, 1997]
alternative_est_options = [3]
pct_options = list(range(5, 100, 5))
arcSpillwayConfiguation_options = ["With", "Without"]

# Create the sidebar dropdowns
with st.sidebar:
    patternYear = st.selectbox("Select Pattern Year", pattern_year_options, index=pattern_year_options.index(1986))
    alternativeEST = st.selectbox("Select Alternative EST", alternative_est_options, index=alternative_est_options.index(3))
    scale_factor_options = scaleFactorLookup[str(patternYear)]
    pct = st.selectbox("Select Percentage", pct_options, index=pct_options.index(75))
    arc_spillway_config = st.selectbox("Select Arc Spillway Config Perfect", arcSpillwayConfiguation_options)

    # Display the selected values
    st.write("Selected Pattern Year:", patternYear)
    st.write("Selected Alternative EST:", alternativeEST)
    st.write("Selected Percentage:", pct)
    st.write("Selected Arc Spillway Configuration:", arc_spillway_config)

# Determine the Arc Spillway Config values
if arc_spillway_config == "With":
    arcSpillwayConfigPerfect = "A"
    arcSpillwayConfigEST = "S"
elif arc_spillway_config == "Without":
    arcSpillwayConfigPerfect = "E"
    arcSpillwayConfigEST = "P"




scaleFactor = st.select_slider("Select Scale Factor", options=scaleFactorLookup[str(patternYear)], value=120)
imagePath = f"output/{patternYear}_{scaleFactor:03d}_{arc_spillway_config}ARC_{pct:02d}NEP.png"

st.image(imagePath, width=1400)




