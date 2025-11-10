import altair as alt
import pandas as pd
from collections import namedtuple
from pyarrow import dataset as ds
import os
alt.renderers.enable('browser')

def getESTData(estDf, reservoirName, pct):

    outputEST = estDf.to_table(filter = (
            (ds.field('Reservoir') == reservoirName) & 
            (ds.field('pct') == pct)
    )).to_pandas()
    

    outputEST.loc[outputEST.variable == 'POOL-ELEV', 'alternative'] = "ID3-IMPERFECT"
    outputEST.loc[outputEST.variable == 'FIRO-TARGET', 'alternative'] = "FIRO-TARGET"
    outputEST.loc[outputEST.variable == f'{reservoirName}-OUT', 'alternative'] = f'{reservoirName}-OUT'
    outputEST.loc[outputEST.variable == f'{reservoirName}-IN', 'alternative'] = f'{reservoirName}-IN'

    return outputEST

def getBaselineData(baselineDf, reservoirName):
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

    return outputPerfectZero, outputPerfectOne, outputPerfectThree 

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
datasets_options = ['HDR_proposals','FVA_config']

# BASELINE Flag - Set to True to include ID0 and ID1 in all plots, False to exclude them
BASELINE = False

scaleFactors = [84,86,88,90,92,94,96,98,100,102,104,106,108,110,120,130]

for scaleFactor in scaleFactors:

    datasetNew = 'NBB_Release_1986_Edits'
    datasetOld = 'ORO_Release_v2'
    patternYear = '1997'
    alternativeEST = 3

    pct = 75
    arc_spillway_config = 'With'



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

    estFeatherFile = f"data/{patternYear}_{scaleFactor}_{arc_spillway_config}_{datasetOld}_Alt3.feather"
    newEstFeatherFile = f"data/{patternYear}_{scaleFactor}_{arc_spillway_config}_{datasetNew}_Alt3.feather"
    baselineFeatherFile = f'data/{patternYear}_{scaleFactor}_{arc_spillway_config}_baseline.feather'

    estDf = ds.dataset(estFeatherFile, format = 'feather')
    estDfNew = ds.dataset(newEstFeatherFile, format = 'feather')
    baselineDf = ds.dataset(baselineFeatherFile, format = 'feather')

    graphics = {}

    nearestLeft = alt.selection_point(nearest=True, on="pointerover",
        fields=["date"], empty=False)

    when_near_left = alt.when(nearestLeft)

    nearestRight = alt.selection_point(nearest=True, on="pointerover",
        fields=["date"], empty=False)

    when_near_right = alt.when(nearestRight)

    for reservoirName in ["ORO","NBB"]:
        zones = zoneLookup[reservoirName]
        elevRange = elevRangeLookup[reservoirName]
        flowRange = flowRangeLookup[reservoirName]


        outputEST = getESTData(estDf, reservoirName, pct)

        outputEstNew = getESTData(estDfNew, reservoirName, pct)


        outputPerfectZero, outputPerfectOne, outputPerfectThree = getBaselineData(baselineDf, reservoirName)

        # Create a list of dataframes containing the desired variables
        dataframes = [
            outputEST.loc[outputEST["variable"] == "POOL-ELEV", :],
            outputEST.loc[outputEST["variable"] == "FIRO-TARGET", :],
            outputPerfectThree.loc[outputPerfectThree["variable"] == "POOL-ELEV", :],
        ]
        
        # Conditionally add baseline data (ID0, ID1) based on BASELINE flag
        if BASELINE:
            dataframes.extend([
                outputPerfectZero.loc[outputPerfectZero["variable"] == "POOL-ELEV", :],
                outputPerfectOne.loc[outputPerfectOne["variable"] == "POOL-ELEV", :],
            ])

        # Concatenate the dataframes into a single dataframe
        elevDf = pd.concat(dataframes)

        if reservoirName == 'NBB':  
            
            outputEstNew.loc[outputEstNew["variable"] == "POOL-ELEV", 'alternative'] = "ID3-IMPERFECT-NEW"
            elevDf = pd.concat([elevDf, outputEstNew.loc[outputEstNew["variable"] == "POOL-ELEV", :]])
               

        dataframes = [
            outputEST.loc[outputEST["variable"] == f'{reservoirName}-OUT', :],
            outputEST.loc[outputEST["variable"] == f'{reservoirName}-IN', :],
            outputPerfectThree.loc[outputPerfectThree["variable"] == f'{reservoirName}-OUT', :],
        ]
        
        # Conditionally add baseline data (ID0, ID1) based on BASELINE flag
        if BASELINE:
            dataframes.extend([
                outputPerfectZero.loc[outputPerfectZero["variable"] == f'{reservoirName}-OUT', :],
                outputPerfectOne.loc[outputPerfectOne["variable"] == f'{reservoirName}-OUT', :],
            ])

        


        defaultwidth = 400

        flowDf = pd.concat(dataframes)

        dataframesNew = [
            outputEstNew.loc[outputEstNew["variable"] == f'{reservoirName}-OUT', :]
        ]

        flowDfNew = pd.concat(dataframesNew)

        # Update flow df to match variable column from elev df
        flowDf.loc[flowDf.alternative == f'{reservoirName}-OUT', 'alternative'] = 'ID3-IMPERFECT'
        flowDf.loc[flowDf.alternative == f'{reservoirName}-IN', 'alternative'] = 'INFLOW'

        if reservoirName == 'NBB':
            flowDfNew.loc[flowDfNew.alternative == f'{reservoirName}-OUT', 'alternative'] = 'ID3-IMPERFECT-NEW'

            flowDf = pd.concat([flowDf, flowDfNew])

            # Define domains and ranges based on BASELINE flag
            if BASELINE:
                flow_domain = ['ID3-IMPERFECT', 'ID3-IMPERFECT-NEW', 'INFLOW', 'ID0', 'ID1', 'ID3-PERFECT']
                flow_range = ['#d7191c', "#4ed50b", '#000000','#fdae61', '#abd9e9','#2c7bb6']
                flow_stroke_range = [[1, 0],[1,0],[1,0],[1,0],[1,0],[1,0]]
            else:
                flow_domain = ['ID3-IMPERFECT', 'ID3-IMPERFECT-NEW', 'INFLOW', 'ID3-PERFECT']
                flow_range = ['#d7191c', "#4ed50b", '#000000','#2c7bb6']
                flow_stroke_range = [[1, 0],[1,0],[1,0],[1,0]]

            flowPlot = alt.Chart(flowDf).mark_line().encode(
                x=alt.X('date:T', title=None).axis(format='%Y-%m-%d'
                    ).scale(
                        domain=[flowDf.date.min().strftime('%Y-%m-%d %H:%M'), 
                        flowDf.date.max().strftime('%Y-%m-%d %H:%M')]),
                y=alt.Y('value:Q', title='Flow (cfs)').scale(domain=(0, round(flowDf.value.max()*1.2,-4))),
                color=alt.Color('alternative:N', title=None, scale=alt.Scale(
                    domain=flow_domain, 
                    range=flow_range)),
                strokeDash=alt.StrokeDash('alternative:N', title=None, scale=alt.Scale(
                    domain=flow_domain, 
                    range=flow_stroke_range))
            ).properties(title = reservoirNamesLookup[reservoirName] )#width=defaultwidth)

            rules = alt.Chart(flowDf).transform_pivot(
                "alternative",
                value="value",
                groupby=["date"]
            ).mark_rule(color="gray").encode(
                x="date:T",
                opacity=when_near_right.then(alt.value(0.3)).otherwise(alt.value(0)),
                tooltip=[
                    alt.Tooltip(c, type="quantitative", format=",.0f") 
                        for c in flow_domain
                    ] + [alt.Tooltip('date:T', type = 'temporal', format = '%Y-%m-%d %H:%M')], # Add date tooltip
            ).add_params(nearestRight)

            flowPlot = (flowPlot + rules)
        else:
            # Define domains and ranges based on BASELINE flag
            if BASELINE:
                flow_domain = ['ID3-IMPERFECT', 'INFLOW', 'ID0', 'ID1', 'ID3-PERFECT']
                flow_range = ['#d7191c', '#000000','#fdae61', '#abd9e9','#2c7bb6']
                flow_stroke_range = [[1, 0],[1,0],[4,4],[1,0],[1,0]]
            else:
                flow_domain = ['ID3-IMPERFECT', 'INFLOW', 'ID3-PERFECT']
                flow_range = ['#d7191c', '#000000','#2c7bb6']
                flow_stroke_range = [[1, 0],[1,0],[1,0]]

            flowPlot = alt.Chart(flowDf).mark_line().encode(
                x=alt.X('date:T', title=None).axis(format='%Y-%m-%d'
                    ).scale(
                        domain=[flowDf.date.min().strftime('%Y-%m-%d %H:%M'), 
                        flowDf.date.max().strftime('%Y-%m-%d %H:%M')]),
                y=alt.Y('value:Q', title='Flow (cfs)').scale(domain=(0, round(flowDf.value.max()*1.2,-4))),
                color=alt.Color('alternative:N', title=None, scale=alt.Scale(
                    domain=flow_domain, 
                    range=flow_range)),
                strokeDash=alt.StrokeDash('alternative:N', title=None, scale=alt.Scale(
                    domain=flow_domain, 
                    range=flow_stroke_range))
            ).properties(title = reservoirNamesLookup[reservoirName] )#width=defaultwidth)

            rules = alt.Chart(flowDf).transform_pivot(
                "alternative",
                value="value",
                groupby=["date"]
            ).mark_rule(color="gray").encode(
                x="date:T",
                opacity=when_near_right.then(alt.value(0.3)).otherwise(alt.value(0)),
                tooltip=[
                    alt.Tooltip(c, type="quantitative", format=",.0f") 
                        for c in flow_domain
                    ] + [alt.Tooltip('date:T', type = 'temporal', format = '%Y-%m-%d %H:%M')], # Add date tooltip
            ).add_params(nearestRight)

            flowPlot = (flowPlot + rules)
        # Prepare Marysville data - combine old and new datasets
        flowMaryDf = outputEST.loc[outputEST["variable"] == "MARYSVILLE", :]
        flowMaryDf.loc[:, 'dataset'] = 'ID3-IMPERFECT'
        
        flowMaryDfNew = outputEstNew.loc[outputEstNew["variable"] == "MARYSVILLE", :]
        flowMaryDfNew.loc[:, 'dataset'] = 'ID3-IMPERFECT-NEW'
        
        # Combine old and new data for Marysville
        flowMaryDfCombined = pd.concat([flowMaryDf, flowMaryDfNew])
        
        maryThreshold = 180000
        flowMary = alt.Chart(flowMaryDfCombined).mark_line().encode(
                x=alt.X('date:T', title=None).axis(format='%Y-%m-%d'
                    ).scale(
                        domain=[flowMaryDfCombined.date.min().strftime('%Y-%m-%d %H:%M'), 
                        flowMaryDfCombined.date.max().strftime('%Y-%m-%d %H:%M')]),
            y=alt.Y('value:Q', title='Flow (cfs)').scale(domain=(0,round(flowMaryDfCombined.value.max()*1.2,-4))),
            color=alt.Color('dataset:N', title=None, scale=alt.Scale(
                domain=['ID3-IMPERFECT', 'ID3-IMPERFECT-NEW'], 
                range=['#d7191c', '#4ed50b'])),
            strokeDash=alt.StrokeDash('dataset:N', title=None, scale=alt.Scale(
                domain=['ID3-IMPERFECT', 'ID3-IMPERFECT-NEW'], 
                range=[[1, 0], [4, 4]]))
        )

        rulesMary = alt.Chart(flowMaryDfCombined).transform_pivot(
            "dataset",
            value="value",
            groupby=["date"]
        ).mark_rule(color="gray").encode(
            x="date:T",
            opacity=when_near_right.then(alt.value(0.3)).otherwise(alt.value(0)),
            tooltip=[
                alt.Tooltip('ID3-IMPERFECT:Q', type="quantitative", format=",.0f"),
                alt.Tooltip('ID3-IMPERFECT-NEW:Q', type="quantitative", format=",.0f")
            ] + [alt.Tooltip('date:T', type='temporal', format='%Y-%m-%d %H:%M')]
        ).add_params(nearestRight)

        highlightMary = flowMary.mark_line(color='red').encode(
            y2=alt.Y2(datum=maryThreshold)
        ).transform_filter(
            alt.datum.value > maryThreshold
        )

        maryFlow = (flowMary + highlightMary + rulesMary).properties( title = "Marysville")#width=defaultwidth,  height=100,

        # Prepare Yuba City data - combine old and new datasets
        flowYubaCityDf = outputEST.loc[outputEST["variable"] == "YUBA CITY", :]
        flowYubaCityDf.loc[:, 'dataset'] = 'ID3-IMPERFECT'
        
        flowYubaCityDfNew = outputEstNew.loc[outputEstNew["variable"] == "YUBA CITY", :]
        flowYubaCityDfNew.loc[:, 'dataset'] = 'ID3-IMPERFECT-NEW'
        
        # Combine old and new data for Yuba City
        flowYubaCityDfCombined = pd.concat([flowYubaCityDf, flowYubaCityDfNew])
        
        yubaThreshold = 180000
        flowYubaCity = alt.Chart(flowYubaCityDfCombined).mark_line().encode(
                x=alt.X('date:T', title=None).axis(format='%Y-%m-%d'
                    ).scale(
                        domain=[flowYubaCityDfCombined.date.min().strftime('%Y-%m-%d %H:%M'), 
                        flowYubaCityDfCombined.date.max().strftime('%Y-%m-%d %H:%M')]),
            y=alt.Y('value:Q', title='Flow (cfs)').scale(domain=(0,round(flowYubaCityDfCombined.value.max()*1.2,-4))),
            color=alt.Color('dataset:N', title=None, scale=alt.Scale(
                domain=['ID3-IMPERFECT', 'ID3-IMPERFECT-NEW'], 
                range=['#d7191c', '#4ed50b'])),
            strokeDash=alt.StrokeDash('dataset:N', title=None, scale=alt.Scale(
                domain=['ID3-IMPERFECT', 'ID3-IMPERFECT-NEW'], 
                range=[[1, 0], [4, 4]]))
        )

        highlightYubaCity = flowYubaCity.mark_line(color='red').encode(
            y2=alt.Y2(datum=yubaThreshold)
        ).transform_filter(
            alt.datum.value > yubaThreshold
        )

        rulesYuba = alt.Chart(flowYubaCityDfCombined).transform_pivot(
            "dataset",
            value="value",
            groupby=["date"]
        ).mark_rule(color="gray").encode(
            x="date:T",
            opacity=when_near_right.then(alt.value(0.3)).otherwise(alt.value(0)),
            tooltip=[
                alt.Tooltip('ID3-IMPERFECT:Q', type="quantitative", format=",.0f"),
                alt.Tooltip('ID3-IMPERFECT-NEW:Q', type="quantitative", format=",.0f")
            ] + [alt.Tooltip('date:T', type='temporal', format='%Y-%m-%d %H:%M')]
        ).add_params(nearestRight)

        yubaFlow = (flowYubaCity + highlightYubaCity+ rulesYuba).properties(  title = "Yuba City")#width=defaultwidth, height=100,

        # Prepare Nicolaus data - combine old and new datasets
        flowNicolausDf = outputEST.loc[outputEST["variable"] == "NICOLAUS", :]
        flowNicolausDf.loc[:, 'dataset'] = 'ID3-IMPERFECT'
        
        flowNicolausDfNew = outputEstNew.loc[outputEstNew["variable"] == "NICOLAUS", :]
        flowNicolausDfNew.loc[:, 'dataset'] = 'ID3-IMPERFECT-NEW'
        
        # Combine old and new data for Nicolaus
        flowNicolausDfCombined = pd.concat([flowNicolausDf, flowNicolausDfNew])
        
        nicolausThreshold = 320000
        flowNicolaus = alt.Chart(flowNicolausDfCombined).mark_line().encode(
                x=alt.X('date:T', title=None).axis(format='%Y-%m-%d'
                    ).scale(
                        domain=[flowNicolausDfCombined.date.min().strftime('%Y-%m-%d %H:%M'), 
                        flowNicolausDfCombined.date.max().strftime('%Y-%m-%d %H:%M')]),
            y=alt.Y('value:Q', title='Flow (cfs)').scale(domain=(0,round(flowNicolausDfCombined.value.max()*1.2,-4))),
            color=alt.Color('dataset:N', title=None, scale=alt.Scale(
                domain=['ID3-IMPERFECT', 'ID3-IMPERFECT-NEW'], 
                range=['#d7191c', '#4ed50b'])),
            strokeDash=alt.StrokeDash('dataset:N', title=None, scale=alt.Scale(
                domain=['ID3-IMPERFECT', 'ID3-IMPERFECT-NEW'], 
                range=[[1, 0], [4, 4]]))
        )

        highlightNicolaus = flowNicolaus.mark_line(color='red').encode(
            y2=alt.Y2(datum=nicolausThreshold)
        ).transform_filter(
            alt.datum.value > nicolausThreshold
        )
        rulesNicolaus = alt.Chart(flowNicolausDfCombined).transform_pivot(
            "dataset",
            value="value",
            groupby=["date"]
        ).mark_rule(color="gray").encode(
            x="date:T",
            opacity=when_near_right.then(alt.value(0.3)).otherwise(alt.value(0)),
            tooltip=[
                alt.Tooltip('ID3-IMPERFECT:Q', type="quantitative", format=",.0f"),
                alt.Tooltip('ID3-IMPERFECT-NEW:Q', type="quantitative", format=",.0f")
            ] + [alt.Tooltip('date:T', type='temporal', format='%Y-%m-%d %H:%M')]
        ).add_params(nearestRight)

        nicolausFlow = (flowNicolaus + highlightNicolaus + rulesNicolaus).properties(  title = "Nicolaus")#width=defaultwidth, height=100,

        # Prepare Confluence data - combine old and new datasets
        flowConfluenceDf = outputEST.loc[outputEST["variable"] == "CONFLUENCE", :]
        flowConfluenceDf.loc[:, 'dataset'] = 'ID3-IMPERFECT'
        
        flowConfluenceDfNew = outputEstNew.loc[outputEstNew["variable"] == "CONFLUENCE", :]
        flowConfluenceDfNew.loc[:, 'dataset'] = 'ID3-IMPERFECT-NEW'
        
        # Combine old and new data for Confluence
        flowConfluenceDfCombined = pd.concat([flowConfluenceDf, flowConfluenceDfNew])
        
        confluenceThreshold = 300000

        flowConfluence = alt.Chart(flowConfluenceDfCombined).mark_line().encode(
                x=alt.X('date:T', title=None).axis(format='%Y-%m-%d'
                    ).scale(
                        domain=[flowConfluenceDfCombined.date.min().strftime('%Y-%m-%d %H:%M'), 
                        flowConfluenceDfCombined.date.max().strftime('%Y-%m-%d %H:%M')]),
            y=alt.Y('value:Q', title='Flow (cfs)').scale(domain=(0,round(flowConfluenceDfCombined.value.max()*1.2,-4))),
            color=alt.Color('dataset:N', title=None, scale=alt.Scale(
                domain=['ID3-IMPERFECT', 'ID3-IMPERFECT-NEW'], 
                range=['#d7191c', '#4ed50b'])),
            strokeDash=alt.StrokeDash('dataset:N', title=None, scale=alt.Scale(
                domain=['ID3-IMPERFECT', 'ID3-IMPERFECT-NEW'], 
                range=[[1, 0], [4, 4]]))
        )

        highlightConfluence = flowConfluence.mark_line(color='red').encode(
            y2=alt.Y2(datum=confluenceThreshold)
        ).transform_filter(
            alt.datum.value > confluenceThreshold
        )

        rulesConfluence = alt.Chart(flowConfluenceDfCombined).transform_pivot(
            "dataset",
            value="value",
            groupby=["date"]
        ).mark_rule(color="gray").encode(
            x="date:T",
            opacity=when_near_right.then(alt.value(0.3)).otherwise(alt.value(0)),
            tooltip=[
                alt.Tooltip('ID3-IMPERFECT:Q', type="quantitative", format=",.0f"),
                alt.Tooltip('ID3-IMPERFECT-NEW:Q', type="quantitative", format=",.0f")
            ] + [alt.Tooltip('date:T', type='temporal', format='%Y-%m-%d %H:%M')]
        ).add_params(nearestRight)

        confluenceFlow = (flowConfluence + highlightConfluence + rulesConfluence).properties( title = "Confluence")#width = defaultwidth, height=100,

        if reservoirName == "NBB":
            # Define domains and ranges based on BASELINE flag
            if BASELINE:
                elev_domain = ['ID3-IMPERFECT','ID3-IMPERFECT-NEW', 'FIRO-TARGET', 'ID0', 'ID1', 'ID3-PERFECT']
                elev_range = ['#d7191c', '#4ed50b', '#000000', '#fdae61', '#abd9e9', '#2c7bb6']
                elev_stroke_range = [[1, 0],[1, 0], [4, 4], [1, 0], [1, 0], [1, 0]]
            else:
                elev_domain = ['ID3-IMPERFECT','ID3-IMPERFECT-NEW', 'FIRO-TARGET', 'ID3-PERFECT']
                elev_range = ['#d7191c', '#4ed50b', '#000000', '#2c7bb6']
                elev_stroke_range = [[1, 0],[1, 0], [4, 4], [1, 0]]

            poolPlot = alt.Chart(elevDf).mark_line().encode(
                x=alt.X(
                'date:T',
                title=None,
                axis=alt.Axis(format='%Y-%m-%d', labels=True)
                ).scale(
                domain=[
                    outputEST.date.min().strftime('%Y-%m-%d %H:%M'),
                    outputEST.date.max().strftime('%Y-%m-%d %H:%M')
                ]
                ),
                y=alt.Y('value:Q', title='Elevation (ft)').scale(domain=elevRange),
                color=alt.Color(
                'alternative:N',
                title=None,
                scale=alt.Scale(
                    domain=elev_domain,
                    range=elev_range
                )
                ),
                strokeDash=alt.StrokeDash(
                'alternative:N',
                title=None,
                scale=alt.Scale(
                    domain=elev_domain,
                    range=elev_stroke_range
                )
                ),
                tooltip=[
                alt.Tooltip(c, type="quantitative", format=",.2f") for c in elev_domain
                ] + [alt.Tooltip('date:T', type='temporal', format='%Y-%m-%d %H:%M')]
            ).properties(title=reservoirNamesLookup[reservoirName])  # width=defaultwidth, height=200
                        
            allZones = create_zone_rules(outputEST.date.min().strftime('%Y-%m-%d %H:%M'), outputEST.date.max().strftime('%Y-%m-%d %H:%M'), zones, elevRange)

            estElevPlot = (poolPlot + allZones)

            rulesElev = alt.Chart(elevDf).transform_pivot(
                "alternative",
                value="value",
                groupby=["date"]
            ).mark_rule(color="gray").encode(
                x="date:T",
                opacity=when_near_left.then(alt.value(0.3)).otherwise(alt.value(0)),
                tooltip=[
                    alt.Tooltip(c, type="quantitative", format=".2f") for c in elev_domain
                    ] + [alt.Tooltip('date:T', type = 'temporal', format = '%Y-%m-%d %H:%M')],
            ).add_params(nearestLeft)


            estElevPlot = (poolPlot +  allZones + rulesElev).resolve_scale(color='shared')            
        else:
            # Define domains and ranges based on BASELINE flag
            if BASELINE:
                elev_domain = ['ID3-IMPERFECT', 'FIRO-TARGET', 'ID0', 'ID1', 'ID3-PERFECT']
                elev_range = ['#d7191c', '#000000', '#fdae61', '#abd9e9', '#2c7bb6']
                elev_stroke_range = [[1, 0], [4, 4], [1, 0], [1, 0], [1, 0]]
            else:
                elev_domain = ['ID3-IMPERFECT', 'FIRO-TARGET', 'ID3-PERFECT']
                elev_range = ['#d7191c', '#000000', '#2c7bb6']
                elev_stroke_range = [[1, 0], [4, 4], [1, 0]]

            poolPlot = alt.Chart(elevDf).mark_line().encode(
                x=alt.X(
                'date:T',
                title=None,
                axis=alt.Axis(format='%Y-%m-%d', labels=True)
                ).scale(
                domain=[
                    outputEST.date.min().strftime('%Y-%m-%d %H:%M'),
                    outputEST.date.max().strftime('%Y-%m-%d %H:%M')
                ]
                ),
                y=alt.Y('value:Q', title='Elevation (ft)').scale(domain=elevRange),
                color=alt.Color(
                'alternative:N',
                title=None,
                scale=alt.Scale(
                    domain=elev_domain,
                    range=elev_range
                )
                ),
                strokeDash=alt.StrokeDash(
                'alternative:N',
                title=None,
                scale=alt.Scale(
                    domain=elev_domain,
                    range=elev_stroke_range
                )
                ),
                tooltip=[
                alt.Tooltip(c, type="quantitative", format=",.2f") for c in elev_domain
                ] + [alt.Tooltip('date:T', type='temporal', format='%Y-%m-%d %H:%M')]
            ).properties(title=reservoirNamesLookup[reservoirName])  # width=defaultwidth, height=200
                        
            allZones = create_zone_rules(outputEST.date.min().strftime('%Y-%m-%d %H:%M'), outputEST.date.max().strftime('%Y-%m-%d %H:%M'), zones, elevRange)

            estElevPlot = (poolPlot + allZones)



            rulesElev = alt.Chart(elevDf).transform_pivot(
                "alternative",
                value="value",
                groupby=["date"]
            ).mark_rule(color="gray").encode(
                x="date:T",
                opacity=when_near_left.then(alt.value(0.3)).otherwise(alt.value(0)),
                tooltip=[
                    alt.Tooltip(c, type="quantitative", format=".2f") for c in elev_domain
                    ] + [alt.Tooltip('date:T', type = 'temporal', format = '%Y-%m-%d %H:%M')],
            ).add_params(nearestLeft)


            estElevPlot = (poolPlot +  allZones + rulesElev).resolve_scale(color='shared')


        durationdf = calculateDurations(outputEST)
        durationPlot = alt.Chart(durationdf).mark_bar(height=5).encode(
            x=alt.X(
            'BeginDate:T',
            title=None,
            axis=alt.Axis(format='%Y-%m-%d', labels=True)
            ).scale(domain=[
            outputEST.date.min().strftime('%Y-%m-%d %H:%M'),
            outputEST.date.max().strftime('%Y-%m-%d %H:%M')
            ]),
            x2='EndDate:T',
            y=alt.Y('duration:N', title='Duration'),
        ).properties(title=reservoirNamesLookup[reservoirName])  # width=defaultwidth, height=100

        # nearest = alt.selection_point(nearest=True, on="pointerover",
        #     fields=["date"], empty=False)

        # when_near = alt.when(nearest)



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
        graphics["ORO"]['elev'].properties(width=800).interactive(),
        graphics["NBB"]['elev'].properties(width=800).interactive(),
        graphics["ORO"]['duration'].properties(width=800),
        graphics["NBB"]['duration'].properties(width=800),
        graphics['confluence'].properties(width=800, height=100),
        graphics['nicolaus'].properties(width=800, height=100),
    ).resolve_scale(
        x='shared', color='independent', strokeDash='independent'
    )

    rightPlot = alt.vconcat(
        graphics["ORO"]['flow'].properties(width=800).interactive(),
        graphics["NBB"]['flow'].properties(width=800).interactive(),
        graphics['yuba'].properties(width=800, height=100),
        graphics['mary'].properties(width=800, height=100),

    ).resolve_scale(
        x='shared', color='independent', strokeDash='independent'
    )

    mergePlot = alt.hconcat(leftPlot, rightPlot).properties(
                title = f"Pattern Year: {patternYear}, Scale Factor: {scaleFactor}, ARC Spillway Configuration: {arc_spillway_config}, Alternative EST: {alternativeEST}, Percent NEP: {pct}")

    
    output_dir = os.path.join('output', datasetNew)
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{patternYear}_{scaleFactor}_{arc_spillway_config}_{datasetNew}_Alt3.png")
    mergePlot.save(output_path, scale_factor=3)




