<!-- Source: https://www.usgs.gov/programs/national-geological-and-geophysical-data-preservation-program/las-format -->
<!-- Converted: html2text -->

#  LAS Format 

By [National Geological and Geophysical Data Preservation Program](https://www.usgs.gov/programs/national-geological-and-geophysical-data-preservation-program)

National Geological and Geophysical Data Preservation Program 

  * [Home](https://www.usgs.gov/programs/national-geological-and-geophysical-data-preservation-program)
  * [Grants](https://www.usgs.gov/programs/national-geological-and-geophysical-data-preservation-program/nggdpp-grants)
  * [Funded Projects](https://www.usgs.gov/programs/national-geological-and-geophysical-data-preservation-program/funded-projects)
  * [Registry of Scientific Collections (ReSciColl)](https://www.usgs.gov/programs/national-geological-and-geophysical-data-preservation-program/rescicoll)
  * [Resources for Collection Management](https://www.usgs.gov/programs/national-geological-and-geophysical-data-preservation-program/resources-collection)
  * [Success Stories](https://www.usgs.gov/programs/national-geological-and-geophysical-data-preservation-program/success-stories)
  * [Publications](https://www.usgs.gov/programs/national-geological-and-geophysical-data-preservation-program/publications)
  * [News](https://www.usgs.gov/programs/national-geological-and-geophysical-data-preservation-program/news)
  * [Connect](https://www.usgs.gov/programs/national-geological-and-geophysical-data-preservation-program/connect)
  * [Partners](https://www.usgs.gov/programs/national-geological-and-geophysical-data-preservation-program/partners)
  * [About](https://www.usgs.gov/programs/national-geological-and-geophysical-data-preservation-program/about)


[ Media ](https://www.usgs.gov/media/images/digitized-gamma-ray-log)

Sources/Usage: Public Domain. [View Media Details](https://www.usgs.gov/media/images/digitized-gamma-ray-log)

Digitized gamma ray log of the well and the selected lithologic units. Obtained from: <https://pubs.usgs.gov/of/2009/1021/ofr2009-1021.pdf> (Public domain.)

Log ASCII Standard, LAS, is a format specification for storing and distributing digital well log data. The standard was defined and is maintained by the Canadian Well Logging Society (CWLS): [http://www.cwls.org/las/](https://na01.safelinks.protection.outlook.com/?url=http%3A%2F%2Fwww.cwls.org%2Flas%2F&data=02%7C01%7C%7Cd948bb8d4f674251fd0a08d61e40344e%7C2b30530b69b64457b818481cb53d42ae%7C0%7C0%7C636729659081330178&sdata=Mzst%2BhL99AAlbwaPJ8iQexZvaEUFjAHV1Vrp%2FdYtn4o%3D&reserved=0). LAS 2.0 is the most used digital well log distribution format. LAS 3.0 extends the LAS 2.0 format so that additional data like tops, core data, horizontal and vertical deviation survey, and drill tests can also be included in the file. LAS 3.0 files are backward compatible with LAS 2.0 so software that reads a 2.0 format file will (should if properly formatted) ignore 3.0 data items. The LAS 2.0 file specification defines basic sections that appear in the text file:

~VERSION – (required) LAS version, delimiter for data sections, and wrapping information

~WELL – (required) well name, location, and information on the start and stop depths, step interval between depths, and null value definitions

~CURVE – (required) list of well log curves included in the file

~PARAMETER – data on well elevation, casing depths, etc.

~OTHER –freeform section that includes comments

~ASCII – (required) digital log curve data

In addition to the format specification, the CWLS also distributes the LAS Certify software, which verifies that a text file meets the LAS format definitions. There are two versions of the software; both work with Windows 10. LAS Certify 2.2.2 is a version that is now distributed only in the Schlumberger digital log tools package. This is a favored version because the software reports elements in a file that do not match the format specification. The CWLS is currently distributing LAS Certify 2.4.14.0. This version works adequately, although may be considered slightly clunky.

Any use of trade, firm, or product names is for descriptive purposes only and does not imply endorsement by the U.S. Government.
