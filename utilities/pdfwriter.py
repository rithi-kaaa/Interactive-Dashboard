import datetime
import pandas as pd
from fpdf import FPDF
import utilities.utils as u
import numpy as np

#Note: dfs=[spotpnls, spotvols, perppnls, perpvols]
def generateMMHourlyReport(dfs, hourlyReportPathName, reportFontPath):
    desired_width=300
    pd.set_option('display.width', desired_width)
    pd.set_option('display.max_columns',20)

    t = datetime.datetime.now()
    report_time = str(t.date()) + " " + str(t.hour) + ":00"

    #set the pnldfs numbering starts from 1
    dfs[0].index = np.arange(1, len(dfs[0])+1)
    dfs[2].index = np.arange(1, len(dfs[2])+1)

    ##Genereate pdf content
    reportTxtFilepath = hourlyReportPathName.replace("xxx",report_time).replace(".pdf",".txt")
    f = open(reportTxtFilepath, 'w+')
    print('Reporting Time: %s UTC+8'%(report_time), file=f)
    f.write('\r\n')
    print('MM SPOT PNL', '\n', dfs[0], file=f)
    f.write('\r\n')
    print('MM SPOT VOLUME', '\n', dfs[1], file=f)
    f.write('\r\n')
    print('MM PERP PNL', '\n', dfs[2], file=f)
    f.write('\r\n')
    print('MM PERP VOLUME ', '\n', dfs[3], file=f)
    f.write('\r\n')
    f.close()
    #
    pdf = FPDF(format=(270, 380))
    # run this line firstly, then can comment it.
    pdf.add_font('Consolas4', '', fname=r'%s'%reportFontPath, uni=True)

    # Add a page
    pdf.add_page()
    # set style and size of font
    pdf.set_font('Consolas4', size=7)

    f = open(reportTxtFilepath, "r+")
    # insert the texts in pdf
    for x in f:
        pdf.cell(400, 5, txt=x.replace('\n', ''), ln=1, align='L')
    reportPdfFilepath = reportTxtFilepath.replace(".txt",".pdf")
    pdf.output(reportPdfFilepath)
    pdf.close()
    u.deleteFile(reportTxtFilepath)

    ## Generate email content in html
    # (refering to https://stackoverflow.com/questions/50564407/pandas-send-email-containing-dataframe-as-a-visual-table)
    emailhtml = """\
    <html>
      <head></head>
      <body>
        <h3>SPOT PNL</h3>
        {0}
        <h3>SPOT VOLUME</h3>
        {1}
        <h3>PERP PNL</h3>
        {2}
        <h3>PERP VOLUME</h3>
        {3}
      </body>
    </html>
    """.format(dfs[0].to_html(),dfs[1].to_html(),dfs[2].to_html(),dfs[3].to_html())
    return reportPdfFilepath, emailhtml

def getDFHtmlForEmail(df):
    if df is None:
        return ""
    dfHtml = df.to_html(classes=None, border=0, justify="right")
    dfHtml = dfHtml.replace('<tbody>', '<tbody style="text-align: right;">')
    return dfHtml

#Note: dfs=[spotpnls, spotvols, perppnls, perpvols]
def generateMMHourlyReportV2(hourlyPnlVolDFs,sodPnlVolDFs,mtdPnlVolDFs,hourlyReportPathName, reportFontPath, reportingEpochs):
    #### Data Gathering ####
    #hourly data
    hourly_spotpnlsDF = hourlyPnlVolDFs[0]
    hourly_spotvolsDF = hourlyPnlVolDFs[1]
    hourly_perppnlsDF = hourlyPnlVolDFs[2]
    hourly_perpvolsDF = hourlyPnlVolDFs[3]

    #sod data
    spotSODPnlDF, isSpotSODPnlDataComplete = sodPnlVolDFs[0], sodPnlVolDFs[1]
    spotSODVolDF, isSpotSODVolDataComplete = sodPnlVolDFs[2], sodPnlVolDFs[3]
    perpSODPnlDF, isPerpSODPnlDataComplete = sodPnlVolDFs[4], sodPnlVolDFs[5]
    perpSODVolDF, isPerpSODVolDataComplete = sodPnlVolDFs[6], sodPnlVolDFs[7]

    #mtd data
    spotMTDPnlDF, isSpotMTDPnlDataComplete = mtdPnlVolDFs[0], mtdPnlVolDFs[1]
    spotMTDVolDF, isSpotMTDVolDataComplete = mtdPnlVolDFs[2], mtdPnlVolDFs[3]
    perpMTDPnlDF, isPerpMTDPnlDataComplete = mtdPnlVolDFs[4], mtdPnlVolDFs[5]
    perpMTDVolDF, isPerpMTDVolDataComplete = mtdPnlVolDFs[6], mtdPnlVolDFs[7]

    desired_width=300
    pd.set_option('display.width', desired_width)
    pd.set_option('display.max_columns',20)

    t = datetime.datetime.now()
    report_time = str(t.date()) + " " + str(t.hour) + ":00"

    #set the pnldfs numbering starts from 1
    hourly_spotpnlsDF.index = np.arange(1, len(hourly_spotpnlsDF)+1)
    hourly_perppnlsDF.index = np.arange(1, len(hourly_perppnlsDF)+1)

    #### Genereate pdf content ####
    reportTxtFilepath = hourlyReportPathName.replace("xxx",report_time).replace(".pdf",".txt")
    f = open(reportTxtFilepath, 'w+')
    print('Reporting Time: %s UTC+8'%(report_time), file=f)
    f.write('\r\n')

    print('SOD:%s to %s'%(u.convertEpochToUTCDT((reportingEpochs["spot-sod"][0][0] / 1000) - (60 * 60)), u.convertEpochToUTCDT(reportingEpochs["spot-sod"][0][1] / 1000)), file=f)
    print('SPOT', '\n', spotSODPnlDF, file=f)
    f.write('\r\n')
    print('\n', spotSODVolDF, file=f)
    f.write('\r\n')
    print('PERP', '\n', perpSODPnlDF, file=f)
    f.write('\r\n')
    print(perpSODVolDF, file=f)
    f.write('\r\n')
    f.write('\r\n')

    print('HOURLY:%s to %s'%(u.convertEpochToUTCDT(reportingEpochs["spot-hourly"][0][0]/1000), u.convertEpochToUTCDT(reportingEpochs["spot-hourly"][0][1]/1000)), file=f)
    print('SPOT', '\n', hourly_spotpnlsDF, file=f)
    f.write('\r\n')
    print(hourly_spotvolsDF, file=f)
    f.write('\r\n')
    print('PERP', '\n', hourly_perppnlsDF, file=f)
    f.write('\r\n')
    print(hourly_perpvolsDF, file=f)
    f.write('\r\n')
    f.write('\r\n')

    print('MTD:%s to %s'%(u.convertEpochToUTCDT((reportingEpochs["spot-mtd"][0][0] / 1000) - (60 * 60)), u.convertEpochToUTCDT(reportingEpochs["spot-mtd"][0][1] / 1000)), file=f)
    print('SPOT', '\n', spotMTDPnlDF, file=f)
    f.write('\r\n')
    print(spotMTDVolDF, file=f)
    f.write('\r\n')
    print('PERP', '\n', perpMTDPnlDF, file=f)
    f.write('\r\n')
    print(perpMTDVolDF, file=f)
    f.write('\r\n')

    f.close()
    #
    pdf = FPDF(format=(270, 380))
    # run this line firstly, then can comment it.
    pdf.add_font('Consolas4', '', fname=r'%s'%reportFontPath, uni=True)

    # Add a page
    pdf.add_page()
    # set style and size of font
    pdf.set_font('Consolas4', size=7)

    f = open(reportTxtFilepath, "r+")
    # insert the texts in pdf
    for x in f:
        pdf.cell(400, 5, txt=x.replace('\n', ''), ln=1, align='L')
    reportPdfFilepath = reportTxtFilepath.replace(".txt",".pdf")
    pdf.output(reportPdfFilepath)
    pdf.close()
    u.deleteFile(reportTxtFilepath)

    ## Generate email content in html
    # (refering to https://stackoverflow.com/questions/50564407/pandas-send-email-containing-dataframe-as-a-visual-table)
    emailhtml = """\
    <html>
      <head></head>
      <body>
        <h1 align="left">SOD:{12} to {13}</h1>
        <h3>SPOT</h3>
        {0}
        {1}
        <h3>PERPETUAL</h3>
        {2}
        {3}
        
        <h1 align="left">HOURLY: {14} to {15}</h1>
        <h3>SPOT</h3>
        {4}
        {5}
        <h3>PERPPETUAL</h3>
        {6}
        {7}
              
        <h1 align="left">MTD: {16} to {17}</h1>
        <h3>SPOT</h3>
        {8}
        {9}
        <h3>PERPETUAL</h3>
        {10}
        {11}
      
      </body>
    </html>
    """.format(
        getDFHtmlForEmail(spotSODPnlDF), getDFHtmlForEmail(spotSODVolDF), getDFHtmlForEmail(perpSODPnlDF), getDFHtmlForEmail(perpSODVolDF),
        getDFHtmlForEmail(hourly_spotpnlsDF), getDFHtmlForEmail(hourly_spotvolsDF), getDFHtmlForEmail(hourly_perppnlsDF), getDFHtmlForEmail(hourly_perpvolsDF),
        getDFHtmlForEmail(spotMTDPnlDF), getDFHtmlForEmail(spotMTDVolDF), getDFHtmlForEmail(perpMTDPnlDF), getDFHtmlForEmail(perpMTDVolDF),
        u.convertEpochToUTCDT(reportingEpochs["spot-sod"][0][0]/1000-60*60),u.convertEpochToUTCDT(reportingEpochs["spot-sod"][0][1]/1000),  #spot and perp epochs will be same
        u.convertEpochToUTCDT(reportingEpochs["spot-hourly"][0][0]/1000),u.convertEpochToUTCDT(reportingEpochs["spot-hourly"][0][1]/1000),
        u.convertEpochToUTCDT(reportingEpochs["spot-mtd"][0][0]/1000-60*60),u.convertEpochToUTCDT(reportingEpochs["spot-mtd"][0][1]/1000)
    )
    return reportPdfFilepath, emailhtml
