import streamlit as st
import altair as alt
import pandas as pd
from collections import namedtuple
import datetime
from pyarrow import dataset as ds

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

@st.cache_data(ttl = 24*60*60)
def calculateDurations(outputEST):
    durTable = outputEST.loc[outputEST.variable == 'DURATION', :].copy()
    # Original lookup dictionary
    lookup = {
        7: "07-Day",
        50: "05-Day",
        57: "07-Day, 05-Day",
        300: "03-Day",
        307: "07-Day, 03-Day",
        350: "05-Day, 03-Day",
        357: "07-Day, 05-Day, 03-Day",
        2000: "02-Day",
        2007: "07-Day, 02-Day",
        2050: "05-Day, 02-Day",
        2057: "07-Day, 05-Day, 02-Day",
        2300: "03-Day, 02-Day",
        2307: "07-Day, 03-Day, 02-Day",
        2350: "05-Day, 03-Day, 02-Day",
        2357: "07-Day, 05-Day, 03-Day, 02-Day",
        10000: "01-Day",
        10007: "07-Day, 01-Day",
        10050: "05-Day, 01-Day",
        10057: "07-Day, 05-Day, 01-Day",
        10300: "03-Day, 01-Day",
        10307: "07-Day, 03-Day, 01-Day",
        10350: "05-Day, 03-Day, 01-Day",
        10357: "07-Day, 05-Day, 03-Day, 01-Day",
        12000: "02-Day, 01-Day",
        12007: "07-Day, 02-Day, 01-Day",
        12050: "05-Day, 02-Day, 01-Day",
        12057: "07-Day, 05-Day, 02-Day, 01-Day",
        12300: "03-Day, 02-Day, 01-Day",
        12307: "07-Day, 03-Day, 02-Day, 01-Day",
        12350: "05-Day, 03-Day, 02-Day, 01-Day",
        12357: "07-Day, 05-Day, 03-Day, 02-Day, 01-Day",
    }

    # Map the 'value' column to the 'durations' column using the combined lookup dictionary
    durTable['durations'] = durTable.loc[:,'value'].map(lambda x: lookup.get(x, '').split(', '))

    # Drop rows with NaN values in the 'durations' column
    durTable = durTable.loc[durTable.value>0, :]

    # Explode the 'durations' column to repeat each row for each element in the list
    durTable = durTable.explode('durations')

    # Reset the index if needed
    durTable = durTable.reset_index(drop=True)
    durTable.loc[:,'value'] = pd.to_numeric(durTable.durations.str.split('-', expand=True)[0])

    # Assuming durTable is your DataFrame and 'durations' is the column with the duration labels
    output = pd.DataFrame()

    for duration, sub_group in durTable.groupby('durations'):
        # Create a date range with 6-hour frequency
        idx = pd.date_range(sub_group.date.min(), sub_group.date.max(), freq="6h")

        # Drop unnecessary columns and reindex with the new date range
        sub_group = sub_group.drop(['durations', 'variable'], axis=1)
        sub_group = sub_group.set_index('date').reindex(idx, fill_value=-99, tolerance='1h', method='nearest')
        sub_group.index.name = 'date'
        sub_group = sub_group.reset_index()

        # Set value to 1 where it is not -99, otherwise set to 0
        sub_group['value'] = sub_group['value'].apply(lambda x: 1 if x != -99 else 0)

        # Create a group identifier for consecutive values
        sub_group['val_grp'] = (sub_group['value'].astype(bool)).astype(int)
        sub_group['val_grp'] = (sub_group['val_grp'].diff(1) != 0).astype('int').cumsum()
        sub_group = sub_group[sub_group['value'] != 0]

        # Create a DataFrame with the results
        res = sub_group.groupby('val_grp').agg(
            BeginDate=('date', 'first'),
            EndDate=('date', 'last'),
            Consecutive=('date', 'size')
        ).reset_index(drop=True)
        res['duration'] = duration

        # Concatenate the results to the output DataFrame
        output = pd.concat([output, res], ignore_index=True)
    return output

reservoirNamesLookup = {
    "ORO": "Oroville",
    "NBB": "New Bullards Bar"
}

flowRangeLookup = {
    "ORO": (0,350000),
    "NBB": (0, 200000)
}

elevRangeLookup = {
    "ORO": (800, 930),
    "NBB": (1870, 1970)
}

scaleFactorLookup = {
    '1986':[100,102,104,106,108,110,112,114,116,118,120,130,140,150],
    '1997':[84,86,88,90,92,94,96,98,100,102,104,106,108,110,120,130]
}

# Define the options for the dropdowns
pattern_year_options = [1986, 1997]
alternative_est_options = [3]
pct_options = list(range(5, 100, 5))
arcSpillwayConfiguation_options = ["With", "Without"]
datasets_options = ['HDR_proposals','FVA_onfig']

# Create the sidebar dropdowns
with st.sidebar:
    dataset = st.selectbox("Select Dataset", datasets_options, index=datasets_options.index('HDR_proposals'))
    patternYear = st.selectbox("Select Pattern Year", pattern_year_options, index=pattern_year_options.index(1986))
    alternativeEST = st.selectbox("Select Alternative EST", alternative_est_options, index=alternative_est_options.index(3))
    scale_factor_options = scaleFactorLookup[str(patternYear)]
    scaleFactor = st.selectbox("Select Scale Factor", scale_factor_options, index=scale_factor_options.index(120))
    pct = st.selectbox("Select Percentage", pct_options, index=pct_options.index(75))
    arc_spillway_config = st.selectbox("Select Arc Spillway Config Perfect", arcSpillwayConfiguation_options)

    # Display the selected values
    st.write("Selected Dataset:", dataset)
    st.write("Selected Pattern Year:", patternYear)
    st.write("Selected Alternative EST:", alternativeEST)
    st.write("Selected Scale Factor:", scaleFactor)
    st.write("Selected Percentage:", pct)
    st.write("Selected Arc Spillway Configuration:", arc_spillway_config)

# Determine the Arc Spillway Config values
if arc_spillway_config == "With":
    arcSpillwayConfigPerfect = "A"
    arcSpillwayConfigEST = "S"
elif arc_spillway_config == "Without":
    arcSpillwayConfigPerfect = "E"
    arcSpillwayConfigEST = "P"

ReservoirZones = namedtuple("ReservoirZones", ["flood_control", "top_conservation", "surcharge", "top_of_dam"])
oroZones = ReservoirZones(900.03, 848.50, 916.20, 922)
nbbZones = ReservoirZones(1956, 1918.32,1962.5,1965)

zoneLookup = {
    "ORO": oroZones,
    "NBB": nbbZones
}

estFeatherFile = f"data/{patternYear}_{scaleFactor}_{arc_spillway_config}_{dataset}_Alt3.feather"
baselineFeatherFile = f'data/{patternYear}_{scaleFactor}_{arc_spillway_config}_baseline.feather'

estDf = ds.dataset(estFeatherFile, format = 'feather')
baselineDf = ds.dataset(baselineFeatherFile, format = 'feather')

graphics = {}
for reservoirName in ["ORO","NBB"]:
    zones = zoneLookup[reservoirName]
    elevRange = elevRangeLookup[reservoirName]
    flowRange = flowRangeLookup[reservoirName]

    outputEST = estDf.to_table(filter = (
            (ds.field('Reservoir') == reservoirName) & 
            (ds.field('pct') == pct)
    )).to_pandas()
    

    outputEST.loc[((outputEST.variable == 'POOL-ELEV','alternative'))] = "ID3-IMPERFECT"
    outputEST.loc[((outputEST.variable == 'FIRO-TARGET','alternative'))] = "FIRO-TARGET"
    outputEST.loc[((outputEST.variable == f'{reservoirName}-OUT')),'alternative'] = f'{reservoirName}-OUT'
    outputEST.loc[((outputEST.variable == f'{reservoirName}-IN')),'alternative'] = f'{reservoirName}-IN'

    outputPerfectZero = baselineDf.to_table(filter = (
        (ds.field('reservoirName') == reservoirName) &
        (ds.field('alternative') == "ID0")
    )).to_pandas()
    
    outputPerfectOne = baselineDf.to_table(filter = (
        (ds.field('reservoirName') == reservoirName) &
        (ds.field('alternative') == "ID1")
    )).to_pandas()

    outputPerfectThree = baselineDf.to_table(filter = (
        (ds.field('reservoirName') == reservoirName) &
        (ds.field('alternative') == "ID3-PERFECT")
    )).to_pandas()

    # Create a list of dataframes containing the desired variables
    dataframes = [
        outputEST.loc[outputEST["variable"] == "POOL-ELEV", :],
        outputEST.loc[outputEST["variable"] == "FIRO-TARGET", :],
        outputPerfectZero.loc[outputPerfectZero["variable"] == "POOL-ELEV", :],
        outputPerfectOne.loc[outputPerfectOne["variable"] == "POOL-ELEV", :],
        outputPerfectThree.loc[outputPerfectThree["variable"] == "POOL-ELEV", :],
    ]

    # Concatenate the dataframes into a single dataframe
    elevDf = pd.concat(dataframes)

    dataframes = [
        outputEST.loc[outputEST["variable"] == f'{reservoirName}-OUT', :],
        outputEST.loc[outputEST["variable"] == f'{reservoirName}-IN', :],
        outputPerfectZero.loc[outputPerfectZero["variable"] == f'{reservoirName}-OUT', :],
        outputPerfectOne.loc[outputPerfectOne["variable"] == f'{reservoirName}-OUT', :],
        outputPerfectThree.loc[outputPerfectThree["variable"] == f'{reservoirName}-OUT', :],
    ]

    defaultwidth = 400

    flowDf = pd.concat(dataframes)

    nearest = alt.selection_point(nearest=True, on="pointerover",
    fields=["date"], empty=False)

    when_near = alt.when(nearest)



    flowMaryDf = outputEST.loc[outputEST["variable"] == "MARYSVILLE", :]
    maryThreshold = 180000
    flowMary = alt.Chart(flowMaryDf).mark_line().encode(
            x=alt.X('date:T', title=None).axis(format='%Y-%m-%d'
                ).scale(
                    domain=[flowMaryDf.date.min().strftime('%Y-%m-%d %H:%M'), 
                    flowMaryDf.date.max().strftime('%Y-%m-%d %H:%M')]),
        y=alt.Y('value:Q', title='Flow (cfs)').scale(domain=(0,300000)),

    )

    rulesMary = alt.Chart(flowMaryDf
    ).mark_rule(color="gray").encode(
        x="date:T",
        opacity=when_near.then(alt.value(0.3)).otherwise(alt.value(0)),
        tooltip = [
            alt.Tooltip('value:Q', type='quantitative', format='.0f', title = 'FLOW'),
            alt.Tooltip('date:T', type='temporal', format='%Y-%m-%d %H:%M')
        ]
    ).add_params(nearest)

    highlightMary = flowMary.mark_line(color='red').encode(
        y2=alt.Y2(datum=maryThreshold)
    ).transform_filter(
        alt.datum.value > maryThreshold
    )

    maryFlow = (flowMary + highlightMary + rulesMary).properties( title = "Marysville")#width=defaultwidth,  height=100,

    flowYubaCityDf = outputEST.loc[outputEST["variable"] == "YUBA CITY", :]
    yubaThreshold = 180000
    flowYubaCity = alt.Chart(flowYubaCityDf).mark_line().encode(
            x=alt.X('date:T', title=None).axis(format='%Y-%m-%d'
                ).scale(
                    domain=[flowYubaCityDf.date.min().strftime('%Y-%m-%d %H:%M'), 
                    flowYubaCityDf.date.max().strftime('%Y-%m-%d %H:%M')]),
        y=alt.Y('value:Q', title='Flow (cfs)').scale(domain=(0,300000)),
                tooltip = [alt.Tooltip('value:Q', type='quantitative', format='.0f'),
            alt.Tooltip('date:T', type='temporal', format='%Y-%m-%d %H:%M')]
    )

    highlightYubaCity = flowYubaCity.mark_line(color='red').encode(
        y2=alt.Y2(datum=yubaThreshold)
    ).transform_filter(
        alt.datum.value > yubaThreshold
    )

    rulesYuba = alt.Chart(flowYubaCityDf
    ).mark_rule(color="gray").encode(
        x="date:T",
        opacity=when_near.then(alt.value(0.3)).otherwise(alt.value(0)),
        tooltip = [
            alt.Tooltip('value:Q', type='quantitative', format='.0f', title = 'FLOW'),
            alt.Tooltip('date:T', type='temporal', format='%Y-%m-%d %H:%M')
        ]
    ).add_params(nearest)

    yubaFlow = (flowYubaCity + highlightYubaCity+ rulesYuba).properties(  title = "Yuba City")#width=defaultwidth, height=100,

    flowNicolausDf = outputEST.loc[outputEST["variable"] == "NICOLAUS", :]
    nicolausThreshold = 320000
    flowNicolaus = alt.Chart(flowNicolausDf).mark_line().encode(
            x=alt.X('date:T', title=None).axis(format='%Y-%m-%d'
                ).scale(
                    domain=[flowNicolausDf.date.min().strftime('%Y-%m-%d %H:%M'), 
                    flowNicolausDf.date.max().strftime('%Y-%m-%d %H:%M')]),
        y=alt.Y('value:Q', title='Flow (cfs)').scale(domain=(0,400000)),
                tooltip = [alt.Tooltip('value:Q', type='quantitative', format='.0f'),
            alt.Tooltip('date:T', type='temporal', format='%Y-%m-%d %H:%M')]
    )

    highlightNicolaus = flowNicolaus.mark_line(color='red').encode(
        y2=alt.Y2(datum=nicolausThreshold)
    ).transform_filter(
        alt.datum.value > nicolausThreshold
    )
    rulesNicholas = alt.Chart(flowNicolausDf
    ).mark_rule(color="gray").encode(
        x="date:T",
        opacity=when_near.then(alt.value(0.3)).otherwise(alt.value(0)),
        tooltip = [
            alt.Tooltip('value:Q', type='quantitative', format='.0f', title = 'FLOW'),
            alt.Tooltip('date:T', type='temporal', format='%Y-%m-%d %H:%M')
        ]
    ).add_params(nearest)

    nicolausFlow = (flowNicolaus + highlightNicolaus + rulesNicholas).properties(  title = "Nicolaus")#width=defaultwidth, height=100,

    flowConfluenceDf = outputEST.loc[outputEST["variable"] == "CONFLUENCE", :]
    confluenceThreshold = 300000

    flowConfluence = alt.Chart(flowConfluenceDf).mark_line().encode(
            x=alt.X('date:T', title=None).axis(format='%Y-%m-%d'
                ).scale(
                    domain=[flowConfluenceDf.date.min().strftime('%Y-%m-%d %H:%M'), 
                    flowConfluenceDf.date.max().strftime('%Y-%m-%d %H:%M')]),
        y=alt.Y('value:Q', title='Flow (cfs)').scale(domain=(0,400000)),
        tooltip = [alt.Tooltip('value:Q', type='quantitative', format='.0f', title = 'FLOW'),
            alt.Tooltip('date:T', type='temporal', format='%Y-%m-%d %H:%M')]
    )

    highlightConfluence = flowConfluence.mark_line(color='red').encode(
        y2=alt.Y2(datum=confluenceThreshold)
    ).transform_filter(
        alt.datum.value > confluenceThreshold
    )

    rulesConfluence = alt.Chart(flowConfluenceDf
    ).mark_rule(color="gray").encode(
        x="date:T",
        opacity=when_near.then(alt.value(0.3)).otherwise(alt.value(0)),
        tooltip = [
            alt.Tooltip('value:Q', type='quantitative', format='.0f', title = 'FLOW'),
            alt.Tooltip('date:T', type='temporal', format='%Y-%m-%d %H:%M')
        ]
    ).add_params(nearest)

    confluenceFlow = (flowConfluence + highlightConfluence + rulesConfluence).properties( title = "Confluence")#width = defaultwidth, height=100,

    poolPlot = alt.Chart(elevDf).mark_line().encode(
        x=alt.X('date:T', title=None).axis(format='%Y-%m-%d'
            ).scale(
                domain=[outputEST.date.min().strftime('%Y-%m-%d %H:%M'), 
                outputEST.date.max().strftime('%Y-%m-%d %H:%M')]).axis(
                    labels=True),
    y=alt.Y('value:Q', title='Elevation (ft)').scale(domain=elevRange),
    color=alt.Color('alternative:N', title=None, scale=alt.Scale(
        domain=['ID3-IMPERFECT','FIRO-TARGET','ID0', 'ID1','ID3-PERFECT'], 
        range=['#d7191c', '#000000','#fdae61', '#abd9e9','#2c7bb6'])),
    strokeDash=alt.StrokeDash('alternative:N', title=None, scale=alt.Scale(
        domain=['ID3-IMPERFECT','FIRO-TARGET','ID0', 'ID1','ID3-PERFECT'], 
        range=[[1,0],[4,4],[1,0],[1,0],[1,0]])),
    tooltip=[
            alt.Tooltip(c, type="quantitative", format=".2f") for c in ['ID3-IMPERFECT','FIRO-TARGET','ID0', 'ID1','ID3-PERFECT']
            ] + [alt.Tooltip('date:T', type = 'temporal', format = '%Y-%m-%d %H:%M')]
    ).properties(title = reservoirNamesLookup[reservoirName] )# width=defaultwidth, height=200
                 
    allZones = create_zone_rules(outputEST.date.min().strftime('%Y-%m-%d %H:%M'), outputEST.date.max().strftime('%Y-%m-%d %H:%M'), zones, elevRange)

    estElevPlot = (poolPlot + allZones)

    nearest = alt.selection_point(nearest=True, on="pointerover",
        fields=["date"], empty=False)

    when_near = alt.when(nearest)

    rulesElev = alt.Chart(elevDf).transform_pivot(
        "alternative",
        value="value",
        groupby=["date"]
    ).mark_rule(color="gray").encode(
        x="date:T",
        opacity=when_near.then(alt.value(0.3)).otherwise(alt.value(0)),
        tooltip=[
            alt.Tooltip(c, type="quantitative", format=".2f") for c in ['ID3-IMPERFECT','FIRO-TARGET','ID0', 'ID1','ID3-PERFECT']
            ] + [alt.Tooltip('date:T', type = 'temporal', format = '%Y-%m-%d %H:%M')],
    ).add_params(nearest)


    estElevPlot = (poolPlot +  allZones + rulesElev).resolve_scale(color='shared')


    durationdf = calculateDurations(outputEST)
    durationPlot = alt.Chart(durationdf).mark_bar(height=5).encode(
        x = alt.X('BeginDate:T', title=None).scale(domain = [outputEST.date.min().strftime('%Y-%m-%d %H:%M'),
                    outputEST.date.max().strftime('%Y-%m-%d %H:%M')]).axis(
                    labels=True
                    ),
        x2 = 'EndDate:T',
        y = alt.Y('duration:N', title='Duration'),
    ).properties(title= reservoirNamesLookup[reservoirName] )#width=defaultwidth, height=100

    nearest = alt.selection_point(nearest=True, on="pointerover",
        fields=["date"], empty=False)

    when_near = alt.when(nearest)

    rules = alt.Chart(flowDf).transform_pivot(
        "alternative",
        value="value",
        groupby=["date"]
    ).mark_rule(color="gray").encode(
        x="date:T",
        opacity=when_near.then(alt.value(0.3)).otherwise(alt.value(0)),
        tooltip=[
            alt.Tooltip(c, type="quantitative", format=".0f") 
                for c in [f'{reservoirName}-OUT', f'{reservoirName}-IN', 'ID0', 'ID1', 'ID3-PERFECT']
            ] + [alt.Tooltip('date:T', type = 'temporal', format = '%Y-%m-%d %H:%M')], # Add date tooltip
    ).add_params(nearest)


    flowPlot = alt.Chart(flowDf).mark_line().encode(
            x=alt.X('date:T', title=None).axis(format='%Y-%m-%d'
                ).scale(
                    domain=[flowDf.date.min().strftime('%Y-%m-%d %H:%M'), 
                    flowDf.date.max().strftime('%Y-%m-%d %H:%M')]),
        y=alt.Y('value:Q', title='Flow (cfs)').scale(domain=flowRange),
        color=alt.Color('alternative:N', title=None, scale=alt.Scale(
            domain=[f'{reservoirName}-OUT', f'{reservoirName}-IN', 'ID0', 'ID1', 'ID3-PERFECT'], 
            range=['#d7191c', '#000000','#fdae61', '#abd9e9','#2c7bb6'])),
        strokeDash=alt.StrokeDash('alternative:N', title=None, scale=alt.Scale(
            domain=[f'{reservoirName}-OUT', f'{reservoirName}-IN', 'ID0', 'ID1', 'ID3-PERFECT'], 
            range=[[1,1],[4,4],[1,0],[1,0],[1,0]]))
    ).properties(title = reservoirNamesLookup[reservoirName] )#width=defaultwidth)

    flowPlot = flowPlot + rules

    graphics[reservoirName] = {}
    graphics[reservoirName]['elev'] = estElevPlot
    graphics[reservoirName]['flow'] = flowPlot
    graphics[reservoirName]['duration'] = durationPlot

    if reservoirName == "ORO":
        graphics['mary'] = maryFlow
        graphics['yuba'] = yubaFlow
        graphics['nicolaus'] = nicolausFlow
        graphics['confluence'] = confluenceFlow


    # if reservoirName == "ORO":
    #     operationPlot = alt.vconcat(estElevPlot.properties(height=200).interactive(), durationPlot, flowPlot.properties(height=200), yubaFlow.properties(height=100), confluenceFlow.properties(height=150)).resolve_scale(
    #             x='shared', color='independent', strokeDash='independent')
    # else:
    #     operationPlot = alt.vconcat(estElevPlot.properties(height=200), durationPlot, flowPlot.properties(height=200), maryFlow.properties(height=100), nicolausFlow.properties(height=150)).resolve_scale(
    #             x='shared', color='independent', strokeDash='independent')
    # graphics[reservoirName] = operationPlot


leftPlot = alt.vconcat(
    graphics["ORO"]['elev'].properties(height=150).interactive(),
    graphics["NBB"]['elev'].properties(height=150).interactive(),
    graphics["ORO"]['duration'].properties(height=75),
    graphics["NBB"]['duration'].properties(height=75),
).resolve_scale(
    x='shared', color='independent', strokeDash='independent'
)

rightPlot = alt.vconcat(
    graphics["ORO"]['flow'].properties(height=150).interactive(),
    graphics["NBB"]['flow'].properties(height=150).interactive(),
    graphics['yuba'].properties(height=75),
    graphics['mary'].properties(height=75),
    graphics['confluence'].properties(height=75),
    graphics['nicolaus'].properties(height=75),   
).resolve_scale(
    x='shared', color='independent', strokeDash='independent'
)



st.set_page_config(layout="wide", page_title="EST Simulation Plots")

# st.altair_chart(merge_plot)
# # Create two columns
col1, col2 = st.columns(2, border=True)

# Display the charts in the columns
with col1:
    st.altair_chart(leftPlot,use_container_width=True)

with col2:
    st.altair_chart(rightPlot, use_container_width=True)


