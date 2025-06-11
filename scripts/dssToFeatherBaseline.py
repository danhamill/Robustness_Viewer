from hecdss import HecDss
import pandas as pd
import datetime


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



windowLookup = {
    '1997': [
        datetime.datetime.strptime('18 Dec 1996 1200', '%d %b %Y %H%M'),
        datetime.datetime.strptime('09 Jan 1997 1200', '%d %b %Y %H%M')
    ],
    '1986': [
        datetime.datetime.strptime('04 Feb 1986 1200', '%d %b %Y %H%M'),
        datetime.datetime.strptime('26 Feb 1986 1200', '%d %b %Y %H%M')
    ],
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

    output = pd.DataFrame()
    for scaleFactor in scaleFactorLookup[str(patternYear)]:
        for arc_spillway_config in arcSpillwayConfiguation_options:

            # Determine the Arc Spillway Config values
            if arc_spillway_config == "With":
                arcSpillwayConfigPerfect = "A"
                arcSpillwayConfigEST = "S"
            elif arc_spillway_config == "Without":
                arcSpillwayConfigPerfect = "E"
                arcSpillwayConfigEST = "P"


            window = windowLookup[str(patternYear)]


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


            output = pd.DataFrame()
            for reservoirName in ["ORO","NBB"]:

                perfectDssFile = "20240708_simulation_combined_HEFS.dss"
                outputPerfectZero = process_paths(perfectDssFile, id0Paths[reservoirName], window, convertTime=True)
                outputPerfectZero.loc[:,'alternative'] = "ID0"
                outputPerfectOne = process_paths(perfectDssFile, id1Paths[reservoirName], window, convertTime=True)
                outputPerfectOne.loc[:,'alternative'] = "ID1"
                outputPerfectThree = process_paths(perfectDssFile, id3Paths[reservoirName], window, convertTime=True)
                outputPerfectThree.loc[:,'alternative'] = "ID3-PERFECT"
                # id0 = pd.MultiIndex.from_product([['ID0'], ['date','variable','value','reservoirName']], names=['alternative',''])
                # outputPerfectZero.columns = id0
                # id1 = pd.MultiIndex.from_product([['ID1'], ['date','variable','value','reservoirName']], names=['alternative',''])
                # outputPerfectOne.columns = id1
                # id3 = pd.MultiIndex.from_product([['ID3-PERFECT'], ['date','variable','value','reservoirName']], names=['alternative',''])
                # outputPerfectThree.columns = id3

                merge = pd.concat([outputPerfectZero, outputPerfectOne, outputPerfectThree])
                merge.loc[:,'reservoirName'] = reservoirName
                output = pd.concat([output, merge])

            output.to_feather(fr"data\{patternYear}_{scaleFactor}_{arc_spillway_config}_baseline.feather")


    


