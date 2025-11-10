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
    # "HDR_proposals": {
    #     "1997": r"data\HDR_proposals\SS-1997_results_v7.dss",
    #     "1986": r"data\HDR_proposals\SS-1986_results_v7.dss",
    # },
    # "FVA_config": {
    #     "1997": r"data\FVA_config\SS-1997_results_v7.dss",
    #     "1986": r"data\FVA_config\SS-1986_results_v7.dss",
    # },
    # "ORO_Release_v2": {
    #     "1997": r"data\ORO_Release_v2\1997_simulation_v7.dss",
    #     "1986": r"data\ORO_Release_v2\1986_simulation_v7.dss",
    # },
    'ORO_Release_TargetVols':{
        '1997':r"data\ORO_Release_TargetVols\1997_simulation_targetVols_v7.dss",
        '1986':r"data\ORO_Release_TargetVols\1986_simulation_targetVols_v7.dss"
    }
}


trialNums = {
    '1986':4,
    '1997':1
}


scaleFactorLookup = {
    '1986':[100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120, 130],#100,102,104,106,108,110,112,114,116,118,120,130,140,150
    '1997':[84,86,88,90,92,94,96,98,100,102,104,106,108,110,120]#130
}

# Define the options for the dropdowns

# Define the options for the dropdowns
pattern_year_options = [1986, 1997]
alternative_est_options = [3]
pct_options = [75]
arcSpillwayConfiguation_options = ["With", "Without"][0:1]



for dataset, estDssFileLookup in estDssFileLookup.items():
    for patternYear in pattern_year_options:

        for arc_spillway_config in arcSpillwayConfiguation_options:

            # Determine the Arc Spillway Config values
            if arc_spillway_config == "With":
                arcSpillwayConfigEST = "S"
            elif arc_spillway_config == "Without":
                arcSpillwayConfigEST = "P"

            for scaleFactor in scaleFactorLookup[str(patternYear)]:

                output = pd.DataFrame()



                windowPST = windowLookupPST[str(patternYear)]
                trialNum = trialNums[str(patternYear)]
                # 'C:000100|SS_FV03S--1'
                alternativeEST = 3
                estAlternative = f"SS_FV0{alternativeEST}{arcSpillwayConfigEST}--{trialNum}"

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


                
                for reservoirName in ["ORO","NBB"]:

                    estDssFile = estDssFileLookup[str(patternYear)]
                    outputEST = process_paths(estDssFile, estPaths[reservoirName], windowPST)
                    outputEST.loc[:,'Reservoir'] = reservoirName
                    outputEST.loc[:,'pct'] = pct_options[0]
                    output = pd.concat([output, outputEST])



                output.to_feather(fr"data\{patternYear}_{scaleFactor}_{arc_spillway_config}_{dataset}_Alt3.feather")


    


