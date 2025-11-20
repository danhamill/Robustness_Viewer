import datetime
import pandas as pd
import altair as alt
from hecdss.hecdss import HecDss
alt.renderers.enable('browser')


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

    durTable = durTable.groupby('date').value.min()
    return durTable


def getDssData(fid, path, variable, window, convertTime=False):

    ts = fid.get(path, startdatetime=window[0], enddatetime=window[1])
    values = ts.values
    times = ts.times

    if convertTime:
        times = [i - datetime.timedelta(hours=8) for i in times]  # Convert to PST
    df = pd.DataFrame(index = pd.DatetimeIndex(times), data = {variable: values})
    
    return df


def process_paths(dss_file, paths, window, convertTime=False):
    output_df = pd.DataFrame()

    fid = HecDss(dss_file)
    for variable, path in paths.items():
        df = getDssData(fid, path, variable, window, convertTime)
        output_df = pd.concat([output_df, df], axis=1)
    fid.close()
    output_df = output_df.stack().reset_index()
    output_df.columns = ['date', 'variable', 'value']
    return output_df



windowLookupPST = {
    '1997': [
        datetime.datetime.strptime('18 Dec 1996 0400', '%d %b %Y %H%M'),
        datetime.datetime.strptime('09 Jan 1997 0400', '%d %b %Y %H%M')
    ],
    '1986': [
        datetime.datetime.strptime('04 Feb 1986 0400', '%d %b %Y %H%M'),
        datetime.datetime.strptime('26 Feb 1986 0400', '%d %b %Y %H%M')
    ],
}

estDssFileLookup = {
    'Event_Model':{
        '1986':r"data\Event_Model\1986_simulation_v7.dss",
        '1997':r"data\Event_Model\1997_simulation_v7.dss"
    }
}


trialNums = {
    '1986':0,
    '1997':0
}


scaleFactorLookup = {
    '1986':[100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120, 130],#100,102,104,106,108,110,112,114,116,118,120,130,140,150
    '1997':[84,86,88,90,92,94,96,98,100,102,104,106,108,110,120,130]#130
}

# Define the options for the dropdowns

# Define the options for the dropdowns
pattern_year_options = [1986, 1997][1:]
patternLetters = {
    '1986':'C',
    '1997':'D'
}
simulationLetters = {
    'imperfect':'I'
}
alternative_est_options = [3]
pct_options = [75]
arcSpillwayConfiguation_options = ["With", "Without"][0:1]
domains = {
    '1986': ['1986-02-09 04:00', '1986-02-21 04:00'],
    '1997': ['1996-12-26 04:00', '1997-01-04 04:00'],
}
yranges = {
    '1986': [2600000, 2900000],
    '1997': [2400000, 2900000],
}
charts = {}

for dataset, estDssFileLookup in estDssFileLookup.items():
    for patternYear, estDssFile in estDssFileLookup.items():

        for arc_spillway_config in arcSpillwayConfiguation_options:

            # Determine the Arc Spillway Config values
            if arc_spillway_config == "With":
                arcSpillwayConfigEST = "A"
            elif arc_spillway_config == "Without":
                arcSpillwayConfigEST = "E"

            for scaleFactor in [100]:

                plotDur = pd.DataFrame()

                for simulationType, simulationLetter in simulationLetters.items():


                    windowPST = windowLookupPST[str(patternYear)]
                    trialNum = trialNums[str(patternYear)]
                    # 'C:000094|RID_F03A--1'
                    alternativeEST = 3
                    estAlternative = f"R{simulationLetter}{patternLetters[str(patternYear)]}_F0{alternativeEST}{arcSpillwayConfigEST}--{trialNum}"

                    estPaths = {
                        "ORO": {
                            "POOL-ELEV": "//OROVILLE-POOL/ELEV//1HOUR/" + f"C:000{scaleFactor:03d}|{estAlternative}" + "/",
                            "FIRO-TARGET": "//OROVILLE-FIRO TARGET/STOR-ZONE//1HOUR/"+ f"C:000{scaleFactor:03d}|{estAlternative}" + "/",
                            "DURATION": f"//ORO_CONTROLLING_DURATION/DURCODE//1HOUR/C:000{scaleFactor:03d}|{estAlternative}/",
                            "ORO_INFLOW_1D":f"//ORO_INFLOW_1D/ORO_INFLOW_1D//1HOUR/C:000{scaleFactor:03d}|{estAlternative}/",
                            "ORO_INFLOW_2D":f"//ORO_INFLOW_2D/ORO_INFLOW_2D//1HOUR/C:000{scaleFactor:03d}|{estAlternative}/",
                            "ORO_INFLOW_3D":f"//ORO_INFLOW_3D/ORO_INFLOW_3D//1HOUR/C:000{scaleFactor:03d}|{estAlternative}/",
                            "ORO_INFLOW_5D":f"//ORO_INFLOW_5D/ORO_INFLOW_5D//1HOUR/C:000{scaleFactor:03d}|{estAlternative}/",
                            "ORO_INFLOW_7D":f"//ORO_INFLOW_7D/ORO_INFLOW_7D//1HOUR/C:000{scaleFactor:03d}|{estAlternative}/",
                        },
                    }

                    outputEST = process_paths(estDssFile, estPaths["ORO"], windowPST)
                    outputEST.loc[:,'Reservoir'] = "ORO"
                    outputEST.loc[:,'pct'] = pct_options[0]
                    outputEST.loc[:,'alternative_est'] = estAlternative

                    
                    durationDf = calculateDurations(outputEST)
                    
                    outputEST = outputEST.set_index('date')

                    # merge durationDf with output variable FIRO-Target
                    durationDf = durationDf.to_frame().merge(outputEST.loc[outputEST.variable == 'FIRO-TARGET', :], 
                                                  left_index=True, right_index=True, how='left', suffixes=('_dur', '_firo'))[['value_dur','value_firo']]
                    
                    # Creatte continious time seres for each valud_dur
                    plotDur= pd.DataFrame()
                    for name, group in durationDf.groupby('value_dur'):
                        idx = pd.date_range(start=group.index.min(), end=group.index.max(), freq='H')
                        group = group.reindex(idx)
                        group.index.name = 'date'
                        plotDur = pd.concat([plotDur, group])

                    df = outputEST.loc[outputEST.variable == 'FIRO-TARGET']

                    a = alt.Chart(df.reset_index()).mark_line(color='black', point=alt.OverlayMarkDef(color='black')).encode(
                        x = alt.X('date:T', title = 'Date').axis(format='%Y-%m-%d'
                        ).scale(domain = domains[patternYear]),
                        y = alt.Y('value:Q', title = 'FIRO Target (ac-ft)').scale(domain=yranges[patternYear]),
                        strokeDash=alt.StrokeDash('variable:N', legend=None, scale=alt.Scale(
                            domain=['FIRO-TARGET'], 
                            range=[[4,4]]))
                    )
                    # a.show()
                    plotDur.loc[plotDur.value_dur.isna(), 'value_dur'] = 0
                    plotDur.loc[:, 'value_dur'] = plotDur.loc[:, 'value_dur'].astype(str) + '-day'

                    # Now create the chart with the complete series (gaps will be null and won't connect)
                    b = alt.Chart(plotDur.reset_index()).transform_impute(
                        'value_firo', key='date', value=None, groupby=['value_dur']
                        ).mark_line(point=True).encode(
                        x = alt.X('date:T', title = 'Date').axis(format='%Y-%m-%d'
                        ).scale(domain = domains[patternYear]),
                        y = alt.Y('value_firo:Q', title = 'FIRO Target (ac-ft)').scale(domain=yranges[patternYear]),
                        color = alt.Color('value_dur:N', 
                                        scale=alt.Scale(
                                            domain=['0.0-day', '1.0-day', '2.0-day', '3.0-day','5.0-day', '7.0-day'],
                                            range=['black', '#1f77b4', '#ff7f0e', '#2ca02c','#9467bd', '#d62728']
                                        ), 
                                        title='Controlling Duration'),
                        tooltip = ['date:T', 'value_dur:O', 'value_firo:Q']
                    )
                    

                    charts[patternYear] = (a+b).properties(width=500, title = f"Pattern {patternYear} - Scale Factor {scaleFactor}")

plot = alt.vconcat(*[charts[year] for year in sorted(charts.keys())]).interactive()
plot.save(r'output\Event_Model\firo_target_controlling_duration.png', scaleFactor=3)





