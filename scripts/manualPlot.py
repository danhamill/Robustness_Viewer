import altair as alt
from pydsstools.heclib.dss import HecDss
import pandas as pd
from collections import namedtuple
import vl_convert as vlc
import os
alt.renderers.enable('browser')
print(alt.__version__)

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
    x=alt.X("date:T", title=None).axis(format='%Y-%m-%d'),
    y=alt.Y("value:Q", title=None).scale(domain=elevRange)
    )

    textFC = baseFC.mark_text(align="left", dx=5, dy=-5).encode(
    text="label:N",
    x=alt.X('date:T', aggregate='min', title=None),
    y=alt.Y('value:Q', aggregate={'argmin': 'date'}, title=None).scale(domain=elevRange),
    )

    baseTC = alt.Chart(tmpTC).mark_line(color='black').encode(
    x=alt.X("date:T", title=None).axis(format='%Y-%m-%d'),
    y=alt.Y("value:Q", title=None).scale(domain=elevRange)
    )

    textTC = baseTC.mark_text(align="left", dx=5, dy=-5).encode(
    text="label:N",
        x=alt.X('date:T', aggregate='min', title=None),
    y=alt.Y('value:Q', aggregate={'argmin': 'date'}, title=None).scale(domain=elevRange),
    )

    baseS = alt.Chart(tmpS).mark_line(color='black').encode(
    x=alt.X("date:T", title=None).axis(format='%Y-%m-%d'),
    y=alt.Y("value:Q", title=None).scale(domain=elevRange)
    )

    textS = baseS.mark_text(align="left", dx=5, dy=-5).encode(
    text="label:N",
        x=alt.X('date:T', aggregate='min', title=None),
    y=alt.Y('value:Q', aggregate={'argmin': 'date'}, title=None).scale(domain=elevRange),
    )

    baseTD = alt.Chart(tmpTD).mark_line(color='black').encode(
    x=alt.X("date:T", title=None).axis(format='%Y-%m-%d'),
    y=alt.Y("value:Q", title=None).scale(domain=elevRange)
    )

    textTD = baseTD.mark_text(align="left", dx=5, dy=-5).encode(
    text="label:N",
        x=alt.X('date:T', aggregate='min', title=None),
    y=alt.Y('value:Q', aggregate={'argmin': 'date'}, title=None).scale(domain=elevRange),
    )

    allZones = baseFC + textFC + baseTC + textTC + baseS + textS + baseTD + textTD
        
    return allZones

def process_paths(dss_file, paths, window):

    def getDssData(dssFile, path, variable, window):

        with HecDss.Open(dssFile) as fid:
            ts = fid.read_ts(path, window=window )
            values = ts.values.copy()
            times = ts.pytimes
            df = pd.DataFrame(index = pd.DatetimeIndex(times), data = {variable: values})
        return df
    output_df = pd.DataFrame()
    for variable, path in paths.items():
        df = getDssData(dss_file, path, variable, window)
        output_df = pd.concat([output_df, df], axis=1)
    output_df = output_df.stack().reset_index()
    output_df.columns = ['date', 'variable', 'value']
    return output_df




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


for patternYear in pattern_year_options:

    arc_spillway_config = "Without"
    alternativeEST = 3

    for scaleFactor in scaleFactorLookup[str(patternYear)]:

        for pct in pct_options:

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


            window = windowLookup[str(patternYear)]



            estAlternative = f"SS_FV0{alternativeEST}{arcSpillwayConfigEST}-P{pct:02d}"

            estPaths = {
                "ORO": {
                    "POOL-ELEV": "//OROVILLE-POOL/ELEV//1HOUR/" + f"C:000{scaleFactor:03d}|{estAlternative}" + "/",
                    "FIRO-TARGET": "//OROVILLE-FIRO TARGET/ELEV-ZONE//1HOUR/"+ f"C:000{scaleFactor:03d}|{estAlternative}" + "/",
                    "ORO-OUT": "//OROVILLE-POOL/FLOW-OUT//1HOUR/" + f"C:000{scaleFactor:03d}|{estAlternative}" + "/",
                    "ORO-IN": "//OROVILLE-POOL/FLOW-IN//1HOUR/" + f"C:000{scaleFactor:03d}|{estAlternative}" + "/",
                    "CONFLUENCE": f"//FEATHER R + YUBA R/FLOW//1HOUR/C:000{scaleFactor:03d}|{estAlternative}/",
                    "NICOLAUS": f"//NICOLAUS/FLOW//1HOUR/C:000{scaleFactor:03d}|{estAlternative}/", # NBB
                    "MARYSVILLE": f"//MARYSVILLE/FLOW//1HOUR/C:000{scaleFactor:03d}|{estAlternative}/", #NBB
                    "YUBA CITY": f"//YUBA CITY/FLOW//1HOUR/C:000{scaleFactor:03d}|{estAlternative}/", #ORO
                    "DURATION": f"//ORO_CONTROLLING_DURATION/DURCODE//1HOUR/C:000{scaleFactor:03d}|{estAlternative}/"#ORO
                },
                "NBB":{
                    "POOL-ELEV": "//NEW BULLARDS BAR-POOL/ELEV//1HOUR/" + f"C:000{scaleFactor:03d}|{estAlternative}" + "/",
                    "FIRO-TARGET": "//NEW BULLARDS BAR-FIRO TARGET/ELEV-ZONE//1HOUR/"+ f"C:000{scaleFactor:03d}|{estAlternative}" + "/",
                    "NBB-OUT": "//NEW BULLARDS BAR-POOL/FLOW-OUT//1HOUR/" + f"C:000{scaleFactor:03d}|{estAlternative}" + "/",
                    "NBB-IN": "//NEW BULLARDS BAR-POOL/FLOW-IN//1HOUR/" + f"C:000{scaleFactor:03d}|{estAlternative}" + "/",
                    "CONFLUENCE": f"//FEATHER R + YUBA R/FLOW/01DEC1996/1HOUR/C:000{scaleFactor:03d}|{estAlternative}/",
                    "NICOLAUS": f"//NICOLAUS/FLOW/01DEC1996/1HOUR/C:000{scaleFactor:03d}|{estAlternative}/",
                    "MARYSVILLE": f"//MARYSVILLE/FLOW/01DEC1996/1HOUR/C:000{scaleFactor:03d}|{estAlternative}/",
                    "YUBA CITY": f"//YUBA CITY/FLOW//1HOUR/C:000{scaleFactor:03d}|{estAlternative}/", #ORO
                    "DURATION": f"//NBB_CONTROLLING_DURATION/DURCODE//1HOUR/C:000{scaleFactor:03d}|{estAlternative}/"
                }
            }


            id0Alt = f"SS_FV00{arcSpillwayConfigPerfect}--0"
            id0Paths = {
                "ORO": {
                    "POOL-ELEV":f"//OROVILLE-POOL/ELEV//1Hour/C:000{scaleFactor:03d}|{id0Alt}/",
                    # "FIRO-TARGET":"//OROVILLE-FIRO TARGET/ELEV-ZONE//1Hour/C:000120|SS_FV00E--0/",
                    "ORO-OUT":f"//OROVILLE-POOL/FLOW-OUT//1Hour/C:000{scaleFactor:03d}|{id0Alt}/",
                    # "ORO-IN":"//OROVILLE-POOL/FLOW-IN//1Hour/C:000120|SS_FV00E--0/",
                },
                "NBB": {
                    "POOL-ELEV":f"//NEW BULLARDS BAR-POOL/ELEV//1Hour/C:000{scaleFactor:03d}|{id0Alt}/",
                    # "FIRO-TARGET":"//OROVILLE-FIRO TARGET/ELEV-ZONE//1Hour/C:000120|SS_FV00E--0/",
                    "NBB-OUT":f"//NEW BULLARDS BAR-POOL/FLOW-OUT//1Hour/C:000{scaleFactor:03d}|{id0Alt}/",
                }
            }

            id1Alt = f"SS_FV01{arcSpillwayConfigPerfect}--0"
            id1Paths = {
                "ORO": {
                    "POOL-ELEV":f"//OROVILLE-POOL/ELEV//1Hour/C:000{scaleFactor:03d}|{id1Alt}/",
                    # "FIRO-TARGET":"//OROVILLE-FIRO TARGET/ELEV-ZONE//1Hour/C:000120|SS_FV00E--0/",
                    "ORO-OUT":f"//OROVILLE-POOL/FLOW-OUT//1Hour/C:000{scaleFactor:03d}|{id1Alt}/",
                    # "ORO-IN":"//OROVILLE-POOL/FLOW-IN//1Hour/C:000120|SS_FV00E--0/",
                },
                "NBB": {
                    "POOL-ELEV":f"//NEW BULLARDS BAR-POOL/ELEV//1Hour/C:000{scaleFactor:03d}|{id1Alt}/",
                    # "FIRO-TARGET":"//OROVILLE-FIRO TARGET/ELEV-ZONE//1Hour/C:000120|SS_FV00E--0/",
                    "NBB-OUT":f"//NEW BULLARDS BAR-POOL/FLOW-OUT//1Hour/C:000{scaleFactor:03d}|{id1Alt}/",
                }
            }

            id3alt = f"SS_FV03{arcSpillwayConfigPerfect}--0"
            id3Paths = {
                "ORO": {
                    "POOL-ELEV":f"//OROVILLE-POOL/ELEV//1Hour/C:000{scaleFactor:03d}|{id3alt}/",
                    # "FIRO-TARGET":"//OROVILLE-FIRO TARGET/ELEV-ZONE//1Hour/C:000120|SS_FV00E--0/",
                    "ORO-OUT":f"//OROVILLE-POOL/FLOW-OUT//1Hour/C:000{scaleFactor:03d}|{id3alt}/",
                    # "ORO-IN":"//OROVILLE-POOL/FLOW-IN//1Hour/C:000120|SS_FV00E--0/",
                },
                "NBB": {
                    "POOL-ELEV":f"//NEW BULLARDS BAR-POOL/ELEV//1Hour/C:000{scaleFactor:03d}|{id3alt}/",
                    # "FIRO-TARGET":"//OROVILLE-FIRO TARGET/ELEV-ZONE//1Hour/C:000120|SS_FV00E--0/",
                    "NBB-OUT":f"//NEW BULLARDS BAR-POOL/FLOW-OUT//1Hour/C:000{scaleFactor:03d}|{id3alt}/",
                }
            }


            graphics = {}
            for reservoirName in ["ORO","NBB"]:
                zones = zoneLookup[reservoirName]
                elevRange = elevRangeLookup[reservoirName]
                flowRange = flowRangeLookup[reservoirName]

                estDssFile = estDssFileLookup[str(patternYear)]
                outputEST = process_paths(estDssFile, estPaths[reservoirName], window)
                outputEST.loc[outputEST.variable == 'POOL-ELEV','alternative'] = "ID3-IMPERFECT"
                outputEST.loc[outputEST.variable == 'FIRO-TARGET','alternative'] = "FIRO-TARGET"
                outputEST.loc[outputEST.variable == f'{reservoirName}-OUT','alternative'] = f'{reservoirName}-OUT'
                outputEST.loc[outputEST.variable == f'{reservoirName}-IN','alternative'] = f'{reservoirName}-IN'

                perfectDssFile = "20240708_simulation_combined_HEFS.dss"
                outputPerfectZero = process_paths(perfectDssFile, id0Paths[reservoirName], window)
                outputPerfectZero.loc[:,'alternative'] = "ID0"
                outputPerfectOne = process_paths(perfectDssFile, id1Paths[reservoirName], window)
                outputPerfectOne.loc[:,'alternative'] = "ID1"
                outputPerfectThree = process_paths(perfectDssFile, id3Paths[reservoirName], window)
                outputPerfectThree.loc[:,'alternative'] = "ID3-PERFECT"


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

                flowDf = pd.concat(dataframes)

                flowMaryDf = outputEST.loc[outputEST["variable"] == "MARYSVILLE", :]
                maryThreshold = 180000
                flowMary = alt.Chart(flowMaryDf).mark_line().encode(
                        x=alt.X('date:T', title=None).axis(format='%Y-%m-%d'
                            ).scale(
                                domain=[flowMaryDf.date.min().strftime('%Y-%m-%d %H:%M'), 
                                flowMaryDf.date.max().strftime('%Y-%m-%d %H:%M')]),
                    y=alt.Y('value:Q', title='Flow (cfs)').scale(domain=(0,300000)),
                )

                highlightMary = flowMary.mark_line(color='red').encode(
                    y2=alt.Y2(datum=maryThreshold)
                ).transform_filter(
                    alt.datum.value > maryThreshold
                )

                maryFlow = (flowMary + highlightMary).properties(width=800,  height=100, title = "Marysville")

                flowYubaCityDf = outputEST.loc[outputEST["variable"] == "YUBA CITY", :]
                yubaThreshold = 180000
                flowYubaCity = alt.Chart(flowYubaCityDf).mark_line().encode(
                        x=alt.X('date:T', title=None).axis(format='%Y-%m-%d'
                            ).scale(
                                domain=[flowYubaCityDf.date.min().strftime('%Y-%m-%d %H:%M'), 
                                flowYubaCityDf.date.max().strftime('%Y-%m-%d %H:%M')]),
                    y=alt.Y('value:Q', title='Flow (cfs)').scale(domain=(0,300000)),
                )

                highlightYubaCity = flowYubaCity.mark_line(color='red').encode(
                    y2=alt.Y2(datum=yubaThreshold)
                ).transform_filter(
                    alt.datum.value > yubaThreshold
                )

                yubaFlow = (flowYubaCity + highlightYubaCity).properties(width=800, height=100,  title = "Yuba City")

                flowNicolausDf = outputEST.loc[outputEST["variable"] == "NICOLAUS", :]
                nicolausThreshold = 320000
                flowNicolaus = alt.Chart(flowNicolausDf).mark_line().encode(
                        x=alt.X('date:T', title=None).axis(format='%Y-%m-%d'
                            ).scale(
                                domain=[flowNicolausDf.date.min().strftime('%Y-%m-%d %H:%M'), 
                                flowNicolausDf.date.max().strftime('%Y-%m-%d %H:%M')]),
                    y=alt.Y('value:Q', title='Flow (cfs)').scale(domain=(0,400000)),
                )

                highlightNicolaus = flowNicolaus.mark_line(color='red').encode(
                    y2=alt.Y2(datum=nicolausThreshold)
                ).transform_filter(
                    alt.datum.value > nicolausThreshold
                )

                nicolausFlow = (flowNicolaus + highlightNicolaus).properties(width=800, height=100,  title = "Nicolaus")

                flowConfluenceDf = outputEST.loc[outputEST["variable"] == "CONFLUENCE", :]
                confluenceThreshold = 300000

                flowConfluence = alt.Chart(flowConfluenceDf).mark_line().encode(
                        x=alt.X('date:T', title=None).axis(format='%Y-%m-%d'
                            ).scale(
                                domain=[flowConfluenceDf.date.min().strftime('%Y-%m-%d %H:%M'), 
                                flowConfluenceDf.date.max().strftime('%Y-%m-%d %H:%M')]),
                    y=alt.Y('value:Q', title='Flow (cfs)').scale(domain=(0,400000)),
                )

                highlightConfluence = flowConfluence.mark_line(color='red').encode(
                    y2=alt.Y2(datum=confluenceThreshold)
                ).transform_filter(
                    alt.datum.value > confluenceThreshold
                )

                confluenceFlow = (flowConfluence + highlightConfluence).properties(width=800, height=100, title = "Confluence")

                poolPlot = alt.Chart(elevDf).mark_line().encode(
                    x=alt.X('date:T', title=None).axis(format='%Y-%m-%d', labels=True
                        ).scale(
                            domain=[outputEST.date.min().strftime('%Y-%m-%d %H:%M'), 
                            outputEST.date.max().strftime('%Y-%m-%d %H:%M')]),
                y=alt.Y('value:Q', title='Elevation (ft)').scale(domain=elevRange),
                color=alt.Color('alternative:N', title=None, scale=alt.Scale(
                    domain=['ID3-IMPERFECT','FIRO-TARGET','ID0', 'ID1','ID3-PERFECT'], 
                    range=['#d7191c', '#000000','#fdae61', '#abd9e9','#2c7bb6'])),
                strokeDash=alt.StrokeDash('alternative:N', title=None, scale=alt.Scale(
                    domain=['ID3-IMPERFECT','FIRO-TARGET','ID0', 'ID1','ID3-PERFECT'], 
                    range=[[1,0],[4,4],[1,0],[1,0],[1,0]])),
                tooltip=['date:T', 'value:Q', 'alternative:N']
                ).properties(width=800)


                allZones = create_zone_rules(outputEST.date.min().strftime('%Y-%m-%d %H:%M'), outputEST.date.max().strftime('%Y-%m-%d %H:%M'), zones, elevRange)


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
                    tooltip=[alt.Tooltip(c, type="quantitative", format=".2f") for c in ['ID3-IMPERFECT','FIRO-TARGET','ID0', 'ID1','ID3-PERFECT']],
                ).add_params(nearest)


                estElevPlot = (poolPlot +  allZones + rulesElev).resolve_scale(color='shared')

                durTable = outputEST.loc[outputEST.variable == 'DURATION', :]
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
                durTable.loc[:, 'durations'] = durTable.loc[:,'value'].map(lambda x: lookup.get(x, '').split(', '))

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

                durationPlot = alt.Chart(output).mark_bar(height=5).encode(
                    x = alt.X('BeginDate:T', title=None).axis(format = '%Y-%m-%d', labels=True).scale(
                        domain = [outputEST.date.min().strftime('%Y-%m-%d %H:%M'),
                                outputEST.date.max().strftime('%Y-%m-%d %H:%M')]),
                    x2 = 'EndDate:T',
                    y = alt.Y('duration:N', title='Duration'),
                ).properties(width=800)

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
                    tooltip=[alt.Tooltip(c, type="quantitative", format=".0f") for c in [f'{reservoirName}-OUT', f'{reservoirName}-IN', 'ID0', 'ID1', 'ID3-PERFECT']],
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
                ).properties(width=800)

                flowPlot = flowPlot + rules

                if reservoirName == "ORO":
                    operationPlot = alt.vconcat(estElevPlot, durationPlot, flowPlot, yubaFlow, confluenceFlow).resolve_scale(
                            x='shared', color='independent', strokeDash='independent')
                else:
                    operationPlot = alt.vconcat(estElevPlot, durationPlot, flowPlot, maryFlow, nicolausFlow).resolve_scale(
                            x='shared', color='independent', strokeDash='independent')
                graphics[reservoirName] = operationPlot


            mergeGraphic = alt.hconcat(graphics['ORO'], graphics['NBB']).properties(
                title = f"Pattern Year: {patternYear}, Scale Factor: {scaleFactor}, ARC Spillway Configuration: {arc_spillway_config}, Alternative EST: {alternativeEST}, Percent NEP: {pct}")

            if not os.path.exists(f"output/{patternYear}_{scaleFactor:03d}_{arc_spillway_config}ARC_{pct:02d}NEP.png"):

                mergeGraphic.save(f"output/{patternYear}_{scaleFactor:03d}_{arc_spillway_config}ARC_{pct:02d}NEP.png", scale_factor=3)





