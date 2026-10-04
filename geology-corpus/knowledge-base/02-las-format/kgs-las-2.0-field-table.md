<!-- Source: https://www.kgs.ku.edu/software/DEWL/HELP/pc_write/index.html -->
<!-- Converted: html2text -->

[ ](https://www.kgs.ku.edu/) | 

# HELP: Save data as Log ASCII Standard (LAS) version 2.0 File 

|   
---|---|---  
  
The LAS (Log ASCII Standard) is rapidly becoming the accepted industry standard for electronic transmission of digital wireline logs. Earlier digital formats were commonly coded in binary (such as LIS) and so required specialized software to read them. The LAS standard was introduced by the Canadian Well Logging Society(1) in 1989 to standardize the organization of digital log curve information for personal computer users. It did this very successfully and the standard became popular worldwide. Version 1.2 was the first version and followed in September 1992 by version 2.0 to address some inconsistencies. A more versatile version LAS 3.0 was released in 1999 however at present LAS 2.0 remains the dominant product. LAS 3.0 clarifies several of the poorly defined specifications of LAS 2.0 and provides expanded data storage capabilities, but has seen limited implementation. 

This program will write a Log ASCII Standard (LAS) version 2.0 file. 

The sections defined for the LAS 2.0 standard are as follows (_**see reference below for the complete document**_): 

  * **"~V"** (also known as "~VERSION INFORMATION SECTION") is a required section; has formatting requirements; must be the first section; identifies the version number and whether data is in "wrapped" or "un-wrapped" mode. The following are considered required fields in the ~Version information section for the LAS version 2.0 standard,  **~Version Information******  
---  
**Mnemonics**| **.Units**| **Value**| **: Description**  
VERS| . | 2.0| : CWLS log ASCII Standard -VERSION 2.0  
WRAP| . | NO| : One line per depth step  
  * **"~W"** (also known as "WELL INFORMATION SECTION") is a required section; has formatting requirements; is preferably the second section; contains information on the well name, location, and start and stop values of the data in this file. The following are considered required fields int the ~Well Information Section for the LAS version 2.0 standard,  **~W(Well Information)**  
---  
**Mnemonics**| **.Units**| **Value**| **: Description**  
STRT| .F| nnnn.nn| : Start Depth  
STOP| .F| nnnn.nn| : Stop Depth  
STEP| .F| nnnn.nn| : Step Depth  
NULL| . | nnnn.nn| : Null Value; Common Null Values are -999.25, -9999, etc.  
COMP| . | aaaaaaaaaaaaaaaaaaaaaaaa| : Company Name  
WELL| . | aaaaaaaaaaaaaaaaaaaaaaaa| : Well Name  
FLD | . | aaaaaaaaaaaaaaaaaaaaaaaa| : Field Name  
LOC | . | aaaaaaaaaaaaaaaaaaaaaaaa| : Well Location  
PROV| . | aaaaaaaaaaaaaaaaaaaaaaaa| : Province; Canadian  
CTRY| . | aaaaaaaaaaaaaaaaaaaaaaaa| : Country; Outside Canada  
STAT| . | aaaaaaaaaaaaaaaaaaaaaaaa| : State  
CNTY| . | aaaaaaaaaaaaaaaaaaaaaaaa| : County  
UWI | . | aaaaaaaaaaaaaaaaaaaaaaaa| : Unique Well ID; Within Canada 16 character string  
API | . | aaaaaaaaaaaaaaaaaaaaaaaa| : API-Number  
SRVC| . | aaaaaaaaaaaaaaaaaaaaaaaa| : Logging Company  
LIC | . | aaaaaaaaaaaaaaaaaaaaaaaa| : Regulatory Licence Number  
DATE| . | aaaaaaaaaaaaaaaaaaaaaaaa| : Date logged, prefferred date MM/DD/YYYY  
  * **"~C"** (also known as ~CURVE INFORMATION SECTION") is a required section; has formatting requirements; contains curve mnemonics and their definitions in the order that they appear in the data section.
  * **"~P"** (also known as ~PARAMETER INFORMATION SECTION") is an optional section; has formatting requirements; contains information on parameters or constants relevant to the wellbore such as mud resistivity, wireline engineer, truck number, elevation data, etc.
  * **"~O"** (also known as "~OTHER") is an optional section; has no formatting requirements; contains other information or comments.
  * **"~A"** (also known as ~ASCII LOG DATA") is a required section; has formatting requirements; is the last section in the file and also referred to as the data section. The index of the data columns is either Depth or Time. The index values always appear in the first column and each column of data must be separated by at least one space (ASCII 32). All values in the ASCII log data section must be floating point or integer (long) values. Other formats such as Text or Exponential values are not supported.


**Log ASCII Standard (LAS) File Example:** [Shamar-l.las](https://www.kgs.ku.edu/software/DEWL/HELP/pc_write/Shamar-1.las)

REFERENCE:  
(1) Canadian Well Logging Society, LAS - Log ASCII Standard <http://www.cwls.org/las_info.php>

  * LAS Version 2.0: Update July 2009 <http://www.cwls.org/docs/las_20_updated_july2009.pdf>
  * LAS Version 3.0 (Adobe Acrobat File) <http://www.cwls.org/docs/LAS_3_File_Structure.PDF>


Author: John R. Victorine [ jvictor@kgs.ku.edu](mailto:jvictor@kgs.ku.edu)
