<!-- Source: asquith-krygowski-basic-well-log-analysis-2004.pdf -->
<!-- Converted: mistral-ocr-latest -->

# Basic Well Log Analysis

(Second Edition)

By

George Asquith and Daniel Krygowski

(with sections by Steven Henderson and Neil Hurley)

AAPG Methods in Exploration Series 16

*Published by*

The American Association of Petroleum Geologists Tulsa, Oklahoma

Copyright © 2004
By the American Association of Petroleum Geologists
All Rights Reserved

ISBN: 0-89181-667-4

AAPG grants permission for a single photocopy of an item from this publication for personal use.
Authorization for additional copies of items from this publication for personal or internal use is granted
by AAPG provided that the base fee of $3.50 per copy and $.50 per page is paid directly to the Copy-
right Clearance Center, 222 Rosewood Drive, Danvers, Massachusetts 01923 (phone: 978/750-8400).
Fees are subject to change.

AAPG Editor: Ernest A. Mancini
Geoscience Director: J. B. "Jack" Thomas

This publication is available from:

The AAPG Bookstore
P.O. Box 979
Tulsa, OK U.S.A. 74101-0979
Phone: 1-918-584-2555
or 1-800-364-AAPG (U.S.A. only)
Fax: 1-918-560-2652
Or 1-800-898-2274 (U.S.A. only)
E-mail: bookstore@aapg.org
www.aapg.org

The American Association of Petroleum Geologists (AAPG) does not endorse or recommend products or services that may
be cited, used, or discussed in AAPG publications or in presentations at events associated with AAPG.

iii

# Table of Contents

|  Acknowledgements | v  |
| --- | --- |
|  About the Authors | vi  |
|  Preface (Second Edition) | viii  |
|  Preface (First Edition) | ix  |
|  **1: Basic Relationships of Well Log Interpretation** | 1  |
|  Introduction | 1  |
|  General | 1  |
|  Borehole Environment | 4  |
|  Invasion and Resistivity Profiles | 6  |
|  Basic Information Needed in Log Interpretation | 7  |
|  Common Equations | 8  |
|  Review | 10  |
|  **2: The Spontaneous Potential Log** | 21  |
|  General | 21  |
|  Formation Water Resistivity (R_{w}) Determination | 22  |
|  Shale Volume Calculation | 23  |
|  Review | 24  |
|  **3: Gamma Ray Log** | 31  |
|  General | 31  |
|  Shale Volume Calculation | 31  |
|  Spectral Gamma Ray Log | 32  |
|  Review | 32  |
|  **4: Porosity Logs** | 37  |
|  General | 37  |
|  Nuclear Magnetic Resonance Log | 37  |
|  Sonic Log | 37  |
|  Density Log | 39  |
|  Neutron Log | 40  |
|  Porosity Measurement Combinations | 41  |
|  Consistency in Lithology Prediction | 54  |
|  Review | 56  |
|  **5: Resistivity Logs** | 77  |
|  General | 77  |
|  Laterologs | 78  |
|  Induction Logs | 79  |
|  Flushed Zone Resistivity Logs | 81  |
|  Interpretation | 82  |
|  High Frequency (dielectric) Measurements | 82  |
|  Review | 86  |
|  **6: Magnetic Resonance Imaging Logs:** by Steven Henderson | 103  |
|  General | 103  |
|  Limitations of Conventional Logs | 103  |
|  Nuclear Magnetic Resonance Applications | 103  |
|  Principle of NMR Logging | 103  |

iv

|  Pore Size and Fluid Moveability | 104  |
| --- | --- |
|  NMR Permeability | 104  |
|  Direct Hydrocarbon Typing | 105  |
|  NMR Applications in Carbonates | 106  |
|  Review | 106  |
|  **7: Log Interpretation** | 115  |
|  General | 115  |
|  Scanning the Logs: A Reconnaissance Technique | 115  |
|  Archie Water Saturations: S_{w} and S_{xo} | 115  |
|  Quick-look Methods | 117  |
|  Bulk Volume Water | 120  |
|  Saturation Crossplots | 121  |
|  Permeability From Logs | 123  |
|  Shaly Sand Analysis | 125  |
|  Review | 128  |
|  **8: Petrophysical Techniques** | 137  |
|  General | 137  |
|  Neutron-Density Lithology Plot | 137  |
|  Neutron-Sonic Lithology Plot | 137  |
|  Density-Sonic Lithology Plot | 138  |
|  M-N Lithology Plot | 138  |
|  MID (Matrix Identification) Lithology Plot (ρ_{maa} vs. Δt_{maa}) | 138  |
|  MID (Matrix Identification) Lithology Plot (U_{maa} vs. ρ_{maa}) | 140  |
|  Alpha Mapping From the SP Log | 141  |
|  Clean Sand or Carbonate Maps From the Gamma Ray Log | 141  |
|  Rock Typing and Facies Mapping | 141  |
|  Review | 142  |
|  **9: Borehole Imaging: by Neil Hurley** | 151  |
|  General | 151  |
|  Electrical Borehole Images | 151  |
|  Acoustic Borehole Images | 152  |
|  Downhole Video Images | 153  |
|  Emerging Technologies: Other Borehole Images | 154  |
|  Borehole Image Interpretation | 154  |
|  Review | 156  |
|  **10: Interpretation Case Studies** | 165  |
|  1: Pennsylvanian Atoka Sandstone, Permian Basin, U.S.A. | 168  |
|  2: Mississippian Mission Canyon Formation, Williston Basin, U.S.A. | 180  |
|  3: Eocene Wilcox Sandstone, Gulf Coast, U.S.A. | 195  |
|  4: Pennsylvanian Upper Morrow Sandstone, Anadarko Basin, U.S.A. | 205  |
|  5: Cretaceous Pictured Cliffs Sandstone, San Juan Basin, U.S.A. | 213  |
|  6: Ordovician-Silurian Chimneyhill Subgroup, Hunton Group, Anadarko Basin, U.S.A. | 224  |
|  7: Pennsylvanian Canyon Limestone, New Mexico, U.S.A. | 235  |
|  **References** | 240  |

v

# Acknowledgements

The idea for this revision came from a discussion at an AAPG Annual Meeting, between George Asquith, members of the AAPG Staff, and myself. At the time, George and I had been teaching the AAPG *Basic Well Logging* short course for about a decade. We all agreed that a revision of *Basic Well Log Analysis for Geologists* was in order, to capture the technological advancements in well logging that had been made since the book’s publication.

George suggested that I start the revisions, to provide a different perspective on his original efforts. Our collaboration began in that way, with the revisions as a starting place for a continuing dialog which resulted in this edition. My sincere thanks and appreciation go to George for his confidence in my abilities, his willingness to put all of his work on the table, and for his efforts as the managing partner in this endeavor.

Our thanks to Bob Cluff who critically reviewed the original book at the beginning of this project. His comments were taken to heart. The review efforts of Rick Erickson and Gary Stewart are to be commended. Not only did they review the text, but they also attacked the case study data in great detail, comparing log displays with printed log values and final results. A special thanks goes out to Jack Thomas at AAPG who has shepherded this process in its final stages.

Many charts and figures used in the text were provided by Baker Atlas, Schlumberger Oilfield Services, and Halliburton. Our thanks for their willingness to share their information with this project.

The log displays from the original book were scanned by Neuralog and provided for the project. Neuralog software converted those images to digital data for display and interpretive processing. The raw data were stored, processed, and displayed using software from Landmark Graphics (a Halliburton Company). The PetroWorks and OpenWorks products were used for this purpose. The log plots and crossplots in the text were produced using PetroWorks software. Our thanks to both companies for providing the means to efficiently convert this work from the paper realm to the digital realm.

And finally a very special thank you to my wife, Monica Krygowski, who has supported me in an effort that took much longer than originally anticipated. Her comments, positive outlook, and encouragement are an integral part of this publication.

**Daniel A. Krygowski**  
**Austin, Texas, U.S.A.**  
**October, 2003**

vi

# About the Authors

## GEORGE B. ASQUITH

George Asquith holds the Pevehouse Chair of Petroleum Geology and is Professor of Geosciences and Director of the Center for Applied Petrophysical and Reservoir Studies at Texas Tech University. He received his B.S. (honors) in geology with a minor in mathematics from Texas Tech and his M.S. and Ph.D. from the University of Wisconsin-Madison with a minor in geophysics. His 25 years of petroleum industry experience include work as research geologist, Atlantic-Richfield Co.; staff geologist, ALPAR Resources; chief geologist, Search Drilling Co.; district geologist, Pioneer Production Corp.; and project leader, Mesa Limited Partnership. His industry projects have included the determination of the reservoir architecture and remaining gas reserves in the Hugoton and West Panhandle fields and exploration and reservoir characterization of selected reservoirs from the Gulf Coast (onshore and offshore), Permian, Alberta, San Juan, Williston, Arkoma, Cooper (Australia), Neiva (Colombia), Maracaibo (Venezuela), and Anadarko basins.

He has authored 123 publications including 5 books in the fields of petrophysics, computer geology, and carbonate and clastic sedimentation and petrology. His book, *Basic Well Log Analysis for Geologists* won the AAPG best book award in 1984 and is the top selling book in the history of AAPG. During 1991-1992, *Log Evaluation of Shaly Sandstones: A Practical Guide* was one of the top 3 selling AAPG publications. His numerous awards include the Distinguished Service and Best Paper Awards from the Society of Professional Well Log Analysts (1994); Leverson Award for best paper at the AAPG Southwest Section meeting (1996); AAPG Distinguished Educator Award (1997); Educator of the Year Award presented by the AAPG Southwest Section (1999); West Texas Geological Society Distinguished Service Award (1999); and the Monroe Cheney Science Award from the Southwest Section of AAPG and Dallas Geological Society (2001).

He has served as Distinguished Lecturer for the Society of Professional Well Log Analysts (1991-1992 and 1994-1995), lecturer for the AAPG Subsurface Carbonate Depositional Modeling school (1980-1986), and is currently lecturer and science advisor for the AAPG Basic Well Log Analysis, Carbonate Well Log Analysis, and Shaly Sand Well Log Analysis schools (1982-present).

Dr. Asquith’s research interests include the documentation and quantitative mapping of relationships between petrophysical responses and depositional and diagenetic lithofacies, the petrophysics of carbonate and shaly-sand reservoirs, and the application of computers to petrophysical analysis.

## DANIEL A. KRYGOWSKI

Daniel Krygowski is part of the software development staff in the Austin, Texas, office of Landmark Graphics (a Halliburton company). As a Domain Expert in the research and development organization, he is focused on the usability, user interface, and petrophysical technology content of PetroWorks and other software products. He received a B.A. in physics from the State University of New York College at Geneseo and M.S. and Ph.D. degrees in geophysics from the Colorado School of Mines. Previous to his employment at Landmark, he held a number of technical and management positions in petrophysics and software development at Cities Service Company (now Occidental) and Atlantic Richfield Company (now BP).

Dan is a member of the AAPG, Society of Petrophysicists and Well Log Analysts, Society of Petroleum Engineers, and Society of Exploration Geophysicists. He teaches the AAPG Basic Well Log Analysis continuing education course with George Asquith.

vii

## NEIL F. HURLEY

Neil Hurley received B.S. degrees in geology and petroleum engineering from the University of Southern California in 1976. He received his M.S. degree in geology from the University of Wisconsin-Madison in 1978. His thesis work involved stratigraphic studies in the Permian reef complex of the Guadalupe Mountains, New Mexico. From 1978 through 1982 he worked as an exploration and research geologist for Conoco in Denver, Colorado; Lafayette, Louisiana; and Ponca City, Oklahoma. In 1982, he entered the University of Michigan as an Exxon Teaching Fellow. In 1986, he received his Ph.D. degree, doing his research on the geology of Devonian reefs in Western Australia. From 1986 to 1996, he worked in reservoir characterization at Marathon’s Petroleum Technology Center in Littleton, Colorado. In 1991-92, he toured the U.S. as an AAPG Distinguished Lecturer. In 1996, Neil Hurley was awarded the Charles Boettcher Distinguished Chair in Petroleum Geology, and he is now a Professor in the Department of Geology and Geological Engineering at the Colorado School of Mines. At CSM, he teaches beginning and advanced log analysis, carbonate geology, field seminars, and integrated exploration courses. He has been the Editor for AAPG, and he is a member of the Society of Professional Well Log Analysts, Society of Petroleum Engineers, Society for Sedimentary Geology, Society of Independent Earth Scientists, International Association of Sedimentologists, Society of Exploration Geophysicists, European Association of Geoscientists and Engineers, Geological Society of America, and Rocky Mountain Association of Geologists. His specialties include carbonate sedimentology and diagenesis, fractured reservoirs, formation evaluation, borehole-imaging logs, and horizontal drilling.

## STEVE HENDERSON

Steve Henderson is a technical instructor at the Fort Worth Training Center of Halliburton Energy Services where he is involved with the training of wireline engineers in measurement physics, field operations, and log analysis. He received his B.S. in geological sciences from The University of Texas at Austin and M.S. and Ph.D. in geosciences from Texas Tech University. His research interests include carbonate diagenesis, clay mineralogy, and their implications in well log analysis. He has authored several published technical articles on the Permian San Andres and Pennsylvanian Cross Cut formations of west Texas, and he is a member of the AAPG, Society for Sedimentary Geology, and Society of Petrophysicists and Well Log Analysts.

viii

# Preface to Basic Well Log Analysis

Formation evaluation (or well log analysis or petrophysics) is at the intersection of a number of disciplines, including, but not limited to, geology, geophysics, and reservoir engineering. Each discipline that encounters and uses well log data does so from its own perspective. In doing so, each discipline sometimes uses the data without a full understanding of how the measurements are made. That incomplete understanding can encompass the processing of the actual measurements into the raw data provided by the data logging companies and to the interpretation methods that convert that data into usable information about the subsurface. It is this incomplete understanding of well log data that commonly produces conflicting interpretations from different sources, when the goal should be a single cohesive model of the subsurface that can be consistently applied by all disciplines.

This book is a revision of George Asquith’s *Basic Well Log Analysis for Geologists*, of one of the most popular books published by the American Association of Petroleum Geologists (AAPG). It does not claim to provide all information about well logs from all perspectives. Like the original publication, it remains focused on the interpretation of basic, or common openhole logging measurements. It also remains focused on the traditional interpretive goals of formation porosity, fluid saturation, and lithology.

The impetus for this revised text was a perception that an update was needed to address the technologies that had been introduced in the two decades since the original publication. We have endeavored to do so, from inclusion of the photoelectric effect ($P_e$ or PEF) curve of the newest-generation density tools, to chapters specifically addressing nuclear magnetic resonance (NMR) logging (by Steven Henderson) and borehole imaging (by Neil Hurley).

Accompanying this book is a CD, which you will find attached to the inside back cover. The CD contains 10 data-based files so that readers of this book will be able to practice the techniques described in the book.

The authors hope that this introductory text will lead the readers to seek other sources on well logs and well log interpretation, which will lead to a deeper and broader understanding of formation evaluation. George Asquith’s Preface to the original publication (reproduced in this edition) still rings true; an understanding of the data and the discipline still comes primarily from the hands-on application of the information and methods shown here, and in other sources. If you have read this far, take the time to read that Preface as well.

There are many resources for petrophysical data. We hesitate to list specific sources here, especially online sources as websites can appear, change, and disappear quickly. Two good (and stable) sources for information (electronic and hardcopy) are the Society of Petrophysicists and Well Log Analysts (SPWLA) and the American Association of Petroleum Geologists (AAPG).

ix

# Preface to Basic Well Log Analysis for Geologists

This book is a basic introduction to open hole logging.

Study of the properties of rocks by petrophysical techniques using electric, nuclear, and acoustical sources is as important to a geologist as the study of rock properties by more conventional means using optical, x-ray, and chemical methods. Nevertheless, despite the importance of petrophysics, it is frequently underutilized by many geologists who are either intimidated by logging terminology and mathematics, or who accept the premise that an in-depth knowledge of logging is only marginally useful to their science because, they feel, it more properly belongs in the province of the log analyst or engineer.

The enormous importance of logging dictates that as geologists, we put aside old notions and apply ourselves diligently to learning log interpretation. The rewards are obvious; in fact, no less than achieving an understanding of the ancient record hangs in the balance. And, it is likely that the success or failure of an exploration program may hinge on a geologist’s logging expertise.

In the interest of conciseness, and so that logs used most often in petroleum exploration are thoroughly discussed, the text is restricted to open hole logs. I hope that the reader initiates his or her own study of other log types which are beyond the scope of this book.

Unfortunately, learning about open hole logging requires more of the reader than a light skimming of the text’s material. The plain truth is that a great deal of hard work, including memorizing log terminology, awaits the serious student; and even then, a facility with logs develops only after plenty of real-life experience. The intent here is simply to provide a foundation of knowledge which can be built upon later. Consequently, many exceptions to rules are left to more advanced books.

It is quite possible that some colleagues will raise objections about the lack of time devoted to tool theory; they may also comment on the paucity of qualifying statements in the text. These objections are understood and indeed there may be disagreements about what constitutes over-simplification. In defense of brevity, it should be pointed out that the surfeit of information available on petrophysics often discourages all but the most ardent beginner. Certainly, many of the difficult decisions which had to be faced in preparing the manuscript dealt with selecting information judged indispensable at an elementary level.

Many in the audience will note frequent references to a book by Douglas Hilchie, Golden, Colorado, entitled *Applied Open Hole Log Interpretation* (1978). For those who are interested in expanding their knowledge of logs, his book will be a great help. Another helpful book is *The Glossary of Terms and Expressions Used in Well Logging*, The Society of Professional Well Log Analysts (1975), which explains the meaning of logging terms by extended definitions.

Finally, a last word — a substantial effort was expended to ensure that a minimum number of errors would appear in the text. However, given the nature of the subject and the almost infinite possibility for mistakes, there may be slip-ups, regardless; hopefully they will not be too serious.

**George B. Asquith**  
 **Pioneer Production Corporation**  
 **Amarillo, Texas**  
 **October, 1982**

1

Asquith, G., and D. Krygowski, 2004, Basic Relationships of Well Log Interpretation, in G. Asquith and D. Krygowski, Basic Well Log Analysis: AAPG Methods in Exploration 16, p. 1–20.

# Basic Relationships of Well Log Interpretation

## INTRODUCTION

This chapter provides a general introduction to well logging principles and methods that will be used throughout the book. Succeeding chapters (2 through 6) introduce the reader to specific log types. The text discusses how different log types measure various properties in the wellbore and surrounding formations, what factors affect these measurements, where on a standard log display a particular curve is recorded, and how interpreted information is obtained from the logs using both charts and mathematical formulas. Unlike many other logging texts, the logging tools are grouped according to their primary interpretation target, rather than their underlying measurement physics.

Spontaneous potential (SP) and gamma ray logs are discussed first, as their primary use is correlation and their primary interpretive target is gross lithology (the distinction between reservoir and nonreservoir). The porosity logs (i.e., sonic, density, and neutron logs) are covered next, then the resistivity logs. Nuclear magnetic-resonance logs, although they provide porosity (among other quantities of interest), are presented after resistivity logs. This is due in part to their recent arrival and to their relative absence in historical data archives.

The final four chapters again deal with interpretation of the data, this time in detail with example problems and their solutions. These chapters bring the introductory material of Chapter 1 together with the specific measurement information and are intended to provide a coherent view of the interpretation process. The reader is encouraged to work the examples to gain familiarity with the interpretation techniques and to begin to understand the limitations on interpretation that are present due to the nature of subsurface information.

The use of charts and simple calculations throughout the text, rather than the use of petrophysical com-

puter software, is intentional. It is only through experience with such manual methods that the reader can gain an appreciation for the effects of parameters on the calculations, and gain a better understanding of the accuracy and precision of the techniques discussed here.

When the first edition of this book was published, virtually all well-logging data were acquired through the use of wireline-conveyed tools; that is, logging tools lowered in the borehole on a 7-conductor cable over which power, operating instructions, and data were sent. Since the mid-1980s, a second formation-evaluation technique, measurement while drilling (MWD) or logging while drilling (LWD), has developed. In this method, the logging sensors are imbedded in the thick-walled drill collars used at the bottom of the drill string (near the bit), and measurement of formation properties is done continuously during the drilling process (hence the name, MWD). Initially, MWD logging technology borrowed heavily from wireline technology, with the goal being to produce LWD measurements comparable to wireline measurements. As LWD technology has progressed, sensor design and other features of LWD have been incorporated back into wireline technology, for the improvement of those measurements.

Unless specifically noted in the text, the interpretation of borehole data is the same irrespective of the source of the data, either wireline or LWD sensors and measurement systems. The techniques shown here are applicable to both data sources and can even be extended to incorporate equivalent core measurements.

## GENERAL

As logging tools and interpretive methods are developing in accuracy and sophistication, they are playing an expanded role in the geological decision-

1

2

ASQUITH AND KRYGOWSKI

making process. Today, petrophysical log interpretation is one of the most useful and important tools available to a petroleum geologist.

Besides their traditional use in exploration to correlate zones and to assist with structure and isopach mapping, logs help define physical rock characteristics such as lithology, porosity, pore geometry, and permeability. Logging data are used to identify productive zones, to determine depth and thickness of zones, to distinguish between oil, gas, or water in a reservoir, and to estimate hydrocarbon reserves. Also, geologic maps developed from log interpretation help with determining facies relationships and drilling locations. Increasingly, the importance of petrophysics and well-log analysis is becoming more evident as more attention is being devoted to the ongoing management of reservoirs. The industry is realizing the importance of detailed petrophysical analyses, based on the details of the available data in monitoring, simulating, and enhancing reservoir performance to maximize the return on investment.

Of the various types of logs, the ones used most frequently in hydrocarbon exploration are called open-hole logs. The name open hole is applied because these logs are recorded in the uncased portion of the wellbore. All the different types of logs and their curves discussed in this text are of this type.

A geologist's first exposure to log interpretation can be a frustrating experience. This is not only because of its lengthy and unfamiliar terminology, but also because knowledge of many parameters, concepts, and measurements is needed before an understanding of the logging process is possible.

Perhaps the best way to begin a study of logging is by introducing the reader to some of the basic concepts of well log analysis. Remember that a borehole represents a dynamic system; that fluid used in the drilling of a well affects the rock surrounding the borehole and, therefore, log measurements. In addition, the rock surrounding the borehole has certain properties that affect the movement of fluids into and out of it.

The two primary parameters determined from well log measurements are porosity and the fraction of pore space filled with hydrocarbons (i.e., hydrocarbon saturation). The parameters of log interpretation are determined directly or inferred indirectly and are measured by one of three general types of logs:

- electrical
- nuclear
- acoustic or sonic logs

The names refer to the sources used to obtain the measurements. The different sources create records (logs), which contain one or more curves related to

some property in the rock surrounding the wellbore (see Society of Professional Well Log Analysts, 1984). For the reader unfamiliar with petrophysical logging, some confusion may develop over the use of the word log. In common usage, the word log may refer to a particular curve, a suite or group of curves, the physical (paper) record of the measurements, a logging tool (sonde), or the process of logging.

Rock properties or characteristics that affect logging measurements are: porosity, lithology, mineralogy, permeability, and water saturation. Additionally, the resistivity of the rock is important because it is directly measured and is an essential part in the interpretation process. It is essential that the reader understand these properties and the concepts they represent before proceeding with a study of log interpretation.

### Porosity

Porosity can be defined as the ratio of voids to the total volume of rock. It is represented as a decimal fraction or as a percentage and is usually represented by the Greek letter phi, φ.

$$\text{porosity, } \phi = \frac{\text{volume of pores}}{\text{total volume of rock}} \tag{1.1}$$

The amount of internal space or voids in a given volume of rock is a measure of the amount of fluid a rock will hold. This is illustrated by Equation 1.1 and is called the total porosity. The amount of void space that is interconnected, and thus able to transmit fluids, is called effective porosity. Isolated pores and pore volume occupied by adsorbed water are excluded from a definition of effective porosity but are included in the definition of total porosity.

### Lithology and Mineralogy

In well-log analysis, the terms lithology and mineralogy are used with some ambiguity. Lithology is often used to describe the solid (matrix) portion of the rock, generally in the context of a description of the primary mineralogy of the rock (e.g., a sandstone as a description of a rock composed primarily of quartz grains, or a limestone composed primarily of calcium carbonate). In the early days of log interpretation (with limited measurements), this was usually a sufficient description. Probably the first instances of lithologic effects on the logs were observed in shaly or clay-containing sandstones. With the advent of multiple porosity measurements and the development of more detailed interpretive methods, it has become possible to estimate the primary solid constituents, normally as a mineral pair or triad.

Basic Relationships of Well Log Interpretation

3

The literature has tended to follow the improved understanding of the constitution of the solid part of the formations of interest, with most current literature referring to the determination of *mineralogy* instead of *lithology*. When one considers the physics of logging measurements, the ambiguity continues. Some measurements (primarily nuclear) are made as the result of molecular-level interactions between the formation and the logging tool. These might be considered as being affected by the formation’s *mineralogy*. Others, especially the acoustic measurements, interact with the formation on a bulk or framework level, and could be considered to be more affected by *lithology* (S. L. Morriss, 1999, personal communication).

The ambiguity between lithology and mineralogy is best seen in porosity crossplots which, through time, have moved from estimating lithology to estimating mineralogy, while the underlying measurements and interpretive techniques have remained essentially the same.

As noted above, the first lithologic effects were probably due to the presence of clays and shales in formations of interest. One parameter that has been used consistently to account for these effects has been shale volume. As our understanding of geological processes matured, it became understood that *shale* and *clay* were different, and that *shaly sands* were usually not just sands with shales mixed in, but sands that contained clays — clays that could be very different from the clays present in the shales near those sands of interest. Again, the literature and our interpretive techniques often use the terms *shale volume* and *clay volume* interchangeably. In this text, *shale volume* will be used preferentially because most of the interpretive techniques in which the volumes are used derive those volumes from the properties of nearby shales.

## Permeability

Permeability is the ability of a rock to transmit fluids. It is related to porosity but is not always dependent upon it. Permeability is controlled by the size of the connecting passages (pore throats or capillaries) between pores. It is measured in darcys or millidarcys (md) and is represented by the symbol $K$. The ability of a rock to transmit a single fluid, when it is completely saturated with that fluid, is called *absolute permeability*. *Effective permeability* refers to the ability of the rock to transmit one fluid in the presence of another fluid when the two fluids are immiscible.

Formation water (connate water in the formation) held by capillary pressure in the pores of a rock serves to inhibit the transmission of hydrocarbons. Stated dif

differently, formation water takes up space both in pores and in the connecting passages between pores. As a consequence, it may block or otherwise reduce the ability of other fluids to move through the rock.

*Relative permeability* is the ratio between effective permeability of a fluid at partial saturation and the permeability at 100% saturation (absolute permeability). When relative permeability of a formation’s water is zero, the formation produces water-free hydrocarbons (i.e., the relative permeability to hydrocarbons is 100%). *With increasing relative permeabilities to water, the formation produces increasing amounts of water relative to hydrocarbons.*

## Water Saturation

Water saturation is the amount of pore volume in a rock that is occupied by formation water. It is represented as a decimal fraction or as a percentage and has the symbol $S_w$.

$$
\text{water saturation, } S_w = \frac{\text{formation water occupying pores}}{\text{total pore space in the rock}} \quad 1.2
$$

Although hydrocarbon saturation is the quantity of interest, water saturation is usually used because of its direct calculation in equations such as Archie’s equation, discussed in a later section in this chapter. Hydrocarbon saturation is usually determined by the difference between unity and water saturation:

$$
S_h = 1 - S_w \tag{1.3}
$$

*Irreducible water saturation* or $S_w$ is the term used to describe the water saturation at which all the water is adsorbed on the grains in a rock or is held in the capillaries by capillary pressure. At irreducible water saturation, water does not move and the relative permeability to water is zero.

## Resistivity

Resistivity is the rock property on which the entire science of logging first developed. Resistivity is the inherent property of all materials, regardless of their shape and size, to resist the flow of an electric current. Different materials have different abilities to resist the flow of electricity.

While the resistance of a material depends on its shape and dimensions, the resistivity is an invariant property; the reciprocal of resistivity is conductivity. In log interpretation, the hydrocarbons, the rock, and the fresh water of the formation are all assumed to act

4

ASQUITH AND KRYGOWSKI

as insulators and are, therefore, nonconductive (or at least very highly resistive) to electric current flow. Salt water, however, is a conductor and has a low resistivity. The measurement of resistivity is then a measurement, albeit indirect, of the amount (and salinity) of the formation water. The unit of measure used for the conductor is a cube of the formation, one meter on each edge. The measured units are ohm-meters²/meter and are called ohm-meters.

$$R = \frac{r \times A}{L} \tag{1.4}$$

where:

$R$ = resistivity (ohm-m)

$r$ = resistance (ohms)

$A$ = cross-sectional area of substance being measured (m²)

$L$ = length of substance being measured (m)

Resistivity is a basic measurement of a reservoir's fluid saturation and is a function of porosity, type of fluid (i.e., hydrocarbons, salt water, or fresh water), amount of fluid, and type of rock. Because both the rock and hydrocarbons act as insulators but salt water is conductive, resistivity measurements made by logging tools can be used to detect hydrocarbons and estimate the porosity of a reservoir. During the drilling of a well, fluids move into porous and permeable formations surrounding a borehole, so resistivity measurements recorded at different distances into a formation often have different values. Resistivity is measured by electric logs, commonly known (in the West) as laterologs and induction logs.

Conrad Schlumberger in 1912 began the first experiments which led, eventually, to the development of modern-day petrophysical logs. The first electric log was run September 5, 1927, by H. G. Doll in Alsace-Lorraine, France. In 1941, G. E. Archie with Shell Oil Company presented a paper to the AIME in Dallas, Texas, which set forth the concepts used as a basis for modern quantitative log interpretation (Archie, 1942).

Archie's experiments showed that the resistivity of a water-filled formation ($R_o$) could be related to the resistivity of the water ($R_w$) filling the formation through a constant called the formation resistivity factor ($F$):

$$R_o = F \times R_w \tag{1.5}$$

Archie's experiments also revealed that the formation factor ($F$) could be related to the porosity of the formation by the following formula:

$$F = \frac{a}{\phi^m} \tag{1.6}$$

where $m$ is the cementation exponent whose value varies with grain size, grain-size distribution, and the complexity of the paths between pores (tortuosity), and $a$ is the tortuosity factor. The higher the tortuosity of the formation, the higher the value of $m$. The tortuosity factor ($a$) is commonly set to 1.0, but is allowed to vary by some petrophysicists.

Water saturation ($S_w$) is determined from the water-filled resistivity ($R_o$) and the actual (true) formation resistivity ($R_t$) by the following relationship:

$$S_w = \left(\frac{R_o}{R_t}\right)^{\frac{1}{n}} \tag{1.7}$$

where $n$ is the saturation exponent, whose value typically varies from 1.8 to 2.5 but is most commonly assumed to be 2.

By combining equations 1.6 and 1.7, the water-saturation formula can be rewritten in the following form:

$$S_w = \left(\frac{F \times R_w}{R_t}\right)^{\frac{1}{n}} \tag{1.8}$$

This is the formula that is most commonly referred to as the Archie equation for water saturation ($S_w$). All present methods of interpretation involving resistivity curves are derived from this equation. In its most general form, Archie's equation becomes:

$$S_w = \left(\frac{a \times R_w}{R_t \times \phi^m}\right)^{\frac{1}{n}} \tag{1.9}$$

Table 1.1 illustrates the range of values for $a$ and $m$. In first-pass or reconnaissance-level interpretations, or where there is no knowledge of the local parameters, the following values can be used to achieve an initial estimate of water saturation:

$$a = 1.0; \ m = n = 2.0$$

Now that the reader is introduced to some of the basic concepts of well log interpretation, our discussion can continue in more detail about the factors that affect logging measurements.

### BOREHOLE ENVIRONMENT

Where a hole is drilled into a formation, the rock plus the fluids in it (the rock-fluid system) are altered in the vicinity of the borehole. The borehole and the rock surrounding it are contaminated by the drilling mud, which affects logging measurements. Figure 1.1

Basic Relationships of Well Log Interpretation

5

Table 1.1. Different coefficients and exponents used to calculate formation factor (F). (Modified after Asquith, 1980.)

|  a: Tortuosity factor | m: Cementation exponent | Comments  |
| --- | --- | --- |
|  1.0 | 2.0 | Carbonates^{1}  |
|  0.81 | 2.0 | Consolidated sandstones^{1}  |
|  0.62 | 2.15 | Unconsolidated sands (Humble formula)^{1}  |
|  1.45 | 1.54 | Average sands (after Carothers, 1968)  |
|  1.65 | 1.33 | Shaly sands (after Carothers, 1968)  |
|  1.45 | 1.70 | Calcareous sands (after Carothers, 1968)  |
|  0.85 | 2.14 | Carbonates (after Carothers, 1968)  |
|  2.45 | 1.08 | Pliocene sands, southern California (after Carothers and Porter, 1970)  |
|  1.97 | 1.29 | Miocene sands, Texas–Louisiana Gulf Coast (after Carothers and Porter, 1970)  |
|  1.0 | φ^{(2.05-φ)} | Clean granular formations (after Sethi, 1979)  |

1Most commonly used

is a schematic illustration of a porous and permeable formation that is penetrated by a borehole filled with drilling mud.

Some of the more important symbols shown in Figure 1.1 are:

## Hole Diameter ($d_h$)

The borehole size is determined by the outside diameter of the drill bit. But, the diameter of the borehole may be

- larger than the bit size because of washout and/or collapse of shale and poorly cemented porous rocks, or
- smaller than the bit size because of a build up of mud cake on porous and permeable formations (Figure 1.1).

Common borehole sizes normally vary from 7-7/8 in. to 12 in., and modern logging tools are designed to operate within these size ranges. The size of the borehole is measured by a caliper log.

## Drilling mud Resistivity ($R_m$)

Today, most wells are drilled with rotary bits and the use of a special fluid, called drilling mud, as a circulating fluid. The mud helps remove cuttings from the wellbore, lubricate and cool the drill bit, and maintain an excess of borehole pressure over formation pressure. The excess of borehole pressure over formation

tion pressure prevents blowouts. The density of the mud is usually kept high enough so that hydrostatic pressure in the mud column is greater than formation pressure. This pressure difference forces some of the drilling fluid to invade porous and permeable formations. As invasion occurs, many of the solid particles (i.e., clay minerals from the drilling mud) are trapped on the side of the borehole and form mud cake (having a resistivity of $R_{mc}$; Figure 1.1). Fluid that filters into the formation during invasion is called mud filtrate (with a resistivity of $R_{mf}$; Figure 1.1). The resistivity values for drilling mud, mud cake, and mud filtrate are recorded on a log's header (Figure 1.2), and are used in interpretation.

## Invaded Zone

The zone in which much of the original fluid is replaced by mud filtrate is called the invaded zone. It consists of a flushed zone (of resistivity $R_{so}$) and a transition or annulus zone (of resistivity $R_i$). The flushed zone occurs close to the borehole (Figure 1.1) where the mud filtrate has almost completely flushed out a formation's hydrocarbons and/or water ($R_w$). The transition or annulus zone, where a formation's fluids and mud filtrate are mixed, occurs between the flushed zone and the uninvaded zone (of resistivity $R_t$). The uninvaded zone is defined as the area beyond the invaded zone where a formation's fluids are uncontaminated by mud filtrate.

The depth of mud-filtrate invasion into the invaded

6

ASQUITH AND KRYGOWSKI

zone is referred to as diameter of invasion ($d_i$ and $d_j$; Figure 1.1). The diameter of invasion is measured in inches or expressed as a ratio: $d_j/d_h$ (where $d_h$ represents the borehole diameter). The amount of invasion that takes place is dependent upon the permeability of the mud cake and not upon the porosity of the rock. In general, an equal volume of mud filtrate can invade low-porosity and high-porosity rocks if the drilling muds have equal amounts of solid particles. The solid particles in the drilling muds coalesce and form an impermeable mud cake. The mud cake then acts as a barrier to further invasion. Because an equal volume of fluid can be invaded before an impermeable mud-cake barrier forms, the diameter of invasion is greatest in low-porosity rocks. This occurs because low-porosity rocks have less storage capacity or pore volume to fill with the invading fluid, and, as a result, pores throughout a greater volume of rock are affected. General invasion diameters in permeable formations are

$d_j/d_h = 2$, for high-porosity rocks;

$d_j/d_h = 5$, for intermediate-porosity rocks; and

$d_j/d_h = 10$, for low-porosity rocks.

## Flushed zone Resistivity ($R_{xo}$)

The flushed zone extends only a few inches from the wellbore and is part of the invaded zone. If invasion is deep or moderate, most often the flushed zone is completely cleared of its formation water by mud filtrate (of resistivity $R_{mf}$). When oil is present in the flushed zone, the degree of flushing by mud filtrate can be determined from the difference between water saturations in the flushed ($S_{xo}$) zone and the uninvaded ($S_w$) zone (Figure 1.1). Usually, about 70% to 95% of the oil is flushed out; the remaining oil is called residual oil [$S_{ro} = (1.0 - S_{xo})$, where $S_{ro}$ is the residual oil saturation, (ROS)].

## Uninvaded zone Resistivity ($R_t$)

The uninvaded zone is located beyond the invaded zone (Figure 1.1). Pores in the uninvaded zone are uncontaminated by mud filtrate; instead, they are saturated with formation water ($R_w$), oil, and/or gas.

Even in hydrocarbon-bearing reservoirs, there is always a layer of formation water on grain surfaces. Water saturation ($S_w$; Figure 1.1) of the uninvaded zone is an important factor in reservoir evaluation because, by using water saturation data, a geologist can determine a reservoir's hydrocarbon saturation. Equation 1.3 expresses the calculation and is repeated here:

$$
S_h = 1 - S_w
$$

where:

$S_h =$ hydrocarbon saturation (i.e., the fraction of pore volume filled with hydrocarbons).

$S_w =$ water saturation of the uninvaded zone (i.e., the fraction of pore volume filled with water).

The ratio of the uninvaded zone's water saturation ($S_w$) to the flushed zone's water saturation ($S_{xo}$) is an index of hydrocarbon moveability.

## INVASION AND RESISTIVITY PROFILES

Invasion and resistivity profiles are diagrammatic, theoretical, cross-sectional views of subsurface conditions moving away from the borehole and into a formation. They illustrate the horizontal distributions of the invaded and uninvaded zones and their corresponding relative resistivities. There are three commonly recognized invasion profiles:

- step
transition
annulus

These three invasion profiles are illustrated in Figure 1.3.

The step profile has a cylindrical geometry with an invasion diameter equal to $d_j$. Shallow-reading resistivity logging tools read the resistivity of the invaded zone ($R_i$), while deeper reading resistivity logging tools read true resistivity of the uninvaded zone ($R_t$).

The transition profile also has a cylindrical geometry with two invasion diameters: $d_j$ (flushed zone) and $d_j$ (transition zone). It is probably a more realistic model for true borehole conditions than is the step profile. At least three resistivity measurements, each sensitive to a different distance away from the borehole, are needed to measure a transitional profile. These three measure resistivities of the flushed ($R_{xo}$), transition ($R_t$), and uninvaded zones ($R_t$) (see Figure 1.3). By using these three resistivity measurements, the deep reading resistivity measurement can be corrected to a more accurate value of true resistivity ($R_t$), and the depth of invasion can be determined.

This ability to estimate the invasion in a formation arrived with the wide introduction of the dual induction and dual laterolog tools in the 1960s. As the names imply, each tool made two induction or two laterolog measurements. These two measurements investigate different distances into the formation and are referred to as *medium* and *deep* measurements. The word *dual* in the names of these logging tools can be

Basic Relationships of Well Log Interpretation

7

confusing, because each tool also made a third measurement, which was shallower than the medium and deep measurements. In the 1980s, *array* resistivity tools made their appearance. Through the use of more sensors, they investigate more distances into the formation (usually 5 to 7), which provides for a more detailed picture of the formation and its invasion.

An annulus profile is only sometimes recorded on a log, because it rapidly dissipates in a well. The annulus profile is detected only by an induction log run soon after a well is drilled. However, it is very important to a geologist, because the profile can only occur in zones that bear hydrocarbons. As the mud filtrate invades the hydrocarbon-bearing zone, the hydrocarbons are moved out first. Next, formation water is pushed out in front of the mud filtrate, forming an annular (circular) ring at the edge of the invaded zone (Figure 1.3). The annulus effect is detected by a higher resistivity reading on a deep induction log than by one on a medium induction log.

Log resistivity profiles illustrate the resistivity values of the invaded and uninvaded zones in the formation being investigated. They are of particular interest because, by using them, a geologist can quickly scan a log and look for potential zones of interest such as hydrocarbon zones. Because of their importance, resistivity profiles for both water-bearing and hydrocarbon-bearing zones are discussed here. These profiles vary, depending on the relative resistivity values of $R_w$ and $R_{mf}$. All the variations and their associated profiles are illustrated in Figures 1.4 and 1.5.

## Water-bearing Zones

Figure 1.4 illustrates the borehole and resistivity profiles for water-bearing zones where the resistivity of the mud filtrate ($R_{mf}$) for a freshwater mud is much greater than the resistivity of the formation water ($R_w$), and where resistivity of the mud filtrate ($R_{mf}$) for a saltwater mud is approximately equal to the resistivity of the formation water ($R_w$). A freshwater mud (i.e., $R_{mf} > 3 R_w$) results in a *wet* log profile where the shallow ($R_{xo}$), medium ($R_i$), and deep ($R_t$) resistivity measurements separate and record high ($R_{xo}$), intermediate ($R_i$), and low ($R_t$) resistivities (Figure 1.4). A saltwater mud (i.e., $R_w = R_{mf}$) results in a wet profile where the shallow ($R_{xo}$), medium ($R_i$), and deep ($R_t$) resistivity measurements all read low resistivity (Figure 1.4). Figures 1.6 and 1.7 illustrate the resistivity curves for wet zones invaded with either freshwater or saltwater mud.

## Hydrocarbon-bearing Zones

Figure 1.5 illustrates the borehole and resistivity profiles for hydrocarbon-bearing zones where the resistivity of the mud filtrate ($R_{mf}$) for a freshwater mud is much greater than the resistivity of the formation water ($R_w$), and where $R_{mf}$ of a saltwater mud is approximately equal to $R_w$. A hydrocarbon zone invaded with freshwater mud results in a resistivity profile where the shallow ($R_{xo}$), medium ($R_i$), and deep ($R_t$) resistivity measurements all record high resistivities (Figure 1.5). In some instances, the deep resistivity is higher than the medium resistivity. When this happens, it is called the annulus effect. A hydrocarbon zone invaded with saltwater mud results in a resistivity profile where the shallow ($R_{xo}$), medium ($R_i$), and deep ($R_t$) resistivity measurements separate and record low ($R_{xo}$), intermediate ($R_i$) and high ($R_t$) resistivities (Figure 1.5). Figures 1.8 and 1.9 illustrate the resistivity curves for hydrocarbon zones invaded with either freshwater or saltwater mud.

## BASIC INFORMATION NEEDED IN LOG INTERPRETATION

### Lithology

In quantitative log analysis, there are several reasons why it is important to know the lithology of a zone (i.e., sandstone, limestone, or dolomite). Porosity logs require a lithology or a matrix constant before the porosity ($\phi$) of the zone can be calculated. The formation factor ($F$), a variable used in the Archie water-saturation equation, also varies with lithology. As a consequence, the calculated water saturation changes as $F$ changes. Table 1.1 is a list of several different values for calculating formation factor and illustrates how lithology affects the formation factor.

### Formation Temperature

Formation temperature ($T_f$) is also important in log analysis, because the resistivities of the drilling mud ($R_m$), the mud filtrate ($R_{mf}$), and the formation water ($R_w$) vary with temperature. The temperature of a formation is determined by knowing:

formation depth
- bottom hole temperature (BHT)
- total depth of the well (TD)
- surface temperature

8

ASQUITH AND KRYGOWSKI

A reasonable value for the formation temperature can be determined by using these data and by assuming a linear geothermal gradient (Figure 1.10). The formation temperature is also calculated (Asquith, 1980) by using the linear regression equation:

$$y = mx + c \tag{1.10}$$

where:

$x =$ depth

$y =$ temperature

$m =$ slope (In this example it is the geothermal gradient.)

$c =$ a constant (In this example it is the mean annual surface temperature.)

An example of how to calculate formation temperature is illustrated here:

### Temperature Gradient Calculation

Assume that:

$y =$ bottom hole temperature (BHT) = 250°F

$x =$ total depth (TD) = 15,000 ft

$c =$ mean annual surface temperature = 70°F

Solve for $m$ (i.e., slope or temperature gradient):

$$m = \frac{y - c}{x}$$

Therefore,

$$m = \frac{250^\circ - 70^\circ}{15,000 \text{ ft}}$$

$$m = 0.012^\circ/\text{ft or } 1.2^\circ/100 \text{ ft}$$

### Formation Temperature Calculation

Assume:

$m =$ temperature gradient = 0.012°/ft

$x =$ formation depth = 8,000 ft

$c =$ surface temperature = 70°

Remember:

$$y = mx + c$$

Therefore:

$$y = (0.012 \times 8,000) + 70$$

$y = 166^\circ$ formation temperature at 8,000 ft

After a formation's temperature is determined either by chart (Figure 1.10) or by calculation, the resistivities of the different fluids ($R_m$, $R_{mf}$, or $R_w$) can be corrected to formation temperature. Figure 1.11 is a chart that is used for correcting fluid resistivities to the formation temperature. This chart is closely approximated by the Arp's formula:

$$R_{TF} = \frac{R_{temp}(Temp + 6.77)}{(T_f + 6.77)} = \left( \frac{R_{temp}(Temp + 21.0)}{(T_f + 21.0)} \text{ for depth in meters} \right) \tag{1.10}$$

where:

$R_{TF} =$ resistivity at formation temperature

$R_{temp} =$ resistivity at a temperature other than formation temperature

$Temp =$ temperature at which resistivity was measured (usually Fahrenheit for depth in feet, Celsius for depth in meters)

$T_f =$ formation temperature (usually Fahrenheit for depth in feet, Celsius for depth in meters)

Using a formation temperature of 166°F and assuming an $R_w$ of 0.04 measured at 70°F, the $R_w$ at 166°F is:

$$R_{w166} = 0.04 \times (70 + 6.77) / (166 + 6.77)$$

$$R_{w166} = 0.018 \text{ ohm-m}$$

Resistivity values of the drilling mud ($R_m$), mud filtrate ($R_{mf}$), mud cake ($R_{mc}$), and the temperatures at which they are measured are recorded on a log's header (Figure 1.2). The resistivity of a formation's water ($R_w$) is obtained by analysis of water samples from a drill stem test, a water-producing well, or from a catalog of water resistivity values. Formation water resistivity ($R_w$) is also determined from the spontaneous-potential log (discussed in Chapter 2), or it can be calculated in water zones (i.e., where $S_w=1$) by the apparent water resistivity ($R_{wa}$) method (see Chapter 7).

### COMMON EQUATIONS

Table 1.2 is a list of common equations that are used for the log evaluation of potential hydrocarbon reservoirs. These formulas are discussed in detail in subsequent chapters.

Basic Relationships of Well Log Interpretation

9

Table 1.2. Common equations of well-log interpretation

Porosity, $\phi$:

$$\phi_{Sonic} = \frac{\Delta t_{log} - \Delta t_{matrix}}{\Delta t_{fluid} - \Delta t_{matrix}}$$

Sonic log porosity

(Wyllie time-average equation)

$$\phi_{Sonic} = \frac{5}{8} \times \left( \frac{\Delta t_{log} - \Delta t_{matrix}}{\Delta t_{log}} \right)$$

Sonic log porosity

(Raymer-Hunt-Gardner equation)

$$\phi_{Density} = \frac{\rho_{matrix} - \rho_{bulk(log)}}{\rho_{matrix} - \rho_{fluid}}$$

Density log porosity

$$\phi_{NDgas} = \sqrt{\frac{\phi_N^2 + \phi_D^2}{2}}$$

Porosity in a gas zone

from neutron and density

Formation factor, $F$:

$$F = a/\phi^m$$

General form of the equation

$$F = 1.0/\phi^{2.0}$$

Carbonates

$$F = 0.81/\phi^{2.0}$$

Consolidated sandstones

$$F = 0.62/\phi^{2.15}$$

Unconsolidated sands

Formation-water resistivity:

$$SSP = -K \times \log(R_{mf}/R_w)$$

Basic SP response equation

$$R_w = 10^{(K \times \log(R_{mf}) + SP)/K}$$

First-order approximation

of $R_w$ from the SP

Water saturation:

$$S_w = \left( \frac{a \times R_w}{R_s \times \phi^m} \right)^{\frac{1}{n}}$$

Water saturation in

the uninvaded zone

$$S_{so} = \left( \frac{a \times R_{mf}}{R_{so} \times \phi^m} \right)^{\frac{1}{n}}$$

Water saturation in the

flushed zone

$$S_w = \left( \frac{R_{so}/R_s}{R_{mf}/R_w} \right)^{0.625}$$

Water saturation,

ratio method

Bulk volume water:

$$BVW = \phi \times S_w$$

Permeability (estimated):

$$K_e = \left( 250 \times \left( \frac{\phi^3}{S_{wirr}} \right) \right)^2$$

Permeability in

millidarcys, oil

reservoir

$$K_e = \left( 79 \times \left( \frac{\phi^3}{S_{wirr}} \right) \right)^2$$

Permeability in

millidarcys, gas

reservoir

10

ASQUITH AND KRYGOWSKI

# REVIEW

1. The four most fundamental rock properties used in petrophysical logging are:

- porosity
- permeability
- water saturation
- lithology

2. The Archie equation for water saturation is:

$$S_{w} = \left( \frac{a \times R_{w}}{R_{t} \times \phi^{m}} \right)^{\frac{1}{m}}$$

where:

$S_{w}$ = water saturation of uninvaded zone

$R_{w}$ = formation water resistivity

$R_{t}$ = formation resistivity (uninvaded zone)

$\phi$ = porosity

$a$ = tortuosity factor

$m$ = cementation exponent

$n$ = saturation exponent

3. Where a porous and permeable formation is penetrated by the drill bit, the liquid part of the drilling mud invades the formation as mud filtrate. The mud filtrate resistivity is designated $R_{mf}$.

4. The invasion of a porous and permeable forma-

tion by mud filtrate creates invaded zones around the wellbore. Shallow-, medium-, and deep-reading resistivity measurements provide information about the invaded and uninvaded zones and about the depth of invasion of the drilling fluid.

5. The lithology of a formation must be known because:

- A matrix value (usually sandstone, limestone, or dolomite) is needed to determine porosity from logs.

- The formation factor varies with lithology.

- The variation in the formation factor changes the water-saturation values.

6. The four fluids (and the symbols for their resistivity) that affect logging measurements are:

- drilling mud ($R_{m}$)

- mud filtrate ($R_{mf}$)

- formation water ($R_{w}$)

- hydrocarbons (assumed infinite resistivity, no symbol)

7. The resistivities of the drilling mud ($R_{m}$), mud cake ($R_{mc}$), mud filtrate ($R_{mf}$) and formation water ($R_{w}$) all vary with changes in temperature. Consequently, a formation's temperature ($T_{f}$) must be determined and all resistivities corrected to $T_{f}$.

Basic Relationships of Well Log Interpretation 11

![img-0.jpeg](img-0.jpeg)

Courtesy Schlumberger Wireline & Testing, ©1998 Schlumberger

Figure 1.1. The borehole environment and symbols used in log interpretation.

This schematic diagram illustrates an idealized version of what happens when fluids from the borehole invade the surrounding rock. Dotted lines indicate the cylindrical nature of the invasion.

$d_h$ = hole diameter
$d_t$ = diameter of invaded zone (inner boundary of flushed zone)
$d_j$ = diameter of invaded zone (outer boundary of invaded zone)
$\Delta r_j$ = radius of invaded zone (outer boundary)
$h_{mc}$ = thickness of mud cake
$R_m$ = resistivity of the drilling mud
$R_{mc}$ = resistivity of the mud cake
$R_{mf}$ = resistivity of mud filtrate
$R_s$ = resistivity of the overlying bed (commonly assumed to be shale)
$R_t$ = resistivity of uninvaded zone (true formation resistivity)
$R_w$ = resistivity of formation water
$R_{so}$ = resistivity of flushed zone
$S_w$ = water saturation of uninvaded zone
$S_{so}$ = water saturation flushed zone

![img-1.jpeg](img-1.jpeg)

Figure 1.2. Reproduction of a typical log heading.

This is the first page of a typical log heading. Following pages contain details of the logging equipment used, the scales used to display the data, general information about the borehole direction, remarks about the logging job, and a disclaimer which outlines the responsibilities of both the acquisition company and the client.

1. The title indicates the services that are associated with the data that appear on this log.
2. Basic well name and location information.
3. More detailed information about the physical surface location of the well.
4. Other services that were run at the same time (during the same trip to the well) as the services in this log.
5. Information about location and elevation from which the well depths are measured. K.B. = kelly bushing elevation, D.F. = drill floor elevation, G.L. = ground level elevation, T.K.B. = top of kelly bushing
6. Environmental information about the well. The drilling mud and borehole size values are especially important in applying the proper environmental corrections and interpretation parameters to the data.
7. General information about the logging equipment, the engineer, and any clients who witnessed the logging job. More detailed information about the specific logging tools is listed in the pages that usually follow this one and in tables that detail the calibration techniques and results.

12

ASQUITH AND KRYGOWSKI

Figure 1.3. Resistivity profiles for three idealized versions of fluid distributions in the vicinity of the borehole. As mud filtrate ($R_{\mathrm{mf}}$) moves into a porous and permeable formation, it can invade the formation in several different ways. Various fluid distributions are represented by the step, transition, or annulus profiles. All three profiles illustrate the effect of a freshwater mud; for profiles using saltwater mud see figures 1.4 and 1.5. Mud cake thickness is indicated by $h_{\mathrm{mc}}$.

# Step profile:

This idealized model is the one inferred by the use of three resistivity logs to estimate invasion. Mud filtrate is distributed with a cylindrical shape around the borehole and creates an invaded zone. The cylindrical invaded zone is characterized by its abrupt contact with the uninvaded zone. The diameter of the cylinder is represented as $d_j$. In the invaded zone, pores are filled with mud filtrate ($R_{\mathrm{mf}}$); pores in the uninvaded zone are filled with formation water ($R_{\mathrm{fo}}$) and hydrocarbons. In this example, the uninvaded zone is wet (water saturated and no hydrocarbons), thus the resistivity beyond the invaded zone is low. The resistivity of the invaded zone is $R_{\mathrm{so}}$, and the resistivity of the uninvaded zone is $R_i$ (where $R_i$ reduces to $R_o$ when the formation is water bearing).

# Transition profile:

This is the most realistic model of true borehole conditions. Here again invasion is cylindrical, but in this profile, the invasion of the mud filtrate ($R_{\mathrm{mf}}$) diminishes gradually, rather than abruptly, through a transition zone toward the outer boundary of the invaded zone (see $d_j$ on diagram for location of outer boundary).

In the flushed part ($R_{\mathrm{so}}$) of the invaded zone, pores are filled with mud filtrate ($R_{\mathrm{mf}}$), giving a high resistivity reading. In the transition part of the invaded zone, pores are filled with mud filtrate ($R_{\mathrm{mf}}$), formation water ($R_{\mathrm{fo}}$), and, if present, residual hydrocarbons. Beyond the outer boundary of the invaded zone, pores are filled with either formation water or formation water and hydrocarbons. In this diagram, hydrocarbons are not present, so resistivity of the uninvaded zone is low. The resistivity of the invaded zone is $R_{\mathrm{so}}$, and the resistivity of the uninvaded zone is $R_f$ (where $R_f$ reduces to $R_o$ when the formation is water bearing).

# Annulus profile:

This reflects a temporary fluid distribution and is a condition that should disappear with time (if the lagging operation is delayed, it might not be recorded on the logs at all). The annulus profile represents a fluid distribution that occurs between the invaded zone and the uninvaded zone and only exists in the presence of hydrocarbons.

In the flushed part ($R_{\mathrm{so}}$) of the invaded zone, pores are filled with both mud filtrate ($R_{\mathrm{mf}}$) and residual hydrocarbons. Thus the resistivity reads high. Pores beyond the flushed part of the invaded zone ($R_i$) are filled with a mixture of mud filtrate ($R_{\mathrm{so}}$), formation water ($R_{\mathrm{fo}}$), and residual hydrocarbons.

Beyond the outer boundary of the invaded zone is the annulus zone, where pores are filled with formation water ($R_{\mathrm{fo}}$) and residual hydrocarbons. When an annulus profile is present, there is an abrupt drop in measured resistivity at the outer boundary of the invaded zone. The abrupt resistivity drop is due to the high concentration of formation water ($R_{\mathrm{fo}}$) in the annulus zone. Formation water has been pushed ahead by the invading mud filtrate into the annulus zone. This causes a temporary absence of hydrocarbons, which have been pushed ahead of the formation water.

Beyond the annulus is the uninvaded zone, where pores are filled with formation water ($R_{\mathrm{fo}}$) and hydrocarbons. The resistivity of the invaded zone is $R_{\mathrm{so}}$, and the resistivity of the uninvaded zone is $R_f$ (where $R_f$ reduces to $R_o$ when the formation is water bearing).

![img-2.jpeg](img-2.jpeg)

![img-3.jpeg](img-3.jpeg)

![img-4.jpeg](img-4.jpeg)

Basic Relationships of Well Log Interpretation

13

![img-5.jpeg](img-5.jpeg)

Figure 1.4. Resistivity profile for a transition-style invasion of a water-bearing formation.

Note: These examples are shown because freshwater muds and saltwater muds are used in different geographic regions, usually exclusively. The geologist needs to be aware that a difference exists. To find out which mud is used in your area, check the log heading of existing wells or ask your drilling engineer. The type of mud used affects the log package selected, as will be shown in later chapters.

# Freshwater muds:

The resistivity of the mud filtrate ($R_{mf}$) is greater than the resistivity of the formation water ($R_w$) (remember, saltwater is conductive). A general rule when freshwater muds are used is: $R_{mf} > 3 R_w$. The flushed zone ($R_{so}$), which has a greater amount of mud filtrate, has higher resistivities. Away from the borehole, the resistivity of the invaded zone ($R_i$) decreases due to the decreasing amount of mud filtrate ($R_{mf}$) and the increasing amount of formation water ($R_w$).

With a water-bearing formation, the resistivity of the uninvaded zone is low because the pores are filled with formation water ($R_w$). In the uninvaded zone, true resistivity ($R_i$) is equal to wet resistivity ($R_o$) because the formation is completely saturated with formation water ($R_f = R_o$ where the formation is completely saturated with formation water).

To summarize: in a water-bearing zone, the resistivity of the flushed zone ($R_{so}$) is greater than the resistivity of the invaded zone ($R_i$), which in turn has a greater resistivity than the uninvaded zone ($R_f$). Therefore: $R_{so} > R_f > R_f$ in water-bearing zones.

# Saltwater muds:

Because the resistivity of mud filtrate ($R_{mf}$) is approximately equal to the resistivity of formation water ($R_{mf} \sim R_w$), there is no appreciable difference in the resistivity from the flushed ($R_{so}$) to the invaded zone ($R_i$) to the uninvaded zone ($R_{so} = R_i = R_f$); all have low resistivities.

Both the above examples assume that the water saturation of the uninvaded zone is much greater than 60%.

14

ASQUITH AND KRYGOWSKI

Figure 1.5. Resistivity profile for a transition-style invasion of a hydrocarbon-bearing formation.

# Freshwater muds:

Because the resistivities of both the mud filtrate ($R_{mf}$) and residual hydrocarbons are much greater than formation water ($R_w$), the resistivity of the flushed zone ($R_{so}$) is comparatively high (remember that the flushed zone has mud filtrate and some residual hydrocarbons).

Beyond its flushed part ($R_{so}$), the invaded zone ($R_i$) has a mixture of mud filtrate ($R_{mf}$), formation water ($R_w$), and some residual hydrocarbons. Such a mixture causes high resistivities. In some cases, resistivity of the invaded zone ($R_i$) almost equals that of the flushed zone ($R_{so}$).

The presence of hydrocarbons in the uninvaded zone causes higher resistivity than if the zone had only formation water ($R_w$), because hydrocarbons are more resistant than formation water. In such a case, $R_i > R_o$. The resistivity of the uninvaded zone ($R_i$) is normally somewhat less than the resistivity of the flushed and invaded zones ($R_{so}$ and $R_i$). However, sometimes when an annulus profile is present, the invaded zone's resistivity ($R_i$) can be slightly lower than the uninvaded zone's resistivity ($R_i$).

To summarize: $R_{so} > R_i > R_i$ or $R_{so} > R_i < R_i$ in hydrocarbon-bearing zones.

# Saltwater muds:

Because the resistivity of the mud filtrate ($R_{mf}$) is approximately equal to the resistivity of formation water ($R_{mf} \sim R_w$), and the amount of residual hydrocarbons is low, the resistivity of the flushed zone ($R_{so}$) is low.

Away from the borehole, as more hydrocarbons mix with mud filtrate in the invaded zone the resistivity of the invaded zone ($R_i$) increases.

Resistivity of the uninvaded zone ($R_i$) is much greater than if the formation were completely water saturated ($R_o$) because hydrocarbons are more resistant than saltwater. Resistivity of the uninvaded zone ($R_i$) is greater than the resistivity of the invaded ($R_i$) zone. So, $R_i > R_i > R_{so}$. Both the above examples assume that the water saturation of the uninvaded zone is much less than 60%.

Horizontal section through a permeable oil-bearing bed

![img-6.jpeg](img-6.jpeg)

Basic Relationships of Well Log Interpretation

15

![img-7.jpeg](img-7.jpeg)

Figure 1.6. Example of dual induction log curves through a water-bearing zone.

Given: the drilling mud is freshwater based ($R_{\mathrm{inf}} > 3R_{\mathrm{w}}$).

Where freshwater drilling muds invade a water-bearing formation ($S_{\mathrm{w}} > 60\%$), there is high resistivity in the flushed zone ($R_{\mathrm{so}}$), a lesser resistivity in the invaded zone ($R_{\mathrm{i}}$), and a low resistivity in the uninvaded zone ($R_{\mathrm{f}}$).

See Figure 1.4 for review. (Figure 1.8 shows the response of these resistivity curves in a hydrocarbon-bearing zone.)

Compare the three curves on the right side of the log (tracks 2 and 3). Resistivity increases from left to right. A key for reading this logarithmic resistivity scale is shown at the bottom of the log. Depth scale is in feet with each vertical increment equal to 2 ft.

# Log curve ILD:

Deep induction log resistivity curves usually measure true formation resistivity ($R_{\mathrm{f}}$), the resistivity of the formation beyond the outer boundary of the invaded zone. In water-bearing zones (in this case from 5870 to 5970 ft), the curve reads a low resistivity because the pores of the formation are saturated with low resistivity connate water ($R_{\mathrm{w}}$).

# Log curve ILM:

Medium induction log resistivity curves measure the resistivity of the invaded zone ($R_{\mathrm{i}}$). In a water-bearing formation, the curve reads a resistivity between $R_{\mathrm{f}}$ and $R_{\mathrm{so}}$ because the fluid in the formation is a mixture of formation water ($R_{\mathrm{w}}$) and mud filtrate ($R_{\mathrm{inf}}$).

# Log curve SFLU:

Spherically focused log resistivity curves measure the resistivity of the flushed zone ($R_{\mathrm{so}}$). In a water-bearing zone, the curve reads a high resistivity because freshwater mud filtrate ($R_{\mathrm{inf}}$) has a high resistivity. The SFL pictured here records a greater resistivity than either the deep (ILD) or medium (ILM) induction curves.

16

ASQUITH AND KRYGOWSKI

![img-8.jpeg](img-8.jpeg)

Figure 1.7. Example of dual laterolog curves through a water-bearing zone.

Given: The drilling mud is saltwater based ($R_{mf} \sim R_w$).

Where saltwater drilling muds invade a water-bearing formation ($S_w > 60\%$), there is low resistivity in the flushed zone ($R_{so}$), a low resistivity in the invaded zone ($R_i$), and low resistivity in the uninvaded zone ($R_i$). Because $R_{mf}$ is approximately equal to $R_w$, the pores in the flushed ($R_{so}$), invaded ($R_i$), and uninvaded ($R_i$) zones are all filled with saline waters; the presence of salt results in low resistivity.

See Figure 1.4 for review. (Figure 1.9 shows the response of these resistivity curves in a hydrocarbon-bearing zone.)

Compare the three curves on the right side of the log (tracks 2 and 3). Resistivity increases from left to right. A key for reading this logarithmic resistivity scale is shown at the bottom of the log. Depth scale is in feet with each vertical increment equal to 2 ft.

# Log curve LLD:

Deep laterolog resistivity curves usually measure true formation resistivity ($R_i$), the resistivity of the formation beyond the outer boundary of the invaded zone. In water-bearing zones (in this case from 9866 to 9924 ft), the curve reads a low resistivity because the pores of the formation are saturated with low resistivity connate water ($R_w$).

# Log curve LLS:

Shallow laterolog resistivity curves measure the resistivity in the invaded zone ($R_i$). In a water-bearing zone, the shallow laterolog (LLS) records a low resistivity because $R_{mf}$ is approximately equal to $R_w$.

# Log curve RXO:

Microresistivity curves measure the resistivity of the flushed zone ($R_{so}$). In water-bearing zones the curve records a low resistivity because saltwater mud filtrate has low resistivity. The resistivity recorded by the microresistivity log is low and approximately equal to the resistivities of the invaded and uninvaded zones.

Basic Relationships of Well Log Interpretation

17

![img-9.jpeg](img-9.jpeg)

Figure 1.8. Example of dual induction log curves through a hydrocarbon-bearing zone.

Given: the drilling mud is freshwater based ($R_{\mathrm{ref}} > 3R_{\mathrm{w}}$).

Where freshwater drilling muds invade a hydrocarbon-bearing formation ($S_w < 60\%$), there is high resistivity in the flushed zone ($R_{\mathrm{so}}$), high resistivity in the invaded zone ($R_i$), and high resistivity in the uninvaded zone ($R_j$). Normally, the flushed zone has slightly higher resistivity than the uninvaded zone.

See Figure 1.5 for review. (Figure 1.6 shows the response of these resistivity curves in a water-bearing zone.)

Compare the three curves on the right side of the log (tracks 2 and 3). Resistivity increases from left to right.

## Log curve ILD:

Deep induction log resistivity curves usually measure true formation resistivity ($R_f$), the resistivity of the formation beyond the outer boundary of the invaded zone. In hydrocarbon-bearing zones (in this case from 8748 to 8774 ft), the curve records a high resistivity because hydrocarbons are more resistant than saltwater in the formation ($R_f > R_g$).

## Log curve ILM:

Medium induction log resistivity curves measure the resistivity of the invaded zone ($R_j$). In a hydrocarbon-bearing zone, because of a mixture of mud filtrate ($R_{\mathrm{ref}}$), formation water ($R_w$), and residual hydrocarbons in the pores, the curve records a high resistivity. This resistivity is normally equal to or slightly more than the deep induction curve (ILD). But, in an annulus situation, the medium curve (ILM) can record a resistivity slightly less than the deep induction (ILD) curve.

## Log curve SFLU:

Spherically focused log resistivity curves measure the resistivity of the flushed zone ($R_{\mathrm{so}}$). In a hydrocarbon-bearing zone, the curve reads a higher resistivity than the deep (ILD) or medium (ILM) induction curves because the flushed zone ($R_{\mathrm{so}}$) contains mud filtrate and residual hydrocarbons. The SFL pictured here records a greater resistivity than either the deep (ILD) or medium (ILM) induction curves.

18

ASQUITH AND KRYGOWSKI

![img-10.jpeg](img-10.jpeg)

Figure 1.9. Example of dual laterolog curves through a hydrocarbon-bearing zone.

Given: The drilling mud is saltwater based ($R_{\mathrm{inf}} \sim R_{\mathrm{w}}$).

Where saltwater drilling muds invade a hydrocarbon-bearing formation ($S_{\mathrm{w}} \ll 60\%$), there is low resistivity in the flushed zone ($R_{\mathrm{inf}}$), an intermediate resistivity in the invaded zone ($R_{\mathrm{i}}$), and high resistivity in the uninvaded zone ($R_{\mathrm{f}}$). The reason for the increase in resistivities deeper into the formation is because of the increasing hydrocarbon saturation.

See Figure 1.5 for review. (Figure 1.7 shows the response of these resistivity curves in a water-bearing zone.)

Compare the three curves on the right side of the log (tracks 2 and 3). Resistivity increases from left to right.

## Log curve LLD:

Deep laterolog resistivity curves usually measure true formation resistivity ($R_{\mathrm{f}}$), the resistivity of the formation beyond the outer boundary of the invaded zone. In hydrocarbon-bearing zones (in this case from 9306 to 9409 ft), the curve reads a high resistivity because of high hydrocarbon saturation in the uninvaded zone ($R_{\mathrm{f}}$).

## Log curve LLS:

Shallow laterolog resistivity curves measure the resistivity in the invaded zone ($R_{\mathrm{i}}$). In a hydrocarbon-bearing zone, the shallow laterolog (LLS) records a lower resistivity than the deep laterolog (LLD) because the invaded zone ($R_{\mathrm{i}}$) has a lower hydrocarbon saturation than the uninvaded zone ($R_{\mathrm{f}}$)

## Log curve MSFL:

Microspherically focused log resistivity curves measure the resistivity of the flushed zone ($R_{\mathrm{inf}}$). In hydrocarbon-bearing zones, the curve records a low resistivity because saltwater mud filtrate has low resistivity and the residual hydrocarbon saturation in the flushed zone ($R_{\mathrm{inf}}$) is low. Therefore, in a hydrocarbon-bearing zone with saltwater-based drilling mud, the uninvaded zone ($R_{\mathrm{f}}$) has high resistivity, the invaded zone ($R_{\mathrm{i}}$) has a lower resistivity, and the flushed zone ($R_{\mathrm{inf}}$) has the lowest resistivity.

Basic Relationships of Well Log Interpretation

19

![img-11.jpeg](img-11.jpeg)

Figure 1.10. Chart for estimating formation temperature ($T_f$) with depth (linear gradient assumed). (Western Atlas International, Inc., 1995, Figure 2-1)

Given:

Surface temperature = 80°F

Bottom hole temperature (BHT) = 200°F

Total depth (TD) = 10,000 ft

Formation depth = 7000 feet

Procedure:

1. Locate BHT (200°F) on the 80 scale (bottom of the chart; mean surface temperature = 80°F).
2. Follow BHT (200°F) vertically up until it intersects the 10,000 ft (TD) line. This intersection defines the temperature gradient.
3. Move parallel to the (diagonal) temperature gradient line up to 7000 ft (formation depth).
4. Formation temperature (164°F) is read on the bottom scale (i.e., 80 scale) vertically down from the point where the 7000 ft line intersects the temperature gradient.

NOTE: In the United States (as an example), 80°F is used commonly as the mean surface temperature in the southern states, and 60°F is used commonly in the northern states. However, a specific mean surface temperature can be calculated if such precision is desired. Another source for mean surface-temperature gradients is any world atlas with such listings.

20

ASQUITH AND KRYGOWSKI

Figure 1.11. Chart for adjusting fluid resistivities for temperature. (Schlumberger, 1998, Figure Gen-9.)

Given:

Resistivity of drilling mud ($R_{\mathrm{cr}}$) equals 1.2 ohm-m at $75^{\circ}\mathrm{F}$. Formation temperature ($T_{\mathrm{f}}$) = $160^{\circ}\mathrm{F}$.

Procedure:

1. Locate the resistivity value, 1.2 ohm-m, on the scale at the left of the chart.
2. Move to the right horizontally along the 1.2 ohm-m line until the vertical line representing a temperature of \(75^{\circ}\mathrm{F}\) (from the bottom of the chart) is encountered (point A on the chart).
3. Move parallel to the (diagonal) constant salinity line to where it intersects the vertical line representing a temperature value of \(160^{\circ}\mathrm{F}\) (point B on the chart).
4. From point B, follow the horizontal line to the left to determine the resistivity of the fluid at the desired temperature (0.58 ohm-m at \(160^{\circ}\mathrm{F}\)).

Each diagonal line on the chart shows the resistivity of a solution of fixed concentration over a range of temperatures. The diagonal lines at the bottom of the chart indicate that an NaCl solution can hold no more than 250,000 to 300,000 ppm NaCl depending on temperature (i.e., the solution is completely salt saturated).

![img-12.jpeg](img-12.jpeg)

2

Asquith, G., and D. Krygowski, 2004, Spontaneous Potential, in G. Asquith and D. Krygowski, Basic Well Log Analysis: AAPG Methods in Exploration 16, p. 21-30.

# Spontaneous Potential

## GENERAL

The spontaneous potential (SP) log was one of the earliest measurements used in the petroleum industry, and it has continued to play a significant role in well log interpretation. Most wells today have this type of log included in their log suites. Primarily, the SP log is used for determining gross lithology (i.e., reservoir vs. nonreservoir) through its ability to distinguish permeable zones (such as sandstones) from impermeable zones (such as shales). It is also used to correlate zones between wells. However, as will be discussed later in this chapter, the SP log has several other uses that are perhaps equally important.

The SP log is a record of direct current (DC) voltage (or *potential*) that develops naturally (or *spontaneously*) between a moveable electrode in the well bore and a fixed electrode located at the surface (Doll, 1948). It is measured in millivolts (mV). Electric voltages arising primarily from electrochemical factors within the borehole and the adjacent rock create the SP log response. These electrochemical factors are brought about by differences in salinities between mud filtrate and formation water within permeable beds. Salinity of a fluid is inversely proportional to its resistivity, and in practice salinity is indicated by mud filtrate resistivity ($R_{mf}$) and formation water resistivity ($R_w$). Because a conductive fluid is needed in the borehole for the generation of these voltages, the SP cannot be used in nonconductive (e.g., oil-base) drilling muds or in air-filled holes.

The SP log is usually recorded on the left track of the log (track 1) and is used to

- detect permeable beds
- detect boundaries of permeable beds
- determine formation-water resistivity \((R_{w})\)
- determine the volume of shale in permeable beds

An auxiliary use of the SP curve is in the detection of hydrocarbons by the suppression of the SP response.

The concept of static spontaneous potential ($SSP$) is important because $SSP$ represents the maximum SP that a thick, shale-free, porous, and permeable formation can have for a given ratio between $R_{mf}$ and $R_w$. $SSP$ is determined by formula or chart and is a necessary element for determining accurate values of $R_w$ and volume of shale. The measured $SP$ value is influenced by bed thickness, bed resistivity, borehole diameter, invasion, shale content, hydrocarbon content, and most important: the ratio of $R_{mf}$ to $R_w$ (Figure 2.1A).

## Bed Thickness

In a thin formation (i.e., less than about 10 ft [3 m] thick), the measured $SP$ is less than $SSP$ (Figure 2.1B). However, the SP curve can be corrected by chart for the effects of bed thickness. As a general rule, whenever the SP curve is narrow and pointed, the $SP$ should be corrected for bed thickness before being used in the calculation of $R_w$.

## Bed Resistivity

Higher resistivities reduce the deflection of the SP curves.

## Borehole and Invasion

Hilchie (1978) indicates that the effects of borehole diameter and invasion on the SP log are very small and, in general, can be ignored.

## Shale Content

The presence of shale in a permeable formation reduces the SP deflection (Figure 2.1B). In water-bear-

21

22

ASQUITH AND KRYGOWSKI

ing zones, the amount of SP reduction is related to the amount of shale in the formation.

### Hydrocarbon Content

In hydrocarbon-bearing zones, the SP deflection is reduced. This effect is called hydrocarbon suppression (Hilchie, 1978). Hydrocarbon suppression of the SP is a qualitative phenomenon, and cannot be used to determine the hydrocarbon saturation of the formation.

The SP response of shales is relatively constant and follows a straight line called a shale baseline. The SP value of the shale baseline is assumed to be zero, and SP curve deflections are measured from this baseline. Permeable zones are indicated where there is SP deflection from the shale baseline. For example, if the SP curve moves either to the left (negative deflection; $R_{mf} > R_w$) or to the right (positive deflection; $R_{mf} < R_w$) of the shale baseline, permeable zones are present.

Permeable bed boundaries are placed at the points of inflection from the shale baseline.

Note that when recording through impermeable zones or through permeable zones where $R_{mf}$ is equal to $R_w$, the SP curve does not deflect from the shale baseline. The magnitude of SP deflection is due to the difference in salinity between mud filtrate and formation water and not to the amount of permeability. This salinity difference produces a difference in the resistivities of the mud filtrate ($R_{mf}$) and formation water ($R_w$).

Over long intervals (several hundreds to thousands of feet), the SP baseline can drift, either in the positive or negative direction. While this is of little consequence when making calculations local to a specific formation, it may introduce errors if the SP magnitude is being calculated over that long interval, especially by means of a computer. Accordingly, the baseline drift can be removed (many programs have such editing routines) so that the SP baseline retains a constant value (usually set to zero) over the length of the logged interval.

### FORMATION WATER RESISTIVITY ($R_w$) DETERMINATION

Figure 2.2 is an induction electric log with an SP curve from a Pennsylvanian upper Morrow sandstone in Beaver County, Oklahoma. In this example, the SP curve is used to find a value for $R_w$ by the following procedure:

1. After determining the formation temperature, correct the resistivities of the mud filtrate ($R_{mf}$) and drilling mud ($R_m$) (obtained from the log heading) to formation temperature (see Chapter 1).
2. To minimize the effect of bed thickness, the SP is corrected to static SP (SSP). SSP represents the maximum SP a formation can have if unaffected by bed thickness. Figure 2.3 is a chart used to correct SP to SSP. The data necessary to use this chart are:

- bed thickness,
- resistivity from the shallow-reading resistivity tool ($R_i$)
- the resistivity of the drilling mud ($R_m$) at formation temperature

3. Once the value of SSP is determined, it is used on the chart illustrated in Figure 2.4 to obtain a value for the $R_{mf}/R_{we}$ ratio. Equivalent resistivity ($R_{we}$) is obtained by dividing $R_{mf}$ by the $R_{mf}/R_{we}$ value from the chart (Figure 2.4).

4. The value of $R_{we}$ is then corrected to $R_w$, using the chart illustrated in Figure 2.5, for average deviation from sodium chloride solutions, and for the influence of formation temperature.

A careful examination of Figures 2.2 to 2.5 should help you gain an understanding of the procedure to determine $R_w$ from the SP. But, rather than using charts in the procedure, you might prefer using the mathematical formulas listed in Table 2.1.

It is important to remember that normally the SP curve has less deflection in hydrocarbon-bearing zones (i.e., hydrocarbon suppression). Using a hydrocarbon-bearing zone to calculate $R_w$ results in too high a value for $R_w$ calculated from SSP. Using a too-high value of $R_w$ in Archie's equation to determine water saturation produces a value of $S_w$ that is also too high, creating the chance for missed production in the interpretive process. Therefore, to determine $R_w$ from SP it is best, whenever possible, to use the SP curve produced by a zone that is known to contain only water.

Spontaneous Potential

23

Table 2.1. Mathematical Calculation of $R_w$ from SSP, for temperatures in °F (after Western Atlas Logging Services, 1985).

|  Identify a zone on the logs that is clean, wet, and permeable. Pick the maximum value for SP in the zone. |   |
| --- | --- |
|  Calculate formation temperature at the depth of the SP value. $AMST =$ Annual Mean Surface Temperature $BHT =$ Bottom Hole Temperature $FD =$ Formation Depth $T_f =$ formation temperature | $$T_f = \left( \frac{BHT - AMST}{TD} \times FD \right) + AMST$$  |
|  Convert $R_{mf}$ from surface (measured) temperature to formation temperature. $R_{mf} = R_{mf}$ at formation temperature $R_{mfsurf} = R_{mf}$ at measured temperature $T_{surf} =$ Measured temperature of $R_{mf}$ | $$R_{mf} = \frac{R_{mfsurf}(T_{surf} + 6.77)}{T_f + 6.77}$$  |
|  Find the equivalent formation water resistivity, $R_{we}$, from the SP and $R_{mf}$. $R_{we} =$ equivalent $R_w$ | $$R_{we} = R_{mf} \times 10^{SP/(61+0.133 \cdot BHT)}$$  |
|  Convert $R_{we}$ to $R_w$ (this value is at formation temperature). | $$R_w = \frac{R_{we} + 0.131 \times 10^{\left( \frac{1}{\log(BHT/19.9)} \right)^{-2}}}{-0.5 \times R_{we} + 10^{\left( \frac{0.0426}{\log(BHT/50.8)} \right)}}$$  |

## SHALE VOLUME CALCULATION

The volume of shale in a sand can be used in the evaluation of shaly sand reservoirs (Chapter 6) and as a mapping parameter for both sandstone and carbonate facies analysis (Chapter 7). The SP log can be used to calculate the volume of shale in a permeable zone by the following formula:

$$
V_{shale} = 1.0 - \frac{PSP}{SSP} \tag{2.1}
$$

where:

$V_{shale} =$ volume of shale

$PSP =$ pseudostatic spontaneous potential (maximum SP of shaly formation)

$SSP =$ static spontaneous potential of a nearby thick clean sand

Or, alternately:

$$
V_{shale} = \frac{PSP - SSP}{SP_{shale} - SSP} \tag{2.2}
$$

where:

$V_{shale} =$ volume of shale

$PSP =$ pseudostatic spontaneous potential (maximum SP of shaly formation)

$SSP =$ static spontaneous potential of a nearby thick clean sand

$SP_{shale} =$ value of SP in a shale (usually assumed to be zero)

24

ASQUITH AND KRYGOWSKI

# REVIEW

1. The spontaneous potential log (SP) can be used to

- detect permeable beds
- detect boundaries of permeable beds
- determine formation water resistivity ($R_w$)
- determine volume of shale ($V_{shale}$) in a permeable bed

2. The variations in the SP are the result of an electric potential that is present between the well bore and the formation as a result of differences in salinities between mud filtrate and formation water. This salinity difference produces a resistivity difference between $R_{mf}$ and $R_w$.

3. The SP response in shales is relatively constant, and a vertical line drawn along the SP response in a shale is referred to as the shale baseline. In permeable beds, the SP has the following responses relative to the shale baseline:

- negative deflection (to the left of the shale baseline) where $R_{mf} > R_w$
- positive deflection (to the right of the shale baseline) where $R_{mf} < R_w$
- no deflection where $R_{mf} = R_w$

4. The SP response can be suppressed by thin beds, shaliness, and the presence of hydrocarbons.

Throughout this text, italics are used to indicate variable names with numeric values. The notation SP is the abbreviation for spontaneous potential, and the variable SP indicates the numerical value (in mV) taken from the SP log.

Spontaneous Potential

25

![img-13.jpeg](img-13.jpeg)

Figure 2.1. Examples of SP deflection from the shale baseline.

2.1A. SP deflection with different resistivities of mud filtrate ($R_{mf}$) and formation water ($R_w$). Where resistivity of the mud filtrate ($R_{mf}$) is equal to the resistivity of the formation water ($R_w$), there is no deflection, positive or negative, from the shale baseline.

Where $R_{mf}$ is greater than $R_w$, the SP deflects to the left of the shale baseline (negative deflection). Where $R_{mf}$ greatly exceeds $R_w$, the deflection is proportionately greater. This is often called a normal SP.

Where $R_{mf}$ is less than $R_w$, the SP deflects to the right of the shale baseline (positive deflection). This condition, often called a reversed SP, is produced by a formation containing fresh water.

Remember, the SP log can used only with conductive (i.e., saltwater base or freshwater base) drilling muds. This log does not work with oil-base muds or in air-filled holes.

2.1B. SP deflection with resistivity of the mud filtrate ($R_{mf}$) much greater than formation water ($R_w$). SSP (static spontaneous potential) at the top of the diagram, is the maximum deflection possible in a thick, shale-free, and water-bearing (wet) sandstone for a given ratio of $R_{mf}/R_w$. All other deflections are less and are relative in magnitude.

SP shows the SP response due to the presence of thin beds and/or the presence of gas.

PSP (pseudostatic spontaneous potential) is the SP response if shale is present.

The formula for the theoretical calculated value of SSP is given:

$$SSP = -K \times \log(R_{mf} / R_w) \tag{2.2}$$

where:

$$K = (0.133 \times T_f) + 60 \tag{2.3}$$

26 ASQUITH AND KRYGOWSKI

![img-14.jpeg](img-14.jpeg)

Spontaneous Potential

27

Figure 2.2. Determination of formation water resistivity ($R_w$) from an SP log. This example uses the charts on Figures 2.3 through 2.5.

Given:

$R_{mf} = 0.51$ ohm-m at 135°F (BHT)

$R_m = 0.91$ ohm-m at 135°F (BHT)

Surface temperature = 60°F

Total depth = 8007 ft

Bottom hole temperature (BHT) = 135°F

From the log:

Formation depth at maximum SP deflection is 7446 ft.

The maximum SP deflection in the sand coincides with -50 mV on the log scale, and the shale base line is at -5 mV. Note that the SP scale goes from -160 mV on the left to +40 mV on the right and has 20 mV per division.

Bed thickness is 8 ft (7442 to 7450 ft).

Short-normal (SN) resistivity ($R_s$) is 33 ohm-m. The short-normal (or 16-inch normal) log measures the shallow formation resistivity (i.e., the resistivity of the invaded zone, $R_s$).

Procedure:

1. Determine $T_f$:

Use Figure 1.10 and the information above to calculate the formation temperature ($T_f$).

$T_f = 130^{\circ}\text{F}$.

2. Correct $R_m$ and $R_{mf}$ to $T_f$:

Use Figure 1.11 and the information above to correct $R_m$ and $R_{mf}$ to formation temperature.

$R_m = 0.94$ ohm-m at 130°F and $R_{mf} = 0.53$ ohm-m at 130°F.

3. Determine SP:

Read the maximum deflection directly from the SP curve in Figure 2.2. In this case, because the SP baseline has a nonzero value (-5 mV), its value must be subtracted from the value of the SP curve.

The SP value is: SP (read from log) - baseline value = (-50 mV) - (-5 mV) = -45 mV

$SP = -45$ mV.

4. Correct SP to SSP (correct for a thin bed):

See the procedure in Figure 2.3

$SSP = -59$ mV

5. Determine $R_{mf}/R_{we}$ ratio, and from that, determine $R_{we}$:

See the procedure in Figure 2.4

$R_{we} = 0.096$ ohm-m

6. Correct $R_{we}$ to $R_w$:

Use the chart in Figure 2.5, and the $R_{we}$ value in step 6

$R_w = 0.10$ ohm-m at $T_f$

28

ASQUITH AND KRYGOWSKI

![img-15.jpeg](img-15.jpeg)

Figure 2.3. SP bed-thickness correction to determine SSP from SP. (Western Atlas, 1995, Figure 3-1)

Procedure, using the values from the log in Figure 2.2:

1. Calculate the ratio $R_{\mathrm{f}} / R_{\mathrm{m}}$ using the values determined in Figure 2.2, where $R_{\mathrm{f}}$ is equal to the short-normal (SN) resistivity and $R_{\mathrm{m}}$ is the value determined at formation temperature.

$$
R_{\mathrm{f}} = \mathrm{SN} = 34 \mathrm{ohm\cdot m}
$$

$$
R_{\mathrm{m}} = 0.94 \mathrm{ohm\cdot m}
$$

$$
R_{\mathrm{f}} / R_{\mathrm{m}} = 36
$$

2. Locate a bed thickness on the vertical scale. Bed thickness \(= 8\) ft.
3. Follow the bed-thickness value horizontally across until it intersects the \(R_{\mathrm{f}} / R_{\mathrm{m}}\) curve.

(Because $R_{\mathrm{f}} / R_{\mathrm{m}} = 36$, the point lies between the $R_{\mathrm{f}} / R_{\mathrm{m}} = 20$ and the $R_{\mathrm{f}} / R_{\mathrm{m}} = 50$ curves.)

3. Drop vertically from this intersection and read the SP correction factor on the scale across the bottom.

SP correction factor is approximately 1.3.

4. Multiply SP by the SP correction factor to find SSP.

$$
SSP = SP \times \text{correction factor}
$$

$$
SSP = -45 \mathrm{mV} \times 1.3 \text{ (SP value taken at 7446 ft, see Figure 2.2)}
$$

$$
SSP = -59 \mathrm{mV}
$$

The nomogram in the upper right part of this figure also gives SSP. Draw a straight line from 45 on the SP scale on the left side of the nomogram through 1.3 on the diagonal SP correction factor scale. Continue this straight line to where it crosses the SSP scale at 59 mV. Remember that the SP value is negative, so the SSP value is also negative.

Spontaneous Potential

29

![img-16.jpeg](img-16.jpeg)

Courtesy Baker Atlas, © 1996-1999 Baker Hughes, Inc.

Figure 2.4. Chart used for determining the $R_{\mathrm{ref}} / R_{\mathrm{we}}$ ratio from SSP values. (Western Atlas, 1995, Figure 3-2)

Procedure, using the log data in Figure 2.2 and the values from Figure 2.3:

1. Locate the SSP value on the scale on the left edge of the chart.

$$
S S P = - 5 9 \mathrm {m V}
$$

2. Follow the value horizontally until it intersects the sloping formation temperature line $(130^{\circ}\mathrm{F}$ ; imagine a line between the $100^{\circ}\mathrm{F}$ and $200^{\circ}\mathrm{F}$ temperature lines).

3. Move vertically from this intersection and read the ratio value on the scale at the bottom of the chart.

The $R_{\mathrm{ref}} / R_{\mathrm{we}}$ ratio value is 5.5

4. Divide the corrected value for $R_{\mathrm{ref}}$ by the ratio $R_{\mathrm{ref}} / R_{\mathrm{we}}$ value.

$$
R _ {w e} = R _ {r e f} / \left(R _ {r e f} / R _ {w e}\right)
$$

$$
R _ {w e} = 0. 5 3 / 5. 5
$$

$$
R _ {w e} = 0. 0 9 6 \mathrm {o h m - m}
$$

30

ASQUITH AND KRYGOWSKI

![img-17.jpeg](img-17.jpeg)

Courtesy Baker Atlas, © 1996-1999 Baker Hughes, Inc.

Figure 2.5. Chart for determining the value of $R_{w}$ from $R_{wo}$. (Western Atlas, 1995, Figure 3-3)

Procedure, using the values from Figure 2.4:

1. Locate the value of \( R_{wo} \) on the vertical scale. \( R_{wo} = 0.096 \) ohm·m
2. Follow it horizontally until it intersects the temperature curve desired. \(130^{\circ}\mathrm{F}\) lies between the \(100^{\circ}\mathrm{F}\) and \(150^{\circ}\mathrm{F}\) temperature curves.
3. Drop vertically from the intersection and read a value for \( R_{w} \) on the scale at the bottom.

$$R_{w} = 0.10 \text{ ohm}\cdot\text{m}$$

3

Asquith, G., and D. Krygowski, 2004, Gamma Ray, in G. Asquith and D. Krygowski, Basic Well Log Analysis: AAPG Methods in Exploration 16, p. 31–35.

# Gamma Ray

## GENERAL

Gamma ray (GR) logs measure the natural radioactivity in formations and can be used for identifying lithologies and for correlating zones. Shale-free sandstones and carbonates have low concentrations of radioactive material and give low gamma ray readings. As shale content increases, the gamma ray log response increases because of the concentration of radioactive material in shale. However, clean sandstone (i.e., with low shale content) might also produce a high gamma ray response if the sandstone contains potassium feldspars, micas, glauconite, or uranium-rich waters.

In zones where the geologist is aware of the presence of potassium feldspars, micas, or glauconite, a spectral gamma ray log can be run in place of the standard the gamma ray log. The spectral gamma ray log records not only the number of gamma rays emitted by the formation but also the energy of each, and processes that information into curves representative of the amounts of thorium (Th), potassium (K), and uranium (U) present in the formation.

If a zone has a high potassium content coupled with a high gamma ray log response, the zone might not be shale. Instead, it could be a feldspathic, glauconitic, or micaceous sandstone.

Like the SP log, gamma ray logs can be used not only for correlation, but also for the determination of shale (clay) volumes. These volumes are essential in calculating water saturations in shale-bearing formations by some shaly-sand techniques. Unlike the SP log, the gamma ray response is not affected by formation water resistivity ($R_w$), and because the gamma ray log responds to the radioactive nature of the formation rather than the electrical nature, it can be used in cased holes and in open holes containing nonconducting drilling fluids (i.e., oil-based muds or air).

The gamma ray log is usually displayed in the left track (track 1) of a standard log display, commonly with a caliper curve. Tracks 2 and 3 usually contain

porosity or resistivity curves. Figure 3.1 is an example of such a display.

## SHALE VOLUME CALCULATION

Because shale is usually more radioactive than sand or carbonate, gamma ray logs can be used to calculate volume of shale in porous reservoirs. The volume of shale expressed as a decimal fraction or percentage is called $V_{shale}$. This value can then be applied to the analysis of shaly sands (see Chapter 7).

Calculation of the gamma ray index is the first step needed to determine the volume of shale from a gamma ray log:

$$I_{GR} = \frac{GR_{\log} - GR_{\min}}{GR_{\max} - GR_{\min}} \tag{3.1}$$

where:

$I_{GR}$ = gamma ray index

$GR_{log}$ = gamma ray reading of formation

$GR_{min}$ = minimum gamma ray (clean sand or carbonate)

$GR_{max}$ = maximum gamma ray (shale)

Unlike the SP log, which is used in a single linear relationship between its response and shale volume, the gamma ray log has several nonlinear empirical responses as well as a linear response. The nonlinear responses are based on geographic area or formation age, or if enough other information is available, chosen to fit local information. Compared to the linear response, all nonlinear relationships are more optimistic; that is, they produce a shale volume value lower than that from the linear equation. For a first-order estimation of shale volume, the linear response, where $V_{shale} = I_{GR}$, should be used.

31

32

ASQUITH AND KRYGOWSKI

The nonlinear responses, in increasing optimism (lower calculated shale volumes), are:

Larionov (1969) for Tertiary rocks:

$$V_{sh} = 0.083(2^{3.7 I_{GR}} - 1) \tag{3.2}$$

Steiber (1970):

$$V_{sh} = \frac{I_{GR}}{3 - 2 \times I_{GR}} \tag{3.3}$$

Clavier (1971):

$$V_{sh} = 1.7 - [3.38 - (I_{GR} - 0.7)^2]^{\frac{1}{2}} \tag{3.4}$$

Larionov (1969) for older rocks:

$$V_{sh} = 0.33 \times (2^{2 I_{GR}} - 1) \tag{3.5}$$

See Figures 3.1 and 3.2 for an example of a shale volume calculation using the gamma ray log.

## SPECTRAL GAMMA RAY LOG

The response of the normal gamma ray log is made up of the combined radiation from uranium, thorium, potassium, and a number of associated daughter products of radioactive decay. Because these different radioactive elements emit gamma rays at different energy levels, the radiation contributed by each element can be analyzed separately. Potassium (potassium 40) has a single energy of 1.46 MeV (million electron volts). The thorium and uranium series emit radiation at various energies; however, they have prominent energies at 2.614 MeV (thorium) and 1.764 MeV (uranium). By using energy-selective sensor windows, the total gamma ray response can be separated into the gamma rays related to each of these elements (Dewan, 1983). Figure 3.3 illustrates one format used to display output from the spectral gamma ray log. In addition to the individual elements shown in tracks 2 and 3, the spectral gamma ray data can be displayed in track 1 as total gamma radiation (SGR-dashed curve) and total gamma radiation minus uranium (CGR-solid curve).

Important uses of the spectral gamma ray log include (Dresser-Atlas, 1981):

- determining shale (clay) volume ($V_{shale}$) in sandstone reservoirs that contain uranium minerals, potassium feldspars, micas, and/or glauconite
- differentiating radioactive reservoirs from shales
- source-rock evaluation
- evaluation of potash deposits
- geologic correlations
- clay typing
- fracture detection
- rock typing in crystalline basement rocks

In most log analyses, the first two uses listed above are the most important uses of spectral log data.

In determining shale volume ($V_{shale}$) in sandstones, Dewan (1983) has suggested the use of only the thorium and potassium components instead of total GR in the $V_{shale}$ equations, because uranium salts are soluble and can be transported and precipitated in the formation after deposition. If potassium minerals are present in the sandstone, Dewan (1983) suggested the use of only the thorium component in the $V_{shale}$ equations. Radioactive reservoirs like the "hot" dolomites of the Permian (west Texas and New Mexico) and Williston (Montana, North Dakota, and South Dakota) basins of the United States are normally differentiated from shales by the low thorium and potassium contents and high uranium content.

## REVIEW

1. Gamma ray logs are lithology logs that measure the natural radioactivity of a formation.
2. Because radioactive material is concentrated in shale, shale has a high gamma ray reading.

Shale-free sandstones and carbonates, therefore, usually have low gamma ray readings.

3. Gamma ray logs are used to identify lithologies, correlate between formations, and calculate volume of shale.

Gamma Ray

33

![img-0.jpeg](img-0.jpeg)

Figure 3.1. Example of a gamma ray log with neutron-density log.

This example illustrates the curves and scales of a gamma ray log, and is also used to pick values for Figure 3.2.

Track 1 (to the left of the depth track): The gamma ray log (GR) is the only one represented on this track. Note that the scale increases from left to right, and ranges from 0 to 150 API gamma ray units in increments of 15 API units.

Tracks 2 and 3 (used together, to the right of the depth track): These tracks include logs representing bulk density (RHOB), neutron porosity (NPHI), and density correction (DRHO). Bulk density (RHOB) is represented by a solid line and ranges from 2.0 to 3.0 g/cm³ increasing from left to right. Neutron porosity (NPHI) is represented by a dashed line and ranges from -0.10 (-10%) to +0.30 (30%) increasing from right to left. The correction curve (DRHO) is represented by a dotted line and ranges from -0.25 to +0.25 g/cm³ increasing from left to right, but only uses track 3.

### Calculation of Gamma Ray Index $I_{GR}$ for Shale Volume Calculation

The minimum gamma ray value ($GR_{min}$) occurs at 13,593 ft and is 14 API units (slightly less than 1 scale division from zero).

The maximum gamma ray value ($GR_{max}$) occurs at 13,577 ft and at 13,720 ft and is 130 API units. These are the shaliest zones in the interval.

The gamma ray readings from three depths are shown in the table below.

From Equation 3.1, the gamma ray index ($I_{GR}$) is:

$$I_{GR} = \frac{GR_{log} - GR_{min}}{GR_{max} - GR_{min}} \tag{3.6}$$

|  Depth (ft) | $GR_{log}$ | $I_{GR}$  |
| --- | --- | --- |
|  13,534 | 32 | 0.16  |
|  13,570 | 28 | 0.12  |
|  13,701 | 55 | 0.35  |

See Figure 3.2 to convert $I_{GR}$ to shale volume ($V_{shale}$).

34

ASQUITH AND KRYGOWSKI

Figure 3.2. Chart for correcting the gamma ray index ($I_{GR}$) to the shale volume ($V_{shale}$). (Western Atlas, 1995, Figure 4-24)

Given (from Figure 3.1):

|  Depth (ft) | $GR_{lag}$ | $I_{GR}$  |
| --- | --- | --- |
|  13,534 | 32 | 0.16  |
|  13,570 | 28 | 0.12  |
|  13,701 | 55 | 0.35  |

# Procedure:

1. For each zone below, find the gamma ray index value \((I_{GR})\) on the horizontal scale on the bottom.
2. Follow the value vertically to where it intersects curve each of the curves listed below.
3. From each curve, move horizontally to the scale at the left and read the shale volume. This is the amount of shale in the formation expressed as a decimal fraction.

![img-1.jpeg](img-1.jpeg)

Courtesy Baker Atlas, ©1996-1999 Baker Hughes, Inc.

|  Depth (ft) | $GR_{lag}$ | $I_{GR}$ | Shale volume, $V_{shale}$  |   |   |
| --- | --- | --- | --- | --- | --- |
|   |   |   |  Linear | Larionov (for rocks older than Tertiary) | Steiber  |
|  13,534 | 32 | 0.16 | 0.16 | 0.08 | 0.06  |
|  13,570 | 28 | 0.12 | 0.12 | 0.06 | 0.04  |
|  13,701 | 55 | 0.35 | 0.35 | 0.21 | 0.15  |

Gamma Ray

35

![img-2.jpeg](img-2.jpeg)

Figure 3.3. Spectral gamma ray log.

This example is from West Texas. The Mississippian Barnett Shale contacts the underlying Mississippian limestone at 9606 ft. In the Barnett Shale, note the great variations in the potassium (POTA), uranium (URAN), and thorium (THOR) contents above the contact with the Mississippian limestone indicating changes in shale mineralogy.

# Symbols:

SGR Total gamma ray (dashed curve, track 1)

CGR Total gamma ray minus uranium (solid curve, track 1)

POTA Potassium 40 in weight percent (tracks 2 and 3)

URAN Uranium in ppm (tracks 2 and 3)

THOR Thorium in ppm (tracks 2 and 3)

4

Asquith, G., and D. Krygowski, 2004, Porosity Logs, in G. Asquith and D. Krygowski, Basic Well Log Analysis: AAPG Methods in Exploration 16, p. 37–76.

# Porosity Logs

## GENERAL

The next class of well logs to be considered is generally referred to as porosity logs. Although each produces a porosity value from basic measurements, none actually measures porosity directly. Two such logs, the density and neutron, are nuclear measurements. A third log, the sonic, uses acoustic measurements, and the fourth and newest log senses the magnetic resonance of formation nuclei. When used individually, each of the first three has a response to lithology which must be accounted for, but when used in concert, two or three at a time, lithology can be estimated and a more accurate porosity derived.

## NUCLEAR MAGNETIC RESONANCE LOG

Nuclear magnetic resonance (NMR) logging was first introduced by Schlumberger in 1978 (Maute, 1992) but was not initially widely used because of operational limitations. With the commercial introduction of the Magnetic Resonance Imaging Log (MRIL) by NUMAR Corporation (now part of Halliburton) in 1980 (Halliburton, 1999) and the release of the Combinable Magnetic Resonance Tool (CMR) by Schlumberger, the technique is steadily gaining acceptance.

The measurement technique is closely related to medical Magnetic Resonance Imaging (MRI) in that it senses the fluids in the formation surrounding the borehole (like MRI senses the fluids in the body) while the solids are largely invisible. In the logging tool, a powerful permanent magnet in the tool causes the protons in the formation fluids (mostly in the hydrogen) to align. An antenna in the tool then sends a signal into the formation, causing the protons to tip away from that original alignment. When the antenna signal is turned off, the protons begin to realign in the strong magnetic field, producing a signal called the spin echo. Repeated application of the antenna’s signal

leads to the measurement of many spin echoes, gathered as a spin echo train which is interpreted to estimate formation properties. Different interpretation and measurement methods lead to estimates of porosity, pore fluid types, and pore size distribution in the formation. Like the other porosity measurements, NMR measures mostly in the invaded and mixed zones of the formation around the wellbore. Unlike the other porosity measurements, the porosity determined from it is much less sensitive to lithologic changes than the porosities determined from those measurements.

Because wide use of NMR logs is relatively new, this technique is often used alone in the determination of porosity rather than in concert with the other porosity tools (sonic, density, and neutron). For these reasons, NMR logging is considered separately in Chapter 6.

## SONIC LOG

The sonic log is a porosity log that measures interval transit time ($\Delta t$, delta t, or DT) of a compressional sound wave traveling through the formation along the axis of the borehole. The sonic log device consists of one or more ultrasonic transmitters and two or more receivers. Modern sonic logs are borehole-compensated (BHC) devices. These devices are designed to greatly reduce the spurious effects of borehole size variations (Kobesh and Blizard, 1959) as well as errors due to tilt of the tool with respect to the borehole axis (Schlumberger, 1972) by averaging signals from different transmitter-receiver combinations over the same length of borehole.

Interval transit time ($\Delta t$) in microseconds per foot, $\mu$sec/ft (or microseconds per meter, $\mu$sec/m) is the reciprocal of the velocity of a compressional sound wave in feet per second (or meters per second). Interval transit time (DT) is usually displayed in tracks 2 and 3 of a log (Figure 4.1). A sonic-derived porosity

37

38

ASQUITH AND KRYGOWSKI

curve (SPHI) is sometimes displayed in tracks 2 and 3, along with the DT curve. Track 1 usually contains a caliper (CALI), and a gamma ray (GR) or an SP.

The interval transit time $(\Delta t)$ is dependent upon both lithology and porosity. Therefore, a formation's matrix interval transit time (Table 4.1) must be known to derive sonic porosity either by chart (Figure 4.2) or by the following formulas:

Wyllie time-average equation (Wyllie et al., 1958):

$$
\phi_{S} = \frac{\Delta t_{\log} - \Delta t_{\max}}{\Delta t_{\text{fl}} - \Delta t_{\max}} \tag{4.1}
$$

Raymer-Hunt-Gardner (RHG) equation (Raymer et al., 1980):

$$
\phi_{S} = \frac{5}{8} \times \frac{\Delta t_{\log} - \Delta t_{\max}}{\Delta t_{\log}} \tag{4.2}
$$

where:

$\phi_{S} =$ sonic-derived porosity

$\Delta t_{\max} =$ interval transit time in the matrix (Table 4.1)

$\Delta t_{\log} =$ interval transit time in the formation

$\Delta t_{\text{fl}} =$ interval transit time in the fluid in the formation (freshwater mud $= 189~\mu \mathrm{sec / ft}$ ; saltwater mud $= 185~\mu \mathrm{sec / ft}$ )

## Unconsolidated Formations

The Wyllie et al. (1958) formula for calculating sonic porosity can be used to determine porosity in consolidated sandstones and carbonates with intergranular porosity (grainstones) or intercrystalline porosity (sucrosic dolomites). However, when sonic

porosities of carbonates with vuggy or fracture porosity are calculated by the Wyllie formula, porosity values are too low. This happens because the sonic log only records matrix porosity rather than vuggy or fracture secondary porosity. The percentage of vuggy or fracture secondary porosity can be calculated by subtracting sonic porosity from total porosity. Total porosity values are obtained from one of the nuclear logs (i.e., density, neutron, or preferably the combination of density and neutron). The percentage of secondary porosity, called SPI or secondary porosity index, can be a useful mapping parameter in carbonate exploration.

Where a sonic log is used to determine porosity in unconsolidated sands, an empirical compaction factor $(C_p)$ should be added to the Wyllie et al. (1958) equation:

$$
\phi_{S} = \left(\frac{\Delta t_{\log} - \Delta t_{\max}}{\Delta t_{\text{fl}} - \Delta t_{\max}}\right) \times \frac{1}{C_{p}} \tag{4.3}
$$

where:

$C_p =$ compaction factor

The compaction factor is obtained from the following formula:

$$
C_{p} = \frac{\Delta t_{\text{sh}} \times C}{100} \tag{4.4}
$$

where:

$t_{\text{sh}} =$ interval transit time in a shale adjacent to the formation of interest.

$C =$ a constant which is normally 1.0 (Hilchie, 1978).

Interval transit time values from selected depths on

Table 4.1. Sonic Velocities and Interval Transit Times for Different Matrixes. These constants are used in the sonic porosity formulas above (after Schlumberger, 1972).

|  Lithology/ Fluid | Matrix velocity ft/sec | $\Delta t_{\text{matrix}}$ or $\Delta t_{\text{fluid}}$ (Wyllie) $\mu \mathrm{sec} / \mathrm{ft}$ [$\mu \mathrm{sec} / \mathrm{m}$] | $\Delta t_{\text{matrix}}$ (RHG) $\mu \mathrm{sec} / \mathrm{ft}$ [$\mu \mathrm{sec} / \mathrm{m}$]  |
| --- | --- | --- | --- |
|  Sandstone | 18,000 to 19,500 | 55.5 to 51.0 [182 to 168] | 56 [184]  |
|  Limestone | 21,000 to 23,000 | 47.6 [156] | 49 [161]  |
|  Dolomite | 23,000 to 26,000 | 43.5 [143] | 44 [144]  |
|  Anhydrite | 20,000 | 50.0 [164] |   |
|  Salt | 15,000 | 66.7 [219] |   |
|  Casing (iron) | 17,500 | 57.0 [187] |   |
|  Freshwater mud filtrate | 5,280 | 189 [620] |   |
|  Saltwater mud filtrate | 5,980 | 185 [607] |   |

Porosity Logs

39

the log in Figure 4.1 are listed in Table 4.5. Those values are used in the chart in Figure 4.2 to determine sonic porosity, which is listed in Table 4.6.

## Hydrocarbon Effects

The interval transit time ($\Delta t$) of a formation is increased due to the presence of hydrocarbons (i.e., hydrocarbon effect). If the effect of hydrocarbons is not corrected, the sonic-derived porosity is too high. Hilchie (1978) suggests the following empirical corrections for hydrocarbon effect:

$$
\phi = \phi_s \times 0.7 \quad (\text{gas}) \tag{4.5}
$$

$$
\phi = \phi_s \times 0.9 \quad (\text{oil}) \tag{4.6}
$$

## DENSITY LOG

Density is measured in grams per cubic centimeter, g/cm³ (or Kg/m³ or Mg/m³), and is indicated by the Greek letter $\rho$ (rho). Two separate density values are used by the density log: the bulk density ($\rho_b$ or RHOB) and the matrix density ($\rho_{ma}$). The bulk density is the density of the entire formation (solid and fluid parts) as measured by the logging tool. The matrix density is the density of the solid framework of the rock. It may be thought of as the density of a particular rock type (e.g., limestone or sandstone) that has no porosity. Since the late 1970s, the density log has also been used for the photoelectric-effect measurement ($P_e$, PE, or PEF) to determine lithology of a formation. The density log can assist the geologist to:

- identify evaporite minerals
- detect gas-bearing zones
- determine hydrocarbon density
- evaluate shaly-sand reservoirs and complex lithologies (Schlumberger, 1972)

The density logging tool has a relatively shallow depth of investigation, and as a result, is held against the side of the borehole during logging to maximize its response to the formation. The tool is comprised of a medium-energy gamma ray source (cobalt 60, cesium 137, or in some newer designs, an accelerator-based source). Two gamma ray detectors provide some measure of compensation for borehole conditions (similar to the sonic logging tool).

When the emitted gamma rays collide with electrons in the formation, the collisions result in a loss of energy from the gamma ray particle. The scattered

gamma rays that return to the detectors in the tool are measured in two energy ranges. The number of returning gamma rays in the higher energy range, affected by Compton scattering, is proportional to the electron density of the formation. For most earth materials of interest in hydrocarbon exploration, the electron density is related to formation bulk density through a constant (Tittman and Wahl, 1965), and the bulk density is related to porosity. Gamma ray interactions in the lower energy range are governed by the photoelectric effect. The response from this energy range is strongly dependent on lithology and only very slightly dependent on porosity.

The bulk-density curve (RHOB) is recorded in tracks 2 and 3 (Figure 4.3). The photoelectric-effect curve ($P_e$ in barns per electron, b/e) is displayed in either track 2 or track 3, with its placement set to minimize its overlap with the bulk-density curve. A correction curve (DRHO in g/cm³ or Kg/m³), is also displayed in either track 2 or track 3 (Figure 4.3). This curve indicates how much correction has been added to the bulk-density curve during processing due to borehole effects (primarily mudcake thickness) and is used primarily as a quality-control indicator. Whenever the correction curve (DRHO) exceeds 0.20 g/cm³, the value of the bulk density obtained from the bulk-density curve (RHOB) should be considered suspect and possibly invalid. A density-derived porosity curve (DPHI) is sometimes present in tracks 2 and 3 along with the bulk-density (RHOB) and correction (DRHO) curves. Track 1 usually contains a gamma ray log and a caliper (Figure 4.3).

The photoelectric-effect curve appeared as part of the second-generation density tools, which are commonly referred to as *Litho* or *Spectral* tools and were introduced around 1978.

Formation bulk density ($\rho_b$) is a function of matrix density, porosity, and density of the fluid in the pores (saltwater mud, freshwater mud, or hydrocarbons). To determine density porosity, either by chart (Figure 4.4) or by calculation, the matrix density (Table 4.2) and type of fluid in the formation must be known. The formula for calculating density porosity is:

$$
\phi_D = \frac{\rho_{ma} - \rho_b}{\rho_{ma} - \rho_{fl}} \tag{4.7}
$$

where:

$\phi_D =$ density derived porosity

$\rho_{ma} =$ matrix density (see Table 4.2 for values)

$\rho_b =$ formation bulk density (the log reading)

$\rho_{fl} =$ fluid density (see Table 4.2 for values)

40

ASQUITH AND KRYGOWSKI

Table 4.2. Matrix densities and photoelectric-effect ($P_e$) values of common lithologies (Courtesy Halliburton, 1991).

|  Lithology/ Fluid | $\rho_{ma}$ or $\rho_{fl}$ g/cm³ [Kg/m³] | $P_e$ (b/e)  |
| --- | --- | --- |
|  Sandstone | 2.644 [2644] | 1.81  |
|  Limestone | 2.710 [2710] | 5.08  |
|  Dolomite | 2.877 [2877] | 3.14  |
|  Anhydrite | 2.960 [2960] | 5.05  |
|  Salt | 2.040 [2040] | 4.65  |
|  Fresh water | 1.0 [1000] |   |
|  Salt water | 1.15 [1150] |   |
|  Barite (mud additive) |  | 267  |

## Importance of Correct $\rho_{ma}$ and $\rho_{fl}$ values

A computer in the logging unit calculates density porosity from the measured bulk density of the formation using Equation 4.7. The wellsite geologist or logging unit engineer specifies the matrix and fluid densities that are to be used. If the formation's actual matrix density ($\rho_{ma}$) is less than the matrix density used to calculate the porosity [e.g., calculating porosity of a sandstone ($\rho_{ma} = 2.64 \text{ g/cm}^3$) using a limestone matrix density ($\rho_{ma} = 2.71 \text{ g/cm}^3$)], the log shows a calculated porosity that is higher than the actual porosity of the formation. If the formation's actual fluid density is less than the fluid density used to calculate the porosity [e.g., calculating the porosity of a saltwater-filled formation ($\rho_{fl} = 1.1 \text{ g/cm}^3$) using a freshwater value ($\rho_{fl} = 1.0 \text{ g/cm}^3$)], the log shows a calculated porosity that is lower than the actual porosity of the formation. Because of the wider range of matrix-density values than fluid-density values, errors in estimating the matrix density have a larger impact on the calculated porosity.

Bulk-density values from selected depths on the log in Figure 4.3 are listed in Table 4.7. Those values are used in the chart in Figure 4.4 to determine density porosity, which is listed in Table 4.8.

## Hydrocarbon Effects

Where invasion of a formation is shallow, the low density of the formation's hydrocarbons causes the calculated density porosity to be greater than the actual porosity. Oil does not significantly affect density porosity, but gas does (gas effect). Hilchie (1978) suggests using a gas density of $0.7 \text{ g/cm}^3$ for fluid density

ty ($\rho_{fl}$) in the density-porosity formula if gas density is unknown. Because the presence of oil has little effect on the density log, this tool usually provides the best indication of porosity in liquid-filled holes.

## Heavy Minerals

Any time the bulk density of a formation ($\rho_b$) is greater than the assumed matrix density ($\rho_{ma}$) of the formation [e.g., when measurements are made in an anhydrite ($\rho_{ma} = 2.96 \text{ g/cm}^3$) but are recorded using a limestone matrix ($\rho_{ma} = 2.71 \text{ g/cm}^3$)], the resulting density porosity is negative. It is important to note that in cases like this the logging tool is operating properly, but the assumptions made in the conversion between bulk density and density porosity are incorrect. In cases like this, where the porosity is clearly erroneous (because it is negative), the log still yields good information. Negative density porosity is often a good indication of the presence of anhydrite or other heavy minerals, as shown in Figure 4.5 over the intervals 11,550 to 11,567 ft and 11,600 to 11,618 ft.

Powdered barite is commonly added to mud to increase mud density. When heavy muds are used (e.g., 14 lb/gal), the high $P_e$ of the barite (Table 4.2) in the mud can mask the $P_e$ of the adjacent rock layers.

## NEUTRON LOG

Neutron logs are porosity logs that measure the hydrogen concentration in a formation. In clean formations (i.e., shale-free) where the porosity is filled with water or oil, the neutron log measures liquid-filled porosity ($\phi_N$, PHIN, or NPHI).

Neutrons are created from a chemical source in the neutron logging tool. The chemical source is usually a mixture of americium and beryllium which continuously emit neutrons. When these neutrons collide with the nuclei of the formation the neutron loses some of its energy. With enough collisions, the neutron is absorbed by a nucleus and a gamma ray is emitted. Because the hydrogen atom is almost equal in mass to the neutron, maximum energy loss occurs when the neutron collides with a hydrogen atom. Therefore, the energy loss is dominated by the formation's hydrogen concentration. Because hydrogen in a porous formation is concentrated in the fluid-filled pores, energy loss can be related to the formation's porosity.

The neutron curves are commonly displayed over tracks 2 and 3, in units referenced to a specific lithology (usually either limestone or sandstone, depending on the geologic environment expected to be encountered), as illustrated in Figure 4.5.

Porosity Logs

41

Neutron log responses vary, depending on:

- differences in detector types and what they detect (gamma rays and/or neutrons of different energies)
- spacing between source and detector
- lithology (i.e., sandstone, limestone, and dolomite)

While the variations due to detector types and tool design are fixed (and are accounted for in the data processing), the variations in response due to lithology must be accounted for by using the appropriate charts (Figures 4.6 and 4.7). A geologist should remember that the responses of different neutron logs differ from each other (unlike all other logs) and must be interpreted from the specific chart designed for a specific log (i.e., Schlumberger charts for Schlumberger logs and Halliburton charts for Halliburton logs). The reason for this is that while other logs are calibrated in basic physical units, neutron logs are not (Dresser Atlas, 1975).

Table 4.11 shows the results of lithology corrections that are made to neutron measurements using the correct and incorrect charts for the specific neutron tool.

The first neutron logs detected the gamma rays that were products of neutron capture by formation nuclei. Initially, each logging company had its own calibration system, but eventually the American Petroleum Institute (API) developed calibration pits to provide a common standard for measurement (Serra, 1984). Generally these logs were displayed in counts per second (cps) or API Neutron Units rather than porosity. Although charts to convert from displayed units to porosity exist (Bassiouni, 1994), arbitrary conversions using core data or estimated formation porosities have most often been used. It should be noted that the neutron log response is inversely proportional to porosity so that low-measurement unit values correspond to high porosities, and high-measurement unit values correspond to low porosities.

The first modern neutron log (where porosity was directly displayed) was the sidewall neutron log. Like the density log (and for the same reason of limited depth of investigation), the sidewall neutron log has both the source and detector in a pad that is pushed against the side of the borehole. Although the sidewall neutron log was relatively insensitive to lithologic effects, it was sensitive to borehole effects, such as rugosity (roughness) which caused measurement difficulties.

The most commonly used neutron log is the compensated neutron log which has a neutron source and

two detectors. Like the sidewall neutron log, it directly displays values of porosity. The advantage of compensated neutron logs over sidewall neutron logs is that they are less affected by borehole irregularities. Both the sidewall and compensated neutron logs can be recorded in apparent limestone, sandstone, or dolomite porosity units. If a formation is limestone, and the neutron log is recorded in apparent limestone porosity units, apparent porosity is equal to true porosity. However, when the lithology of a formation is sandstone or dolomite, apparent limestone porosity must be corrected to true porosity by using the appropriate chart (Figure 4.6 illustrates the lithology corrections for one model of Halliburton neutron log, and Figure 4.7 the corrections for a Schlumberger neutron log). The procedure is identical for each of the charts and is shown in Figures 4.6 and 4.7.

Neutron-porosity values from selected depths on the log in Figure 4.5 are listed in Table 4.9. Those values are used in the chart in Figure 4.6 to determine sonic porosity, which is listed in Table 4.10.

## Hydrocarbon effects

Whenever pores are filled with gas rather than oil or water, the reported neutron porosity is less than the actual formation porosity. This occurs because there is a lower concentration of hydrogen in gas than in oil or water. This lower concentration is not accounted for by the processing software of the logging tool, and thus is interpreted as low porosity. A decrease in neutron porosity by the presence of gas is called *gas effect*.

## Shale Effect

Whenever clays are part of the formation matrix, the reported neutron porosity is greater than the actual formation porosity. This occurs because the hydrogen that is within the clay’s structure and in the water bound to the clay is sensed in addition to the hydrogen in the pore space. Because the processing software of the logging tool expects all hydrogen in the formation to reside in the pores, the extra hydrogen is interpreted as being part of the porosity. An increase in neutron porosity by the presence of clays is called *shale effect*.

## POROSITY MEASUREMENT COMBINATIONS

Although the advent of porosity logs provided a substantial improvement in log interpretation, the significant change, from a geological viewpoint, was the development of interpretive techniques that combined the measurements from different porosity tools. With

42

ASQUITH AND KRYGOWSKI

combinations of two or three measurements, lithology could be interpreted (rather than having to be known) and a better estimate of porosity produced. The interpretation of lithology and porosity is accomplished through crossplots. These are x-y plots of the quantities of interest, usually overlain with lines for "pure" lithologies (normally sandstone, limestone, and dolomite) with porosity indicated on each lithology line (e.g., Figure 4.11).

## Neutron-density Combination: Quick-look Lithology and Porosity

The combination of the neutron and density measurements is probably the most widely used porosity log combination. The neutron-density log display consists of neutron-porosity (NPHI) and density-porosity (DPHI) curves recorded in tracks 2 and 3 (Figure 4.5) and a caliper (CALI) and gamma ray (GR) in track 1. Both the neutron and density curves are normally recorded in limestone porosity units, however, porosity referenced to sandstone and dolomite can also be recorded.

The extensive use of the neutron-density combination may be due in part to the fact that they were among the first logging tools that could be physically combined and their data acquired in a single logging run. The response of the combination is such that for reconnaissance evaluation one can forego the crossplot and rely on recognition of the curve patterns (the position of the curves with respect to each other) to quickly determine the most likely predominant lithology and formation porosity.

Figure 4.8 illustrates the use of the neutron-density

combination to determine formation lithology and to estimate porosity. The reconnaissance technique works best with the following constraints:

- Both the neutron and density curves are in porosity (decimal or percent) referenced to limestone units.
- The formations are clean (no clays in the formations).
- There is no gas in the formations, only water or oil.

Using only the neutron-porosity and density-porosity curves, single lithologies can be predicted with little ambiguity. Adding the gamma ray may help, as in identifying dolomite from shale. In mixed lithologies, such as the sandy limestone and sandy dolomite shown, even the addition of the gamma ray does not help.

If the density log is of the newer *litho* or *spectral* type and a photoelectric curve ($\mathrm{P_e}$) is available, the ambiguity can be further lessened, especially in the case of mixed lithologies. The value of the $\mathrm{P_e}$ curve in mixed lithologies falls between the single lithology value of each member, so some distinction can be made. Table 4.3 summarizes the patterns and values for common lithologies.

The estimation of porosity is equally straightforward: the formation porosity can be estimated to within about 2 porosity units (0.02) by taking the average of the neutron porosity and density porosity.

In areas of the world where sand and shale intervals predominate, the neutron and density are referenced to sandstone rather than limestone to eliminate the need for matrix conversion. (This also helps highlight the gas crossover effect described below.) While Figure

Table 4.3. Estimation of formation lithologies using the neutron-density combination (Campaign, W. J., personal communication).

Neutron and density are run with a limestone matrix; formation is water filled or oil filled

|  Lithology | $\phi_N$ and $\phi_D$ | $P_e$  |
| --- | --- | --- |
|  Sandstone | Neutron-density crossover ($\phi_N > \phi_D$) of 6 to 8 porosity units. | less than 2  |
|  Limestone | Neutron and density curves overlay ($\phi_N - \phi_D$). | about 5  |
|  Dolomite | Neutron-density separation ($\phi_N < \phi_D$) of 12 to 14 porosity units. | about 3  |
|  Anhydrite | Neutron porosity is greater than density porosity ($\phi_N > \phi_D$) by 14 porosity units or more. $\phi_N$ – zero. | about 5  |
|  Salt | Neutron porosity is slightly less than zero. Density porosity is 40 porosity units (0.40) or more. Watch for washed out hole (large caliper values) and bad density data. | 4.7  |

Porosity Logs

43

4.8 focuses on lithology changes in clean (clay-free) formations with widely varying lithologies, Figure 4.9 illustrates neutron and density patterns in a variety of shaly sands, with both porosities referenced to sandstone. The effects of gas and clays are greater on the neutron measurement than on the density, with the neutron simultaneously being driven lower by gas and higher by clays in a shaly gassy formation. The exact location of the neutron curve with respect to the density curve is determined by the amounts of clay and gas present in the formation.

Table 4.12 shows the quick-look lithology determination in Figure 4.8 applied to the data in Figure 4.5.

## Neutron-density Combination: Gas Detection

Another technique using the neutron and density logs and the identification of curve patterns is that of gas identification. Gas in the pores causes the density porosity to be too high (gas has a lower density than oil or water) and causes the neutron porosity to be too low (there is a lower concentration of hydrogen atoms in gas than in oil or water). Figure 4.10 shows an example of a gas zone. In that zone, the neutron porosity is less than the density porosity, and the two porosity curves cross over each other. This is called *crossover*. The magnitude of the crossover (the amount of separation between the curves) is qualitatively related to the gas saturation, however, the crossover is more strongly influenced (again qualitatively) by the formation pressure. Low-pressure zones, either at shallow depths or depleted from production, tend to show large crossover.

Neutron-density crossover can also be caused by lithologic effects, as when the curves are displayed referenced to a lithology that is different from the actual lithology of the formation. Figure 4.8 illustrates this in the sandstone formations with the curves displayed referenced to limestone. It is important to check the log header for lithology-reference information as well as knowing the actual lithology of the formation in question before predicting the presence of gas from the log patterns only.

The porosity of a gas-bearing formation can be estimated by either form of the following equation:

$$
\phi_{NDgas} = \sqrt{\frac{\phi_N^2 + \phi_D^2}{2}} = \frac{1}{3} \times \phi_N + \frac{2}{3} \times \phi_D \tag{4.8}
$$

where:

$\phi_{NDgas} =$ porosity of the gas-bearing formation

$\phi_N =$ neutron porosity

$\phi_D =$ density porosity

## Porosity Combinations: Crossplots

Crossplots are a graphical way to solve fairly complex relationships using two (or three) porosity measurements to estimate formation lithology and porosity. All these crossplots have the same general format: one measurement is displayed along the x-axis, and another is displayed along the y-axis. The measurements are either in porosity units referenced to limestone or, in the case of density and sonic logs, they can be in the original measurement units ($\rho_b$ in $\mathrm{g/cm^3}$ or $\mathrm{Kg/m^3}$ for the density, and $\Delta t$ in $\mu\mathrm{sec/ft}$ or $\mu\mathrm{sec/m}$ for the sonic). Superimposed on the plot (as an *overlay*) are *pure* lithology lines, usually sandstone, limestone, and dolomite. Porosity is indicated along each of these lines. See Figure 4.11 as an example.

In the interpretation, the values of the two measurements of interest are plotted on the crossplot. The intersection of those values on the plot determines both the porosity and the lithology of the point. If the point lies between two lithology lines, the lithology is taken as a mixture of those two lithologies (with the dominant lithology being that of the line closest to the point). The porosity is estimated by joining points of equal porosity on the two lithology lines and interpolating between the lines of equal porosity. Figure 4.11 illustrates the interpretive process.

It should be noted that not all interpretations are unique. In fact, the data often plot in such a way that there are two possible lithology pairs, and the decision of which to chose lies with the interpreter's knowledge of the area (or the application of other data). In some plots, as noted below and shown in the accompanying figures, the choice of lithologic pair significantly affects the predicted porosity value.

Other minerals can also be plotted on the crossplot, as distinct points (rather than lines indicating varying porosity). Figure 4.11 shows the location of halite and anhydrite. Log values for other pure minerals are available in the log interpretation chartbooks provided by most well log (wireline and MWD) acquisition companies. Although the existence of pure (and thick) beds of some minerals is very rare, the location of the mineral point on the crossplot (and the shift of the data toward that point) may sometimes give some indication that the mineral is present in the formation of interest.

Table 4.4 details the advantages and limitations of each of the four crossplots. The crossplots are listed in the order of preference of use, from top to bottom.

Figures 4.11 to 4.14 and Tables 4.13 to 4.15 illustrate the determination of porosity and lithology using the first three crossplot techniques in Table 4.4.

44

ASQUITH AND KRYGOWSKI

Table 4.4. Comparison of porosity crossplots (in order of preference of use)

|  Crossplot | Advantages | Limitations  |
| --- | --- | --- |
|  Neutron Density (Figure 4.11) | Given two possible lithology pair solutions, the porosity remains relatively invariant between solutions. The combination of neutron and density is the most common of all porosity tool pairs. | In rough holes or in heavy drilling muds, the density data might be invalid.  |
|  Neutron Sonic (Figure 4.12) | Given two possible lithology pair solutions, the porosity remains relatively invariant between solutions. The sonic is less sensitive to rough holes than the density. | The combination of sonic and neutron data (without the density) is not common.  |
|  Spectral Density (bulk density-P_{e}) (Figure 4.13) | Both measurements are made with the same logging tool; both will be available in newer wells. | The choice of lithology pair will have a significant effect of the estimation of porosity. In rough holes or in heavy drilling mud, the data may be invalid. The P_{e} measurement will not be present in wells logged before about 1978.  |
|  Sonic Density (Figure 4.14) | Best for identifying radioactive reservoirs, rather than predicting lithology and porosity: Potential reservoirs plot along the closely spaced lithology lines while shales tend to fall toward the lower right of the plot. This can indicate the presence of radioactive reservoirs which are intermingled with shales (which tend to have high radioactivity). | The choice of lithology pair has a significant effect on the estimation of porosity. The lithology lines are closely spaced, so any uncertainty in the measurements produces large changes in the lithology and porosity estimates.  |

## Extending the Crossplot Technique

Given that the use of two porosity measurements can lead to the prediction of a more lithologically complex subsurface (i.e., the formation described as a two-mineral mixture), the natural extension is to use three measurements to estimate a ternary mixture. There are two different techniques, with one having two variations. Both techniques are more concerned with determining lithology than with determining porosity, the porosity having been determined from the previous two-measurement crossplots (usually the neutron-density).

## M-N Lithology Plots

This technique is the oldest of the three-measurement lithology techniques, and was based on combining the three porosity measurements in such a way so that two quantities could be used in a crossplot. The two calculated quantities are:

$$
M = \frac{\Delta t_{ft} - \Delta t}{\rho_b - \rho_{ft}} \times 0.01
$$

$$
\left( M = \frac{\Delta t_{ft} - \Delta t}{\rho_b - \rho_{ft}} \times 0.003 \text{ (metric)} \right) \tag{4.9}
$$

Porosity Logs

45

Table 4.5. Values to be used with the chart in Figure 4.2 to determine the sonic porosity, SPHI.

|  Depth | Raw Data |   |   |   | SPHI (Wyllie) |   | SPHI (RHG) |   | DPHI |   | NPHI  |   |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|   |  DT | RHOB | PE | NPHI | Lime | Dolo | Lime | Dolo | Lime | Dolo | Dolo | Sand  |
|  11,508 | 51 |  |  |  |  |  |  |  |  |  |  |   |
|  11,522 | 47 |  |  |  |  |  |  |  |  |  |  |   |
|  |   |   |   |   |   |   |   |   |   |   |   |   |
|  11,545 | 57 |  |  |  |  |  |  |  |  |  |  |   |
|  11,560 | 48 |  |  |  |  |  |  |  |  |  |  |   |
|  |   |   |   |   |   |   |   |   |   |   |   |   |
|  11,593 | 50 |  |  |  |  |  |  |  |  |  |  |   |
|  11,615 | 51 |  |  |  |  |  |  |  |  |  |  |   |
|  11,631 | 67 |  |  |  |  |  |  |  |  |  |  |   |
|  11,645 | 52 |  |  |  |  |  |  |  |  |  |  |   |
|  11,655 | 57 |  |  |  |  |  |  |  |  |  |  |   |
|  11,665 | 52 |  |  |  |  |  |  |  |  |  |  |   |
|  11,696 | 50 |  |  |  |  |  |  |  |  |  |  |   |

Table 4.6. Determination of sonic porosity by two methods.

|  Depth | Raw Data |   |   |   | SPHI (Wyllie) |   | SPHI (RHG) |   | DPHI |   | NPHI  |   |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|   |  DT | RHOB | PE | NPHI | Lime | Dolo | Lime | Dolo | Lime | Dolo | Dolo | Sand  |
|  11,508 | 51 |  |  |  | 0.024 | 0.051 | 0.053 | 0.110 |  |  |  |   |
|  11,522 | 47 |  |  |  | 0.000 | 0.025 | 0.000 | 0.060 |  |  |  |   |
|  |   |   |   |   |   |   |   |   |   |   |   |   |
|  11,545 | 57 |  |  |  | 0.067 | 0.092 | 0.125 | 0.170 |  |  |  |   |
|  11,560 | 48 |  |  |  | 0.005 | 0.031 | 0.010 | 0.073 |  |  |  |   |
|  |   |   |   |   |   |   |   |   |   |   |   |   |
|  11,593 | 50 |  |  |  | 0.017 | 0.045 | 0.040 | 0.098 |  |  |  |   |
|  11,615 | 51 |  |  |  | 0.024 | 0.051 | 0.053 | 0.010 |  |  |  |   |
|  11,631 | 67 |  |  |  | 0.138 | 0.163 | 0.203 | 0.235 |  |  |  |   |
|  11,645 | 52 |  |  |  | 0.032 | 0.059 | 0.070 | 0.122 |  |  |  |   |
|  11,655 | 57 |  |  |  | 0.067 | 0.092 | 0.125 | 0.170 |  |  |  |   |
|  11,665 | 52 |  |  |  | 0.032 | 0.059 | 0.070 | 0.122 |  |  |  |   |
|  11,696 | 50 |  |  |  | 0.017 | 0.045 | 0.040 | 0.098 |  |  |  |   |

46

ASQUITH AND KRYGOWSKI

Table 4.7. Values to be used with the chart in Figure 4.4 to determine the density porosity, DPHI.

|  Depth | Raw Data |   |   |   | SPHI (Wyllie) |   | SPHI (RHG) |   | DPHI |   | NPHI  |   |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|   |  DT | RHOB | PE | NPHI | Lime | Dolo | Lime | Dolo | Lime | Dolo | Dolo | Sand  |
|  11,508 | 51 |  |  |  | 0.024 | 0.051 | 0.053 | 0.110 |  |  |  |   |
|  11,522 | 47 | 2.75 |  |  | 0.000 | 0.025 | 0.000 | 0.060 |  |  |  |   |
|  |   |   |   |   |   |   |   |   |   |   |   |   |
|  11,545 | 57 |  |  |  | 0.067 | 0.092 | 0.125 | 0.170 |  |  |  |   |
|  11,560 | 48 |  |  |  | 0.005 | 0.031 | 0.010 | 0.073 |  |  |  |   |
|  |   |   |   |   |   |   |   |   |   |   |   |   |
|  11,593 | 50 |  |  |  | 0.017 | 0.045 | 0.040 | 0.098 |  |  |  |   |
|  11,615 | 51 |  |  |  | 0.024 | 0.051 | 0.053 | 0.010 |  |  |  |   |
|  11,631 | 67 | 2.50 |  |  | 0.138 | 0.163 | 0.203 | 0.235 |  |  |  |   |
|  11,645 | 52 |  |  |  | 0.032 | 0.059 | 0.070 | 0.122 |  |  |  |   |
|  11,655 | 57 | 2.64 |  |  | 0.067 | 0.092 | 0.125 | 0.170 |  |  |  |   |
|  11,665 | 52 | 2.68 |  |  | 0.032 | 0.059 | 0.070 | 0.122 |  |  |  |   |
|  11,696 | 50 |  |  |  | 0.017 | 0.045 | 0.040 | 0.098 |  |  |  |   |

Table 4.8. Determination of density porosity.

|  Depth | Raw Data |   |   |   | SPHI (Wyllie) |   | SPHI (RHG) |   | DPHI |   | NPHI  |   |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|   |  DT | RHOB | PE | NPHI | Lime | Dolo | Lime | Dolo | Lime | Dolo | Dolo | Sand  |
|  11,508 | 51 | 2.73 |  |  | 0.024 | 0.051 | 0.053 | 0.110 | -0.013 | 0.078 |  |   |
|  11,522 | 47 | 2.75 |  |  | 0.000 | 0.025 | 0.000 | 0.060 | -0.022 | 0.068 |  |   |
|  |   |   |   |   |   |   |   |   |   |   |   |   |
|  11,545 | 57 | 2.67 |  |  | 0.067 | 0.092 | 0.125 | 0.170 | 0.022 | 0.110 |  |   |
|  11,560 | 48 | 2.96 |  |  | 0.005 | 0.031 | 0.010 | 0.073 | < 0 | < 0 |  |   |
|  |   |   |   |   |   |   |   |   |   |   |   |   |
|  11,593 | 50 | 2.70 |  |  | 0.017 | 0.045 | 0.040 | 0.098 | 0.005 | 0.095 |  |   |
|  11,615 | 51 | 2.97 |  |  | 0.024 | 0.051 | 0.053 | 0.010 | < 0 | < 0 |  |   |
|  11,631 | 67 | 2.50 |  |  | 0.138 | 0.163 | 0.203 | 0.235 | 0.125 | 0.200 |  |   |
|  11,645 | 52 | 2.82 |  |  | 0.032 | 0.059 | 0.070 | 0.122 | < 0 | 0.030 |  |   |
|  11,655 | 57 | 2.64 |  |  | 0.067 | 0.092 | 0.125 | 0.170 | 0.042 | 0.125 |  |   |
|  11,665 | 52 | 2.68 |  |  | 0.032 | 0.059 | 0.070 | 0.122 | 0.020 | 0.105 |  |   |
|  11,696 | 50 | 2.76 |  |  | 0.017 | 0.045 | 0.040 | 0.098 | -0.028 | 0.063 |  |   |

Porosity Logs

47

Table 4.9. Values will be used with the chart in Figure 4.4 to determine the neutron porosity, NPHI, referenced to other lithologies (dolomite and sandstone).

|  Depth | Raw Data |   |   |   | SPHI (Wyllie) |   | SPHI (RHG) |   | DPHI |   | NPHI  |   |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|   |  DT | RHOB | PE | NPHI | Lime | Dolo | Lime | Dolo | Lime | Dolo | Dolo | Sand  |
|  11,508 | 51 | 2.73 |  |  | 0.024 | 0.051 | 0.053 | 0.110 | -0.013 | 0.078 |  |   |
|  11,522 | 47 | 2.75 |  | 0.090 | 0.000 | 0.025 | 0.000 | 0.060 | -0.022 | 0.068 |  |   |
|  |   |   |   |   |   |   |   |   |   |   |   |   |
|  11,545 | 57 | 2.67 |  |  | 0.067 | 0.092 | 0.125 | 0.170 | 0.022 | 0.110 |  |   |
|  11,560 | 48 | 2.96 |  |  | 0.005 | 0.031 | 0.010 | 0.073 | < 0 | < 0 |  |   |
|  |   |   |   |   |   |   |   |   |   |   |   |   |
|  11,593 | 50 | 2.70 |  |  | 0.017 | 0.045 | 0.040 | 0.098 | 0.005 | 0.095 |  |   |
|  11,615 | 51 | 2.97 |  |  | 0.024 | 0.051 | 0.053 | 0.010 | < 0 | < 0 |  |   |
|  11,631 | 67 | 2.50 |  | 0.290 | 0.138 | 0.163 | 0.203 | 0.235 | 0.125 | 0.200 |  |   |
|  11,645 | 52 | 2.82 |  |  | 0.032 | 0.059 | 0.070 | 0.122 | < 0 | 0.030 |  |   |
|  11,655 | 57 | 2.64 |  | 0.160 | 0.067 | 0.092 | 0.125 | 0.170 | 0.042 | 0.125 |  |   |
|  11,665 | 52 | 2.68 |  | 0.010 | 0.032 | 0.059 | 0.070 | 0.122 | 0.020 | 0.105 |  |   |
|  11,696 | 50 | 2.76 |  |  | 0.017 | 0.045 | 0.040 | 0.098 | -0.028 | 0.063 |  |   |

Table 4.10. Lithology conversions for the neutron log.

|  Depth | Raw Data |   |   |   | SPHI (Wyllie) |   | SPHI (RHG) |   | DPHI |   | NPHI  |   |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|   |  DT | RHOB | PE | NPHI | Lime | Dolo | Lime | Dolo | Lime | Dolo | Dolo | Sand  |
|  11,508 | 51 | 2.73 |  | 0.005 | 0.024 | 0.051 | 0.053 | 0.110 | -0.013 | 0.078 | < 0 | 0.015  |
|  11,522 | 47 | 2.75 |  | 0.090 | 0.000 | 0.025 | 0.000 | 0.060 | -0.022 | 0.068 | 0.070 | 0.140  |
|  |   |   |   |   |   |   |   |   |   |   |   |   |
|  11,545 | 57 | 2.67 |  | 0.130 | 0.067 | 0.092 | 0.125 | 0.170 | 0.022 | 0.110 | 0.105 | 0.185  |
|  11,560 | 48 | 2.96 |  | -0.010 | 0.005 | 0.031 | 0.010 | 0.073 | < 0 | < 0 | < 0 | < 0  |
|  |   |   |   |   |   |   |   |   |   |   |   |   |
|  11,593 | 50 | 2.70 |  | 0.000 | 0.017 | 0.045 | 0.040 | 0.098 | 0.005 | 0.095 | < 0 | 0.015  |
|  11,615 | 51 | 2.97 |  | -0.010 | 0.024 | 0.051 | 0.053 | 0.010 | < 0 | < 0 | < 0 | < 0  |
|  11,631 | 67 | 2.50 |  | 0.290 | 0.138 | 0.163 | 0.203 | 0.235 | 0.125 | 0.200 | 0.250 | 0.365  |
|  11,645 | 52 | 2.82 |  | 0.140 | 0.032 | 0.059 | 0.070 | 0.122 | < 0 | 0.030 | 0.115 | 0.200  |
|  11,655 | 57 | 2.64 |  | 0.160 | 0.067 | 0.092 | 0.125 | 0.170 | 0.042 | 0.125 | 0.135 | 0.220  |
|  11,665 | 52 | 2.68 |  | 0.010 | 0.032 | 0.059 | 0.070 | 0.122 | 0.020 | 0.105 | < 0 | 0.030  |
|  11,696 | 50 | 2.76 |  | 0.010 | 0.017 | 0.045 | 0.040 | 0.098 | < 0 | 0.063 | < 0 | 0.030  |

48

ASQUITH AND KRYGOWSKI

Table 4.11. Differences in neutron porosity using correct and incorrect charts for the specific neutron tool.

|  Zone | Log Values |   |   | NPHI (incorrect chart for the example data) |   | NPHI (incorrect chart for the example data)  |   |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  Depth | NPHI | RHOB | DT | dolo | sand | dolo | sand  |
|  11,508 |  |  |  |  |  |  |   |
|  11,631 | 0.29 | 2.50 | 67 | 0.250 | 0.365 | 0.210 | 0.335  |
|  11,645 |  |  |  |  |  |  |   |
|  11,655 | 0.16 | 2.64 | 57 | 0.135 | 0.220 | 0.080 | 0.210  |
|  11,665 | 0.01 | 2.68 | 52 | < 0 | 0.030 | < 0 | 0.040  |
|  11,696 |  |  |  |  |  |  |   |

Table 4.12. Lithology determination on the data from the intervals in Figure 4.5, using the curve patterns in Figure 4.8.

|  Depth | Zone range | Raw Data |   |   |   | ND Quicklook  |
| --- | --- | --- | --- | --- | --- | --- |
|   |   |  RHOB | DPHI | PE | NPHI | Lithology  |
|  11,508 | 11,490-11,518 | 2.73 | -0.013 | 5.0 | 0.005 | Limestone  |
|  11,522 | 11,518-11,528 | 2.75 | -0.022 | 3.2 | 0.090 | Dolomite  |
|   | 11,528-11,543 |  |  |  |  | Dolomite w/anhydrite  |
|  11,545 | 11,543-11,546 | 2.67 | 0.020 | 3.7 | 0.130 | Dolomite  |
|  11,560 | 11,546-11,570 | 2.96 | < 0 | 4.8 | -0.010 | Anhydrite  |
|   | 11,570-11,580 |  |  |  |  | Dolomite (w/anhydrite?)  |
|  11,593 | 11,580-11,598 | 2.70 | 0.005 | 5.6 | 0.000 | Limestone  |
|  11,615 | 11,598-11,625 | 2.97 | < 0 | 5.1 | -0.010 | Anhydrite  |
|  11,631 | 11,625-11,641 | 2.50 | 0.125 | 3.8 | 0.290 | Dolomite  |
|  11,645 | 11,641-11,649 | 2.82 | < 0 | 3.5 | 0.140 | Dolomite (w/anhydrite?)  |
|  11,655 | 11,649-11,659 | 2.64 | 0.042 | 3.5 | 0.160 | Dolomite  |
|  11,665 | 11,659-11,680 | 2.68 | 0.020 | 5.5 | 0.010 | Limestone  |
|  11,696 | > 11680 | 2.76 | -0.028 | 5.1 | 0.010 | Limestone w/anhydrite  |

$$N = \frac{\phi_{Nfl} - \phi_N}{\rho_b - \rho_{fl}} \tag{4.10}$$

where:

$\Delta t$ = interval transit time in the formation (from the log)

$\Delta t_{fl}$ = interval transit time in the fluid in the formation

$\rho_b$ = formation bulk density (from the log)

$\rho_{fl}$ = fluid density

$\phi_N$ = neutron porosity (in limestone units, from the log)

$\phi_{Nfl}$ = neutron porosity of the fluid of the formation (usually = 1.0)

Figure 4.15 shows the resulting plot. As in the two-mineral crossplots, a number of common mineral points are plotted. For the common minerals (lithologies) of interest (quartz [sandstone], calcite [limestone], and dolomite), each mineral is associated with a group of points. The open and closed circles connected by dashed lines indicate the location of the point in freshwater and saltwater muds, respectively. The groups of these connected points indicate ranges in porosity.

Porosity Logs

49

Table 4.13. Log values from Figures 4.1, 4.3, and 4.5, used to determine porosity and lithology.

|  Depth | Raw Data |   |   |   | Neutron-Density Crossplot  |   |
| --- | --- | --- | --- | --- | --- | --- |
|   |  DT | RHOB | PE | NPHI | Lithology | PhiND  |
|  11,508 | 51 | 2.73 | 5.0 | 0.005 | Limestone | 0.000  |
|  11,522 | 47 | 2.75 | 3.2 | 0.090 | Dolomite | 0.070  |
|  |   |   |   |   |   |   |
|  11,545 | 57 | 2.67 | 3.7 | 0.130 | Dolomite | 0.110  |
|  11,560 | 48 | 2.96 | 4.8 | -0.010 | Anhydrite | 0.000  |
|  |   |   |   |   |   |   |
|  11,593 | 50 | 2.70 | 5.6 | 0.000 | Limestone | 0.000  |
|  11,615 | 51 | 2.97 | 5.1 | -0.010 | Anhydrite | 0.000  |
|  11,631 | 67 | 2.50 | 3.8 | 0.290 | Dolomite (w/anhydrite?) | 0.230  |
|  11,645 | 52 | 2.82 | 3.5 | 0.140 | Dolomite (w/anhydrite?) | 0.100  |
|  11,655 | 57 | 2.64 | 3.5 | 0.160 | Dolomite | 0.130  |
|  11,665 | 52 | 2.68 | 5.5 | 0.010 | Limestone | 0.010  |
|  11,696 | 50 | 2.76 | 5.1 | 0.010 | Dolomitic limestone | 0.005  |

Table 4.14. Log values from Figures 4.1, 4.3, and 4.5, used to determine porosity and lithology.

|  Depth | Raw Data |   |   |   | Neutron-Sonic Crossplot  |   |
| --- | --- | --- | --- | --- | --- | --- |
|   |  DT | RHOB | PE | NPHI | Lithology | PhiNS  |
|  11,508 | 51 | 2.73 | 5.0 | 0.005 | Sandy limestone | 0.000  |
|  11,522 | 47 | 2.75 | 3.2 | 0.090 | Dolomite | 0.070  |
|  |   |   |   |   |   |   |
|  11,545 | 57 | 2.67 | 3.7 | 0.130 | Limestone | 0.130  |
|  11,560 | 48 | 2.96 | 4.8 | -0.010 | Anhydrite | 0.000  |
|  |   |   |   |   |   |   |
|  11,593 | 50 | 2.70 | 5.6 | 0.000 | Limestone | 0.010  |
|  11,615 | 51 | 2.97 | 5.1 | -0.010 | Anhydrite? | 0.000  |
|  11,631 | 67 | 2.50 | 3.8 | 0.290 | Dolomite | 0.240  |
|  11,645 | 52 | 2.82 | 3.5 | 0.140 | Dolomite | 0.120  |
|  11,655 | 57 | 2.64 | 3.5 | 0.160 | Limy dolomite | 0.145  |
|  11,665 | 52 | 2.68 | 5.5 | 0.010 | Sandy limestone | 0.020  |
|  11,696 | 50 | 2.76 | 5.1 | 0.010 | Sandy limestone | 0.010  |

50

ASQUITH AND KRYGOWSKI

Table 4.15. Log values from Figures 4.1, 4.3, and 4.5, used to determine porosity and lithology.

|  Depth | Raw Data |   |   |   | Spectral Density Crossplot  |   |
| --- | --- | --- | --- | --- | --- | --- |
|   |  DT | RHOB | PE | NPHI | Lithology | PhiSpD  |
|  11,508 | 51 | 2.73 | 5.0 | 0.005 | Limestone (w/anhydrite?) | 0.000  |
|  11,522 | 47 | 2.75 | 3.2 | 0.090 | Dolomite | 0.060  |
|  |   |   |   |   |   |   |
|  11,545 | 57 | 2.67 | 3.7 | 0.130 | Limy dolomite | 0.080  |
|  11,560 | 48 | 2.96 | 4.8 | -0.010 | Anhydrite | 0.000  |
|  |   |   |   |   |   |   |
|  11,593 | 50 | 2.70 | 5.6 | 0.000 | Limestone | 0.000  |
|  11,615 | 51 | 2.97 | 5.1 | -0.010 | Anhydrite | 0.000  |
|  11,631 | 67 | 2.50 | 3.8 | 0.290 | Limy dolomite | 0.160  |
|  11,645 | 52 | 2.82 | 3.5 | 0.140 | Limy dolomite | 0.010  |
|  11,655 | 57 | 2.64 | 3.5 | 0.160 | Limy dolomite | 0.100  |
|  11,665 | 52 | 2.68 | 5.5 | 0.010 | Limestone | 0.010  |
|  11,696 | 50 | 2.76 | 5.1 | 0.010 | Limestone (w/anhydrite?) | 0.000  |

Data plotted on this crossplot show the following patterns: For a single pure mineralogy, the data plot around the point representing that mineralogy. For binary mineral systems, the data plot along a line connecting the two mineralogical members, with the location of the points along the line indicative of the mineral mixture of each point. For ternary systems, the data plot in a triangle with the three member mineralogies as the vertices of the triangle, and with the location of each data point in the triangle indicative of the mineral mixture of that point. Note that porosity is not predicted from this plot but is determined from the earlier two-component crossplots.

Although two common mineral triangles are usually used as examples (either quartz/calcite/dolomite or calcite/dolomite/anhydrite), any three minerals that plot uniquely on the crossplot can be used. One need not see data clustered around a particular mineral endpoint to sense the presence of a mineral. The presence of small amounts of a mineral tend to draw the data away from the primary mineral (or mineral mixture) and toward the secondary mineral endpoint.

Table 4.16 shows the calculation of $M$ and $N$ values and the resulting lithology estimations from Figure 4.15.

## Mineral-identification Plots

These plots rely on the calculation of apparent matrix values as crossplot parameters. The apparent matrix values are determined (when done graphically) through what are essentially crossplots, created to emphasize matrix values rather than porosity. Apparent matrix density $(\rho_{\mathrm{maa}})$ is determined from an equivalent of the neutron-density crossplot and is shown in Figure 4.16. Apparent matrix travel time $(\Delta t_{\mathrm{maa}})$ is determined from an equivalent of the neutron-sonic crossplot and is shown in Figure 4.17. The calculation of apparent matrix values (Western Atlas, 1995) is:

$$
\rho_{\mathrm{maa}} = \frac{\rho_b - \phi_{ND} \times \rho_{fl}}{1 - \phi_{ND}} \tag{4.11}
$$

$$
\Delta t_{\mathrm{maa}} = \frac{\Delta t - \phi_{NS} \times \Delta t_{fl}}{1 - \phi_{NS}} \tag{4.12}
$$

where:

$\rho_b =$ bulk density (from the log)

$\rho_{fl} =$ fluid density

$\phi_{ND} =$ neutron-density crossplot porosity

$\Delta t =$ interval transit time (from the log)

$\Delta t_{fl} =$ fluid transit time

Porosity Logs

51

Table 4.16. Log values from Figures 4.1, 4.3, and 4.5, lists of values of M and N calculated from the equations above, and lithology estimates from the M-N crossplot.

|  Depth | Raw Data |   |   |   | M-N Lithology Plot  |   |   |
| --- | --- | --- | --- | --- | --- | --- | --- |
|   |  DT | RHOB | PE | NPHI | M | N | Lithology  |
|  11,508 | 51 | 2.73 | 5.0 | 0.005 | 0.798 | 0.578 | Limestone (w/anhydrite?)  |
|  11,522 | 47 | 2.75 | 3.2 | 0.090 | 0.811 | 0.520 | Dolomite  |
|  |   |   |   |   |   |   |   |
|  11,545 | 57 | 2.67 | 3.7 | 0.130 | 0.790 | 0.521 | Dolomite  |
|  11,560 | 48 | 2.96 | 4.8 | -0.010 | 0.719 | 0.515 | Anhydrite  |
|  |   |   |   |   |   |   |   |
|  11,593 | 50 | 2.70 | 5.6 | 0.000 | 0.818 | 0.588 | Limestone  |
|  11,615 | 51 | 2.97 | 5.1 | -0.010 | 0.701 | 0.513 | Anhydrite  |
|  11,631 | 67 | 2.50 | 3.8 | 0.290 | 0.813 | 0.473 | Limy dolomite  |
|  11,645 | 52 | 2.82 | 3.5 | 0.140 | 0.753 | 0.473 | Dolomite  |
|  11,655 | 57 | 2.64 | 3.5 | 0.160 | 0.805 | 0.512 | Limy dolomite  |
|  11,665 | 52 | 2.68 | 5.5 | 0.010 | 0.815 | 0.589 | Limestone  |
|  11,696 | 50 | 2.76 | 5.1 | 0.010 | 0.790 | 0.563 | Dolomite  |

$\phi_{NS} =$ neutron-sonic crossplot porosity

The neutron and density data (through the neutron-density crossplot) produce an apparent matrix density (as well as a neutron-density crossplot porosity), and the neutron and sonic data (through the neutron-sonic crossplot) produce an apparent matrix travel time (as well as a neutron-sonic crossplot porosity).

These two apparent matrix values are then applied to a crossplot (Figure 4.18). In Figure 4.18, the three common lithologies, highlighted in the previous crossplots, occur on the plot as points which are connected to form a triangle. The location of the point on the plot, with respect to that mineral triangle, indicates the relative lithologic mixture. In practice, any three minerals that have unique values (with respect to each other) can be used as endpoints in a mineral triangle (e.g., a calcite, dolomite, and anhydrite choice is common in a known carbonate area). As with the $M-N$ plot described previously, data from a single pure mineralogy plot around the point representing that mineralogy. For binary mineral systems, the data plot along a line connecting the two mineralogical members, with the location of the points along the line indicative of the mineral mixture of each point. Note that porosity is not predicted from this plot, but is determined from the earlier two-component crossplots.

Figures 4.16 and 4.17 and Tables 4.17 and 4.18

show the calculation of apparent matrix values. Figure 4.18 and Table 4.19 show the application of those apparent matrix values to determine lithology.

A variation on this technique was developed with the advent of the $\mathrm{P_e}$ curve on the more recent density logs. Using the $\mathrm{P_e}$ curve, the bulk-density curve, and the neutron porosity another matrix parameter, apparent matrix volumetric photoelectric factor $(\mathrm{U}_{\mathrm{maa}})$, can be determined (as shown in Figure 4.19), or its value can be calculated from (Western Atlas, 1995):

$$
U_{maa} = \frac{(Pe \times \rho_b) - (\phi_{ND} \times U_{fl})}{1 - \phi_{ND}} \tag{4.13}
$$

where:

$U_{fl} =$ fluid volumetric cross section (0.398 barns/cm$^3$ for fresh water, 1.36 barns/cm$^3$ for salt water)

$\phi_{ND} =$ porosity from the neutron-density crossplot

This apparent matrix crossplot then uses apparent matrix density, $\rho_{maa}$, and apparent matrix volumetric cross section, $\mathrm{U}_{maa}$, to determine formation lithology (Figure 4.20). As with the $\rho_{maa} - \Delta \rho_{maa}$ crossplot, the three common lithologies are connected in a mineral triangle, but any three unique mineralogies can be used to estimate a three-mineral solution.

Figures 4.16 and 4.19, and Tables 4.17 and 4.20

52

ASQUITH AND KRYGOWSKI

Table 4.17. Log values from Figures 4.1, 4.3, and 4.5, and a list of values of apparent matrix density determined from the crossplot.

|  Depth | Raw Data |   |   |   | Apparent Matrix Values |   |   | MID Plot  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
|   |  DT | RHOB | PE | NPHI | DTmaa | Rhomaa | Umaa | Lithology  |
|  11,508 | 51 | 2.73 | 5.0 | 0.005 |  | 2.74 |  |   |
|  11,522 | 47 | 2.75 | 3.2 | 0.090 |  | 2.89 |  |   |
|  |   |   |   |   |   |   |   |   |
|  11,545 | 57 | 2.67 | 3.7 | 0.130 |  | 2.88 |  |   |
|  11,560 | 48 | 2.96 | 4.8 | -0.010 |  | 2.97 |  |   |
|  |   |   |   |   |   |   |   |   |
|  11,593 | 50 | 2.70 | 5.6 | 0.000 |  | 2.70 |  |   |
|  11,615 | 51 | 2.97 | 5.1 | -0.010 |  | 2.99 |  |   |
|  11,631 | 67 | 2.50 | 3.8 | 0.290 |  | 3.07 |  |   |
|  11,645 | 52 | 2.82 | 3.5 | 0.140 |  | 3.15 |  |   |
|  11,655 | 57 | 2.64 | 3.5 | 0.160 |  | 2.91 |  |   |
|  11,665 | 52 | 2.68 | 5.5 | 0.010 |  | 2.70 |  |   |
|  11,696 | 50 | 2.76 | 5.1 | 0.010 |  | 2.77 |  |   |

Table 4.18. Log values from Figures 4.1, 4.3, and 4.5, and a list values of apparent matrix transit time determined from the crossplot.

|  Depth | Raw Data |   |   |   | Apparent Matrix Values |   |   | MID Plot  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
|   |  DT | RHOB | PE | NPHI | DTmaa | Rhomaa | Umaa | Lithology  |
|  11,508 | 51 | 2.73 | 5.0 | 0.005 | 51.0 | 2.74 |  |   |
|  11,522 | 47 | 2.75 | 3.2 | 0.090 | 43.0 | 2.89 |  |   |
|  |   |   |   |   |   |   |   |   |
|  11,545 | 57 | 2.67 | 3.7 | 0.130 | 47.5 | 2.88 |  |   |
|  11,560 | 48 | 2.96 | 4.8 | -0.010 | 48.0 | 2.97 |  |   |
|  |   |   |   |   |   |   |   |   |
|  11,593 | 50 | 2.70 | 5.6 | 0.000 | 50.0 | 2.70 |  |   |
|  11,615 | 51 | 2.97 | 5.1 | -0.010 | 52.0 | 2.99 |  |   |
|  11,631 | 67 | 2.50 | 3.8 | 0.290 | 43.0 | 3.07 |  |   |
|  11,645 | 52 | 2.82 | 3.5 | 0.140 | 44.0 | 3.15 |  |   |
|  11,655 | 57 | 2.64 | 3.5 | 0.160 | 45.5 | 2.91 |  |   |
|  11,665 | 52 | 2.68 | 5.5 | 0.010 | 51.0 | 2.70 |  |   |
|  11,696 | 50 | 2.76 | 5.1 | 0.010 | 49.5 | 2.77 |  |   |

Porosity Logs

53

Table 4.19. Log values from Figures 4.1, 4.3, and 4.5, apparent matrix values from Figures 4.16 and 4.17, and a list of the estimates of lithology determined from the crossplot.

|  Depth | Raw Data |   |   |   | Apparent Matrix Values |   |   | NDS MID Plot  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
|   |  DT | RHOB | PE | NPHI | DTmaa | Rhomaa | Umaa | Lithology  |
|  11,508 | 51 | 2.73 | 5.0 | 0.005 | 51.0 | 2.74 |  | Dolomitic sand  |
|  11,522 | 47 | 2.75 | 3.2 | 0.090 | 43.0 | 2.89 |  | Dolomite  |
|  |   |   |   |   |   |   |   |   |
|  11,545 | 57 | 2.67 | 3.7 | 0.130 | 47.5 | 2.88 |  | Dolomite (w/anhydrite?)  |
|  11,560 | 48 | 2.96 | 4.8 | -0.010 | 48.0 | 2.97 |  | Anhydrite  |
|  |   |   |   |   |   |   |   |   |
|  11,593 | 50 | 2.70 | 5.6 | 0.000 | 50.0 | 2.70 |  | Sandy limestone  |
|  11,615 | 51 | 2.97 | 5.1 | -0.010 | 52.0 | 2.99 |  | Anhydrite  |
|  11,631 | 67 | 2.50 | 3.8 | 0.290 | 43.0 | 3.07 |  | Dolomite?  |
|  11,645 | 52 | 2.82 | 3.5 | 0.140 | 44.0 | 3.15 |  | off chart  |
|  11,655 | 57 | 2.64 | 3.5 | 0.160 | 45.5 | 2.91 |  | Dolomite  |
|  11,665 | 52 | 2.68 | 5.5 | 0.010 | 51.0 | 2.70 |  | Sandy limestone (w/dolomite?)  |
|  11,696 | 50 | 2.76 | 5.1 | 0.010 | 49.5 | 2.77 |  | Sandy dolomite  |

Table 4.20. Log values from Figures 4.1, 4.3, and 4.5, and a list of values of apparent matrix transit time determined from the crossplot.

|  Depth | Raw Data |   |   |   | PhiND | Apparent Matrix Values |   |   | MID Plot  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|   |  DT | RHOB | PE | NPHI |   | DTmaa | Rhomaa | Umaa | Lithology  |
|  11,508 | 51 | 2.73 | 5.0 | 0.000 | 0.000 | 51.0 | 2.74 | 13.7 |   |
|  11,522 | 47 | 2.75 | 3.2 | 0.090 | 0.070 | 43.0 | 2.89 | 9.2 |   |
|  |   |   |   |   |   |   |   |   |   |
|  11,545 | 57 | 2.67 | 3.7 | 0.130 | 0.110 | 47.5 | 2.88 | 11.2 |   |
|  11,560 | 48 | 2.96 | 4.8 | -0.010 | 0.000 | 48.0 | 2.97 | 14.3 |   |
|  |   |   |   |   |   |   |   |   |   |
|  11,593 | 50 | 2.70 | 5.6 | 0.000 | 0.000 | 50.0 | 2.70 | 15.2 |   |
|  11,615 | 51 | 2.97 | 5.1 | -0.010 | 0.000 | 52.0 | 2.99 | 15.3 |   |
|  11,631 | 67 | 2.50 | 3.8 | 0.290 | 0.230 | 43.0 | 3.07 | 12.4 |   |
|  11,645 | 52 | 2.82 | 3.5 | 0.140 | 0.100 | 44.0 | 3.15 | 11.1 |   |
|  11,655 | 57 | 2.64 | 3.5 | 0.160 | 0.130 | 45.5 | 2.91 | 10.7 |   |
|  11,665 | 52 | 2.68 | 5.5 | 0.010 | 0.010 | 51.0 | 2.70 | 15.0 |   |
|  11,696 | 50 | 2.76 | 5.1 | 0.010 | 0.005 | 49.5 | 2.77 | 14.5 |   |

54

ASQUITH AND KRYGOWSKI

Table 4.21. Log values from Figures 4.1, 4.3, and 4.5, apparent matrix values from Figures 4.16 and 4.19, and a list of the estimates of lithology determined from the crossplot.

|  Depth | Raw Data |   |   |   | PhiND | Apparent Matrix Values |   |   | MID Plot  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|   |  DT | RHOB | PE | NPHI |   | DTmaa | Rhomaa | Umaa | Lithology  |
|  11,508 | 51 | 2.73 | 5.0 | 0.005 | 0.000 | 51.0 | 2.74 | 13.7 | Limestone  |
|  11,522 | 47 | 2.75 | 3.2 | 0.090 | 0.070 | 43.0 | 2.89 | 9.2 | Dolomite  |
|  |   |   |   |   |   |   |   |   |   |
|  11,545 | 57 | 2.67 | 3.7 | 0.130 | 0.110 | 47.5 | 2.88 | 11.2 | Dolomite w/limestone and anhydrite  |
|  11,560 | 48 | 2.96 | 4.8 | -0.010 | 0.000 | 48.0 | 2.97 | 14.3 | Anhydrite  |
|  |   |   |   |   |   |   |   |   |   |
|  11,593 | 50 | 2.70 | 5.6 | 0.000 | 0.000 | 50.0 | 2.70 | 15.2 | Limestone  |
|  11,615 | 51 | 2.97 | 5.1 | -0.010 | 0.000 | 52.0 | 2.99 | 15.3 | Anhydrite  |
|  11,631 | 67 | 2.50 | 3.8 | 0.290 | 0.230 | 43.0 | 3.07 | 12.4 | ???  |
|  11,645 | 52 | 2.82 | 3.5 | 0.140 | 0.100 | 44.0 | 3.15 | 11.1 | ???  |
|  11,655 | 57 | 2.64 | 3.5 | 0.160 | 0.130 | 45.5 | 2.91 | 10.7 | Dolomite w/anhydrite  |
|  11,665 | 52 | 2.68 | 5.5 | 0.010 | 0.010 | 51.0 | 2.70 | 15.0 | Limestone  |
|  11,696 | 50 | 2.76 | 5.1 | 0.010 | 0.005 | 49.5 | 2.77 | 14.5 | Limestone w/anhydrite?  |

show the calculation of apparent matrix values. Figure 4.20 and Table 4.21 show the application of those apparent matrix values to determine lithology.

## Beyond the three-mineral model

For more complex mineralogical solutions, the use of other log measurements is required. These techniques go beyond the crossplotting techniques discussed here. Some techniques are deterministic in nature (as are the crossplot techniques) but rely on iterative computational techniques for a solution. Other techniques rely on the use of statistical techniques to estimate the most likely solution.

Figure 4.21 is an example of a deterministic solution. In this case, shale volume is calculated independently (the gamma ray was used for this example) and was used as one of the input curves. With the additional inputs of interval transit time, neutron porosity, bulk density, and $P_0$, the software solved for four minerals (beyond the shale volume): calcite, dolomite, anhydrite, and quartz. In the figure, porosity and fluid saturations (from the deep resistivity log) were also determined and are shown incorporated into the same display.

## Implications for Correlation and Mapping

Standard correlation (and mapping) practices use the raw logs (gamma ray, resistivity, etc.) to trace formation boundaries in the subsurface. With the existence of software that can easily and quickly estimate formation lithologies and porosities, the correlation process might be better served (and be more accurate) if correlations were made on the actual quantities of interest (like lithology), instead of on the raw logs, many of which respond to multiple properties of the formations in the subsurface.

This section summarizes the crossplot methods previously discussed.

## CONSISTENCY IN LITHOLOGY PREDICTION

Seven methods to determine lithology have been covered in this chapter. One is based on pattern recognition (quick-look neutron-density), three on the simultaneous use of two porosity tools, and three on the simultaneous use of three porosity tools. Table 4.22 compares the lithology prediction results of these methods. With some exceptions, the results are fairly consistent, but they are not identical. The variation in the results has many sources. Borehole conditions may

Porosity Logs

55

Table 4.22: Comparison of lithology estimation from the various crossplot methods.

|  Depth | Zone range | Lithology  |   |   |   |   |   |   |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
|   |   |  Neutron-Density Quicklook | Neutron-Density Crossplot | Neutron-Sonic Crossplot | Spectral-Density Crossplot | M-N Crossplot | Neutron-Density-Sonic MID Plot | Neutron-Spectral-Density MID Plot  |
|  11,508 | 11,490-11,518 | Limestone | Limestone | Sandy limestone | Limestone (with anhydrite?) | Sandy dolomite | Dolomitic sand | Limestone  |
|  11,522 | 11,518-11,528 | Dolomite | Dolomite | Dolomite | Dolomite | Limy dolomite | Dolomite | Dolomite  |
|   | 11,528-11,543 | Dolomite with anhydrite |  |  |  |  |  |   |
|  11,545 | 11,543-11,546 | Dolomite | Dolomite | Limestone | Limy dolomite | Dolomite | Dolomite (with anhydrite?) | Dolomite and with limestone anhydrite  |
|  11,560 | 11,546-11,570 | Anhydrite | Anhydrite | Anhydrite | Anhydrite | Anhydrite | Anhydrite | Anhydrite  |
|   | 11,570-11,580 | Dolomite (with anhydrite?) |  |  |  |  |  |   |
|  11,593 | 11,580-11,598 | Limestone | Limestone | Limestone | Limestone | Limestone | Sandy limestone | Limestone  |
|  11,615 | 11,598-11,625 | Anhydrite | Anhydrite | Anhydrite? | Anhydrite | Anhydrite | Anhydrite | Anhydrite  |
|  11,631 | 11,625-11,641 | Dolomite | Dolomite (with anhydrite?) | Dolomite | Limy dolomite | Dolomite | Dolomite? | off chart  |
|  11,645 | 11,641-11,649 | Dolomite (with anhydrite?) | Dolomite (with anhydrite?) | Dolomite | Limy dolomite | Dolomite? | off chart | off chart  |
|  11,655 | 11,649-11,659 | Dolomite | Dolomite | Limy dolomite | Limy dolomite | Dolomite | Dolomite with anhydrite | Dolomite with anhydrite  |
|  11,665 | 11,659-11,680 | Limestone | Limestone | Sandy limestone | Limestone | Dolomite | Sandy limestone (with dolomite?) | Limestone  |
|  11,696 | > 11680 | Limestone with anhydrite | Dolomitic limestone | Sandy limestone | Limestone (with anhydrite?) | Dolomite | Sandy dolomite | Limestone (with anhydrite?)  |

56

ASQUITH AND KRYGOWSKI

play a part in the variation, especially since, in this case, the data were used directly from the logs with no attempt at environmental corrections. Formation thickness and, hence, the effect of adjacent beds on the measurement in the target bed also play a part.

The variability of the formations themselves probably has a more significant effect. In a geologic environment like this one (Figure 4.21), it can be expected that the lithologies encountered are not always pure. The response of the individual measurements to that mixture vary between measurements and contribute to the variation seen here.

The results of the crossplots, while not wildly variable, underscores the need for other data, in this case, samples of the formations themselves. Cores through the section would be ideal, but their cost would probably be prohibitive. Cuttings samples would be a good source of lithology information, even given the potential mixing and contamination problems. Sidewall cores, either in this well (if the log analysis could be completed quickly) or in subsequent wells in zones with questionable predicted lithology, would help to reconcile the results shown here.

## REVIEW

1. The three common types of porosity logs are:

sonic
density
neutron

2. The sonic log is a porosity log that measures the interval transit time (delta t, or DT, or $\Delta t$) of a com

compressional sound wave through the formation. The unit of measure is microseconds per foot ($\mu$sec/ft) or microseconds per meter ($\mu$sec/m). Interval transit time is related to formation porosity.

3. The density log is a porosity log that measures the electron density of a formation. The formation's electron density is related to a formation's bulk density (RHOB or \(\rho_{b}\)). Bulk density is measured in \(\mathrm{g/cm^3}\) or \(\mathrm{Kg/m^3}\). Bulk density, in turn, can be related to formation porosity.
4. Density logs made since about 1980 also have a photoelectric curve \((\mathrm{P_e},\mathrm{PE},\) or PEF) that responds primarily to formation lithology and is affected in only a minor way by porosity and the type of fluids in the pore space.
5. The neutron log is a porosity log that measures the hydrogen concentration in a formation. In shale-free formations where porosity is filled with water, the neutron log can be related to water-filled porosity (PHIN, or NPHI, or \(\phi_N\)).
6. In gas reservoirs, the neutron log records a lower porosity than the formation's true porosity because gas has a lower hydrogen concentration than oil or water (gas effect).
7. The neutron-density combination is the most widely used porosity measurement combination. Porosity, adjusted for lithology, can be determined from the neutron-density combination either by a crossplot chart or by formula.
8. Additional uses of the neutron-density combination are:

- detection of gas bearing zones
- determination of lithology

Porosity Logs

57

![img-3.jpeg](img-3.jpeg)

Figure 4.1. Example sonic log with gamma ray log and caliper.

This example is shown to illustrate a common presentation format for sonic logs, and to be used in determining a porosity (SPHI) from interval transit time (DT) in Figure 4.2.

Track 1: This track includes both the gamma ray (GR) and caliper (CALI) curves. Note that the gamma ray scale reads from 0 to 100 API units, increasing from left to right in increments of 10 units. The gamma ray curve is represented by a long-dashed line.

The caliper scale ranges from 6 to 16 inches from left to right in one-inch increments, and the curve is represented by a short-dashed line.

Tracks 2 and 3: Both the interval transit time (DT) scale and the porosity (SPHI) scales are shown in these tracks. Sonic log interval transit time (DT) is represented by a solid line, on a scale ranging from 140 to $40\mu \mathrm{sec} / \mathrm{ft}$ increasing from right to left. The sonic porosity measurement (calculated using a limestone matrix value, 47.6 $\mu \mathrm{sec} / \mathrm{ft}$ ) is shown by a long dashed line on a scale ranging from $-0.10$ to $0.30$ $(-10\%$ to $30\%)$ increasing from right to left.

58

ASQUITH AND KRYGOWSKI

![img-4.jpeg](img-4.jpeg)

Courtesy Halliburton Energy Services, ©1994 Halliburton Energy Services

Figure 4.2. Chart for converting interval transit time ($\Delta t$) to sonic porosity ($\phi_s$).

# Procedure:

1. Find the interval transit time (DT) taken from the sonic log in Figure 4.1 on the scale at the bottom of the chart.
2. To calculate sonic limestone porosity using the Wyllie time-average equation (labeled "Time Average"), follow the DT value vertically until it intersects the calcite line, then move horizontally to intersect the y-axis and read the porosity value.
3. To calculate sonic dolomite porosity using the Wyllie time-average equation, follow the procedure in step 2 above, except intersect the dolomite line instead of the calcite line.
4. To calculate sonic limestone porosity using the Raymer-Hunt-Gardner (RHG) equation (curved lines, labeled "Empirical"), follow the DT value vertically until it intersects the curved calcite line, then move horizontally to intersect the y-axis and read the porosity value.
5. To calculate sonic dolomite porosity using the Raymer-Hunt-Gardner (RHG) equation, follow the procedure in step 4 above, except intersect the curved dolomite line instead of the curved calcite line.

NOTE: While the values in Table 4.6 are in decimal, the porosity values on the chart are in percent.

Porosity Logs

59

![img-5.jpeg](img-5.jpeg)

Figure 4.3. Example density log with gamma ray and caliper.

This example is shown to illustrate a common presentation format for a density log, and to be used in determining a porosity (DPHI) from bulk density (RHOB) in Figure 4.4.

Track 1: This track includes both the gamma ray (GR) and caliper (CALI) curves. Both scales increase from left to right. The gamma ray values range from 0 to 100 API gamma ray units, and the caliper measures the borehole diameter from 6 to 16 inches.

Track 2: The density log correction curve (DRHO) ranges in value from $-0.05\mathrm{g/cm^3}$ to $+0.45\mathrm{g/cm^3}$ in increments of $0.05\mathrm{g/cm^3}$. It is shown as a light, dashed line. The photoelectric effect curve (PEF) ranges from 0 to $10\mathrm{b/e}$ and is shown as a heavy, dashed line. (The dashes on the PEF curve are longer than those on the DRHO curve.)

Tracks 2 and 3: The bulk-density (RHOB) scale ranges in value from $2.0\mathrm{g/cm^3}$ to $3.0\mathrm{g/cm^3}$ and the curve is a solid line.

60

ASQUITH AND KRYGOWSKI

![img-6.jpeg](img-6.jpeg)

Courtesy Halliburton Energy Services, ©1994 Halliburton Energy Services

Figure 4.4. Chart for converting bulk density ($\rho_b$, RHOB) to density porosity ($\phi_D$, DPHI).

# Procedure:

1. Find the bulk density (RHOB) taken from the density log in Figure 4.3 on the scale at the bottom of the chart. Note that the scale is displayed from high values on the left to low values on the right.
2. Follow the RHOB value vertically until it intersects the proper matrix line [calcite (limestone) or dolomite] then move horizontally to intersect the y-axis representing the proper fluid density, in this case \(1.00\mathrm{g/cm^3}\) (fresh water, the middle scale) to read the porosity (DPHI).

NOTE: The values in Table 4.8 are decimal fractions, the porosity values on the chart are in percent.

Porosity Logs

61

![img-7.jpeg](img-7.jpeg)

Figure 4.5. Example combination neutron density log with gamma ray and caliper.

This example is shown to illustrate a common presentation format for a neutron density combination, to be used in applying a lithology conversion to the neutron porosity in Figure 4.6, and in determining lithology and crossplot porosity from the neutron-density crossplot in Figure 4.8.

Track 1: This track contains both gamma ray (GR) and caliper (CALI). Note that the gamma ray scale reads from 0 to 100 API units and the caliper measures a borehole size from 6 to 16 inches.

Track 2: The photoelectric effect (PEF) is displayed from 0 to 10 b/e. The density correction (DRHO) is displayed from $-0.05$ to $+0.45\mathrm{g/cm^3}$.

Tracks 2 and 3: Both neutron porosity (NPHI) and density porosity (DPHI) are plotted across tracks 2 and 3. The scale for both is the same, ranging from $-0.10$ $(-10\%)$ to $0.30$ $(+30\%)$, and is expressed in limestone porosity units. On this log the density porosity (DPHI) is represented by a solid line, and the neutron porosity (NPHI) is represented by a dashed line.

62

ASQUITH AND KRYGOWSKI

Figure 4.6. Chart for correcting Halliburton DSN-II neutron-porosity curve for lithology.

NOTE: For neutron logs, the chart used to correct the logged porosity for lithology MUST correspond to the type of neutron log run, and the company used to acquire the log data. A mismatch between the actual log used and the chart used for the conversion can lead to significant errors in the determination of lithology.

# Procedure:

1. Find the neutron porosity (NPHI) taken from the neutron density log in Figure 4.2 on the scale at the bottom of the chart. The original neutron log data is referenced to limestone lithology.
2. Follow the NPHI value vertically until it intersects the proper matrix line (Dolomite or Sandstone) then move horizontally to intersect the y-axis the porosity, NPHI. Use the smallest value \(\Sigma_{\mathrm{mo}}\) for each lithology to do the calculations.

NOTE: The values in the table are decimal fractions, but the porosity values on the chart are in percent.

![img-8.jpeg](img-8.jpeg)

Courtesy Halliburton Energy Services, ©1994 Halliburton Energy Services

Figure 4.7. Chart for correcting Schlumberger CNL thermal-neutron curves (NPHI and TNPH) for lithology.

NOTE: For neutron logs, the chart used to correct the logged porosity for lithology MUST correspond to the type of neutron log run, and the company used to acquire the log data. A mismatch between the actual log used and the chart used for the conversion can lead to significant errors in the determination of lithology.

In the example, the Halliburton neutron log from Figure 4.5, is corrected using a Schlumberger chart (NPHI curves). Note the difference in porosity results between the charts.

![img-9.jpeg](img-9.jpeg)

Courtesy Schlumberger Wireline & Testing, ©1998 Schlumberger

Porosity Logs

63

![img-10.jpeg](img-10.jpeg)

Figure 4.8. Example of the generalized lithologic response of the neutron and density logs, used as a quick-look lithology technique.

The gamma ray (GR) and photoelectric effect (PEF) are provided for additional information.

# Procedure:

The neutron-porosity and density-porosity curves are scanned for their relationship to each other and for their values. The relative position of the curves is an indicator of the lithology encountered, and the average of the two curves at any depth is a good approximation of the porosity (within two porosity units).

The gamma ray may be used to distinguish ambiguous patterns, like shale and dolomite patterns.

The photoelectric effect may be used to distinguish ambiguous patterns (sandy limestone from dolomitic sand) or to confirm the neutron-density interpretation.

# Assumptions:

There is liquid in the pore space, either water or oil but not gas.
The formations encountered do not contain clay (except for the shale).
- Both porosity curves are referenced to limestone.

Note the lithology interpretations listed on the log.

64

ASQUITH AND KRYGOWSKI

![img-11.jpeg](img-11.jpeg)

Figure 4.9. Example of the generalized lithologic response of the neutron and density logs, used as a quick-look lithology technique. This example is primarily for showing log response in shaly formations, and when the porosity curves are referenced to sandstone.

Procedure:

The neutron-porosity and density-porosity curves are scanned for their relationship to each other, and for their values. The relative position of the curves is an indicator of the lithology encountered.

Assumptions:

- There is liquid in the pore space, either water or oil, but not gas, except in the intervals where noted.
- The formations encountered do not contain clay (except in the intervals where noted).
- The density and neutron-porosity curves (PHID and PHIN) are referenced to sandstone. PHIE is the effective porosity, calculated from PHIN and PHID.

The Interpretation:

The neutron and density measurements depend on the amount of clay present in the formation and the physical properties of that clay. In general, the presence of clay in a liquid-filled formation causes the neutron log to read higher than actual porosity, while the density log reads lower than actual porosity. In a liquid-filled sandstone (when the measurements are referenced to sandstone), the curves separate with the neutron higher than the density.

Gas in the formation drives the neutron value lower than actual porosity and the density value slightly higher than actual porosity, resulting in the neutron log reading lower than the density log, the classic crossover response.

With both gas and clays in the formation, the response is not fully predictable because the two effects simultaneously work in opposite ways on both measurements. In very shaly formations with low to medium gas saturations, the presence of gas may be noted only by a decrease in the crossover effect. In formations with medium gas saturations and small amounts of shale, there may be no noticeable gas effect, with the curves at approximately the same values.

The illustration here is but one of many possible examples of the log responses in shaly gas-bearing formations.

Porosity Logs

65

![img-12.jpeg](img-12.jpeg)

![img-13.jpeg](img-13.jpeg)

Figure 4.10. An example of neutron and density porosity response in a gas zone.

The interval from 14,601 ft to 14,624 ft shows the (low) gamma ray response of a reservoir and the neutron-density crossover (NPHI < DPHI) of a gas-bearing zone. The neutron- and density-porosity curves are referenced to the lithology of the zone.

NOTE: Curves recorded in apparent limestone units show a false crossover in a sandstone, because of the lithologic effect.

66

ASQUITH AND KRYGOWSKI

Figure 4.11. Neutron-density crossplot.

Lithology and porosity can be determined from the neutron-density crossplot.

Procedure:

1. The point is located on the plot from the intersection of the neutron and density (limestone) values. Density may be bulk density (left axis of chart) or density porosity (right axis of chart).
2. The porosity of the point is determined by its location relative to lines connecting points of equal porosity on the two lithology lines between which it is plotted. Note that the neutron porosity (NPHI) values in Table 4.13 are decimal fractions, and the neutron limestone porosity values in Figure 4.11 are in percent. A value listed as 0.010 in the table is equal to a value of 1% on the figure.
3. The lithology of the point is determined by its location relative to the two lithology lines, with the proximity to each line an indication of the percentage of each of the mineral pairs. Note that the lithology determination can be ambiguous (e.g., a point lying between the calcite and dolomite lines also lies between the quartz and dolomite lines). Use the smallest value Σ_ns for each lithology to do the calculations.

![img-14.jpeg](img-14.jpeg)

Courtesy Halliburton Energy Services, ©1994 Halliburton Energy Services

Porosity Logs

67

![img-15.jpeg](img-15.jpeg)

Courtesy Halliburton Energy Services, ©1994 Halliburton Energy Services

Figure 4.12. Neutron-sonic crossplot.

Lithology and porosity can be determined from the neutron-sonic crossplot.

Procedure:

1. The point is located on the plot from the intersection of the neutron and sonic values.

2. The porosity of the point is determined by its location relative to lines connecting points of equal porosity on the two lithology lines between which it is plotted. Note that the neutron porosity (NPHI) values in Table 4.13 are decimal fractions, and the neutron limestone porosity values in Figure 4.12 are in percent. A value listed as 0.010 in the table is equal to a value of 1% on the figure.

3. The lithology of the point is determined by its location relative to the two lithology lines, with the proximity to each line an indication of the percentage of each of the mineral pairs. Note that the lithology determination can be ambiguous (e.g., a point lying between the calcite and dolomite lines also lies between the quartz and dolomite lines). For this exercise, use the curves labeled Empirical, which are based on the Gardner-Hunt-Raymer equation.

Note: On this graph, anhydrite plots at the point where neutron limestone porosity = -1% and interval transit time = 50 lsec/ft.

68

ASQUITH AND KRYGOWSKI

Figure 4.13. Spectral density crossplot (bulk density and photoelectric effect).

Lithology and porosity can be determined from the spectral-density crossplot.

Procedure:

1. The point is located on the plot from the intersection of the bulk-density and \(P_{\mathrm{a}}\) values.
2. The porosity of the point is determined by its location relative to lines connecting points of equal porosity on the two lithology lines between which it is plotted.
3. The lithology of the point is determined by its location relative to the two lithology lines, with the proximity to each line an indication of the percentage of each of the mineral pairs. Note that the lithology determination can be ambiguous (e.g., a point lying between the calcite and dolomite lines also lies between the quartz and dolomite lines).

![img-16.jpeg](img-16.jpeg)

Courtesy Schlumberger Wireline & Testing, © 1998 Schlumberger

Porosity Logs

69

![img-17.jpeg](img-17.jpeg)

Courtesy Halliburton Energy Services, ©1994 Halliburton Energy Services

Figure 4.14. Sonic-density crossplot.

Although this crossplot could be used in the same way as the previous three crossplots, it is not usually used in that manner. The main reason is that the estimated porosity varies significantly depending on the assumed mineral pair.

This plot is valuable, however, in areas where the reservoirs are radioactive. In the case of radioactive reservoirs, the data points from the reservoirs plot among the lithology lines, while shales plot in the lower right (southeast) quadrant of the plot, usually well away from the lithology lines. In this case, even though the lithology and porosity cannot be determined without significant uncertainty, radioactive reservoirs can be distinguished from shales in a straightforward manner.

70

ASQUITH AND KRYGOWSKI

Figure 4.15. M-N lithology plot.

The M-N lithology plot can be used to estimate lithology from the combination of neutron-porosity, bulk-density, and interval-transit time measurements. Unlike the previous two-measurement crossplots which required the assumption of a two-mineral matrix, this plot allows for a three-mineral matrix assumption. Any three minerals which have unique M and N values can be used, although the most common mineral triads used are calcite-quartz-dolomite and calcite-dolomite-anhydrite.

Procedure:

1. From Equations 4.9 and 4.10 (reproduced below), calculate M and N using the values for freshwater mud and fresh water.

$$M = \frac{\Delta t_{fl} - \Delta t}{\rho_b - \rho_{fl}} \times 0.01$$

$$N = \frac{\phi_{NB} - \phi_N}{\rho_b - \rho_{fl}}$$

Δtfl = 189 μsec/ft for freshwater mud and 185 μsec/ft for saltwater mud

ρfl = 1.0 g/cm³ for fresh water and 1.15 g/cm³ for salt water

$$\phi_{NB} = 1.0$$

2. Plot the points on the crossplot. The relative mineral percentages are inversely proportional to the distance from each mineral vertex. Points lying along a line between two minerals is composed of those two minerals only, with none of the third mineral present.

Note that the numbers at the dolomite and quartz sandstone points correspond to the expected porosity range of the formation as follows: 1: φ = 0.00 (tight formation); 2: φ = 0.00 to 0.12; 3: φ = 0.12 to 0.27; 4: φ > 0.27.

![img-18.jpeg](img-18.jpeg)

Courtesy Schlumberger Wireline & Testing, ©1998 Schlumberger

Porosity Logs

71

![img-19.jpeg](img-19.jpeg)

Courtesy Halliburton Energy Services, ©1994 Halliburton Energy Services

Figure 4.16. Determination of apparent matrix density.

This value of apparent matrix density ($\rho_{ma}$) will be used in Figures 4.18 and 4.20 to estimate the formation lithology.

# Procedure:

1. The point is located on the plot at the intersection of the bulk-density and neutron-porosity values.
2. The apparent matrix density of the point is determined by its location relative to the apparent-density lines. The value can be interpolated when the point falls between the lines.

72

ASQUITH AND KRYGOWSKI

Figure 4.17. Determination of apparent matrix interval transit time.

This value of apparent matrix interval transit time ($\Delta t_{\mathrm{max}}$) will be used in Figure 4.18 to estimate the formation lithology.

# Procedure:

1. The point is located on the plot from the intersection of the interval transit time and neutron-porosity values.
2. The apparent matrix interval transit time of the point is determined by its location relative to the apparent transit time lines. The value can be interpolated when the point falls between the lines.

![img-20.jpeg](img-20.jpeg)

Courtesy Halliburton Energy Services, ©1994 Halliburton Energy Services

Porosity Logs

73

![img-0.jpeg](img-0.jpeg)

Figure 4.18. Matrix identification plot, using neutron, sonic, and density.

This plot uses the apparent matrix values calculated in Figures 4.16 and 4.17 to estimate formation lithology.

Procedure:

1. Plot the points on the crossplot. The relative mineral percentages are inversely proportional to the distance from each mineral vertex. Points lying along a line between two minerals will be composed of those two minerals only, with none of the third mineral present.

Courtesy Halliburton Energy Services, ©1994 Halliburton Energy Services

74

ASQUITH AND KRYGOWSKI

Figure 4.19. Determination of apparent matrix capture cross section.

This value of apparent matrix capture cross section ($U_{maa}$) will be used in Figure 4.20 to estimate the formation lithology.

# Procedure:

1. The point is located on the plot at the intersection of the neutron-density crossplot porosity (shown on the chart as the apparent total porosity, \(\phi_{\mathrm{ta}}\)) and the photoelectric factor. The photoelectric factor on the x-axis of the plot is determined by starting with the bulk-density value on the scale at the bottom of the page, and connecting a line from that point to the value of photoelectric factor \((P_{\mathrm{p}})\) on the scale immediately above. That line is extended to the x-axis of the plot, then extended vertically until it reaches the porosity value drawn from the y-axis.
2. The apparent photoelectric cross section of the point is determined by its location relative to the apparent photoelectric cross section lines. The value can be interpolated when the point falls between the lines.

![img-1.jpeg](img-1.jpeg)

Courtesy Halliburton Energy Services, ©1994 Halliburton Energy Services

Porosity Logs

75

![img-2.jpeg](img-2.jpeg)

Figure 4.20. Matrix identification plot, using neutron and spectral density.

This plot uses the apparent matrix values calculated in Figures 4.16 and 4.19 to estimate formation lithology.

Procedure:

1. Plot the points on the crossplot. The relative mineral percentages are inversely proportional to the distance from each mineral vertex. Points lying along a line between two minerals will be composed of those two minerals only, with none of the third mineral present.

Courtesy Halliburton Energy Services, ©1994 Halliburton Energy Services

76

ASQUITH AND KRYGOWSKI

Figure 4.21: Lithology determined by software using a four-mineral model of the subsurface.

This is an example of a deterministic solution. In this case, shale volume in calculated independently (the gamma ray was used for this example) and was used as one of the input curves. The software solved for four mineral volumes (in addition to the shale volume): calcite, dolomite, anhydrite, and quartz.

The mineral volumes are displayed in the following order (from left to right):

Calcite

Dolomite

Anhydrite

Quartz

Shale

The width of the track represents the total volume of the formation, so any distance between the right edge of the track and the last mineral curve (shale) indicates porosity. Because the program also calculated porosity and fluid volumes, the fluids are also represented. The distance between the right edge of the track and the BVW (bulk volume water) curve, filled in blue, represents the water saturation in the formation. The area between BVW and PHIE (effective porosity), filled in green, represents the hydrocarbon saturation of the formation.

![img-3.jpeg](img-3.jpeg)

5

Asquith, G., and D. Krygowski, 2004, Resistivity Logs, in G. Asquith and D. Krygowski, Basic Well Log Analysis: AAPG Methods in Exploration 16, p. 77–101.

# Resistivity Logs

## GENERAL

Resistivity logs are used to:

- determine hydrocarbon-bearing versus water-bearing zones
- indicate permeable zones
- determine porosity

By far the most important use of resistivity logs is the determination of hydrocarbon-bearing versus water-bearing zones. Because the rock's matrix or grains are nonconductive and any hydrocarbons in the pores are also nonconductive, the ability of the rock to transmit a current is almost entirely a function of water in the pores. As the hydrocarbon saturation of the pores increases (as the water saturation decreases), the formation's resistivity increases. As the salinity of the water in the pores decreases (as $R_w$ increases), the rock's resistivity also increases. A geologist, by knowing (or determining) several parameters ($a$, $m$, $n$, and $R_w$), and by determining from logs the porosity ($\phi$) and formation bulk, or true, resistivity ($R_t$), can determine the formation's water saturation ($S_w$) from the Archie equation:

$$S_w = \left( \frac{a \times R_w}{R_t \times \phi^m} \right)^{\frac{1}{n}} \tag{5.1}$$

where:

$S_w$ = water saturation

$a$ = tortuosity factor

$m$ = cementation exponent

$n$ = saturation exponent

$R_w$ = resistivity of formation water

$\phi$ = porosity

$R_t$ = true formation resistivity as derived from a deep reading resistivity log

Resistivity logs produce a current in the adjacent formation and measure the response of the formation to that current. The current can be produced and measured by either of two methods. Electrode tools (also called galvanic devices or, for presently available versions, laterologs) have electrodes on the surface of the tool to emit current and measure the resistivity of the formation. Induction tools use coils to induce a current and measure the formation's conductivity. These two types of tools have many variations, which are summarized in Table 5.1. In many cases, it is desirable to use both electrode and induction tools to produce a single resistivity log. For example, an electrode device might be used to measure the resistivity of the invaded zone (see Chapter 1) while an induction device is being used for measurements of the uninvaded zone.

While the earliest well logs were electrode logs (hence the reference to any well log as an electric log or e-log), the most common type of electrical logging device in present use is the induction tool (Dresser Atlas, 1975). The earliest versions of the electrode logs are no longer used in logging in the western hemisphere, although those designs were modified and embellished in the former Soviet Union and are still used there today.

Outside the Soviet Union, two distinct types of electrode tools, the normal and the lateral, were developed. They differ from each other in the configuration of their electrodes. The lateral has an asymmetric electrode pattern (with respect to the axis of the tool) and is very different in its interpretation than the normal curves or the measurements available today (Hilchie, 1979). The normal log was developed in two configurations, each with its own electrode spacing. The 16-inch spacing was called the short normal and a 64-inch spacing was called the long normal. These older measurements were unfocused electrode devices and were ineffective in high borehole salinities (low resistivities) and in thin beds (Bassiouni, 1994). With the

77

78

ASQUITH AND KRYGOWSKI

advent of induction logs and laterologs, the use of these older tools diminished quickly. However, the short normal is useful for measuring the resistivity of the invaded zone, and its use continued in combination with induction logs.

In all the cases above, e-logs, induction logs, and laterologs, at least two resistivity measurements are made

as part of the service. These measurements seek to interrogate the formation at different distances from the borehole, so that invasion into the formation can be detected and so that the resistivity of the part of the formation undisturbed by the drilling process (the *true* formation resistivity) can be determined.

Table 5.1. Classification of Resistivity Logs.

|  Induction Logs [coil logs] (measure formation conductivity)  |   |   |
| --- | --- | --- |
|  Induction (deep and medium)  |   |   |
|  Galvanic devices [electrode logs and laterologs] (measure formation resistivity)  |   |   |
|  Normal | Microlaterolog (MLL)  |   |
|  Lateral | Microlog (ML)  |   |
|  Laterolog (deep and shallow) | Proximity Log (PL)  |   |
|  Spherically Focused Log (SFL) | MicroSpherically Focused Log (MSFL)  |   |
|  Resistivity Log Depth of Investigation  |   |   |
|  Flushed Zone (Rxo) | Invaded Zone (Ri) | Uninvaded Zone (Rt)  |
|  MicroLog (ML) | Short Normal (SN) | Long Normal (LN)  |
|  Microlaterolog (MLL) | Laterolog-8 (LL8) | Lateral Log  |
|  Proximity Log (PL) | Spherically Focused Log (SFL) | Deep Induction Log (ILd)  |
|  MicroSpherically Focused Log (MSFL) | Medium Induction Log (ILm) | Deep Laterolog (LLd)  |
|   | Shallow Laterolog (LLs) | Laterolog-3 (LL3)  |
|   |  | Laterolog-7 (LL7)  |

# LATEROLOGS

To overcome the limitations of the original electrode logs, another class of logging devices, the *laterolog*, was developed. These are also electrode logs and are designed to measure formation resistivity in boreholes filled with saltwater muds (where $R_{mf} \sim R_w$). A current from the surveying electrode is forced into the formation by focusing electrodes. Focusing electrodes emit current of the same polarity as the surveying electrode but are located above and below it. The focusing electrodes (sometimes called guard electrodes) prevent the surveying current from flowing up the borehole filled with saltwater mud (Figure 5.1). The effective depth of laterolog investigation is controlled by the extent to which the surveying current is focused. Deep-reading laterologs are therefore more strongly focused than shallow-reading laterologs.

Invasion can influence the laterolog. However,

because the resistivity of the mud filtrate is approximately equal to the resistivity of formation water ($R_{mf} \sim R_w$) when a well is drilled with saltwater muds, invasion does not strongly affect $R_t$ values derived from a laterolog. But, when a well is drilled with freshwater muds (where $R_{mf} > 3 R_w$), the laterolog can be strongly affected by invasion. Under these conditions, a laterolog should not be used (see Figure 5.2). The borehole size and formation thickness affect the laterolog, but normally the effect is small enough so that laterolog resistivity can be taken as $R_t$.

The first generation of laterologs, introduced in the early 1950s (Maute, 1992) consisted of devices that produced a single curve of formation resistivity. Several models, which interrogated different distances away from the borehole, were developed. In the early 1970s, the dual laterolog was released commercially (Maute, 1992), which simultaneously recorded two measurements at different depths of investigation.

Resistivity Logs

79

Because the laterolog is an galvanic device, it must have continuous electrical contact with the formation through the drilling mud. It does not work in air-filled boreholes or oil-based muds. It works best in salty muds (where $R_{mf} \sim R_w$) and in medium to high-resistivity formations.

## Laterolog

This version of the laterolog was common from the early 1950s to the early 1970s. It consisted of a single laterolog measurement and sometimes a microlaterolog measurement. The laterolog curve (Figure 5.3) appears in track 2 of the log and has a linear scale. Because saltwater mud (where $R_{mf} \sim R_w$) gives a very poor SP response, a natural gamma-ray log was often run in track 1 as a lithology and correlation curve. The microlaterolog, if run, was recorded in track 3.

## Dual Laterolog

The dual laterolog (Figure 5.4) was introduced in the early 1970s and is still in use today. It consists of a deep-reading measurement ($R_{LLD}$) and a shallow-reading measurement ($R_{LLS}$). Both curves are displayed in tracks 2 and 3 of the log, usually on a four-cycle logarithmic scale ranging from 0.2 to 2000 ohm-m. A natural gamma ray log is often displayed in track 1. The third resistivity measurement is the microspherically focused resistivity ($R_{MSFL}$), a pad-type, focused electrode log that has a very shallow depth of investigation and measures the formation resistivity very close (within a few inches) of the wellbore. When this three resistivity-curve combination (i.e., deep, shallow, and very shallow) is used, the deep laterolog curve can be corrected for invasion effects to produce $R_t$ (Suau et al., 1972). A *tornado chart* (Figure 5.5) is used to graphically correct $R_{LLD}$ to $R_t$ and to determine the diameter of invasion ($d_i$) and the ratio $R_t/R_{xo}$, from which $R_{xo}$ can be determined. The correction procedure is illustrated in Figure 5.5.

## INDUCTION LOGS

Unlike the original (unfocused) electrode logs and laterologs, induction logs measure formation conductivity rather than resistivity. Formation conductivity is related to formation resistivity through the following equation:

$$
C = \frac{1000}{R} \tag{5.2}
$$

where:

$C =$ conductivity in millimho/m (= milliSiemens)

$R =$ resistivity in ohm-m

An induction tool consists of several transmitting coils that emit a high-frequency alternating current of constant intensity. The alternating electromagnetic field that is created induces currents in the formation. These currents flow as ground-loop currents perpendicular to the axis of the logging tool and create electromagnetic fields which induce signals in the receiver coils. The receiver signals are essentially proportional to conductivity (Schlumberger, 1972). The responses of the individual coils are combined in such a way as to minimize the effect of materials in the borehole, the invaded zone, and other nearby formations (Figure 5.6). While the older generation of the tools, which are still in use, relied on electronic circuitry to properly mix the receiver signals to minimize the various near-borehole effects, newer *array tools* usually have more receivers and process the received signals with computer-based algorithms which model the response of the tool to formation properties. Induction logs have evolved from a single induction measurement run in combination with the older short-normal measurement, to the dual induction, which makes two different induction measurements simultaneously, to the array measurements, which measure formation resistivity at different frequencies and distances away from the borehole.

By design, induction logs work well in wells containing nonconducting fluids in the borehole (such as air and oil-based mud) or in freshwater muds (where $R_{mf} > 3 R_w$). They are most affected by salty muds. Induction logs work best in low to moderate formation resistivities. The uncertainty in the measurement increases at high formation resistivities, making induction logs less desirable than the laterolog for highly resistive formations (resistivities greater than about 100 ohm-m).

## Induction Electric Log

Like the laterolog, the first version of the induction log, the induction electric log (Figure 5.7), had a single deep induction measurement ($R_{IL}$). It, however, was combined with the earlier (electrode-type) short-normal measurement ($R_{SN}$) to simultaneously measure the resistivity of the formation at two distances from the borehole. The SP measurement was a common correlation measurement in this suite. This version was used from the mid-1950s until the early 1970s.

The short-normal measurement interrogated the

80

ASQUITH AND KRYGOWSKI

formation at a shallow distance from the wellbore, and comparison of the two measurement values, $R_{SN}$ and $R_{IL}$, was an indication of invasion and, thus, formation permeability.

The short-normal tool can record a reliable value for resistivity from a bed thickness of four feet or greater. The short-normal curve is usually recorded in track 2 on a linear scale. The short-normal tool works best in freshwater muds (where $R_{mf} > 3 R_w$), so saltwater muds (where $R_{mf} \sim R_w$) are not a good environment for its use. In addition to providing a value for $R_i$, the short-normal curve can be used to calculate a value for resistivity-derived porosity if a correction is made for unflushed oil in the invaded zone. To obtain a more accurate reading of $R_i$ from the short-normal curve, an amplified short-normal curve (the same data displayed on a more sensitive scale) is sometimes displayed in track 2 along with the short-normal curve.

The induction log has a transmitter-receiver spacing of 40 inches and can measure a reliable value for resistivity down to a bed thickness of about five feet. The induction curve on the induction electric log appears in track 2 (Figure 5.7). Because the induction device is a conductivity measuring tool, a conductivity curve is presented in track 3. The track 3 conductivity curve is useful to more accurately determine the resistivity value in low-resistivity formations and to eliminate possible errors in the acquisition system's derivation of resistivity from conductivity. Because the induction log does not require the transmission of electrical current through drilling fluid, it can be run in nonconducting borehole fluids such as air, oil, or foam.

## Dual Induction Log

The second-generation induction log is called the dual induction (Tixier et al., 1963) and was introduced in the mid-1960s (Maute, 1992). This log (Figure 5.8) consists of a deep-reading induction device, which attempts to measure $R_t$, and a medium-reading induction device which measures $R_i$. The deep-reading measurement is similar to the induction curve from an induction electric log. The dual induction log also has a third resistivity curve, a shallow-reading, focused, laterolog-type measurement that is similar in depth of investigation to the short normal. The shallow-reading laterolog may be either a laterolog-8 (LL8) or a spherically focused log (SFL).

The dual induction log is useful in formations that are deeply invaded by mud filtrate. Because of deep invasion, the deep reading induction may not accurately measure the true resistivity of the formation ($R_t$).

Resistivity values obtained from the three curves on a dual induction log are used to correct deep resistivity to true resistivity ($R_t$) from a tornado chart (Figure 5.9). This tornado chart can also help determine the diameter of invasion ($d_i$) and the ratio of $R_{so}/R_t$. An example of the correction procedure is presented in Figure 5.9.

The three resistivity curves on the dual induction log are usually recorded on a four-cycle logarithmic scale ranging from 0.2 to 2000 ohm/m (Figure 5.8) and correspond to tracks 2 and 3 on the induction electric log. Usually, a spontaneous potential or a gamma ray curve is placed in track 1.

The deep induction log does not always record an accurate value for deep resistivity in thin, resistive zones (where $R_t > 100$ ohm-m). Therefore, an alternate method to determine true resistivity ($R_t$) should be used. The technique is called $R_{t\ minimum}$ ($R_{t\ min}$) and is calculated by the following formula:

$$R_{t\ min} = R_i \times \frac{R_w}{R_{mf}} \tag{5.3}$$

where:

$R_{t\ min}$ = true resistivity (also called $R_{t\ minimum}$)

$R_{mf}$ = resistivity of mud filtrate at formation temperature

$R_w$ = resistivity of formation water at formation temperature

$R_i$ = resistivity tool measuring in the invaded zone, usually laterolog-8 or spherically focused log

The rule for applying $R_{t\ min}$ is to determine $R_t$ from both the dual induction log tornado chart (Figure 5.9) and from the $R_{t\ min}$ formula, and use whichever value of $R_t$ is the greater. In addition to the $R_{t\ min}$ method for determining $R_t$ in thin resistive zones, correction curves (Schlumberger, 1979) or forward modeling algorithms are available to correct the deep induction log resistivity to $R_t$.

## Other resistivity devices

Induction logs have undergone some advancement in recent years. The first such advancement, in the mid-1980s, was the measurement of another signal (the X-signal) from the formation (Barber, 1983), using the standard sensor configuration of the induction tool. This phase measurement, sometimes combined with measurements at different transmitter frequencies, improved responses of the induction tool to the borehole and formation environments and increased the depth of investigation of the measurement.

The second advancement in induction logs was the

Resistivity Logs

81

introduction of the array tools, first by BPB Wireline Services (now Reeves Wireline) in 1983 (Maute, 1992). Induction logs of this type are generally composed of a single transmitter and several receivers and, depending on the vendor, may also operate at several frequencies. The focusing is done mathematically rather than physically through the coil arrangements used by the standard induction log. The processing can yield different depths of investigation and different vertical resolutions, depending on the needs of the client. Figure 5.10 is an example of an array-type resistivity tool.

Resistivity sensors on the drill string (measurement while drilling, MWD, or logging while drilling, LWD) made their debut around 1980, with the 16-inch normal (short normal). This was followed in 1983 with the introduction of the propagation resistivity measurement, essentially an induction-type device. The original propagation tools provided two resistivity measurements with slightly different apparent depths of investigation. Many presently available tools have multiple transmitters and receivers and produce two or more measurements with significantly different depths of investigation into the formation.

Interpretation of the newer versions of wireline measurements and LWD measurements is no different than interpretation of the resistivity logs explicitly mentioned here. Often, the newer versions of induction logs, laterologs, and LWD measurements have environmental corrections applied in realtime (as the data are being acquired), so it is important to check for that condition and not make the corrections to the already-corrected data.

## FLUSHED ZONE RESISTIVITY LOGS

At the same time that resistivity tools were being designed to interrogate the undisturbed region of the formation, another class of tools, based on the same physical principles, was being designed expressly to interrogate the region very close to the borehole. This region is usually flushed of original formation fluids by the drilling mud. By knowing the resistivity of the flushing fluid (the resistivity of the mud filtrate, $R_{mf}$) and making some assumptions about the fluid saturation of the flushed zone, formation porosities and saturations could be better estimated. These *microresistivity* devices are either unfocused electrode or focused electrode (laterolog) devices. Because of their very shallow depths of investigation (on the order of a few inches), the electrodes are mounted on pads that are pressed against the borehole wall. Figure 5.11 is a schematic of two such tools. The tool must make good

contact with the borehole wall for a valid measurement, and a thick mudcake or a rough hole adversely affects the measurement.

## Microlog (ML)

The microlog (Figure 5.12) is a pad-type resistivity device that primarily detects mudcake (Hilchie, 1978). The pad is in contact with the borehole and consists of three electrodes spaced one inch apart. Two resistivity measurements are made; the micronormal ($R_2$) and the microinverse ($R_{1x1}$). The micronormal device investigates three to four inches into the formation (measuring $R_{xo}$) and the microinverse investigates approximately one to two inches into the formation and is significantly affected by the resistivity of the mudcake ($R_{mc}$). The detection of mudcake by the microlog indicates that invasion has occurred and the formation is permeable. On the microlog, permeable zones show up when the micronormal curve reads higher resistivity than the microinverse curve ($R_2 > R_{1x1}$). This is known as *positive separation* (Figure 5.12). The microlog tool also has a caliper that measures the borehole diameter. A decrease in borehole diameter can indicate mudcake and support the interpretation of permeability. In Figure 5.12, mudcake is indicated where the caliper shows a borehole size smaller than the diameter of the drill bit used to drill the hole.

Shale zones are indicated by no separation or *negative separation* (i.e., micronormal < microinverse). Positive separation can only occur when $R_{mc} > R_m > R_{mf}$. If there is any doubt, check the log heading for resistivity values of the mudcake, drilling mud, and mud filtrate.

Remember that even though the resistivity of the mud filtrate ($R_{mf}$) is less than the resistivity of the mudcake ($R_{mc}$), the micronormal curve reads a higher resistivity in a permeable zone than the shallower reading microinverse curve. This is because the filtrate has invaded the formation, and part of the resistivity measured by the micronormal curve is read from the rock matrix, whereas the microinverse curve measures only the mudcake ($R_{mc}$) which has a lower resistivity than rock. However, in enlarged boreholes, a shale zone can exhibit minor, positive separation. To detect zones of erroneous positive separation, a microcaliper log is run in track 1 (Figure 5.12), so that borehole irregularities are detected. Nonporous and impermeable zones have high resistivity values on both the micronormal and microinverse curves (Figure 5.12). Hilchie (1978) states that resistivities of approximately ten times the resistivity of the drilling

82

ASQUITH AND KRYGOWSKI

mud ($R_m$) at formation temperature indicate an impermeable zone.

The microlog does not work well in saltwater muds (where $R_{mf} \sim R_w$) or gypsum-based muds because the mudcake may not be strong enough to keep the pad away from the formation. Where the pad is in contact with the formation, positive separation cannot occur.

Because the microlog is so greatly affected by borehole conditions, it generally does not provide a good estimate of flushed-zone resistivity ($R_{xo}$).

### Other Microresistivity Logs

The microlaterolog (MLL), the proximity log (PL) (Figure 5.13), and the microspherically focused log (MSFL) are pad-type, focused, electrode logs designed to measure the resistivity in the flushed zone ($R_{xo}$). Unlike the microlog, all produce a single resistivity curve, but because of their focused design they are more accurate predictors of flushed-zone resistivity. Because the microlaterolog is strongly influenced by mudcake thicknesses greater than 1/4 inch (Hilchie, 1978), the microlaterolog should be run only with saltwater muds. The proximity log, which is more strongly focused than the microlaterolog, is designed to investigate deeper so it can be used with freshwater muds where mudcake is thicker, but with low invasion it might measure beyond the invaded zones.

The microspherically focused log, introduced by Schlumberger in 1972 (Maute, 1992), and other tools of similar design seem to generally be very good at determining flushed-zone resistivity ($R_{xo}$).

### INTERPRETATION

#### Resistivity-derived Porosity

The minerals that make up the grains in the matrix of the rock and the hydrocarbons in the pores of the rock are nonconductive. Therefore, the ability of rock to transmit an electrical current is almost entirely the result of the water in the pore space. Thus, resistivity measurements can be used to determine porosity. Normally, measurements of a formation's resistivity close to the borehole (flushed zone, $R_{xo}$, or invaded zone, $R_i$) are used to determine porosity.

When a porous, permeable, water-bearing formation is invaded by drilling fluid, formation water is displaced by mud filtrate. Porosity in a water-bearing formation can be related to shallow resistivity ($R_{xo}$) by the following equations:

$$S_{xo} = \sqrt{F \times \frac{R_{mf}}{R_{xo}}} \tag{5.4}$$

In a water-bearing zone $S_{xo} = 1.0$ (100%), so the equation becomes:

$$1.0 = \sqrt{F \times \frac{R_{mf}}{R_{xo}}} \tag{5.5}$$

Squaring both sides, remembering that $F = a/\phi^m$, and solving for porosity ($\phi$):

$$\phi = \left( \frac{a \times R_{mf}}{R_{xo}} \right)^{\frac{1}{m}} \tag{5.6}$$

where:

$\phi$ = formation porosity

$R_{mf}$ = resistivity of mud filtrate at formation temperature

$S_{xo}$ = water saturation in the flushed zone

$R_{xo}$ = flushed-zone resistivity

$a$ = tortuosity factor

$m$ = cementation exponent

$F$ = formation factor

The saturation exponent ($n$) is assumed to be 2.

In hydrocarbon-bearing zones, the shallow resistivity ($R_{xo}$) is affected by the unflushed residual hydrocarbons left by the invading mud filtrate. These residual hydrocarbons result in a value for shallow resistivity ($R_{xo}$) that is too high because hydrocarbons have a higher resistivity than formation water. Therefore, the calculated resistivity porosity in hydrocarbon-bearing zones is too low. To correct for residual hydrocarbons in the flushed zone, water saturation of the flushed zone ($S_{xo}$) must be known or estimated (Table 5.2). Then, a formation's shallow resistivity ($R_{xo}$) can be related to porosity by the following (again solving Equation 5.4 for porosity, with $S_{xo} < 1.0$):

$$\phi = \left[ \frac{a}{S_{xo}^2} \times \frac{R_{mf}}{R_{xo}} \right]^{\frac{1}{m}} \tag{5.7}$$

where:

$S_{xo}$ = flushed zone water saturation = 1.0 - RHS (residual hydrocarbon saturation)

### HIGH-FREQUENCY (DIELECTRIC) MEASUREMENTS

The standard resistivity logs, such as the deep laterolog and deep induction log generate an electromagnetic wave in the frequency range of 35 to 20,000 Hz (where hertz = cycles/second). At these frequencies,

Resistivity Logs

83

Table 5.2. Typical percentages of residual hydrocarbon saturation (RHS) as a function of hydrocarbon density and porosity (modified after Hilchie, 1978).

|   | Oil Gravity (°API) | RHS (%) | S_{xo} (%)  |
| --- | --- | --- | --- |
|  Gas |  | 40 to 5 | 60 to 95  |
|  High-gravity oil | 40 to 50 | 10 to 5 | 90 to 95  |
|  Medium-gravity oil | 20 to 40 | 20 to 10 | 80 to 90  |
|  Low-gravity oil | 10 to 20 | 30 to 20 | 70 to 80  |
|  Porosity (%) |   | RHS (%) | S_{xo} (%)  |
|  25 to 35 |   | 30 | 70  |
|  15 to 20 |   | 15 | 85  |

the predominant influence on the wave is the conductivity of the substance it is traveling through. In a reservoir, the conductivity is strongly influenced by the salinity and distribution of the formation water, and the distribution of formation water is controlled by the pore type and formation wettability.

At higher frequencies [in the 20 MHz (million hertz) to 1.1 GHz (billion hertz) range], the dielectric properties of a substance become very important to wave propagation (Hilchie, 1982). High dielectric-constant values are associated with polar compounds such as water. Since water is a polar compound, it requires energy to orient all its dipoles in the direction of the electromagnetic wave (dipolar polarizability, Schlumberger, 1984). Thus, an electromagnetic field moving through water is weakened. Rock matrix and hydrocarbons are both nonpolar compounds with very low dielectric constants, and therefore weaken an electromagnetic field less than water does.

Table 5.3 is a list of the various dielectric logs run

by the different service companies. The Halliburton (and older Gearhart and Welex) and Atlas Wireline logs are called dielectric logs and the Schlumberger log is called an electromagnetic propagation tool (EPT). These logs measure propagation time of the electromagnetic wave by reduction in wave amplitude and by shifts in the phase of the wave (Serra, 1984).

Table 5.4 is a list of dielectric constants and propagation times for various materials. It is apparent that water has a much greater wave travel time and dielectric constant than any other material on the list. The dielectric log therefore can be used to detect water-bearing versus hydrocarbon-bearing zones, and unlike the resistivity logs, the dielectric measurement is independent of water distribution (and depending on the measurement frequency, independent of water salinity). Therefore, pore type and wettability do not influence its value. For a detailed discussion of the dielectric and EPT logs, see Serra (1984), Dewan (1983), and Hilchie (1982).

Table 5.3. List of the Various Dielectric Logs from Different Service Companies

|  Company | Tool Name | Frequency | Investigation Depth  |
| --- | --- | --- | --- |
|  Halliburton | HFDT-A (pad) | 1.0 GHz | Flushed zone  |
|  Gearhart (now Halliburton) | DCL (mandrel) | 30 MHz | Invaded zone  |
|  Welex (now Halliburton) | DT (mandrel) | 20 MHz | Invaded zone  |
|  Atlas Wireline (Baker Atlas) | DL (mandrel) DL (pad) | 47 MHz 200 MHz | Invaded zone, Flushed zone  |
|  Schlumberger | EPT (pad) | 1.1 GHz | Flushed zone  |

MHz = megahertz (million cycles/sec)

GHz = gigahertz (billion cycles/sec)

84

ASQUITH AND KRYGOWSKI

Table 5.4. Dielectric Constants and Propagation Times for Various Materials (modified after Dewan, 1983)

|  Material | Dielectric Constant, ε (farads/m) | Matrix Propagation Time, $tp_{ma}$ (ns/m) | Fluid Propagation Time, $tp_{fl}$ (ns/m)  |
| --- | --- | --- | --- |
|  Sandstone | 4.65 | 7.2 |   |
|  Limestone | 7.50 | 9.1 |   |
|  Dolomite | 6.80 | 8.7 |   |
|  Anhydrite | 6.35 | 8.4 |   |
|  Halite | 5.6 to 6.35 | 7.9 to 8.4 |   |
|  Shale | 5 to 25 | 7.5 to 16.6 |   |
|  Oil | 2.2 |  | 4.9  |
|  Gas | 3.3 |  | 6.0  |
|  Fresh water (at 25°C) | 78.3 |  | 29.5  |

ns/m = nanoseconds/meter; $tp = (11.1 \times \varepsilon)^{0.5}$

The most common ways of presenting dielectric logging data is in the form of a log which either displays neutron-density crossplot porosity versus water-filled dielectric porosity, or a value for flushed-zone or invaded-zone water saturation ($S_{xo}$ or $S_i$) calculated from the dielectric log. The equations for calculating water-filled porosity ($\phi_w$) and water saturations ($S_{xo}$ or $S_i$) from the dielectric constant logs and EPT logs are:

Dielectric Logs:

$$\phi_w = \frac{\left(\varepsilon^{0.5} - \varepsilon_{ma}^{0.5}\right)}{\left(\varepsilon_w^{0.5 \times p} - \varepsilon_{ma}^{0.5}\right)} \tag{5.8}$$

$$S_i = \frac{\phi_w}{\phi_{ND}} \quad (20, 30, 47 \text{ Mhz tools}) \tag{5.9}$$

$$S_{xo} = \frac{\phi_w}{\phi_{ND}} \quad (200 \text{ MHz, 1.0 and 1.1 GHz tools}) \tag{5.10}$$

where:

$\phi_w$ = water-filled porosity

$\phi_{ND}$ = neutron-density crossplot porosity

$\varepsilon$ = dielectric constant from the log

$\varepsilon_w$ = dielectric constant of water

$\varepsilon_{ma}$ = dielectric constant of rock matrix

$p$ = a constant that varies with water salinity. A value of 1.2 can be used, or the value for $p$ can be calculated from a nearby water zone by substituting $\phi_{ND}$ for $\phi_w$.

$S_{xo}$ = flushed zone water saturation

$S_i$ = invaded zone water saturation

EPT Log:

$$\phi_{EPT} = \frac{tp_o - tp_{ma}}{tp_{fl} - tp_{ma}} \tag{5.11}$$

$$S_{xo} = \frac{[(tp_o - tp_{ma}) + \phi_{ND} \times (tp_{ma} - 4.1)]}{\phi_{ND} \times (tp_{fl} - 4.1)} \tag{5.12}$$

where:

$\phi_{EPT}$ = water-filled porosity from EPT log

$\phi_{ND}$ = neutron-density porosity (from crossplot)

$tp_o$ = loss-free travel time

$$tp_o = \left[ tp_l^2 - \left(\frac{EAC^2}{3604}\right) \right]^{0.5} \tag{5.13}$$

$tp_{fl}$ = travel time in water

$$tp_{fl} = 20 \times \left[ \frac{710 - \frac{Tf}{3}}{444 + \frac{Tf}{3}} \right] \tag{5.14}$$

$tp_{ma}$ = travel time in the matrix (see Table 5.4 for values)

$tp_l$ = travel time from log in ns/m (nanoseconds/meter)

$EAC$ = fixed spreading losses correction: $EAC = ATT - 50$

Resistivity Logs

85

[ATT = attenuation of the wave (from the log) in decibels/meter]

$T_f$ = formation temperature

$S_{xo}$ = water saturation of the flushed zone from EPT log

4.1 = hydrocarbon travel time

If a zone is wet, water-filled porosity calculated from the dielectric or EPT log equals the porosity derived from the neutron-density porosity crossplot. If however, hydrocarbons are present, then water-filled porosity is less than the porosity calculated from porosity logs. This occurs because hydrocarbons and rock matrix have such low dielectric constants and travel times when compared to water (Table 5.4). The measured dielectric constant or travel time is lowered by the presence of hydrocarbons, causing the calculated water-filled porosity value to decrease also (see Equations 5.8 and 5.12).

Another way to use dielectric or EPT data is to calculate the single textural parameter ($w$) for use in the Archie water-saturation equation (Asquith, 1991). The equations used to calculate $w$ from dielectric or EPT logs are:

$$
w = \frac{\log\left(\frac{R_z}{R_{sl}}\right)}{\log(\phi_w)} \tag{5.15}
$$

where:

$w$ = single textural parameter to use in the Archie water saturation equation ($w = m = n$) (Guillotte, et al., 1979)

$R_z$ = mixed water resistivity:

$$
R_z = \frac{1}{\left[\frac{z}{R_w} + \frac{1 - z}{R_{mf}}\right]} \tag{5.16}
$$

$z = 0.025$ for very deep invasion

0.035 for deep invasion

0.05 for average invasion

0.075 for shallow invasion

0.1 very shallow invasion

$R_{sl}$ = resistivity from shallow resistivity log (i.e., SFL)

$\phi_w$ = water-filled porosity from dielectric or EPT log

If the shallow-reading log is in fact a microresistivity log (that is, it reads the flushed zone of the formation), then $R_{sl} = R_{xo}$ and $R_z = R_{mf}$.

The water saturation equation is:

$$
S_w = \left(\frac{1}{\phi}\right) \times \left(\frac{R_w}{R_t}\right)^{\frac{1}{w}} \tag{5.17}
$$

where:

$S_w$ = Archie water saturation using $w = n = m$

$\phi$ = porosity from porosity log

$R_w$ = formation-water resistivity

$R_t$ = true formation resistivity

$w$ = single textural parameter (see Equation 5.15)

An EPT log example is offered here (Figures 5.14 to 5.16) to illustrate how dielectric or EPT logs are used to detect hydrocarbons and calculate more reliable water saturations. The well is located in western Kansas, and the zones of interest are two basal Mississippian Chester sandstones.

Figure 5.14 is a dual induction-SFL log through the basal part of the Mississippian Chester Formation. The two basal sandstones are in the interval from 5704 to 5738 ft. The upper sandstone (5704 to 5714 ft) has deep resistivities (ILD) of 20 to 38 ohm-m, and the lower sandstone (5724 to 5738 ft) has deep resistivities of 2.5 to 7 ohm-m.

Figure 5.15 is a gamma ray neutron-density log over the same interval. The neutron-density crossplot porosities in the upper sandstone (12 to 14%) and lower sandstone (14 to 16%) are similar. Archie water saturations for the upper sandstone are 25 to 29% and are 70 to 72% for the lower sandstone. The drastically lower resistivities and higher water saturations in the lower sandstone indicate that it should produce water. The more resistive upper sandstone with much lower water saturations should, therefore, produce hydrocarbons.

Figure 5.16 is a computer generated log through the basal Chester sandstones. In Figure 5.16, note that neutron-density porosity (PHIA) is greater than water-filled EPT porosity (ECMP) indicating hydrocarbons in both sandstones. The calculated values for flushed-zone water saturations ($S_{xo}$) using the EPT log for the upper sandstone are 43 to 50% and 43 to 44% for the lower sandstone. These similar $S_{xo}$ values indicate that both sandstones should produce hydrocarbons. This well was perforated from 5700 to 5738 ft (gross perforations) and had an initial production of 157 BOPD. After 90 days, the well had a cumulative production of 9000 BO and 230 BW, thus verifying the interpretation from the EPT log. The important question to ask is why are the resistivities so much lower in the lower sandstone. The answer is the lower sandstone has thin clay coatings of mixed-layered illite-smectite on the grains and the upper sandstone has no clay coatings (Asquith, 1991). The presence of these clay coatings

86

ASQUITH AND KRYGOWSKI

causes an increase in surface conductance, which lowers resistivity. However, the dielectric log (EPT) measures the bulk distribution of water-filled porosity and is therefore not effected by the clay coatings.

Asquith (1991) calculated an average value for w of 1.45 for the lower sandstone using the EPT porosity. When water saturations are recalculated for the lower sandstone using w = 1.45, the saturation values range from 30 to 41%. This example illustrates how important dielectric logs can be in the interpretation of difficult log-analysis problems.

# REVIEW

1. Resistivity logs are used to:

- determine hydrocarbon-bearing versus water-bearing zones
- indicate permeable zones
- determine porosity when no porosity measurements are available

2. A formation's resistivity can be measured by either induction logs or laterologs.
3. Induction logs should be run where the drilling fluid is air, foam, freshwater mud, or oil-based mud (where $R_{mf} > 3 R_w$).
4. Laterologs should be run in saltwater drilling muds (where $R_{mf} \sim R_w$).
5. By use of tornado charts, the deep resistivity log on either the dual induction log or the dual laterolog with $R_{so}$ can be corrected for the effects of invasion to determine a more accurate value of true formation resistivity ($R_t$). The resulting estimate of true formation resistivity is lower than the deep induction reading, and higher than the deep laterolog reading.
6. Most minerals that make up the matrix of the rock and the hydrocarbons in the pores are nonconductive. Therefore, the ability of the rock to transmit an electric current is almost entirely a function of the water in the rock's pores.

Resistivity Logs

87

![img-4.jpeg](img-4.jpeg)

Figure 5.1. Schematic illustration of a focused laterolog illustrating current flow (Suou et al., 1972).

This schematic illustration of a dual laterolog tool shows that the focusing (or guard) electrode pairs (shown as long dark cylinders) force the survey current from the central electrode out into the formation. The pattern of the survey current is that of a disk that is perpendicular to the axis of the tool. Unlike the neutron and density tools, which have the sensors on one side of the tool and primarily measure one quadrant of the formation, the laterolog electrodes completely encircle the tool, and the resulting measurement accounts for the resistivity in all four quadrants around the tool.

The illustration is really two diagrams, the left half representing the deep measurement and the right half representing the shallow measurement. It attempts to show that the measurements are made simultaneously with the same electrodes by using different measurement frequencies.

![img-5.jpeg](img-5.jpeg)

Figure 5.2. Chart for quick determination of preferred conditions for using an induction log versus a laterolog (Western Atlas International, Inc, 1995, Log Interpretation Charts, Figure 7-1).

Selection of the particular type of logging measurement is a function of the ratio of $R_{\mathrm{ref}}/R_{\mathrm{w}}$ and, to some extent, porosity.

The shaded area indicates higher uncertainties in both measurements because of the borehole and formation conditions. Under these conditions, it is often best to run both types of resistivity logs until it can be determined which works best for the specific conditions. Then only the measurement with the best response need be used.

Courtesy Baker Atlas, ©1996-1999 Baker Hughes, Inc.

88

ASQUITH AND KRYGOWSKI

Figure 5.3. Example of a laterolog and microlaterolog. This log illustrates the curves and provides an example for picking log values. These logs are used when $R_{int} = R_{in}$.

Track 1: The log track on the far left contains gamma ray (GR) and caliper (CALI) curves, shown as solid and dashed lines respectively. Gamma ray logs commonly accompany laterologs. This one is recorded in units that predate API units, microgram-Radium equivalents per ton ($\mu$gRa-eq/ton).

Track 2: This displays the laterolog (LL3), which measures the deep resistivity or true resistivity ($R_t$) of the formation. Note that the scale increases linearly from left to right in increments of 5 ohm-m from 0 to 50. Laterologs are sometimes displayed on a hybrid scale that increases linearly from 0 to 50 on its left half and nonlinearly from 50 to infinity on its right half. The hybrid scale is not shown here.

At the depth of 3948 ft, the laterolog value reads 21 ohm-m.

Track 3: The microlaterolog (MLL) measures the resistivity of the flushed zone ($R_{co}$). Note that the scale starts with zero at the left edge of track 3. The scale ranges from 0 to 50 ohm-m in increments of 5 ohm-m.

At the depth of 3948 ft the microlaterolog reads 8 ohm-m.

![img-6.jpeg](img-6.jpeg)

![img-7.jpeg](img-7.jpeg)

Note: To correct the laterolog (for invasion) to true resistivity ($R_t$), use the following formula from (Hilchie, 1979). Using the example at 3948 ft:

$$
R_t = 1.67 (R_{L1}) - 0.67 (R_{co}) \quad R_t = 1.67 (21) - 0.67 (8)
$$

$$
R_t = 29.7 \text{ ohm-m}
$$

where:

$R_t =$ resistivity of the uninvaded zone

$R_{L1} =$ laterolog resistivity (21 ohm-m at 3948 ft)

$R_{co} =$ microlaterolog resistivity (8 ohm-m at 3948 ft)

Resistivity Logs

89

![img-8.jpeg](img-8.jpeg)

Figure 5.4. Example of dual laterolog with microspherically focused log.

These logs are used when $R_{mf} \sim R_{w}$ and invasion is deep.

The resistivity scale in tracks 2 and 3 is a four-cycle logarithmic scale ranging from 0.2 to 2000 ohm·m; the values increase from left to right.

# Deep laterolog resistivity:

The LLD (long-dashed line) measures the deep resistivity of the formation, if invasion is not deep and the bed of interest is thick (>2 ft), the deep reading commonly approximates true formation resistivity ($R_f$).

At the depth of 9324 ft, the deep laterolog resistivity ($R_{LLD}$) is 16 ohm·m.

# Shallow laterolog resistivity:

The LLS (short-dashed line) measures the shallow resistivity of the formation or the resistivity of the invaded zone ($R_f$).

At 9324 ft, the shallow laterolog resistivity ($R_{LLS}$) is 10 ohm·m.

# Microspherically focused log (MSFL) resistivity:

The MSFL (solid line) measures the resistivity of the flushed zone ($R_{so}$).

At 9324 ft, the MSFL resistivity ($R_{MSFL}$) is 4.5 ohm·m.

The following ratios are needed for work on the tornado chart (Figure 5.5), and the values represented are picked from the log as shown above:

$$
\mathrm{LLD/MSFL} = R_{LLD}/R_{MSFL} = 16/4.5 = 3.6
$$

$$
\mathrm{LLD/LLS} = R_{LLD}/R_{LSS} = 16/10 = 1.6
$$

90

ASQUITH AND KRYGOWSKI

Thick beds, 8-in. [203-mm] hole,
no annulus, no transition zone, Rso/Rm = 50,
use data corrected for borehole effect

![img-9.jpeg](img-9.jpeg)

Courtesy Schlumberger Wireline & Testing, ©1998 Schlumberger.

Resistivity Logs

91

Figure 5.5. Dual laterolog-$R_{eo}$ tornado chart for correcting deep resistivity to $R_{f}$ (Schlumberger, 1998, Chart Rint-9b)

Log values in this exercise are picked from the example dual laterolog-MSFL in Figure 5.4.

Given:

$$
\mathrm{LLD} = R_{LLD} = 16.0 \text{ ohm-m}
$$

$$
\mathrm{LLS} = R_{LLS} = 10.0 \text{ ohm-m}
$$

$$
\mathrm{MSFL} = R_{MSFL} = 4.5 \text{ ohm-m}
$$

$$
R_{LLD}/R_{MSFL} = R_{LLD}/R_{eo} = 3.6
$$

$$
R_{LLD}/R_{LLS} = 1.6
$$

Procedure:

Plot $R_{LLD}/R_{eo}$ (= 3.6) on the vertical axis and $R_{LLD}/R_{LLS}$ (= 1.6) on the horizontal axis. Plot the intersection of these values on the tornado chart, and determine subsequent ratio values.

$R_{f}/R_{LLD}$: The scale for this value is represented by the solid red lines. The scale values are in red and range from 1.1 to 1.8. Our value falls between the scale values 1.3 and 1.4, so we assign a value of 1.32.

$d_{i}$: The diameter of invasion around the borehole is picked from the chart by following the dashed, blue lines to the scales at the top of the chart. The scale from 20 to 120 gives $d_{i}$ in inches, and the scale from 0.50 to 3.04 gives $d_{i}$ in meters. Our value falls between the scale values of 40 and 50 inches, so we assign a value of 43 inches.

$R_{f}/R_{eo}$: The scale for this ratio value is represented by the heavy, blue, solid lines. The scale values are in black, increase from bottom to top, and range from 1.5 to 100. Our value falls between the scale values 3 and 5 (much closer to 5), so we assign a value of 4.8.

Finally, corrected values for true resistivity of the formation ($R_{f}$) and resistivity of the flushed zone ($R_{eo}$) are determined using these ratios.

$$
(R_{f}/R_{LLD}) \times R_{LLD} = R_{f} \text{ (corrected)}
$$

$$
(\text{ratio}) \times \log \text{value} = R_{f} \text{ (corrected)}
$$

$$
1.32 \times 16.0 \text{ ohm-m} = 21.1 \text{ ohm-m} (= R_{f}, \text{true formation resistivity}).
$$

And:

$$
R_{f} \text{ (corrected)} / (R_{f}/R_{eo}) = R_{eo}
$$

$$
R_{f} \text{ (corrected)} / (\text{ratio value from chart}) = R_{eo}
$$

$$
21.1 \text{ ohm-m} / 4.8 = 4.4 \text{ ohm-m} (= R_{eo}, \text{resistivity of flushed zone})
$$

When the deep laterolog log reading is corrected for invasion via the tornado chart, the resulting estimate of true formation resistivity is always greater than the deep laterolog reading.

92

ASQUITH AND KRYGOWSKI

Figure 5.6. Schematic illustration of a basic three-coil induction system. (Ellis, 1987)

The figure schematically shows the configuration of a three-coil induction system with one transmitter (Xmtr) and two receivers [Rcvr (1) and Rcvr (2)]. In this example, Rcvr (2) is constructed with a polarity opposite that of Rcvr (1). In this case, the response of Rcvr (2) is subtracted from that of Rcvr (1), making the tool less sensitive to the formation near the wellbore and improving its response to the parts of the formation away from the borehole (shown by the curve labeled "Composite"). The standard induction tool consists of 6 coils, with the combination of the 6 responses producing two curves sensitive to different distances away from the borehole.

![img-10.jpeg](img-10.jpeg)

![img-11.jpeg](img-11.jpeg)

Figure 5.7. Induction Electric Log.

The Induction Electric Log is normally used when $R_{inf} > R_{air}$.

Track 1: The log track on the far left contains the spontaneous potential (SP) log. The SP scale increases from -160 mV on the left to +40 mV log on the right and has 10 increments of 20 mV. The value at the depth of 7446 ft is about -50 mV. The value of the SP in is measured from the shale baseline (i.e., the SP value in the shales where the SP value is zero), and the deflection from the baseline is negative.

![img-12.jpeg](img-12.jpeg)

Track 2: The middle log track contains two resistivity curves. The short normal (SN, also called the 16-inch normal) represented by the solid line, measures the invaded zone resistivity ($R_i$). The induction log (ILD), represented by the dashed line, measures the uninvaded zone resistivity ($R_i$).

At 7446 ft, the short normal has a value of 30 ohm-m. The induction value at the same depth is 10 ohm-m.

Tracks 2 and 3: These tracks contain the conductivity curve (CILD) which is the basic induction-log measurement. The conductivity curve can be used to convert values to resistivity. In this way, track 2 resistivity values can be checked for accuracy, or values can be derived more accurately at low resistivities.

For example, to convert track 3 values to resistivity the procedure is as follows:

The values on the conductivity scale increase from right to left, from 0 to 1000 are marked in 50 mmhos/meter increments. At a depth of 7446 ft, the curve in track 3 is or nearly 2 increments from the right and shows a value of 97 mmhos/meter).

Because resistivity equals 1000/conductivity, the resistivity = 1000/97 = 10.3 ohm-m.

When the logs are displayed on linear scales, as in this example, resistivity can determined more accurately from conversion of the conductivity curve than from reading the resistivity curve itself.

Resistivity Logs

93

![img-13.jpeg](img-13.jpeg)

Figure 5.8. Example of a dual induction log.

The dual induction log is normally used when $R_{inf}$ is much greater than $R_{in}$ and also where invasion is deep.

Track 1 in this log suite contains gamma ray and SP curves.

The resistivity scale in tracks 2 and 3 is a logarithmic scale from 0.2 to 2000 ohm·m, increasing from left to right. Note the following logs.

# Deep induction log resistivity:

The dashed ILD curve measures the deep resistivity of the formation, or close to true resistivity ($R_t$). At the depth of 13,591 ft, the deep resistivity (ILD) is 70 ohm·m.

# Medium induction log resistivity:

The dotted ILM curve measures the medium resistivity of the formation or resistivity of the invaded zone ($R_t$). At 13,591 ft, the medium resistivity (ILM) is 105 ohm·m.

# Spherically focused log resistivity:

The solid SFLU curve measures the shallow resistivity of the formation or resistivity of the flushed zone ($R_{to}$). At 13,591 ft, the resistivity of the flushed zone is 320 ohm·m.

The following ratios are needed for work on the tornado chart (Figure 5.9), and the values are picked from the example log:

$$
\begin{array}{l} \mathrm{SFLU/ILD} = R_{SFLU}/R_{ILD} = 320 \text{ ohm}\cdot\text{m}/70 \text{ ohm}\cdot\text{m} \\ = 4.6 \end{array}
$$

$$
\mathrm{ILM/ILD} = R_{ILM}/R_{ILD} = 105 \text{ ohm}\cdot\text{m}/70 \text{ ohm}\cdot\text{m} = 1.5
$$

94

ASQUITH AND KRYGOWSKI

![img-14.jpeg](img-14.jpeg)

Courtesy Schlumberger Wireline & Testing, ©1998 Schlumberger.

Resistivity Logs

95

Figure 5.9. Dual Introduction-SFL tornado chart used for correcting $R_{ILD}$ values to $R_{I}$ true formation resistivity. (Schlumberger, 1998, Chart Rint-2c)

Log values used in this exercise are picked from the example dual induction log in Figure 5.8.

Given:

$$
\mathrm{ILD} = R_{ILD} = 70 \text{ ohm-m}
$$

$$
\mathrm{ILM} = R_{ILM} = 105 \text{ ohm-m}
$$

$$
\mathrm{SFLU} = R_{SFL} = 320 \text{ ohm-m}
$$

$$
R_{SFL}/R_{ILD} = 4.6
$$

$$
R_{ILM}/R_{ILD} = 1.5
$$

Procedure:

Plot the $R_{SFL}/R_{ILD}$ ratio (= 4.6) on the vertical axis (labeled $R_{SFL}/R_{ID}$ on this chart) and the $R_{ILM}/R_{ILD}$ ratio (= 1.5) on the horizontal axis (labeled $R_{ILM}/R_{ID}$ on this chart). Plot the intersection of these values on the tornado chart, and pick the following values:

$R_I/R_{ILD}$: The scale for this value is represented by the solid red lines. The scale values are in red and range from 1.0 to 0.8, decreasing from left to right. The $R_I/R_{ILD}$ value falls on the 0.80 line.

$d_i$: The diameter of invasion around the borehole is picked from the chart by following the dashed, blue lines to the appropriate scale. Note that the $d_i$ scale is in inches across the top of the tornado and is in meters through the middle part of the tornado chart; both scales increase from left to right. In this example, the value is between the 60-inch and 70-inch lines, and $d_i$ is about 68 inches.

$R_{eo}/R_I$: This is the ratio of resistivity of the flushed zone ($R_{eo}$) over the true resistivity of the formation (corrected $R_f$). This ratio, derived from the chart, is used in later calculations. The scale is represented by the heavy, blue, solid lines, and the scale values are shown as whole numbers midway across the lines. In this example, the plotted sample falls on the line with a value of 7.0.

Finally, with values taken from the chart, calculate corrected values for $R_f$ and $R_{eo}$.

$$
(R_f/R_{ILD}) \times R_{ILD} = R_f \text{ (corrected)}
$$

(ratio value from chart) $\times$ log value $= R_f$ (corrected)

$0.80 \times 70 = 56$ ohm-m ($R_f$ corrected, or true formation resistivity)

And:

$$
(R_{eo}/R_f) \times R_f \text{ (corrected)} = R_{eo} \text{ (corrected)}
$$

(ratio value from chart) $\times$ (corrected $R_f$ value) $= R_{eo}$ (corrected)

$7 \times 56 = 392$ ohm-m ($R_{eo}$, corrected resistivity of the flushed zone)

When the deep induction log reading is corrected for invasion via the tornado chart, the resulting estimate of true formation resistivity is always less than the deep induction reading.

96

ASQUITH AND KRYGOWSKI

![img-15.jpeg](img-15.jpeg)

![img-16.jpeg](img-16.jpeg)

Figure 5.10. Example of an array induction log.

In this example from Halliburton Energy Services, the high resolution induction log was run in combination with the neutron, density, gamma ray and SP. As is common with array tools, the response of each receiver is highly processed, in this case, to produce curves which all have the same vertical resolution (one foot, in this example) but which respond to the formation at different depths away from the borehole. As indicated by the resistivity curve names in track 2, curves are displayed having depths of investigation of 24, 30, 40, 60, and 90 inches.

Depending on the vendor and the type of tool, the tool may operate at more than one measurement frequency to increase its depth of investigation or to enhance its vertical resolution.

Resistivity Logs

97

![img-17.jpeg](img-17.jpeg)

(a)

![img-18.jpeg](img-18.jpeg)

(b)

Figure 5.11. Microresistivity tools (Hearst and Nelson, 2000)

This figure shows the configuration of electrodes on the pads of a microlag (a) and a spherically focused lag (b). It also illustrates the current flow from each tool into the formation. The electrodes on the microlag ($A$, $M_1$, $M_2$) are spaced one inch apart.

98

ASQUITH AND KRYGOWSKI

Figure 5.12. Microlog with SP log and caliper.

This log demonstrates permeability two ways: by *positive separation* between the micronormal and microinverse logs (MNOR > MINV) in tracks 2 and 3 and by decreased borehole diameter due to mudcake, detected by the caliper log in track 1.

Examine the interval from 5147 to 5246 ft.

Track 1: The caliper measurement is shown by the long-dashed line in track 1. The short-dashed line shows the bit size (BS), which is 8.75 inches. Just above 5147 ft, the caliper shows a borehole diameter of approximately 11 inches, but the hole size decreases to about 8.5 inches from 5147 to 5224 ft, indicating the presence of mudcake and a permeable zone. Mudcake is also present at 5237 to 5245 ft. Note how the SP corresponds with these two mudcake intervals.

Tracks 2 and 3: The micronormal log (MNOR, shown by the dashed line) measures the resistivity of the flushed zone, and the microinverse (MINV, shown by the solid line) measures the resistivity of any mudcake that might be present. Mudcake and permeability are indicated by *positive separation*, which occurs where micronormal log shows a higher resistivity than the microinverse log. Note the positive separation from 5150 to 5224 ft and from 5237 to 5246 ft. The separation is about 0.5 ohm-m.

The fluid in the flushed zone is a combination of mud filtrate, formation water, and possibly residual hydrocarbons. The fluid in the mudcake is just mud filtrate, which has a higher resistivity than

![img-19.jpeg](img-19.jpeg)

Feet MD

5100

5200

![img-20.jpeg](img-20.jpeg)

the fluids in the flushed zone. Based on this alone, we might expect the microinverse to show a higher resistivity than the micronormal over intervals of mudcake. Remember, however, that rock generally has a higher resistivity than the fluids in it or around it. The rock in the flushed zone is compacted and cemented, but the rock part of the mudcake (cuttings and mud solids) is not compacted or cemented. Mudcake contains much more fluid and much less rock than an equal volume of the formation in the flushed zone. The higher concentration of fluid in the mudcake gives the mudcake a lower resistivity than the flushed zone.

Resistivity Logs

99

![img-21.jpeg](img-21.jpeg)

Feet MD

4100

4200

![img-22.jpeg](img-22.jpeg)

Figure 5.13. Example of a proximity log with a microlog and caliper.

The proximity log is designed to read the resistivity of the flushed zone ($R_{45}$). This particular log package includes a proximity log to read $R_{45}$, a microlog to determine permeable zones, and a caliper to determine the size of the borehole.

Examine the log curves at 4144 ft.

Track 1: Track 1 shows both a microlog and a caliper log. On this example, the resistivity values for micronormal and microinverse increase from right to left, so that the positive separation shows the same pattern with respect to the depth track as it does when displayed in track 2.

At the depth of 4144 ft, the micronormal (MNOR, shown by the dashed line) shows higher resistivity than microinverse (MINV, shown by the solid line). The microinverse has a value of about 1.5 ohm-m, and the micronormal has a value of about 3.0 ohm-m. The microlog indicates a permeable zone. The caliper log indicates a borehole slightly less than 9 inches.

Tracks 2 and 3: The proximity log measures resistivity of the flushed zone ($R_{45}$). In this example the scale is logarithmic, reading from left to right. At 4144 ft, we read a proximity curve value ($R_{45}$) of 18 ohm-m.

100

ASQUITH AND KRYGOWSKI

![img-23.jpeg](img-23.jpeg)

Figure 5.14. Dual induction-SFL log through two Mississippian Chester sandstones in western Kansas.

The Chester sandstones are from 5704 to 5718 ft and from 5724 to 5738 ft.

![img-24.jpeg](img-24.jpeg)

Figure 5.15. Neutron-density log through two Mississippian Chester sandstones in western Kansas.

The Chester sandstones are from 5704 to 5718 ft and from 5724 to 5738 ft. The gray shading indicates neutron-density crossover (NPHI < DPHI), indicating gas in the formation.

Resistivity Logs

101

![img-25.jpeg](img-25.jpeg)

Figure 5.16. Computer-generated neutron-density porosity (PHIA) and EPT porosity (ECMP) lag through two Mississippian Chester sandstones in western Kansas.

The Chester sandstones are from 5704 to 5718 ft and from 5724 to 5738 ft. Note that in both the upper sand and the lower sand, the EPT porosity (ECMP) is less than neutron-density (PHIA) indicating that both sands should be productive. The gray shading shows depths where ECMP<PHIA.

6

Henderson, Steven, 2004, Nuclear Magnetic Resonance Logging, in G. Asquith and D. Krygowski, Basic Well Log Analysis: AAPG Methods in Exploration 16, p. 103-113.

# Nuclear Magnetic Resonance Logging

## GENERAL

At the time of publication of this book, nuclear magnetic resonance (NMR) logs are still not widely used, and their use in some geologic and drilling environments is still problematic. At present, while they create estimates of porosity that are equivalent to the other porosity logs (and have some advantages over those logs), they are most powerful when used in conjunction with that other data rather than instead of it. This chapter is focused on the interpretive applications of NMR logs.

## LIMITATIONS OF CONVENTIONAL LOGS

Conventional porosity and resistivity logs provide the geologist with a first look at the reservoir, but there are practical limits to the accuracy and usefulness of these data. Neutron, density, and sonic porosities are more sensitive to lithology than to reservoir fluids (this is not always the case in a gas-bearing formation). As a result, even small amounts of clay minerals may cause errors in porosity measurements. In addition, reservoirs commonly contain clay-bound, capillary-bound, and moveable water. Resistivity tools are sensitive to *all* water, and Archie water-saturation calculations can overestimate the amount of producible water. Thus, potential pay zones might remain elusive with conventional logs.

Porosity measurements with neutron-density combinations provide an estimate of *total porosity*, which is *all* the pore space in the reservoir whether the pores are interconnected or isolated. Still, with volume of shale ($V_{\text{shale}}$) corrections, it is possible to mostly eliminate the shale effect and arrive at an estimate of *effective porosity* or producible pore space. What remains to be resolved in this situation is the critical difference between any capillary-bound water and moveable water. Furthermore, porosity and resistivity logs pro

provide few clues about other petrophysical information such as hydrocarbon type (e.g., low-viscosity versus high-viscosity oils), pore-size and grain-size distributions, and permeability.

## NUCLEAR MAGNETIC RESONANCE APPLICATIONS

Nuclear magnetic resonance is rapidly gaining popularity in the petroleum industry as a means of overcoming the limitations of conventional logs. The primary advantages of NMR logging over conventional porosity measurements are that it uses no nuclear (radioactive) sources and it provides a lithology-independent measure of porosity. Much like the neutron tool, an NMR tool responds to the amount of hydrogen in the formation or *hydrogen index*. However, unlike the neutron measurement, hydrogen existing in matrix and clay minerals is transparent to the NMR porosity measurement. The result is a porosity measurement that is sensitive only to fluids occupying the pore space. Other petrophysical information may be deduced from the manner in which hydrogen protons react to magnetic fields created by the tool.

At the wellsite, NMR tools are capable of providing measures of both effective and clay-bound porosity (a combination of which yields total porosity), estimates of permeability, hydrocarbon type, pore size distribution, and information pertaining to the moveability of fluids. In many cases, the data obtained from NMR logs are in close agreement with core data. Post-processing of the data away from the well site, incorporating conventional logs and capillary pressure data from core analysis, may provide for a comprehensive evaluation of the uninvaded zone.

## PRINCIPLE OF NMR LOGGING

All formation fluids contain hydrogen protons that are randomly oriented throughout the pore space.

103

104

HENDERSON

NMR tools use a strong permanent magnetic field to align, or *polarize*, the spin axes of these protons in a preferred orientation. For these protons to generate a measurable signal, they must be at a condition of resonance. Resonance is achieved by pulsing the formation with an oscillatory magnetic field which causes the spin axes of the protons to tip away from their preferred orientation. Once the oscillatory magnetic field is removed, the signal generated by the hydrogen protons decays rapidly.

A sequence of repetitive pulses is applied with the NMR tool so that the protons generate a series of measurable signals or *echoes*. The initial amplitude of the measurable signal represents the amount of hydrogen in the formation and is therefore proportional to porosity. The amplitude of each successive echo, however, never regains that of the previous echo. The result of the pulsing sequence is a series of measurable echoes which, through a process called *relaxation*, exhibit an exponential decay (Figure 6.1). After some period of time, the amplitude of the echo is too small to be of any use, and the hydrogen protons must be allowed to realign with the permanent magnetic field through a process called *polarization*.

The exponential decay of the measurable signal—represented by the time constant $T_2$, or *relaxation time*—is a composite of a number of individual fluid decays in the formation. Through processing, the relaxation time ($T_2$) of each fluid component can be determined. These relaxation times are a function of the petrophysical properties of those fluids and the pores that contain them. The key to understanding the applications of NMR logs lies in the relationship of this relaxation time ($T_2$) to pore size (and fluid properties).

## PORE SIZE AND FLUID MOVEABILITY

Mathematical modeling shows that the relaxation time ($T_2$) of a given fluid within a single pore is proportional to the size of that pore (Coates et al., 1999). Water occupying small pores exhibits short relaxation times because of the rapid attenuation of proton movement in close proximity to grain surfaces. In larger pores where protons are not in such close proximity to grain surfaces, water exhibits longer relaxation times. As a first approximation, the distribution of $T_2$ data within a reservoir (Figure 6.2) depicts the pore-size distribution. This may also be related to grain-size distribution of the reservoir.

Clay-bound water occupies micropores that are characterized by very fast relaxation times ($T_2$). With a specialized pulse sequence, NMR tools may be configured to identify clay-bound water. This provides an

accurate method of distinguishing clay-bound porosity from effective pore space that may contain both capillary-bound and moveable, or free, fluids.

In addition to identifying clay-bound fluids, a primary benefit of NMR logging is its ability to differentiate between producible fluids (*free-fluid index*, or *FFI*) and capillary-bound fluids (*bulk volume irreducible*, or *BVI*). Free fluids generally occupy larger pores, whereas smaller pores contain fluids mostly bound by high capillary pressures. Because the $T_2$ distribution of a reservoir reflects a distribution of pore sizes, it can be used to determine the relative amounts of producible fluids and capillary-bound fluids (Figures 6.3a and 6.3b). This is extremely valuable in shaly sands and other fine-grained sands where Archie water-saturation calculations overestimate the amount of producible water. When combined with conventional porosity and resistivity data, NMR logs can be used effectively to identify the proportions of free water, clay-bound water, capillary-bound water, and hydrocarbons in a reservoir.

## NMR PERMEABILITY

In theory, permeability increases with pore size and the amount of effective porosity. The larger the pores are and more interconnected the pore network is, the more capable a reservoir is of transmitting fluids. Because relaxation time ($T_2$) is related to pore-size distribution, it can also be used to investigate permeability. For a homogeneous pore network like that of sandstones, small pore sizes generally result in lower permeabilities, whereas larger pore sizes can be associated with higher permeabilities.

There is a variety of methods used to determine NMR permeability, depending upon preference, reservoir conditions, and service company. These methods resolve only matrix permeability and underestimate the permeability of a fractured formation. In many cases, NMR permeability estimates are comparable with core data (Figure 6.4). The two most common permeability models are the free-fluid (or Coates) model and the mean-$T_2$ (or SDR) model.

The free-fluid (Coates) model of permeability determination uses a form of the following equation:

$$
k = \left( \frac{\Phi_{NMR}}{C} \right)^4 \left( \frac{FFI}{BVI} \right)^2 \tag{6.1}
$$

where:

$k =$ NMR-derived permeability

$\phi_{NMR} =$ NMR-derived effective porosity

$C =$ constant, depending on formation

Nuclear Magnetic Resonance Logging

105

$FFI =$ proportion of moveable fluids occupying effective porosity

$BVI =$ proportion of capillary-bound fluids occupying effective porosity

The free-fluid model uses the relative proportion of free-fluid to capillary-bound fluid within effective pore space to determine permeability. In a basic sense, smaller pores contain more capillary-bound fluid ($BVI$) and result in lower calculated permeability, while larger pores contain more free-fluid ($FFI$) and result in higher calculated permeability. This approach is satisfactory for sandstones where the pore network is rather homogeneous, but may be more problematic in carbonates where there is commonly a wider distribution of pore sizes. In carbonates, isolated vuggy pores contain a large quantity of free-fluid ($FFI$) with respect to capillary-bound fluid ($BVI$), but these pores might not contribute to permeability. As a result, permeability is overestimated. In reservoirs containing heavy oils, permeability can be underestimated because of the difficulty in distinguishing high-viscosity fluids from bound fluids on the basis of their fast relaxation times ($T_2$).

The free-fluid model is sensitive to the selection of a $T_2$ cutoff. For a given distribution of $T_2$ data (Figure 6.5), a cutoff may be determined to distinguish capillary-bound fluids from free fluids. For sandstones, this value is approximately 33 msec. Those pores with relaxation times ($T_2$) less than the selected cutoff are assumed to contain mostly capillary-bound fluids, and pores with relaxation times ($T_2$) greater than the cutoff are assumed to contain mostly free fluids. The $T_2$-cutoff selection depends upon lithology (carbonates may have a cutoff of as high as 100 msec) as well as capillary pressure. Therefore, conventional logs and core data can assist in determining a more accurate NMR permeability for a given reservoir.

An alternate method of permeability determination is the mean-$T_2$ (or SDR) model which uses a form of the following equation:

$$
k = a \left(\Phi_{NMR}\right)^4 \left(T_{2gm}\right)^2 \tag{6.2}
$$

where:

$k =$ NMR-derived permeability

$a =$ a constant, depending on formation

$\Phi_{NMR} =$ NMR-derived effective porosity

$T_{2gm} =$ geometric mean of the $T_2$ distribution

The mean-$T_2$ permeability model does not depend on the selection of a $T_2$ cutoff and, therefore, is not as sensitive to lithology or capillary pressure. Furthermore, in carbonates where there is a wider distribution of $T_2$ values (i.e., wider distribution of pore sizes), the

mean-$T_2$ model may provide a more accurate estimate of permeability through its use of the geometric mean of the $T_2$ distribution (Logan et al., 1997; Figure 6.5).

The presence of hydrocarbons influences the distribution of $T_2$ data, so permeability estimates can be slightly in error in oil-bearing and, particularly, gas-bearing zones. Both the free-fluid and mean-$T_2$ models tend to underestimate permeability in a gas-bearing reservoir. Because the NMR tool responds to the hydrogen index, it underestimates porosity just as the neutron tool does in a gas-bearing zone. To compensate for this effect, hydrogen index corrections can be performed on the NMR measurements to obtain a more accurate value of effective porosity ($\Phi_{NMR}$), or effective porosity may be taken from an alternate source.

## DIRECT HYDROCARBON TYPING

Reservoir fluids are characterized by different polarization times ($T_1$) and relaxation times ($T_2$) as illustrated in Table 1. NMR logging takes advantage of the differences in these time constants to provide several stand-alone methods of hydrocarbon typing. Specialized pulse sequences are required for successful direct hydrocarbon typing from NMR logs, and this requires careful planning before logging is started.

Table 6.1. Typical NMR Properties of Reservoir Fluids (modified after Coates et al., 1999).

|   | Polarization Time T1 (msec) | Relaxation Time T2 (msec) | Viscosity (cp)  |
| --- | --- | --- | --- |
|  Brine | 1 – 500 | 1 – 500 | 0.2 – 0.8  |
|  Oil | 3,000 – 4,000 | 300 – 1,000 | 0.2 – 1,000  |
|  Gas | 4,000 – 5,000 | 30 – 60 | 0.011 – 0.014 (methane)  |

The two most common methods of stand-alone hydrocarbon typing are *time-domain analysis* (TDA) and *diffusion analysis*. The basis for time-domain analysis is that brine and hydrocarbons require dramatically different polarization times ($T_1$). TDA data are acquired using a pulse sequence with two separate wait times (*dual $T_w$*): one short and one long. Brine is fully polarized after both the short $T_w$ and the long $T_w$; therefore, its signal amplitude on $T_2$ distributions for the two wait time measurements is almost the same (Figure 6.6a). Hydrocarbons, however, are fully polarized only after the long $T_w$. The difference in the two

106

HENDERSON

$T_{2}$ distributions is used to detect the presence and determine the saturation of medium to light oils and gas (Figure 6.7 and Figure 6.8). Hydrogen index corrections can also be applied to the data to obtain more accurate values for porosity and permeability in oil-bearing and gas-bearing formations. A requirement of TDA is that there be sufficient $T_{2}$ contrast between reservoir fluids. If very light hydrocarbons exist, it might be difficult to distinguish them from brine and gas based on their similar relaxation times $(T_{2})$.

Rate of diffusion of hydrocarbons is related to the viscosity of the fluid that holds them, and *diffusion analysis* takes advantage of this diffusion contrast between hydrocarbons. Hydrogen in gas is more prone to diffusion than hydrogen in medium to heavy oils. Diffusion analysis data are acquired with a pulse sequence using two separate spacings between pulses, or *interecho spacings* $(T_{e})$: one short and one long. Brine and medium oil relax much faster during long-$T_{e}$ measurements than during short-$T_{e}$ measurements. Light oil exhibits a large difference in relaxation times $(T_{2})$ between the two interecho spacings, and heavy oils exhibit only a minor (if any) difference in $T_{2}$. Brine can be distinguished from medium to light oil by a shift in the $T_{2}$ distribution between the short and long interecho-spacing measurements (Figure 6.6b). An *enhanced diffusion analysis* method is also available that uses a long $T_{e}$ and dual $T_{w}$ to increase the signal generated by more viscous intermediate oils, and it is reliable over a wider range of viscosities (Akkurt et al., 1998). Neither diffusion-analysis method is useful for gas detection, however, because gas can experience such an extreme shift in the $T_{2}$ distribution that it is easily confused with capillary-bound water and clay-bound water.

In a more conventional sense, NMR data can be combined with density porosity data to provide a method of gas detection similar to neutron-density combinations. Because of the low hydrogen index of gas-bearing zones, they are characterized by underestimated NMR porosities. Gas-bearing zones can therefore be identified where density porosity is greater than NMR porosity.

## NMR APPLICATIONS IN CARBONATES

The majority of NMR applications were developed for sandstone reservoirs, but these applications have been expanded to carbonate reservoirs as well. Interpretation of NMR logs in carbonates may be more problematic than in sandstones, primarily because of the complex heterogeneous nature of the pore network. In carbonates, there is a weaker relationship between pore size and relaxation time $(T_{2})$. This might

require calibration of NMR data to core or conventional logs for more accurate results; however, NMR logs in carbonates provide much of the same information as in sandstones.

Though lithology plays little role in the NMR measurement, it still must be considered to configure the tool for obtaining accurate information. One source of difficulty involves the fact that carbonates have longer polarization times $(T_{1})$ than sandstones. If a pulse sequence is initiated before all hydrogen in the formation has been fully polarized, the NMR porosity would be underestimated. The potential underestimation of porosity can cause compounded errors in the determination of fluid moveability, permeability, and hydrocarbon type.

Carbonates generally require a pulse sequence with long wait times $(T_{w})$. While this may reduce the error in measurements, it may also translate into slower logging speeds or require additives to the drilling fluid. In addition, the wider pore-size distributions (i.e., $T_{2}$ distributions) of carbonates tend to introduce some problems into their interpretation. With information from conventional logs and core analysis, however, it is possible to determine cutoff parameters in carbonates that provide accurate estimates of fluid moveability, permeability, and hydrocarbon type.

## REVIEW

1. NMR logs provide lithology-independent measurements of effective porosity as well as total porosity, thus overcoming many of the limitations of conventional porosity measurements (i.e., neutron, density, and sonic).
2. A major advantage of NMR logs is the ability to differentiate between irreducible and moveable fluids in a reservoir. This, combined with effective porosity measurements, leads to more accurate estimates of the amount of producible water.
3. NMR logs provide estimates of permeability, grain-size and pore-size distributions, and even viscosity; all of which are problematic or impossible to determine with conventional porosity and resistivity logs.
4. Through a variety of direct hydrocarbon-typing methods, NMR logs are capable of identifying hydrocarbons and determining their saturations without incorporating data from conventional porosity and resistivity logs.
5. Although the NMR measurement is sensitive only to fluids, the best results are obtained when information about the lithology of a reservoir (e.g., core analysis or a conventional porosity log) is available.

Nuclear Magnetic Resonance Logging

107

![img-26.jpeg](img-26.jpeg)

Series of Exponential Decays

![img-27.jpeg](img-27.jpeg)

Courtesy Halliburton Energy Services ©1999, Halliburton Energy Services

![img-28.jpeg](img-28.jpeg)

Courtesy Halliburton Energy Services ©1999, Halliburton Energy Services

Figure 6.1. A sequence of oscillatory magnetic field pulses (induced by radio-frequency energy) generates echoes which exhibit an exponential decay in amplitude. This exponential decay is a composite of a number of individual fluid decays in the reservoir. The rate of decay—expressed as the time constant $T_{2}$, or relaxation time—is a function of the petrophysical properties of those fluids and the pores that contain them. Initial amplitude of the decay curve is calibrated to represent porosity.

Following a series of pulses, the amplitude of the signal becomes too small to measure and hydrogen protons must be allowed to repolarize with the permanent magnetic field. If the wait time ($T_{w}$) is not long enough, then underpolarization of hydrogen results in an underestimation of NMR porosity.

Pulse sequences can be customized, depending upon the type of data to be gathered. Variables in the pulse sequence that can be altered include wait time ($T_{w}$), the number of pulses, and the spacing between these pulses ($T_{e}$).

Figure 6.2. Inversion processing of the individual decay components in a reservoir yields a $T_{2}$ distribution. Calibration of the NMR tool insures that the area beneath the curve is porosity. If a reservoir is at 100% water saturation, then the distribution of $T_{2}$ data reflects the pore size distribution of the reservoir.

Reservoirs with large amounts of irreducible fluids (short relaxation time, $T_{2}$) exhibit peaks to the left of the $T_{2}$ distribution. Reservoirs with a larger proportion of moveable fluids will exhibit peaks to the right of the $T_{2}$ distribution. With data from core and conventional logs, a $T_{2}$ cutoff can be established to differentiate between irreducible fluids and moveable fluids in a given reservoir.

In addition to whether the fluid present is irreducible or moveable, the presence of hydrocarbons will tend to skew the $T_{2}$ distribution, depending upon their type, viscosity, and relative amounts.

108

HENDERSON

Figure 6.3a. Example of induction and neutron-density logs through a hydrocarbon-bearing shaly sand in the Gulf of Mexico, North America.

In this example, resistivity gradually decreases with depth through the zone of interest (XX160 – XX260). This decrease in resistivity might be the result of larger amounts of moveable water in the lower half of the zone. However, the gamma ray curve indicates a coarsening-upward sequence, so a great percentage of the water present in the lower half of the zone could be trapped by clays or within smaller pore throats and would not be produced.

![img-29.jpeg](img-29.jpeg)

Courtesy Halliburton Energy Services ©1999, Halliburton Energy Services

Nuclear Magnetic Resonance Logging

109

![img-30.jpeg](img-30.jpeg)

Courtesy Halliburton Energy Services ©1999, Halliburton Energy Services

Figure 6.3b. Example of Magnetic Resonance Imaging Log™ through a hydrocarbon-bearing shaly sand in the Gulf of Mexico, North America.

This log is from the same well as illustrated in Figure 6.3a.

Track 1 contains gamma ray and caliper curves as well as partial porosities of each fluid decay component in the reservoir. The partial porosities may be ignored for the purpose of this discussion.

Track 2 contains resistivity curves measured by the induction log and a permeability curve (MRIL PERM) determined from the NMR measurements.

Track 3 displays the T₂ distribution resulting from the measured exponential decays. Notice that the shales above and below the zone of interest exhibit large peaks to the left of the distribution, indicating large amounts of irreducible fluids (for an explanation, see Figure 6.5).

Track 4: This track contains an effective porosity curve (MPHI) and a bulk volume irreducible curve (BVI). BVI represents the amount of capillary-bound fluid in the reservoir, and the yellow-shaded region between the MPHI and BVI curves represents the amount of moveable, or free, fluid in the reservoir.

A coarsening-upward sequence can be further confirmed by the increase of BVI with depth. Below a depth of X210, the NMR log indicates an increasing proportion of irreducible fluids (BVI, gray-shaded area) than moveable fluids (FFI, yellow-shaded area). If the moveable fluid present is hydrocarbons, the larger fraction of irreducible water would be responsible for the lower resistivities seen in the lower half of the zone of interest. The presence of hydrocarbons can be determined by incorporating the conventional resistivity data into the NMR processing (see Figure 6.8).

110

HENDERSON

Figure 6.4. Example of Magnetic Resonance Imaging Log™ through a shaly sand in Egypt illustrating the comparison of NMR permeability (MPERM) to core permeability (CPERMH) and NMR porosity (MPHI) to core porosity (CPOR).

![img-31.jpeg](img-31.jpeg)

Courtesy Halliburton Energy Services ©1999, Halliburton Energy Services

Nuclear Magnetic Resonance Logging

111

![img-32.jpeg](img-32.jpeg)

Courtesy Halliburton Energy Services ©1999, Halliburton Energy Services

Figure 6.5. T₂ distributions illustrating the free-fluid (Coates) and mean-T₂ (SDR) methods of permeability estimation from NMR logs.

The free-fluid (Coates) permeability model uses the ratio of moveable fluid (FFI) to irreducible fluid (BVI) to estimate permeability. With information from core and/or conventional logs, a T₂ cutoff may be established. The pore space beneath the curve and to the right of the T₂ cutoff is assumed to contain free, or moveable, fluids (FFI). The pore space beneath the curve and to the left of the T₂ cutoff is assumed to contain irreducible fluids (BVI).

The mean-T₂ (SDR) permeability model uses the geometric mean of the T₂ distribution to differentiate between moveable fluid and irreducible fluid. Pore space beneath the curve and to the right of the mean-T₂ is assumed to contain moveable fluid (FFI). The pore space beneath the curve and to the left of the mean-T₂ is assumed to contain irreducible fluid (BVI).

You can use the information on this page to interpret track 3 of Figure 6.3b.

![img-33.jpeg](img-33.jpeg)

(a) Dual TW Logging: T₁-Weighted

![img-34.jpeg](img-34.jpeg)

(b) Dual TE Logging: D-Weighted

![img-35.jpeg](img-35.jpeg)

Courtesy Halliburton Energy Services ©1999, Halliburton Energy Services

Figure 6.6. Changes in T₂ distributions for different methods of NMR direct hydrocarbon typing.

6a: Time-domain analysis uses a combination of short and long wait times (T_w) to detect and determine the saturations of medium to light oils and gas. After the short wait time, the water signal is at a maximum amplitude while oil and gas have only been partially polarized. After the long wait time, the oil and gas have been fully polarized and there is no change in the amplitude of the water signal. The difference in T₂ distributions between the two wait time measurements can be used to determine the saturations of oil and gas.

6b: Diffusion analysis uses a combination of short and long inter-echo spacings (T_e) to detect and determine the saturations of oil. Relaxation times (T₂) of water and medium to heavy oils are much faster using long-T_e measurements than when using short-T_e measurements. The shift in peaks of the T₂ distributions may be used to detect and determine the saturations of these fluids. Diffusion analysis is not effective for detecting gas because gas may exhibit such a dramatic shift in T₂ that it is confused with the irreducible water signal.

112

HENDERSON

Figure 6.7. Example of dual-$T_w$ Magnetic Resonance Imaging Log$^{\text{TM}}$ through an oil-bearing shaly sand in the Gulf of Mexico, North America.

Track 1 illustrates gamma ray and caliper curves. Track 2 shows the NMR permeability curve (MRIL PERM). Track 3 displays the $T_2$ distribution of the long-$T_w$ measurement ($T_w = 8$ sec) and Track 4 displays the $T_2$ distribution for the short-$T_w$ measurement ($T_w = 1$ sec). Tracks 5 and 6 display effective porosity (MPHI) and irreducible fluid (BVI) as determined from both the long- and short-$T_w$ measurements, respectively. In Tracks 5 and 6, the yellow-shaded region represents the proportion of moveable fluid (FFI) for the different $T_w$ measurements.

Comparison of BVI and FFI values between the long-$T_w$ (track 5) and short-$T_w$ (track 6) measurements may be used as a quick-look indicator of hydrocarbons. Gas and light oil have longer polarization times ($T_1$) and require a longer wait time ($T_w$) for full polarization than does water. Water, either bound or free, is fully polarized after the short-$T_w$. Light oil and gas (requiring longer polarization), is polarized only after the long-$T_w$. Therefore, if hydrocarbons are present, the long-$T_w$ should show a larger FFI than the short-$T_w$. Note that the yellow-shaded region (FFI) in track 5 (long-$T_w$) is wider than the yellow-shaded region (FFI) in track 6 (short-$T_w$), indicating the presence of light oil or gas. Heavy oils, with very short relaxation times ($T_2$), might appear as an increase in BVI between the short and long wait times.

For this example, integration of resistivity measurements from the induction log showed that all of the moveable fluid occupying the zone of interest from XX690 to XX865 is oil. The reservoir is therefore determined to be at irreducible water saturation ($S_{\text{win}}$). NMR permeability data (track 2) also indicate that there is sufficient permeability to produce this oil.

![img-36.jpeg](img-36.jpeg)

Courtesy Halliburton Energy Services ©1999, Halliburton Energy Services

Nuclear Magnetic Resonance Logging

113

![img-37.jpeg](img-37.jpeg)

Courtesy Halliburton Energy Services ©1999, Halliburton Energy Services

Figure 6.8. Example of time domain analysis of Magnetic Resonance Imaging Log™ data incorporating resistivity measurements through a hydrocarbon-bearing shaly sand in the Gulf of Mexico, North America.

This log is from the same well as illustrated in Figures 6.3a and 6.3b.

Track 2 contains resistivity measurements from the induction log and the NMR permeability curve (MRIL PERM). Track 4 illustrates a differential spectrum (DIF SPEC) representing the different between T₂ distributions obtained during the long-Tw and short-Tw measurements. In subtracting the short-Tw distribution from the long-Tw distribution, the water signal cancels out and only the hydrocarbon signal remains in the differential spectrum. Track 5 displays the results of incorporating resistivity measurements with NMR measurements.

By combining resistivity measurements from the induction log, it becomes apparent that the moveable fluid (FFI) indicated in 6.3b is actually a combination of oil (shaded green) and water (shaded blue). This well was drilled with a water-based drilling fluid, and the free water indicated from XX160 to XX240 is nothing more than invaded mud filtrate. Because of the large proportion of irreducible fluid (BVI) and high NMR permeability, this formation is likely at irreducible water saturation (Swin) and would produce water free.

7

Asquith, G., and D. Krygowski, 2004, Log Interpretation, in G. Asquith and D. Krygowski, Basic Well Log Analysis: AAPG Methods in Exploration 16, p. 115-135.

# Log Interpretation

## GENERAL

As shown in the previous chapters, determining the porosity and true resistivity of a zone is the first step in converting the raw log data into estimated quantities of oil, gas, and water in a formation. These estimated quantities are used to evaluate a zone and to determine whether a well completion attempt is warranted. This chapter covers some of the different methods from which these estimates are derived. The methods discussed are: Archie water saturations ($S_w$ and $S_{xo}$) and the ratio method, quick-look technique, bulk volume water ($BVW$), and saturation crossplots (Pickett plots and Hingle plots). Determination of log-derived permeability ($K_e$) and shaly sand analysis are also discussed.

As important as this log-derived information is, however, it should not be applied without the inclusion of other data. This statement is, perhaps, obvious to the reader, but it can't be overemphasized. A geologist should always consider every item of relevant data, such as drill stem tests, sample shows, mud-log analysis, nearby production, etc., before making a decision to set pipe.

## SCANNING THE LOGS: A RECONNAISSANCE TECHNIQUE

It is an exceedingly rare log that contains more reservoir than nonreservoir, and when one is unfamiliar with an area or wants to broadly reconnoiter an area, a scanning technique that sorts reservoir from nonreservoir can be helpful, even with access to computer-aided processing. A good scanning technique not only identifies the reservoirs, but can also give the geologist hints as to potential pay and wet zones. Remember that in the interpretive process, the identification of wet zones is as important as the discovery of those containing hydrocarbons, because the com

comparison of the two helps clearly identify both the presence and amount of the hydrocarbons.

Figure 7.1 is a flowchart for one such scanning technique. Note that it has two paths, one for clastics and one for carbonates. In the clastic case, the resistivity log is the primary reconnaissance measurement because clastics tend to consist of reservoirs surrounded by shales of slowly varying resistivity. The changes in resistivity due to changes in fluid content of the reservoirs tend to stand out against this relatively constant background. On the carbonate path, on the other hand, formation resistivities tend to vary widely with changing rock types, and commonly there are few shales against which to measure changes. In this case, the porosity log is the primary reconnaissance measurement. By first finding the porous zones, those with the capacity to hold fluids (of any type) can be identified.

Figure 7.2 shows the details of a log interpretation, once zones of interest are identified, with references to the chapters in which the information is discussed.

## ARCHIE WATER SATURATIONS: $S_w$ AND $S_{xo}$

Water saturation ($S_w$) of a reservoir's uninvaded zone is calculated by the Archie (1942) formula:

$$
S_w = \left( \frac{a \times R_w}{R_t \times \phi^m} \right)^{\frac{1}{n}} \tag{7.1}
$$

where:

$S_w =$ water saturation of the uninvaded zone

$R_w =$ resistivity of formation water at formation temperature

$R_t =$ true formation resistivity (i.e., deep induction or deep laterolog corrected for invasion)

$\phi =$ porosity

$a =$ tortuosity factor (Table 1.1; Chapter 1)

115

116

ASQUITH AND KRYGOWSKI

$m =$ cementation exponent (Table 1.1; Chapter 1)

$n =$ saturation exponent

The uninvaded zone's water saturation ($S_w$), determined by the Archie equation, is the most fundamental quantity used in log evaluation. But merely knowing a zone's water saturation ($S_w$) does not provide enough information to completely evaluate a zone's potential productivity. A geologist must also determine if:

- the water saturation is low enough for a water-free completion
the hydrocarbons are moveable
the zone is permeable
- there is an commercial volume of recoverable hydrocarbon reserves

Water saturation of a formation's flushed zone ($S_{xo}$) is also based on the Archie equation, but two variables are changed: mud filtrate resistivity ($R_{mf}$) in place of formation water resistivity ($R_w$) and flushed zone resistivity ($R_{xo}$) in place of uninvaded zone resistivity ($R_t$).

$$
S_{xo} = \left( \frac{a \times R_{mf}}{R_{xo} \times \phi^m} \right)^{\frac{1}{n}} \tag{7.2}
$$

where:

$S_{xo} =$ water saturation of the flushed zone

$R_{mf} =$ resistivity of the mud filtrate at formation temperature

$R_{xo} =$ shallow resistivity from a very shallow reading device, such as laterolog-8, microspherically focused log, or microlaterolog

$\phi =$ porosity

$a =$ tortuosity factor (Table 1.1; Chapter 1)

$m =$ cementation exponent (Table 1.1; Chapter 1)

$n =$ saturation exponent

Water saturation of the flushed zone ($S_{xo}$) can be used as an *indicator of hydrocarbon moveability*. For example, if the value of $S_{xo}$ is much larger than $S_w$, then hydrocarbons in the flushed zone have probably been moved or flushed out of the zone nearest the borehole by the invading drilling fluids ($R_{mf}$).

## Ratio Method

The ratio method identifies hydrocarbons from the difference between water saturations in the flushed zone ($S_{xo}$) and the uninvaded zone ($S_w$). When the uninvaded zone form of Archie's equation (Equation 7.1) is divided by the flushed zone form (Equation 7.2), the following results:

$$
\left( \frac{S_w}{S_{xo}} \right)^2 = \frac{R_{xo} / R_t}{R_{mf} / R_w} \tag{7.3}
$$

where:

$S_w =$ water saturation in the uninvaded zone

$S_{xo} =$ water saturation in the flushed zone

$R_{xo} =$ formation's shallow resistivity from a measurement such as laterolog-8, microspherically focused log, or microlaterolog

$R_t =$ true formation resistivity (i.e., deep induction or deep laterolog corrected for invasion)

$R_{mf} =$ resistivity of the mud filtrate at formation temperature

$R_w =$ resistivity of formation water at formation temperature

When $S_w$ is divided by $S_{xo}$, the formation factor ($F = a/\phi^m$) is cancelled out of the equation because the same formation factor is used to calculate both $S_w$ and $S_{xo}$. This can be very helpful in log analysis because, from the ratio $(R_{xo}/R_t)/(R_{mf}/R_w)$, the geologist can determine a value for both the moveable hydrocarbon index ($S_w/S_{xo}$) and water saturation by the ratio method without knowing porosity. Therefore, a geologist can still derive useful formation evaluation log parameters even though porosity logs are unavailable.

The moveable hydrocarbon index by the ratio method is:

$$
\frac{S_w}{S_{xo}} = \left( \frac{R_{xo} / R_t}{R_{mf} / R_w} \right)^{\frac{1}{2}} \tag{7.4}
$$

where:

$S_w/S_{xo} =$ moveable hydrocarbon index

$R_{xo} =$ shallow resistivity from measurements such as laterolog-8, microspherically focused log, or microlaterolog

$R_t =$ true formation resistivity (i.e., deep induction or deep laterolog corrected for invasion)

$R_{mf} =$ resistivity of mud filtrate at formation temperature

$R_w =$ resistivity of formation water at formation temperature

The cementation exponent ($n$) is assumed to be 2.0

If the ratio $S_w/S_{xo}$ is equal to or greater than 1.0, then hydrocarbons were not moved during invasion. This is true regardless of whether or not a formation contains hydrocarbons. Whenever the ratio $S_w/S_{xo}$ is less than 0.7 for sandstones or less than 0.6 for carbonates, moveable hydrocarbons are indicated (Schlumberger, 1972).

To determine water saturation by the ratio method

Log Interpretation

117

($S_{wr}$), you must know the flushed zone's water saturation. In the flushed zone of formations with moderate invasion and average residual hydrocarbon saturation, the following relationship normally works well:

$$S_{xo} = (S_w)^{\frac{1}{5}} \tag{7.5}$$

where:

$S_{xo}$ = water saturation of the flushed zone

$S_w$ = water saturation of the uninvaded zone

Substituting Equation 7.5 in Equation 7.4 and solving for $S_w$, the ratio method water saturation ($S_{wr}$) is:

$$S_{wr} = \left( \frac{R_{xo} / R_t}{R_{mf} / R_w} \right)^{\frac{5}{8}} \tag{7.6}$$

or:

$$S_{wr} = \left( \frac{R_{xo} / R_t}{R_{mf} / R_w} \right)^{0.625} \tag{7.7}$$

where:

$S_{wr}$ = moveable hydrocarbon index

$R_{xo}$ = shallow resistivity from measurements such as laterolog-8, microspherically focused log, or microlaterolog

$R_t$ = true formation resistivity (i.e., deep induction or deep laterolog corrected for invasion)

$R_{mf}$ = resistivity of mud filtrate at formation temperature

$R_w$ = resistivity of formation water at formation temperature

To use the ratio method in an interpretation process, the water saturation of the uninvaded zone should be calculated by both the Archie equation ($S_{wa}$) and the ratio method ($S_{wr}$). The following observations can be made:

1. If $S_{wa} \sim S_{wr}$, the assumption of a step-contact invasion profile is indicated to be correct, and all values determined ($S_w$, $R_t$, $R_{xo}$, and $d_i$) are correct.

2. If $S_{wa} > S_{wr}$, then the value for $R_{xo}/R_t$ is too low. $R_{xo}$ is too low because invasion is very shallow, or $R_t$ is too high because invasion is very deep. Also, a transition-type invasion profile might be indicated and $S_{wa}$ is considered a good value for the zone's actual water saturation.

3. If $S_{wa} < S_{wr}$, then the value for $R_{xo}/R_t$ is too high. $R_{xo}$ is too high because of the effect of adjacent, high-resistivity beds, or $R_t$ estimated from the deep resistivity measurement is too low because $R_{xo}$ is less than $R_t$. Also, an annulus-type invasion profile might be indicated and/or $S_{xo} < S_w^{1/5}$ (from Equation 7.5). In this case, a more accurate value for water saturation

can be estimated using the following equation (from Schlumberger, 1977):

$$(S_w)_{COR} = S_{wa} \times \left( \frac{S_{wa}}{S_{wr}} \right)^{0.25} \tag{7.8}$$

where:

($S_w$)$_{COR}$ = corrected water saturation of the uninvaded zone

$S_{wa}$ = water saturation of the uninvaded zone (Archie method)

$S_{wr}$ = water saturation of the uninvaded zone (ratio method)

4. If $S_{wa} < S_{wr}$, the reservoir might be a carbonate with moldic (i.e., oomoldic, fossil-moldic, etc.) porosity and low permeability.

### QUICK-LOOK METHODS

#### General

Quick-look methods are helpful to the geologist because they provide flags, or indicators, that point to possible hydrocarbon zones requiring further investigation. The four quick-look methods discussed here are:

- $R_{xo}/R_t$
- apparent water resistivity ($R_{wa}$)
- conductivity-derived porosity
- Wet resistivity ($R_o$)

#### $R_{xo}/R_t$

The $R_{xo}/R_t$ technique relies on the comparison of the resistivity ratio, plotted as a curve on the log display, to the SP curve.

#### Procedure

1. Calculate the $R_{xo}/R_t$ ratio from the deep and shallow reading resistivity measurements;
2. Plot the ratio in the same track as the SP, and look for the following patterns.

#### Patterns to observe

1. In a shale, the ratio is relatively constant, like the SP, and usually close to 1.
2. In a water-bearing zone, the $R_{xo}/R_t$ ratio tracks the SP.
3. In a hydrocarbon-bearing zone, the $R_{xo}/R_t$ ratio moves away from the SP [a deflection to the right for the case of a normal (negative) SP].

118

ASQUITH AND KRYGOWSKI

Basis for the technique

From Chapter 2, the equation relating the SP to fluid resistivities is:

$$SP = -K \times \log \left( \frac{R_{mf}}{R_w} \right) \tag{7.9}$$

In water-bearing zones:

$$R_{xo} = F \times R_{mf} \quad (\text{flushed zone}) \tag{7.10}$$

$$R_o = F \times R_w \quad (\text{uninvaded zone}) \tag{7.11}$$

Solving Equations 7.2 and 7.3 for $R_{mf}$ and $R_w$ respectively, and substituting the results in Equation 7.1 yields:

$$SP = -K \times \log \left( \frac{R_{xo}}{R_o} \right) \tag{7.12}$$

The $R_{xo}/R_o$ ratio is then related to the SP through a constant. Since $R_o$ is just a special case of $R_t$ ($R_o$ is the resistivity in the undisturbed, water-bearing zone), $R_t$ can be substituted for $R_o$ for the more general case. In water-bearing intervals, the $R_{xo}/R_t$ ratio parallels the response of the SP, and both curves move in the same direction from their respective baseline values. In a hydrocarbon-bearing interval, while the SP still responds to the differences in connate water and mud filtrate resistivities and moves accordingly, the $R_{xo}/R_t$ ratio decreases (because of increasing $R_t$) and the $R_{xo}/R_t$ curve moves away from the SP.

The $R_{xo}$ curve usually used for the ratio is derived from a shallow-reading measurement, such as a microspherically focused log or a microlaterolog. The $R_t$ curve is derived from a deep-reading measurement such as the deep induction log or deep laterolog. In practice, especially when the ratio is calculated and displayed as part of the logging job, the measurements are normally used without any environmental corrections being applied.

### Apparent water resistivity ($R_{wa}$)

The $R_{wa}$ technique relies on the comparison of calculated values of water resistivity between intervals in a well. This comparison can be made between different zones or within the same zone if a water-hydrocarbon contact is suspected in that zone. The assumption is that this lowest value of $R_{wa}$ is the closest approximation to the true formation water resistivity ($R_w$) and that values of $R_{wa}$ greater than the minimum value are indicative of the presence of hydrocarbons. A water saturation can also be calculated from the values of $R_{wa}$.

Procedure

1. Calculate an apparent water resistivity ($R_{wa}$) from the porosity and uninvaded zone resistivity measurements.
2. Look for the lowest value of $R_{wa}$ in a porous and permeable zone and compare it to the values of $R_{wa}$ calculated in the other zones.
3. If desired, an Archie water saturation can be calculated from the $R_{wa}$ values in the compared zones.

Patterns to observe

1. The zone with the lowest value of $R_{wa}$ is the most likely to be water-bearing, and the value of $R_{wa}$ is closest to the actual value of $R_w$ in the formation.
2. Zones with values of $R_{wa}$ greater than the minimum observed are likely to have some hydrocarbon saturation.

Interpretation pitfalls

The $R_w$ values in the zones that are compared are assumed to be the same.

In low-porosity zones (less than about 10% porosity), the $R_{wa}$ value is lower than the actual $R_w$ value.

Basis for the technique

Recall from Chapter 1 that

$$R_o = F \times R_w \tag{7.13}$$

and

$$F = \frac{a}{\phi^m} \tag{7.14}$$

Combining Equations 7.5 and 7.6, and solving for $R_w$ yields:

$$R_w = \frac{R_o \times \phi^m}{a} \tag{7.15}$$

From Equation 7.7 above, define apparent water resistivity ($R_{wa}$) as:

$$R_{wa} = \frac{R_t \times \phi^m}{a} \tag{7.16}$$

When a given zone is water bearing, $R_t$ reverts to the water-bearing resistivity ($R_o$) and $R_{wa}$ equals $R_w$. If the zone contains hydrocarbons, $R_t$ is greater than $R_o$, and $R_{wa}$ is greater than $R_w$. By comparing a number of zones (or different depths in the same zone, where a water-hydrocarbon contact is suspected) and assuming the zone with the lowest value of $R_{wa}$ is wet, the minimum value of $R_{wa}$ can be used as an estimate for the value of $R_w$ in all the zones being considered. If the zone with the minimum $R_{wa}$ value actually contains

Log Interpretation 119

some hydrocarbons, then the other zones contain even more hydrocarbons than anticipated.

In practice, especially when calculated and displayed as a curve during a logging job, the following values are used for simplicity: a = 1.0, m = 2.0. The deep induction log or deep laterolog is used as R_t, usually without any environmental corrections. Porosity is usually derived from the sonic or density log using the proper matrix and fluid parameters for the formations to be encountered. If available in real time during logging, the neutron-density crossplot porosity should be used for the best estimate of porosity.

An Archie water saturation can also be calculated from the ratio of the R_wa values.

$$S_w = \sqrt{\frac{R_{wa\ minimum}}{R_{wa\ zone}}} \tag{7.17}$$

where the cementation exponent (n) in the equation above is assumed to be 2.

A shortcut to the saturation calculation, used as a scanning aid, is:

- (R_wa zone/R_wa minimum) = 3 yields S_w = 0.58;
- (R_wa zone/R_wa minimum) = 4 yields S_w = 0.50;
- (R_wa zone/R_wa minimum) = 5 yields S_w = 0.45.

Where a = 1.0 and m = 2.0.

### Conductivity-derived porosity (also referred to as resistivity-porosity)

Although this technique originated with the use of the conductivity curve (Dresser Atlas, 1975), the conductivity curve is now rarely presented on log displays, and the technique is described here using the resistivity measurement.

This technique calculates a porosity from Archie's equation, using the form of the equation for water-bearing zones (S_w = 1). The porosity values are generated as a curve and are normally displayed in the same track as the SP, scaled from high porosity values on the left to low porosity values on the right.

### Procedure

1. Calculate the porosity from Archie's equation (assuming S_w = 1.0), using the uninvaded zone resistivity measurement.
2. Compare the curve values and the relative position of the curve in porous and permeable zones.
3. If desired, an Archie water saturation can be calculated by comparing the conductivity-derived porosi-

ty to porosity from one of the porosity measurements (sonic, density, or neutron).

### Patterns to observe

1. In water-bearing zones, the conductivity-derived porosity is high and approximately equal to the true formation porosity.
2. In zones that contain hydrocarbons, the conductivity-derived porosity is low, lower than the true formation porosity.

### Interpretation pitfalls

The choice of an incorrect value for R_w would change the value of conductivity-derived porosity, and might make its comparison to true formation porosity inaccurate. It would not, however, change the results of comparison of the curve values in different zones.

### Basis for the technique

From Chapter 1, Archie's equation can be solved for porosity:

$$\phi = \left(\frac{a \times R_w}{R_t \times S_w^n}\right)^{\frac{1}{m}} \tag{7.18}$$

If the water-bearing case is considered, where S_w = 1, the equation reduces to:

$$\phi = \left(\frac{a \times R_w}{R_t}\right)^{\frac{1}{m}} \tag{7.19}$$

By using the form of the equation above (7.19), the water-filled porosity is determined. Where the formation is actually water filled, R_t reverts to the water-bearing resistivity (R_o). The porosity calculated from this equation is close to the actual formation porosity, assuming that the parameters in the equation are close to the actual formation parameters. When the formation contains hydrocarbons, R_t is greater than R_o, and the calculated porosity is less than the actual formation porosity.

Traditionally this curve has been plotted in the same log track as the SP curve, and its movement compared to the SP. It can also be plotted in the same track as a porosity curve from one of the porosity tools, where decreases in conductivity-derived porosity with respect to the porosity curve indicate the presence of hydrocarbons.

Water saturation can be estimated by the following equation:

$$S_w = \frac{\phi_{conductivity}}{\phi_{actual}} \tag{7.20}$$

120

ASQUITH AND KRYGOWSKI

# Wet resistivity ($R_o$)

The wet-resistivity curve ($R_o$) is one of the oldest quick-look techniques. Unlike the other curves, which tend to be compared to the SP curve, it is plotted as an overlay on the resistivity curve.

## Procedure

1. Calculate \( R_{o} \) from the porosity and an estimate of formation water resistivity \( (R_{w}) \).
2. Plot \( R_{o} \) as a curve at the same scale as the resistivity curves and compare the values to the value of the deep-resistivity measurement.
3. If desired, an Archie water saturation can be calculated in any zone from the values of \( R_{o} \) and the deep resistivity measurement.

## Patterns to observe

1. In water-bearing zones, \( R_{o} \) and the deep resistivity should overlay.
2. In hydrocarbon-bearing zones, the deep resistivity is higher than \( R_{o} \), with the separation increasing with increasing hydrocarbon saturation.

## Interpretation pitfalls

If the value of $R_w$ chosen to calculate $R_o$ is incorrect, the curves would not align in water-bearing zones.

## Basis for the technique

Recall from chapter 1 that:

$$
R_o = F \times R_w = \frac{a \times R_w}{\phi^m} \tag{7.21}
$$

$R_o$ is then calculated from a porosity measurement, usually the sonic or density, with an estimate of $R_w$, $a$, and $m$. The curve can be generated and displayed during the logging job.

# BULK VOLUME WATER

The product of a formation's water saturation ($S_w$) and its porosity ($\phi$) is the bulk volume of water ($BVW$).

$$
BVW = S_w \times \phi \tag{7.22}
$$

where:

$BVW =$ bulk volume water

$S_w =$ water saturation of uninvaded zone

$\phi =$ porosity

If values for bulk volume water, calculated at several depths in a formation, are constant or very close to

constant, they indicate that the zone is of a single rock type and at irreducible water saturation ($S_{w\,irr}$). When a zone is at irreducible water saturation, water in the uninvaded zone ($S_w$) does not move because it is held on grains by capillary pressure. Therefore, hydrocarbon production from a zone at irreducible water saturation should be water free (Morris and Biggs, 1967).

A formation not at irreducible water saturation ($S_{w\,irr}$) exhibits wide variations in bulk volume water values. The Buckles plot (Buckles, 1965) is a graph of porosity ($\phi$) versus $S_w$. Points of equal $BVW$ form hyperbolic curves across this plot. Figure 7.3 illustrates Buckles plots using data from three wells in the Ordovician Red River B-zone, Beaver Creek Field, North Dakota. If $BVW$ is plotted using data from a formation at irreducible water saturation, the points fall along a single hyperbolic curve (Figure 7.3a). If the data come from reservoirs with higher percentages of produced water, the points are more scattered (Figures 7.3b and 7.3c).

Because the amount of water a formation can hold by capillary pressure increases with decreasing grain size, the bulk volume water also increases with decreasing grain size. Table 7.1 illustrates the relationship of bulk volume water values to decreasing grain size and lithology.

Table 7.1. Bulk volume water ($BVW$) as a function of grain size and lithology. A comparative chart.

|  Lithology | Grain Size (millimeters) | Bulk Volume Water ($BVW$)  |
| --- | --- | --- |
|  *Clastics*  |   |   |
|  Coarse | 1.0 to 0.5 | 0.02 to 0.025  |
|  Medium | 0.5 to 0.25 | 0.025 to 0.035  |
|  Fine | 0.25 to 0.125 | 0.035 to 0.05  |
|  Very Fine | 0.125 to 0.062 | 0.05 to 0.07  |
|  Silt | < 0.062 | 0.07 to 0.09  |
|  *Carbonates*  |   |   |
|  Vuggy |  | 0.005 to 0.015  |
|  Vuggy and intercrystalline (intergranular) |  | 0.015 to 0.025  |
|  Intercrystalline |  | 0.025 to 0.04  |
|  Chalky |  | 0.05  |

The bulk volume water values for carbonates should be used only as a very general guide to different types of porosity.

Log Interpretation

121

# SATURATION CROSSPLOTS

Saturation crossplots, also called resistivity-porosity crossplots (or specifically, Pickett plots and Hingle plots) are similar to the porosity crossplots discussed in Chapter 4. They are x-y plots of log data from which quantities of interest are derived; in this case, that quantity is water saturation ($S_w$). Both the Pickett and Hingle methods are essentially graphical solutions to the Archie saturation equation. They were created before the use of computers to aid log interpretation. These techniques minimize the number of calculations that must be done and aid the comparison of potentially productive zones. With the advent of early (mostly nongraphic) log-interpretation software, their use declined, but this decline was reversed as people realized the power of the techniques to use the ability of the human mind to recognize patterns in data. These techniques are currently regarded as necessary components of full-functioned computer-based log-interpretation systems.

## Pickett Crossplot Method

The Pickett plot (Pickett, 1966, 1973) is one of the simplest and most effective crossplot methods in use. This technique estimates water saturation and can also help determine:

- formation water resistivity ($R_w$)
- cementation factor ($m$)
- matrix parameters for sonic and density logs ($\Delta t_{ma}$ and $\rho_{ma}$)

The Pickett method is based on the observation that true resistivity ($R_t$) is a function of porosity ($\phi$), water saturation ($S_w$), and cementation exponent ($m$). It is actually a graphical solution of Archie's equation in terms of resistivity. Archie's equation (Equation 7.1) is solved for resistivity:

$$R_t = \frac{a \times R_w}{\phi^m \times S_w^n} \tag{7.23}$$

Taking the logarithm of the equation produces:

$$\log(R_t) = \log(a \times R_w) - m \log(\phi) - n \log(S_w) \tag{7.24}$$

If the zone is water-bearing, $S_w = 1$, $\log(S_w) = 0$, and the equation reduces to:

$$\log(R_t) = \log(a \times R_w) - m \log(\phi) \tag{7.25}$$

This form of the equation ($y = b + mx$) indicates that by plotting $R_t$ on the y-axis (on a logarithmic scale) against porosity ($\phi$) on the x-axis (on a logarith-

mic scale), one can determine the product ($a \times R_w$) from intercept of the line (b), and the cementation exponent ($m$) from the slope of the line ($m$). In practice, the resistivity ($R_t$) is usually plotted on the x-axis and the porosity ($\phi$) on the y-axis (Figure 7.4). This convention stems from the availability of full-logarithmic graph paper (both scales logarithmic) at the time Pickett developed the technique. The best format to use (for the best data resolution) is two decades for porosity (0.01 to 1.0, or 1% to 100%) and three decades for the resistivity (0.1 to 100, or 1 to 1000). The only 2-by-3 full-logarithmic paper available was constructed with 2 decades on the y-axis and 3 decades on the x-axis so the plot was modified to fit the paper (G. R. Pickett, personal communication).

Using the convention driven by graph-paper availability, the equation becomes:

$$\log(\phi) = \log(a \times R_w) - \frac{1}{m} \log(R_t) - n \log(S_w) \tag{7.26}$$

Plotting a mixture of water-bearing and hydrocarbon-bearing points on a Pickett plot results in the following attributes (as shown in Figure 7.4):

- Water-bearing points of different porosities plot along a straight line with a slope of (-1/m) and an intercept (at porosity = 1.0) of ($a \times R_w$). From this line, the cementation exponent ($m$) can be determined, and if the tortuosity factor ($a$) is known (or can be estimated), $R_w$ can be predicted. This is the water-bearing, or $R_o$, line.
- Hydrocarbon-bearing points lie away from the line, moved horizontally to the right from the water-bearing line by their increased resistivity. The horizontal distance of a point from the water-bearing line depends on the water saturation ($S_w$) of that point. If the saturation exponent ($n$) is known (or can be estimated), the water saturation can be determined. Lines of constant water saturation lie parallel to the water-bearing line.

The power in the Pickett plot is that water resistivity ($R_w$) and cementation exponent ($m$) can be estimated from the data, rather than having to be derived from local knowledge or from expensive core measurements.

Although porosity is now normally plotted on the Pickett plot, Pickett originally used two other quantities:

($\rho_b - \rho_{ma}$) instead of the density porosity

where:

$\rho_b$ = formation bulk density (from the log)

$\rho_{ma}$ = formation matrix density

122

ASQUITH AND KRYGOWSKI

and:

$(\Delta t - \Delta t_{\mathrm{ma}})$ instead of the sonic porosity where:

$\Delta t =$ formation sonic travel time (from the log)

$\Delta t_{\mathrm{ma}} =$ formation matrix travel time

Both quantities are the numerators in porosity equations $(\rho_{b} - \rho_{ma})$ from the density porosity equation (Chapter 4, Equation 4.7), and $(\Delta t - \Delta t_{ma})$ from the Wyllie time-average sonic equation (Chapter 4, Equation 4.1). The quantities are plotting shortcuts to avoid the calculation of porosity, but they serve another purpose as well. If there is a range of porosities in the zones defining the water-bearing line on the Pickett plot, and if the matrix value is chosen correctly, the line is straight. If the chosen matrix value is either too high or too low, the line is curved. Thus, with a spread of good data in the water-bearing zone, the proper matrix value can be chosen by trial and error by modifying the matrix value until the water-bearing line is straight and not curved.

The water saturation of a point plotting away from the water-bearing line can be determined by the equation:

$$
S _ {w} = \left(\frac {R _ {o}}{R _ {t}}\right) ^ {\frac {1}{n}} \tag {7.27}
$$

In practice, this means reading the resistivity of the point $(R_{t})$ and the resistivity of the water-bearing line $(R_{o})$ at the same porosity value as the point, estimating a value for saturation exponent $(n)$ and making the calculation.

The table below can be used to draw saturation lines on a Pickett plot, as a reference. The technique is:

- At some value of porosity (0.10 is often convenient), note the resistivity value of the \( R_{o} \) line.
- Multiply that resistivity value by the factors below, and plot those values on the Pickett plot at the same porosity.
- Draw the saturation lines parallel to the water-bearing line, with each line going through the calculated points.
- Those parallel lines can be labeled with the value of water saturation shown. Note that the lines are for a saturation exponent \((n)\) of 2.0.

In its fullest use, then, the Pickett plot can be used to determine formation water resistivity $(R_{w})$ , cementation exponent $(m)$ , and formation matrix values $(\rho_{ma}$ or $\Delta t_{ma})$ . As expected, there are assumptions to the interpretation. The prime assumption is that in the zones being compared, all the parameters (matrix value, $a$ , $m$ , $n$ , and $R_{w}$ ) do not change.

Table 7.2. Factors for positioning water-saturation lines on Pickett and Hingle plots.

|  Multiplier | $S_w$ (for $n = 2.0$)  |
| --- | --- |
|  1.56 | 0.80  |
|  2.04 | 0.70  |
|  2.78 | 0.60  |
|  4 | 0.50  |
|  6.25 | 0.40  |
|  11.11 | 0.30  |
|  25 | 0.20  |

## Hingle Crossplot Method

The oldest of the resistivity-porosity crossplot methods that can be used to determine water saturation $(S_{w})$ is the Hingle (1959) plot. As in other crossplot techniques, a significant benefit of Hingle's technique is that a value for water saturation $(S_{w})$ can be determined even if matrix properties $(\rho_{ma}$ or $\Delta t_{ma})$ of a reservoir are unknown. This is also true if a reservoir's water resistivity $(R_{w})$ is unknown.

As with the Pickett plot, the Hingle plot seeks to plot resistivity against porosity. Plotting resistivity against porosity on linear scales produces a family of nonlinear trends. By solving Archie's equation (Equation 7.1) in the following form, the nonlinear trends become straight lines (Bassiouni, 1994):

$$
\left(\frac {a}{R _ {t}}\right) ^ {\frac {1}{m}} = \left(\frac {S _ {w} ^ {n}}{R _ {w}}\right) ^ {\frac {1}{m}} \times \phi \tag {7.28}
$$

While porosity is plotted on a linear scale, the resistivity is plotted on a very nonlinear scale. In practice, the resistivity is plotted on a grid that has been constructed for specific values of tortuosity factor $(a)$ and cementation exponent $(m)$ . The grid constructed using $a = 1.0$ and $m = 2.0$ is usually used for sandstones (Figure 7.5), and the grid constructed using $a = 0.62$ and $m = 2.15$ is used for carbonates (Figure 7.6). Using the constructed grids, resistivity values can be plotted directly on the graph without the need for any calculations.

Plotting a mixture of water-bearing and hydrocarbon-bearing points on a Hingle plot results in the following attributes (as shown in Figure 7.7):

- Water-bearing points of different porosities plot along a straight line. The $x$ -intercept of the line (where conductivity is zero and resistivity is infinite) occurs at the point where porosity is

Log Interpretation

123

zero. If the bulk density or acoustic travel time of the formation, instead of the porosity, is plotted along the x-axis, the x-intercept predicts the matrix value (matrix density or matrix travel time) of the formation. The line extends to the northeast quadrant (i.e., upper right) from its x-intercept.

- Hydrocarbon-bearing points lie below the line of 100% water saturation, moved downward from the water-bearing line by their increased resistivity. The vertical distance from a point to the water-bearing line depends on the water saturation ($S_w$) of that point. If the saturation exponent ($n$) is known (or can be estimated), the water saturation can be determined. Lines of decreasing water saturation radiate from the x-axis intercept and spread like a fan toward the right side of the chart.

As with the Pickett plot, the Hingle plot allows the interpreter to predict some of the parameters from the logs rather than estimating them by other methods. The formation water resistivity ($R_w$) can be estimated by choosing any point along the water-bearing line. The point's resistivity ($R_o$) and porosity can be read from the plot, and values of tortuosity factor ($a$) and cementation exponent ($m$) are assumed based on the chart that is chosen. Formation water resistivity is then:

$$R_w = \frac{R_o \times \phi^m}{a} \tag{7.29}$$

By plotting the bulk density ($\rho_b$) or sonic travel time ($\Delta t$) values on the x-axis, rather than the porosity, the matrix density or matrix travel time ($\rho_{ma}$ or $\Delta t_{ma}$) can be estimated. If there is a sufficient range of porosities used to determine the water-bearing line, the line can be extrapolated to the zero-conductivity value (the bottom of the chart). The value of this intercept is the matrix value for the porosity equation. On Figure 7.5 or Figure 7.6, the placement of the zero porosity point is arbitrary. If porosity is plotted on the x-axis, setting the zero porosity point at the left side of the plot makes the most sense. If $\rho_b$ or $\Delta t$ is used, the anticipated zero porosity point (the anticipated matrix value) could be displaced from the lower left corner if the matrix value is different than the expected matrix value. Regardless of the values used on the x-axis (porosity, $\rho_b$, or $\Delta t$), the values increase from left to right.

The water saturation of a point plotting away from the water-bearing line can be determined by Equation 7.26. In practice, this means reading the resistivity of the point ($R_t$) and the resistivity of the water-bearing line ($R_o$) at the same porosity value as the point, esti-

mating a value for saturation exponent ($n$), and making the calculation.

Table 7.2, previously used for the Pickett plot, can be used to draw saturation lines on a Hingle plot. The technique is:

- At some value of porosity (0.10 is often convenient), note the resistivity value of the $R_o$ line.
- Multiply that resistivity value by the factors in Table 7.2, and plot those values on the Hingle plot at the same porosity.
- Draw the saturation lines to intersect the water-bearing line at the zero porosity point on the x-axis, with each line going through the calculated points.
- Those lines can be labeled with the value of water saturation shown. Note that the lines are for a saturation exponent ($n$) of 2.0.

In routine analyses, many people favor one of the crossplots over the other, as a matter of personal preference or experience. Bassiouni (1994), however, describes an iterative technique using both plots to refine the estimates of the matrix values and cementation exponents in areas where both are unknown. Table 7.3 lists advantages and limitations of both plots.

### PERMEABILITY FROM LOGS

Log-derived permeability formulas are only valid for estimating permeability in formations at irreducible water saturation (Schlumberger, 1977). When a geologist evaluates a formation by using log-derived permeability formulas, the permeability values, if possible, should be compared with values of nearby producing wells from the same formation. Productivity estimates can be based on log-derived permeabilities if the formation evaluated is compared with both good and poor production histories in these nearby wells. By using comparisons of log-derived permeabilities from several wells, a geologist is not using an absolute value for log-derived permeability.

Four methods for calculating log-derived permeability are discussed here. Before these formulas can be applied, a geologist must first determine whether or not a formation is at irreducible water saturation. Whether or not a formation is at irreducible water saturation depends upon bulk volume water values ($BVW = S_w \times \phi$). When the bulk volume water values of a formation are constant (Figure 7.3a), the zone is at irreducible water saturation. If the values are not constant, a zone is not at irreducible water saturation (Figures 7.3b and 7.3c), and the estimates of permeability are suspect.

124

ASQUITH AND KRYGOWSKI

Table 7.3. Advantages and Limitations of Pickett and Hingle plots (after Bassiouni, 1994).

|   | Pickett plots | Hingle plots  |
| --- | --- | --- |
|  Advantages | Water saturation can be predicted without prior knowledge of $R_w$, $a$, or $m$. $R_w$ is directly predicted (if tortuosity factor ($a$) is known or estimated) from the intercept of the water-bearing line at a porosity of 1 ($\phi = 100\%$). Cementation exponent ($m$) is directly predicted from the slope of the water-bearing line. When using the plot by hand, the graph paper to be used (full logarithmic) is readily available. | Water saturation can be predicted without prior knowledge of $R_w$, $\rho_{ma}$ or $\Delta t_{ma}$, $\rho_{ma}$ or $\Delta t_{ma}$ can be directly predicted from the intercept of the water-bearing line at a conductivity of zero (a resistivity of infinity).  |
|  Limitations | Values for $\rho_{ma}$ and $\Delta t_{ma}$ must be assumed (although in cases with a wide range of porosities in the water-bearing zone, the matrix values can be estimated from the water-bearing line). | Values for tortuosity factor ($a$) and cementation exponent ($m$) must be assumed. To use the plot, the resistivity parameter has to be calculated or a special graph paper used.  |
|  Limitations for both techniques | A wide range of porosity must be present to positively determine a water-bearing line. Formation lithology and water resistivity must be constant over the intervals compared in the plot.  |   |

Table 7.4. Data for use with Pickett plot (Figure 7.4) and Hingle plot (Figure 7.7). Morrow Sandstone, Cimarron County, Oklahoma.

|  Zone number | Depth (ft) | $\rho_b$ (g/cm³) | $\phi_D$ (decimal) | $R_t$ (ohm-m)  |
| --- | --- | --- | --- | --- |
|  1 | 4400 | 2.38 | 0.163 | 1.7  |
|  2 | 4402 | 2.44 | 0.127 | 2.1  |
|  3 | 4410 | 2.35 | 0.181 | 1.3  |
|  4 | 4414 | 2.42 | 0.139 | 1.6  |
|  5 | 4426 | 2.42 | 0.139 | 1.8  |
|  6 | 4430 | 2.33 | 0.194 | 1.0  |
|  7 | 4438 | 2.30 | 0.212 | 0.9  |
|  8 | 4536 | 2.30 | 0.212 | 40  |
|  9 | 4540 | 2.30 | 0.212 | 45  |
|  10 | 4546 | 2.30 | 0.212 | 40  |

## Wyllie and Rose (1950)

This method for determining permeability utilizes a chart (Figure 7.8) or the two forms of the following formula:

$$
K = \left( 250 \times \frac{\phi^3}{S_{w\,irr}} \right)^2 \quad \text{(medium-gravity oils)} \tag{7.30}
$$

$$
K = \left( 79 \times \frac{\phi^3}{S_{w\,irr}} \right)^2 \quad \text{dry gas} \tag{7.31}
$$

where:

$K =$ permeability in millidarcys

$\phi =$ porosity

$S_{w\,irr} =$ water saturation ($S_w$) of a zone at irreducible water saturation

## Timur (1968)

$$
K = \left( \frac{93 \times \phi^{2.2}}{S_{w\,irr}} \right)^2 \tag{7.32}
$$

## Coates and Dumanoir (1973)

A more complex method for calculating permeability is the Coates and Dumanoir (1973) formula. Unlike the Wyllie and Rose (1950) formulas, hydrocarbon density is explicitly part of the equation, instead of being indirectly accounted for by changing a constant. The following data are required to calculate permeability by the Coates and Dumanoir formula.

$R_w =$ formation water resistivity at formation temperature

$R_{t\,irr} =$ true formation resistivity from a formation at irreducible water saturation

Log Interpretation

125

$\rho_{h} =$ hydrocarbon density in $\mathrm{g / cm^3}$

$\phi =$ porosity

A first step in the Coates and Dumanoir permeability formula is calculation of values for two constants: $C$ and $W$.

$$
C = 23 + 465 \times \rho_{h} - 188 \times \rho_{h}^{2} \tag{7.33}
$$

where:

$C =$ constant in Coates and Dumanoir permeability formula

$\rho_{h} =$ hydrocarbon density in $\mathrm{g / cm^3}$

$$
W = \left\{(3.75 - \phi) + \left[ \frac{(\log(R_{w} / R_{\mathrm{irr}}) + 2.2)^{2}}{2.0} \right] \right\}^{\frac{1}{2}} \tag{7.34}
$$

where:

$W =$ constant in Coates and Dumanoir permeability formula

$\phi =$ porosity

$R_{w} =$ formation water resistivity at formation temperature

$R_{\mathrm{irr}} =$ deep resistivity from a zone at irreducible water saturation ($S_{w\mathrm{irr}}$)

Once determined, the constants $C$ and $W$ can be used to calculate permeability.

$$
K = \left[ \frac{C \times \phi^{2W}}{W^{4} \times (R_{w} / R_{\mathrm{irr}})} \right]^{2} \tag{7.35}
$$

where:

$K =$ permeability in millidarcys (md)

$C =$ constant based on hydrocarbon density

$W =$ constant

$\phi =$ porosity

$R_{\mathrm{irr}} =$ deep resistivity from a zone at irreducible water saturation ($S_{w\mathrm{irr}}$)

$R_{w} =$ formation water resistivity at formation temperature

## SHALY SAND ANALYSIS

Not long after the work of Archie and others in devising a method to quantify water saturation from logs, it became clear that there were limitations to the method, especially in formations containing shale and/or clay and commonly referred to as *shaly sands*. The early literature tended to refer to the formations as containing *shale*, and a number of modifications were made to Archie’s equation using shale volume (among

other parameters) to account for those effects. As our understanding of geological processes matured, it became understood that *shale* and *clay* are different and that shaly sands are usually not just sands with shales mixed in but sands that contain clays. These clays could be very different from the clays present in the shales near those sands of interest. Again, the literature and our interpretive techniques commonly use the terms *shale volume* and *clay volume* interchangeably. Most of the shaly sand techniques developed over the years concern themselves with shale volume, but a few, notably the Waxman-Smits and dual water methods, seek to use the electrical properties of the clays in the formations to predict an accurate water saturation.

Beginning in the late 1960s, the work of Waxman and Smits (1968) and Waxman and Thomas (1974) helped to better understand the physical causes of the responses of logging measurements to shaly sands and to develop interpretive models to better approximate the physical reality of formations. Clavier et al. (1977) built on the work of Waxman and his colleagues with the introduction of the dual water model for the determination of water saturation. The dual water model postulates two different types of water in a shaly formation, a immovable water layer next to the clay surfaces (bound water) and movable water that can be displaced by hydrocarbons (free water). This technique, while more complex in its use, continues to gain popularity because of its closer approximation to the responses of shaly sands in a wide variety of conditions.

The presence of shale or clay minerals in a reservoir can cause erroneous values for water saturation and porosity derived from logs. These erroneous values are not limited to sandstones but also occur in limestones and dolomites.

Essentially all measurements, then, are affected in some way by the presence of clays and/or shales. Hilchie (1978) notes that the most significant effect of shale in a formation is to reduce the resistivity contrast between oil or gas, and water. The net result is that if enough shale is present in a reservoir, it may be very difficult, or perhaps impossible, to determine if a zone is productive. Hilchie (1978) suggests that for shale to significantly affect log-derived water saturations, shale content must be greater than 10 to \(15\%\).

Remember that all shaly sandstone formulas reduce the water saturation value from the value that would be calculated if shale effect were ignored. However, this lowering of water saturation can be a problem in log evaluation, because, if a geologist overestimates shale content, a water-bearing zone might appear to be a hydrocarbon-bearing zone.

126

ASQUITH AND KRYGOWSKI

Table 7.5. Effects of days and shales on logging measurements.

|  Measurement | Effect  |
| --- | --- |
|  Spontaneous potential, SP | SP is decreased in magnitude with respect to the shale baseline.  |
|  Gamma ray | Increased radioactivity is apparent as less movement away from the nearby shale values than an equivalent clean sand.  |
|  Sonic | Sonic porosity is higher than the actual formation porosity due to the higher travel time of the clays/shales.  |
|  Neutron | Neutron porosity is higher than the actual formation porosity due to the water that is part of the clay structure and is adsorbed on the clay surfaces.  |
|  Density | Density porosity is higher than the actual formation porosity due to the generally lower matrix densities of most clay minerals. If the matrix density of the clay is close to that of the formation matrix, there is little or no effect on porosity.  |
|  Resistivity | Resistivity is less than that in an equivalent clean formation due to the conductivity of the clay. This produces a calculated water saturation greater than the actual formation water saturation. (Archie's equation assumes that all conductivity is from the formation water and that the formation matrix is completely nonconducting.)  |

## Determining Shale/Clay Volume

The first step in shaly sand analysis is to determine the volume of shale. There are several techniques available, the most common being those from the SP, gamma ray, and neutron-density crossplot. Perhaps the most widely used log is the gamma ray, in part because there are several (empirical) relationships between the response of the measurement and shale or clay volume (Chapter 3).

Once shale volume, $V_{shale}$, is determined, the available porosity logs can be corrected for shale effects:

Sonic log (Dresser Atlas, 1979):

$$
\phi_{Se} = \left( \frac{\Delta t_{log} - \Delta t_{ma}}{\Delta t_{fl} - \Delta t_{ma}} \times \frac{100}{\Delta t_{sh}} \right) - V_{shale} \left( \frac{\Delta t_{sh} - \Delta t_{ma}}{\Delta t_{fl} - \Delta t_{ma}} \right) \tag{7.36}
$$

or (from Dewan, 1983):

$$
\phi_{Se} = \phi_S - V_{shale} \times \phi_{Ssh} \tag{7.37}
$$

where:

$\phi_{Se} =$ effective (shale-corrected) sonic porosity

$\phi_S =$ sonic porosity

$\phi_{Ssh} =$ sonic porosity in a nearby shale

$V_{shale} =$ shale volume

$\Delta t_{log} =$ interval transit time of the formation (from the sonic log)

$\Delta t_{ma} =$ matrix interval transit time

$\Delta t_{fl} =$ fluid interval transit time

$\Delta t_{sh} =$ interval transit time in a nearby shale

The neutron and density logs (Schlumberger, 1975):

$$
\phi_{Ne} = \phi_N - \left[ \left( \frac{\phi_{Nshale}}{0.45} \right) \times 0.03 \times V_{shale} \right] \tag{7.38}
$$

$$
\phi_{De} = \phi_D - \left[ \left( \frac{\phi_{Nshale}}{0.45} \right) \times 0.13 \times V_{shale} \right] \tag{7.39}
$$

or, from Dewan (1983):

$$
\phi_{Ne} = \phi_N - V_{shale} \times \phi_{Nsh} \tag{7.40}
$$

$$
\phi_{De} = \phi_D - V_{shale} \times \phi_{Dsh} \tag{7.41}
$$

and, using either of the single porosity measurement pairs above:

$$
\phi_{ND} = \sqrt{ \frac{ \phi_{Ne}^2 + \phi_{De}^2 }{ 2 } } \tag{7.42}
$$

where:

$\phi_{ND} =$ neutron-density shale-corrected porosity

$\phi_N =$ neutron porosity

$\phi_{Ne} =$ shale-corrected neutron porosity

$\phi_D =$ density porosity

$\phi_{De} =$ shale-corrected density porosity

$\phi_{Nsh} =$ neutron porosity of a nearby shale

Log Interpretation

127

$\phi_{Dsh} =$ density porosity of a nearby shale

$V_{shale} =$ shale volume

## Determining Water Saturation

After the shale-corrected porosity has been determined, the water saturation can be calculated. A variety of techniques are briefly introduced below, but the methodology for their use is beyond the scope of this book and is not detailed. The reader is referred to Asquith (1991), Bassiouni (1994), or Dewan (1983) for details of usage of the individual techniques.

A technique popular in the 1950s was the automatic compensation technique (Dewan, 1983). It used the resistivity and sonic logs with Archie's equation. Since the presence of shale caused the porosity $(\phi_S)$ to read too high and the resistivity $(R_t)$ to read too low, one compensated for the other in the saturation equation:

$$
S_w = 0.9 \frac{\sqrt{R_w / R_t}}{\phi_S} \tag{7.43}
$$

In the 1960s, with the advent of the density log, the dispersed-clay model gained popularity (Dewan, 1983). In this model, the density was assumed to respond only to the liquid-filled porosity, while the sonic was affected by the clays with the difference $(q)$ being the fraction of the intergranular space filled with clay:

$$
q = \frac{\phi_S - \phi_D}{\phi_S} \tag{7.44}
$$

and the saturation given by:

$$
S_w = \frac{\left[ \sqrt{\frac{0.8 \times R_w}{\phi_S^2 \times R_t} + \left(\frac{q}{2}\right)^2} - \frac{q}{2} \right]}{(1 - q)} \tag{7.45}
$$

A number of $V_{shale}$-based methods became popular in the late 1960s and 1970s, and many of these are still being used. These include:

Fertl, 1975:

$$
S_w = \frac{1}{\phi} \times \left[ \sqrt{\frac{R_w}{R_t} + \left(\frac{a \times V_{shale}}{2}\right)^2} - \frac{a \times V_{shale}}{2} \right] \tag{7.46}
$$

where:

$a = 0.25$ in the Gulf Coast and $a = 0.35$ in the Rocky Mountains.

Schlumberger, 1975:

$$
S_w = \frac{\sqrt{\left(\frac{V_{shale}}{R_{sh}}\right)^2 + \frac{\phi^2}{0.2 \times R_w \times R_t \times (1 - V_{shale})} - \frac{V_{shale}}{R_{sh}}}}{\frac{\phi^2}{0.4 \times R_w \times (1 - V_{shale})}} \tag{7.47}
$$

Simandoux, 1963:

$$
S_w = \left(\frac{0.4 \times R_w}{\phi^2}\right) \times \left[ \sqrt{\left(\frac{V_{shale}}{R_{sh}}\right)^2 + \frac{5 \times \phi^2}{R_t \times R_w}} - \frac{V_{shale}}{R_{sh}} \right] \tag{7.48}
$$

The dual water method is perhaps the most widely used of the techniques that go beyond the shale-volume methods. This method is more fully described in Dewan (1983) and Bassiouni (1994). It faces the reality that there is no way to measure cation-exchange capacity (CEC) directly from logs and that CEC measurements on cores are rare, so $V_{shale}$ methods are used to correct porosity for clay content and to calculate the bound-water saturation $(S_{wb})$. The bound-water and free-water resistivities are determined from nearby shales and clean sands, and the apparent water resistivity $(R_{wa})$ in the sand of interest is calculated.

The total (shale-corrected) water saturation of the formation is:

$$
S_{wt} = b + \sqrt{b^2 + \frac{R_w}{R_{wa}}} \tag{7.49}
$$

where:

$$
b = \frac{S_{wb}(1 - (R_w / R_b))}{2} \tag{7.50}
$$

The effective water saturation of the formation is:

$$
S_{we} = \frac{S_{wt} - S_{wb}}{1 - S_{wb}} \tag{7.51}
$$

and the volumetric fraction of hydrocarbons is:

$$
\phi_h = \phi_t (1 - S_{wt}) \tag{7.52}
$$

where $\phi_t =$ total porosity (from the neutron and density).

A major problem encountered in shaly sand analysis is determining a resistivity value for shale/clay in a formation. The percentage of shale is not the critical factor, rather it is clay's cation-exchange capacity (Hilchie, 1978) because cation-exchange capacity greatly affects resistivity of the clay. Kaolinite and

128

ASQUITH AND KRYGOWSKI

chlorite have extremely low cation-exchange values; illite and montmorillonite have high cation-exchange values. Therefore, montmorillonite and illite decrease resistivity much more than kaolinite and chlorite. In shaly sand analysis, a geologist must make an assumption that resistivity of an adjacent shale ($R_{sh}$) is the same as resistivity of shale in the formation. This assumption is not always correct.

Most shaly sand interpretation problems occur in formations with $R_w$ values that are not too salty [NaCl < 20,000 ppm or $R_w > 0.3$ ohm-m at 80°F (Hilchie, 1978)]. Where formation water is very salty, shale has less effect on the formation's resistivity. Therefore, calculated water saturations without correction for shale are close to true formation water saturation.

This chapter discussed several log-interpretation techniques. These techniques are based on many of the formulas already presented in the text. What the formulas are, and where they are found is summarized on the log-interpretation flow chart included at the end of this chapter (Figure 7.2).

# REVIEW

1. The Archie equation is used to calculate a formation's water saturation in both the invaded ($S_{xo}$) and uninvaded ($S_w$) zones.

2. The ratio method for determining water saturation \((S_{w})\) does not require a value for porosity \((\phi)\)
3. The ratio between the water saturations in the invaded \((S_{xo})\) and uninvaded \((S_w)\) zones (i.e., \(S_{w} / S_{xo}\)) can be used as an index for the degree of hydrocarbon moveability.
4. Bulk volume water (BVW) is important because it indicates when a reservoir is at irreducible water saturation \((S_{w}\) irr).
5. Quick-look methods are important because they provide flags that indicate zones of potential interest.
6. Hingle and Pickett crossplot techniques are simple and rapid methods for determining a formation's:

water saturation \((S_w)\)
water resistivity \((R_{w})\)
- cementation factor \((m)\)
- matrix values (travel time or density)

7. Log-derived data can be used to estimate permeability of a formation, but only if the formation is at irreducible water saturation.
8. The flow charts included in this chapter (Figures 7.1 and 7.2) will help you review the steps used in log interpretation and will also provide an index of where different pieces of information are located.

Log Interpretation

129

![img-0.jpeg](img-0.jpeg)

Figure 7.1. Flowchart for scanning logs to identify zones of interest (both pay and wet). The scanning flowchart has two paths, one for clastics and one for carbonates.

# Clastics:

The resistivity log is the primary reconnaissance measurement because clastics tend to consist of reservoirs surrounded by shales whose resistivities vary gradually with depth. Differences in the fluid content of the reservoirs tend to produce reservoir resistivities that stand out against the relatively constant resistivity of the surrounding shales.

# Carbonates:

Formation resistivities tend to vary widely with changing rock types, and commonly there are few shales against which to measure changes. In this case, the porosity log is the primary reconnaissance measurement. By first finding the porous zones, the zones with the capacity to hold fluids (of any type) can be identified.

Using this scanning technique in combination with the neutron-density quick-look technique discussed in Chapter 4 (if those logs are available) allows one to identify lithology (and sometimes fluid type) in the course of identifying the zones of interest.

1 Zones that appear to be shales might be radioactive productive zones.
2 Shaly zones might produce oil or gas even if they have low resistivity.

![img-1.jpeg](img-1.jpeg)

Figure 7.2. Flowchart for interpretation.

The sources of raw data, both well logs and other well-bore information, are shown in the left column. In many cases, the information generated from that raw data (shown in the center column) is used in computations to produce the quantities of interest (shown in the right column).

The chart shows that there are several ways to calculate porosity ($\phi$) and shale volume ($V_{\mathrm{shale}}$) from the raw data.

The chapters that explain the calculations are listed in the flowchart.

130

ASQUITH AND KRYGOWSKI

![img-2.jpeg](img-2.jpeg)

![img-3.jpeg](img-3.jpeg)

![img-4.jpeg](img-4.jpeg)

Figure 7.3. Buckles plots (porosity vs. water saturation).

Because production of water in a well can affect a prospect's economics, it is important to know the bulk volume water and whether the formation is at irreducible water saturation ($S_{W\text{it}}$).

These Buckles plots are taken from the Ordovician Red River B-zone, Beaver Creek Field, Golden Valley County, North Dakota (after Jaafar, 1980).

With $S_{W}$ and porosity plotted on linear scales, points of equal bulk volume water (BVW) plot as hyperbolic curves. A series of points plotting along a particular hyperbolic curve indicates that the bulk volume water is constant and that the formation is close to irreducible water saturation. A reservoir in that condition would not produce water. As the amount of formation water increases, the bulk volume water values become scattered from the hyperbolic curves and the formation has more water than it can hold by capillary pressure. The water saturation is no longer at, or near, irreducible, so more water is produced relative to oil.

Figure 7.3a is an example of nearly constant BVW. The formation shown produces 96% oil. Note that all the points plot between 0.04 and 0.05 BVW. The formation is very close to, or at, irreducible water saturation.

Figure 7.3b shows a well producing 68% oil. About half the points cluster around a BVW value of 0.04, but the other half have higher values of BVW, indicating moveable water.

Figure 7.3c shows a well producing no oil (all water). Note the scatter of BVW values from the hyperbolic curves, indicating that the formation is not at irreducible water saturation.

Log Interpretation

131

![img-5.jpeg](img-5.jpeg)

Figure 7.4. Pickett plot (saturation crossplot or resistivity-porosity crossplot) illustrating water-bearing and hydrocarbon-bearing zones in a well.

Data are from the Morrow Sandstone, Cimarron County, Oklahoma (Table 7.4).

Density porosity was calculated assuming a matrix density of $2.65\mathrm{g/cm^3}$ and a fluid density of $1.0\mathrm{g/cm^3}$. The water-bearing line ($S_w = 100\%$) was drawn through the cluster of points with a slope of $-1/2$ ($m = 2$). (Because of the limited porosity range of the points and their scatter, other values of $m$ from 1.8 to 2.15 could be justified.)

The intercept of the water-bearing line at $100\%$ porosity ($\mathrm{DPHI} = 1.0$) is $a \times R_{w}$. If the intercept were not off the plot in this illustration, the value could be read directly from the plot. In cases such as this, the value for $a \times R_{w}$ can be determined from $R_{a}$ by using Equation 7.28.

$$
R _ {w} = \frac {R _ {o} \times \phi^ {m}}{a}
$$

Remember that $R_{a}$ is the resistivity in the undisturbed, water-bearing zone, and for all points on the water-bearing line $R_{f} = R_{a}$.

Procedure to calculate $R_{w}$:

For some porosity value, read the value of $R_{a}$ from the water-bearing line on the crossplot. In this case, for a porosity of $10\%$ ($\mathrm{DPHI} = 0.10$), $R_{a} = 4.6$ ohm-m.

Assume a value of tortuosity factor ($a$). In this case, $a = 1.0$.

The value of cementation exponent ($m$) is determined from the crossplot. In this case, $m = 2.0$.

By substitution in the above equation,

$$
R _ {w} = \frac {4 . 6 \times 0 . 1 0 ^ {2 . 0}}{1 . 0}
$$

$R_{w} = 0.046$ ohm-m at formation temperature

The water saturation lines are constructed on the plot from the value for $R_{a}$ and the multipliers from Table 7.2. The multipliers are for a saturation exponent ($n$) of 2.0. For each line to be plotted, multiply $R_{a}$ by the multiplier to get the $y$-intercept and draw a line from the $y$-intercept parallel to the water-bearing line. To plot the line for $50\%$ water saturation, for example, if $R_{a}$ (at $\mathrm{DPHI} = 0.10$) is 4.6 and the multiplier (from Table 7.2) is 4, the $y$-intercept for the $50\%$ water saturation line (at $\mathrm{DPHI} = 0.10$) is 18.4.

To determine the water saturation of the anomalous points (with more accuracy than estimating the values from the crossplot), the following equation can be used:

$$
S _ {w} = \left(\frac {R _ {o}}{R _ {f}}\right) ^ {\frac {1}{n}}
$$

In this case, the value for $R_{a}$ is the value at the water-bearing line at the same porosity as the point of interest. For the two points of interest (both having the same porosity), $R_{a} = 0.80$ ohm-m. For the point who's resistivity is 40 ohm-m, the saturation is found by:

$$
S _ {w} = \left(\frac {0 . 8}{4 0}\right) ^ {\frac {1}{2 . 0}}
$$

$$
S _ {w} = 0. 1 4
$$

For comparison interpretation, Figure 7.7 is a Hingle plot with the same data shown.

132

ASQUITH AND KRYGOWSKI

![img-6.jpeg](img-6.jpeg)

Figure 7.5. Hingle plot (saturation crossplot or resistivity-porosity crossplot) generally used for sandstones. (Western Atlas International, Inc., 1995, Chart 7-79)
The y-axis is constructed with tortuosity factor (a) = 1.0 and cementation exponent (m) = 2.0.

Log Interpretation

133

![img-7.jpeg](img-7.jpeg)

Figure 7.6. Hingle plot (saturation crossplot or resistivity-porosity crossplot) generally used for carbonates. (Western Atlas International, Inc., 1995, Chart 7-80) The y-axis is constructed with tortuosity factor $(a) = 0.62$ and cementation exponent $(m) = 2.15$

134

ASQUITH AND KRYGOWSKI

Figure 7.7. Hingle plot (saturation crossplot or resistivity-porosity crossplot) illustrating water-bearing and hydrocarbon-bearing zones in a well. Data are from the Morrow Sandstone, Cimarron County, Oklahoma (Table 7.4).

The Hingle grid using $a = 1.0$ and $m = 2.0$ was chosen as the common parameters for sandstones.

The $x$-axis has been scaled in bulk density, and the points plotted accordingly. The water-bearing line drawn through the cluster of points intersects the $x$-axis at $2.65\mathrm{g/cm^3}$, the matrix-density value for the formation. (Given the limited porosity range and the scatter of those points, other values for matrix density could also be justified.)

$R_{u}$ is determined using Equation 7.28:

$$
R_{u} = \frac{R_{u} \times \phi^{m}}{a}
$$

For some porosity value, read the value of $R_{0}$ from the water-bearing line on the crossplot. In this case, for a porosity of $10\%$ (bulk density $= 2.485$ $\mathrm{g/cm^3}$), $R_{0} = 4.1$ ohm-m.

The values of tortuosity factor $(a)$ and cementation exponent $(m)$ were assumed by choice of the particular crossplot grid.

By substitution in the above equation,

$$
R_{u} = \frac{4.1 \times 0.10^{2n}}{1.0}
$$

$R_{u} = 0.041$ ohm-m at formation temperature

The water saturation lines are constructed on the plot from the value for $R_{0}$ and the multipliers from Table 7.2. The multipliers are for a saturation exponent $(n)$ of 2.0.

![img-8.jpeg](img-8.jpeg)

For each line to be plotted, multiply $R_{0}$ by the multiplier and plot that line so that it intersects the water-bearing line at infinite resistivity. In this example, $R_{0}$ (at bulk density $= 2.485$ $\mathrm{g/cm^3}$) is 4.1. The intercept for the $50\%$ water-saturation line (at bulk density $= 2.485$ $\mathrm{g/cm^3}$) is 16.4.

To determine the water saturation of the anomalous points (with more accuracy than estimating the values from the crossplot), the following equation can be used:

$$
S_{w} = \left(\frac{R_{w}}{R_{s}}\right)^{\frac{1}{2}}
$$

In this case, the value for $R_{0}$ is the value at the water-bearing line at the same porosity as the point of interest. For the two points of interest (both having the same porosity), $R_{0} = 0.83$ ohm-m. For the point who's resistivity is 40 ohm-m, the saturation is found by:

$$
S_{w} = \left(\frac{0.83}{40}\right)^{\frac{1}{2n}}
$$

$$
S_{w} = 0.144
$$

For comparison of interpretation, Figure 7.4 is a Pickett plot with the same data shown.

Log Interpretation

135

![img-9.jpeg](img-9.jpeg)

Figure 7.8. Chart of porosity ($\phi$) versus irreducible water saturation ($S_{W\,W}$) for estimating permeability and determining bulk volume water. (Schlumberger, 1998, Chart K-3)

Given: Porosity ($\phi$) = 0.25 (= 25 porosity units, p.u.) and irreducible water saturation ($S_{W\,W}$) = 40% for an oil-bearing sandstone. The chart is constructed with the assumption of a medium-gravity oil.

Procedure:

1. Find porosity ($\phi$ = 25 p.u.) on the bottom horizontal scale, and find irreducible water saturation ($S_{W\,W}$ = 40%) on the left vertical scale.

Note that irreducible water saturation is labeled $S_{WI}$ on this chart.

Follow the two values into the chart to the point where they intersect.

2. The heavy curve on which this point falls represents permeability. In this case, permeability, $K$ = 130 md.

3. The light hyperbolic curves ($C = S_{W\,W} \times \phi$) represent lines of equal value for bulk volume water. In this example, the bulk volume water equals 0.10 ($BVW$ = 0.10).

Note: It is important to remember that this chart is only valid for estimating permeability ($K$) in zones at irreducible water saturation ($S_{W\,W}$).

Zones at irreducible water saturation have bulk volume water values that are fairly constant. On the chart, data points from different intervals in a zone at irreducible saturation plot in a coherent pattern, on or parallel to one of the hyperbolic curves. Data points from zones not at $S_{W\,W}$ scatter from this pattern.

8

Asquith, G., and D. Krygowski, 2004, Petrophysical Techniques, in G. Asquith and D. Krygowski, Basic Well Log Analysis: AAPG Methods in Exploration 16, p. 137-149.

# Petrophysical Techniques

## GENERAL

Petrophysical techniques provide most of the subsurface data available to an exploration geologist. Besides their importance in completion decisions, they are also invaluable methods for mapping and identifying lithologies. Presented here are nine techniques that can assist geologists with lithologic determination and mapping. They are:

- Neutron-density lithology plot
- Neutron-sonic lithology plot
Density-sonic lithology plot
- \(M - N\) lithology plot
- Matrix identification plot \((\rho_{\text{maa}}\) vs. \(\Delta t_{\text{maa}})\)
- Matrix identification plot \((\rho_{\text{maa}}\) vs. \(U_{\text{maa}})\)
Alpha mapping from the SP log
- Clean sand or carbonate from gamma ray log
- Rock typing and facies mapping.

These techniques are especially important to a geologist when lithologic data from core or samples are unavailable.

Figures 8.1 and 8.2 are logs through the Silurian Fusselman Formation in West Texas. The log suite for this well consists of a dual induction-SFL, SP, gamma ray, and neutron-lithodensity log (Figure 8.1), and a sonic log with gamma ray (Figure 8.2). Using data from these logs, we will illustrate how lithologies are determined using the first six methods listed above. It is important to mention that the porosity zone (9088 to 9126 ft) in the Fusselman has a combination of vuggy and intercrystalline porosity. How the presence of vuggy porosity affects the different lithology plots will be discussed in the text below. The software used to generate the results from the original log data is called CBA (Carbonate Advisor; The Logic Group, 1994). The various lithology plots and crossplots were rendered in PetroWorks, from Landmark Graphics, a Halliburton company.

## NEUTRON-DENSITY LITHOLOGY PLOT

The gamma ray log (Chapter 3) measures the natural radiation of a formation and primarily functions as a lithology log. It helps differentiate shales (high radioactivity) from sands, carbonates, and anhydrites (low radioactivity). The neutron log is a porosity device that is used to measure the amount of hydrogen in a formation, which is assumed to be related to porosity (Chapter 4). The density log is a porosity device that measures electron density, and from that, formation bulk density (Chapter 4). When these three logs are used together, lithologies can be determined. Figure 4.8 is a schematic illustration of how responses from the gamma ray, neutron, and density logs are related to lithology.

Figure 8.3 is a neutron-density lithology plot of the data from the Fusselman Formation (Figures 8.1 and 8.2). On the lithology plot (Figure 8.3), the Fusselman data cluster between the lithology lines of dolomite and limestone. The amounts of each lithology are illustrated in the column next to the lithology plot. As a quick-look method, where there are a limited number of lithologies, this plot works well for basic lithologic and facies mapping. The problem is how the geologist determines if the Fusselman is a mixture of dolomite and limestone or a mixture of dolomite and sandstone.

## NEUTRON-SONIC LITHOLOGY PLOT

The sonic log is a porosity device (Chapter 3) that measures the speed of a compressional sound wave through the formation. Figure 8.4 is neutron-sonic plot for the Fusselman Formation. The Fusselman data from the porous zone (9088 to 9126 ft) cluster along the dolomite lithology line, and the data from the nonporous zone above 9088 ft cluster along the limestone lithology line (Figure 8.4). The amounts of each lithology are illustrated in the column next to the lithology

137

138

ASQUITH AND KRYGOWSKI

plot. A comparison of Figures 8.3 and 8.4 reveals that the neutron-sonic plot indicates a much more dolomitic lithology compared to the neutron-density plot. This difference is due to the presence of vuggy porosity from 9088 to 9126 ft. Remember that the sonic log measures only matrix porosity (intergranular and intercrystalline) and the nuclear logs (neutron and density) measure total porosity. Therefore, when vuggy porosity is present sonic porosity is less than total (neutron-density) porosity and the data cluster lower on the neutron-sonic plot (i.e., more dolomitic; Figure 8.4).

## DENSITY-SONIC LITHOLOGY PLOT

Figure 8.5 is a density-sonic plot of the Fusselman interval illustrated in Figures 8.1 and 8.2. The calculated lithologies are displayed in the column next to the lithology plot. The density-sonic plot is the least desirable of the lithology plots because the lines representing the different lithologies (i.e., sandstone, limestone, and dolomite) are much closer together. Therefore, it is harder to differentiate the different lithologies. An examination of the lithology for the vuggy zone (9088 to 9126 ft) reveals that the lithology is now limestone (Figure 8.5). The presence of the vuggy porosity causes the sonic log to underestimate porosity, which shifts the data to the left of the plot so that the lithology appears to be limestone. It is important to remember that all lithology plots that require a sonic log may be unreliable if there is a large amount of vuggy porosity. However, as can be observed in Figures 8.4 and 8.5, this confusion about lithology in the interval from 9088 to 9126 ft informs the log analyst that the reservoir has vuggy porosity. Or to state it another way, if all the porosity were intergranular or intercrystalline, all the lithology plots would indicate similar lithologies.

## M-N LITHOLOGY PLOT

The M-N plot requires a sonic log, neutron log, and density log, of which are all necessary to calculate the lithology-dependent variables M and N. M and N values are largely independent of matrix porosity (intergranular and intercrystalline). A crossplot of these two variables makes lithology more apparent. M and N values are calculated by the following equations (Schlumberger, 1972):

$$M = \frac{\Delta t_{fl} - \Delta t}{\rho_b - \rho_{fl}} \times 0.01$$

$$\left( M = \frac{\Delta t_{fl} - \Delta t}{\rho_b - \rho_{fl}} \times 0.003 \text{ (metric)} \right) \tag{8.1}$$

$$N = \frac{\phi_{Nfl} - \phi_N}{\rho_b - \rho_{fl}} \tag{8.2}$$

where:

$\Delta t$ = interval-transit time in the formation (from the log)

$\Delta t_{fl}$ = interval-transit time in the fluid in the formation

$\rho_b$ = formation bulk density (from the log)

$\rho_{fl}$ = fluid density

$\phi_N$ = neutron porosity (in limestone units, from the log)

$\phi_{Nfl}$ = neutron porosity of the fluid of the formation (usually = 1.0)

When the matrix parameters ($\Delta t_{ma}$, $\rho_{ma}$, $\phi_{Nma}$; Table 8.1) are used in the M and N equations instead of formation parameters, M and N values can be obtained for the various minerals (Table 8.2). Note that the quantities M and N above are related to lithology and have no relation to the cementation exponent (m) and the saturation exponent (n) in Archie's equation.

Figure 8.6 is an M-N plot of data from the Silurian Fusselman Formation illustrated in Figures 8.1 and 8.2. The data above a depth of 9088 ft plot in the sand-calcite-dolomite triangle. The calculated lithologies are illustrated in the column next to the M-N plot. The data from the porous vuggy interval (9088 to 9126 ft) plot above the tie line between calcite and dolomite, indicating the presence of vuggy porosity. If only matrix intercrystalline or intergranular porosity were present, the data would have plotted on or below the calcite-dolomite tie line. Remember, that the presence of vuggy porosity results in an underestimation of sonic interval transit time and therefore an overestimation of M. Because the data from the interval from 9088 to 9126 ft plot out of the lithology triangle, the calculated lithologies are not reliable.

## MATRIX IDENTIFICATION PLOT ($\rho_{maa}$ VS. $\Delta t_{maa}$)

The matrix identification plot, like the M-N plot, is a crossplot technique that helps identify lithology and secondary porosity. As with the M-N plot, the matrix-identification plot requires data from neutron, density, and sonic logs.

The first step in constructing a matrix identification plot is to determine values for the apparent matrix parameters, apparent matrix density ($\rho_{maa}$) and apparent matrix traveltime ($\Delta t_{maa}$). These values are calculated from neutron ($\phi_N$), density ($\rho_b$) and sonic ($\Delta t$) data using the following equations (Western Atlas, 1995):

Petrophysical Techniques

139

Table 8.1. Matrix Coefficients of Several Minerals and Types of Porosity (Liquid-filled Boreholes).

|  Minerals | Δt_{ma} μsec/ft | ρ_{ma} g/cm³ | φ_{SNPma}* (decimal) | CNLma* (decimal) | P_{e} (b/e)  |
| --- | --- | --- | --- | --- | --- |
|  Sandstone (1): V_{ma} = 18,000 ft/sec; φ > 0.10 | 55.5 | 2.65 | -0.035^{a} | -0.05^{a} | 1.81  |
|  Sandstone (2): V_{ma} = 19,500 ft/sec; φ < 0.10 | 51.2 | 2.65 | -0.035^{a} | -0.005 | 1.81  |
|  Limestone | 47.5 | 2.71 | 0.00 | 0.00 | 5.08  |
|  Dolomite (1): φ = 0.055 to 0.30 | 43.5 | 2.87 | 0.035^{a} | 0.085^{a} | 3.14  |
|  Dolomite (2): φ = 0.015 to 0.055 and φ > 0.30 | 43.5 | 2.87 | 0.02^{a} | 0.065^{a} | 3.14  |
|  Dolomite (3): φ = 0.0 to 0.015 | 43.5 | 2.87 | 0.005^{a} | 0.04^{a} | 3.14  |
|  Anhydrite | 50.0 | 2.98 | -0.005 | -0.002 | 5.06  |
|  Gypsum | 52.0 | 2.35 | 0.49^{b} | 0.6 | 3.99  |
|  Salt | 67.0 | 2.03 | 0.04 | -0.01 | 4.65  |
|  ^{a} Average values  |   |   |   |   |   |
|  ^{b} Based on hydrogen-index computation  |   |   |   |   |   |
|  *φ_{SNPma} and φ_{CNLma} values are specific to Schlumberger neutron tools.  |   |   |   |   |   |

From Schlumberger (1972). Courtesy Schlumberger Well Services.

Table 8.2. Values of M and N lithology parameters, calculated for common minerals.

|  Minerals | Fresh mud ρ = 1.0 g/cm³ |   | Salt mud ρ = 1.1 g/cm³  |   |
| --- | --- | --- | --- | --- |
|   |  M | N | M | N  |
|  Sandstone (1): V_{ma} = 18,000 ft/sec; φ > 0.10 | 0.810 | 0.628 | 0.835 | 0.669  |
|  Sandstone (2): V_{ma} = 19,500 ft/sec; φ < 0.10 | 0.835 | 0.628 | 0.862 | 0.669  |
|  Limestone | 0.827 | 0.585 | 0.854 | 0.621  |
|  Dolomite (1): φ = 0.055 to 0.30 | 0.778 | 0.516 | 0.800 | 0.544  |
|  Dolomite (2): φ = 0.015 to 0.055 and φ > 0.30 | 0.778 | 0.524 | 0.800 | 0.554  |
|  Dolomite (3): φ = 0.0 to 0.015 | 0.778 | 0.532 | 0.800 | 0.561  |
|  Anhydrite | 0.702 | 0.505 | 0.718 | 0.532  |
|  Gypsum | 1.015 | 0.378 | 1.064 | 0.408  |
|  Salt |  |  | 1.269 | 1.032  |

From Schlumberger Log Interpretation Principles, © 1972 Schlumberger. Courtesy Schlumberger Well Services.

140

ASQUITH AND KRYGOWSKI

$$
\rho_{maa} = \frac{\rho_b - (\phi_{ND} \times \rho_{fl})}{1 - \phi_{ND}} \tag{8.3}
$$

$$
\Delta t_{maa} = \frac{\Delta t - (\phi_{SN} \times \Delta t_{fl})}{1 - \phi_{SN}} \tag{8.4}
$$

where:

$\rho_{maa} =$ apparent grain density in $\mathrm{g/cm^3}$ or $\mathrm{Kg/m^3}$

$\Delta t_{maa} =$ apparent matrix interval transit time in $\mu\mathrm{sec/ft}$ or $\mu\mathrm{sec/m}$

$\rho_b =$ bulk density from the log

$\rho_{fl} =$ density of fluid

$\Delta t =$ interval transit time from the log

$\Delta t_{fl} =$ interval transit time of fluid

$\phi_{ND} =$ neutron-density crossplot porosity

$\phi_{SN} =$ sonic-neutron crossplot porosity

When matrix parameters $(\Delta t_{ma}, \rho_{ma},$ and $\phi_{Nma};$ Table 8.1) are used in the matrix identification equations instead of formation parameters, $\Delta t_{maa}$ and $\rho_{maa}$ values can be obtained for the various minerals (Table 8.3).

Table 8.3. Apparent matrix values for calculated for common minerals

|  Mineral | $\rho_{maa}$ (g/cm³) | $\Delta t_{maa}$ (μsec/ft) | $U_{maa}$ (barns/cm³)  |
| --- | --- | --- | --- |
|  Sandstone | 2.65 | 55.5 | 4.78  |
|  Limestone | 2.71 | 47.5 | 13.80  |
|  Dolomite | 2.87 | 43.5 | 8.98  |
|  Anhydrite | 2.98 | 50.0 | 14.90  |
|  Gypsum | 2.35 | 52.0 | 13.97  |
|  Salt | 2.03 | 67.0 | 9.68  |

Figure 8.7 is a matrix identification plot of data from the Silurian Fusselman Formation illustrated in Figures 8.1 and 8.2. The data above a depth of 9088 ft plot in the quartz-calcite-dolomite triangle with the calculated lithologies presented in the column to the right of the matrix identification plot. The porous interval with vuggy porosity (9088 to 9126 ft) plots above the quartz-calcite-dolomite triangle as it did on the $M-N$ plot (Figure 8.6). The calculated lithologies are illustrated in the column to the right of the lithology plot (Figure 8.7). Therefore, as with the $M-N$ plot (Figure 8.6), the lithologies determined for the porosity zone (9088 to 9126 ft) from the matrix identification plot (Figure 8.7) are unreliable.

## MATRIX-IDENTIFICATION PLOT ($U_{maa}$ VS. $\rho_{maa}$)

The third-generation density logs provide not only a bulk density ($\rho_b$) measurement but also a photoelectric absorption ($P_e$) measurement. The photoelectric measurement reflects the average atomic number of the formation and is therefore a good indicator of the formation's lithology (Dewan, 1983). The measurements of $\rho_b$ and $P_e$ are made from the same density tool at the long-spaced detector using energy selection (high energy for $\rho_b$ and low energy for $P_e$) of the incoming gamma rays. On the log (Figure 8.1), the $P_e$ curve is displayed with the neutron and density curves in track 3. The units for the $P_e$ curve are barns/electron. $P_e$ values for some of the common minerals are listed in Table 8.1.

The matrix-identification ($U_{maa}$ vs. $\rho_{maa}$) plot uses apparent matrix density ($\rho_{maa}$) and apparent volumetric cross section ($U_{maa}$) in barns/cm³ (Table 8.3). $U_{maa}$ is calculated from the $P_e$, $\phi_N$, and $\rho_b$ values using the following equation (Western Atlas, 1995):

$$
U_{maa} = \frac{(P_e \times \rho_b) - (\phi_{ND} \times U_{fl})}{1 - \phi_{ND}} \tag{8.5}
$$

where:

$U_{maa} =$ apparent volumetric cross section in barns/electron

$P_e =$ photoelectric absorption in barns/electron

$\rho_b =$ bulk density

$\phi_{ND} =$ neutron-density porosity

$U_{fl} =$ photoelectric absorption of fluid

When matrix parameters ($\rho_{ma}$, $P_e$ and $\phi_{Nma}$; Table 8.1) are used in the matrix identification equations instead of formation parameters, $U_{maa}$ and $\rho_{maa}$ values can be obtained for the various minerals (Table 8.3).

Figure 8.8 is a matrix identification plot ($U_{maa}$ vs. $\rho_{maa}$) of data from the Silurian Fusselman Formation illustrated in Figures 8.1 and 8.2. The data above a depth of 9088 ft and the data from the vuggy porosity zone (9088 to 9126 ft) all plot in the quartz-calcite-dolomite triangle with the calculated lithologies presented in the column to the right of the matrix identification plot. Because the $P_e$ measurement is insensitive to the presence of vuggy porosity, the lithologies are all reliable.

Therefore, if only two lithologies are present in a vuggy reservoir the preferred lithology plots are neutron-density and matrix identification ($U_{maa}$ vs. $\rho_{maa}$); however, if three lithologies are present in a vuggy reservoir the preferred lithology plot is the matrix identification plot ($U_{maa}$ vs. $\rho_{maa}$). If the porosity is matrix intergranular or intercrystalline the neutron-

Petrophysical Techniques

141

density, neutron-sonic, and density-sonic plots work for two lithologies and the $M-N$ and both matrix identification plots work for three lithologies.

Figure 8.9 is a plot of the lithologies from the matrix identification plot ($U_{maa}$ vs. $\rho_{maa}$) (Figure 8.8) and neutron-density porosities for the Silurian Fusselman Formation. The digital lithology and porosity data together with depths can be used in a mapping program for further analysis.

## ALPHA MAPPING FROM THE SP LOG

The spontaneous potential (SP) log (Chapter 2) can be used to map clean (shale-free) sands vs. shaly sands. The technique is called alpha ($\alpha$) mapping (Dresser Atlas, 1974) and is based on the observation that the presence of shale in a formation decreases the SP response.

The alpha method can be extremely valuable in mapping because it can more narrowly define desirable zones. Alpha values from nearby wells can be used to construct clean-sand (high-energy) maps (in effect, mapping isoalpha values).

To construct an alpha map, the static spontaneous potential (SSP) that a sand would have, if it were completely shale-free and unaffected by bed thickness, is calculated. The equation for SSP is:

$$
SSP = -K \times \log \left( \frac{R_{mf}}{R_w} \right) \tag{8.6}
$$

where:

$SSP =$ static spontaneous potential

$K = 60 + [0.133 \times$ formation temperature ($^\circ$F)]

$R_{mf} =$ resistivity of mud filtrate at formation temperature

$R_w =$ resistivity of formation water at formation temperature

The SSP must be calculated for the formation in each well, so that variations in $R_{mf}$ and $R_w$ can be accounted for. Next, the alpha values are determined by the method shown in Figure 8.10. The alpha cutoff ($0.75\alpha$, $0.50\alpha$, or whatever value chosen) is arbitrary, but should be based on production histories in the area.

The resulting alpha ($\alpha$) map delineates clean sand environments. In the above example (Figure 8.10), the greater alpha thickness for a given alpha cutoff (i.e., $0.75\alpha$ or $0.50\alpha$) indicates a greater thickness of higher energy, low-shale sandstones. Also, because the presence of shale in a sandstone can decrease its permeability, an alpha map indicates better reservoir conditions.

The problem with alpha mapping from an SP log is that SP response is decreased, not only by shale, but also by thin beds (less than 10 ft) and the presence of hydrocarbons (Chapter 2). Bed thickness problems are minimized by making an SP log bed thickness correction (Chapter 2). But the SP log can't be corrected for hydrocarbons.

## CLEAN SAND OR CARBONATE MAPS FROM GAMMA RAY LOG

The gamma ray log can be used to map clean (shale-free) sandstones or carbonates vs. shaly sandstones and carbonates. Because shales are more radioactive than clean sandstones or carbonates (Chapter 3), when the percentage of shale increases in these rock types, the gamma ray reading also increases.

Figure 8.11 is a gamma ray density neutron log through the Mississippian, upper Mission Canyon Formation in Roosevelt County, Montana. In this interval, crinoid and fenestrate-bryozoan bioherms are commonly developed. Because the bioherm facies is composed of clean carbonate relative to the facies that is not bioherm, the gamma ray log can be used to map the bioherm facies. The procedure for obtaining a clean carbonate cutoff from a gamma ray log is described in Figure 8.10.

A gamma ray value of 20 API units on the gamma ray log (Figure 8.11) represents clean carbonate with a volume of shale ($V_{shale}$) equal to or less than 0.05 (5%). By drawing a vertical line on the gamma ray log equal to 20 API units (Figure 8.10), the geologist can identify and map the clean carbonate (or sand).

Figure 8.12 is an isopach map of clean carbonate for the upper Mission Canyon Formation in Roosevelt County, Montana. Because the relationship between clean carbonate and the crinoid fenestrate-bryozoan bioherm facies is already established, the map (Figure 8.12) delineates the distribution of the bioherm facies. Clean carbonate maps have also been used to map the Pennsylvanian banks (bioherms) of north central Texas (Wermund, 1975).

## ROCK TYPING AND FACIES MAPPING

An important contribution to subsurface analysis of carbonate rocks has been the attempt to establish relationships between log responses and carbonate facies. Pickett (1977), Asquith (1979), and Watney (1979, 1980) used crossplots to identify the relationship of log response to rock type. Table 8.4 is a list of the crossplots applied by these authors.

142

ASQUITH AND KRYGOWSKI

Table 8.4. Types of Carbonate Rock-identification Crossplots (after Pickett, 1977; Asquith, 1979; and Watney, 1979 and 1980).

|  Δt (interval transit time) | vs. | φN (neutron porosity)  |
| --- | --- | --- |
|  ρb (bulk density) | vs. | φN (neutron porosity)  |
|  ρb (bulk density) | vs. | Δt (interval transit time)  |
|  Rt (deep resistivity) | vs. | φN (neutron porosity)  |
|  GR (gamma ray) | vs. | φN (neutron porosity)*  |
|  Rt (deep resistivity) | vs. | φS (sonic porosity)  |

*Watney (1979 and 1980) also uses neutron log readings measured in counts/second.

To date, crossplots have been used to establish log vs. lithology relationships only when petrographic data are available from cores or cuttings in selected wells. Petrographic analysis from selected wells is essential to firmly establish rock type.

When establishing log/lithology relationships, log responses from control wells (i.e., wells with petrographic analysis) are crossplotted. Next, areas that delineate rock-type clusters are outlined (see Figure 8.13) on the crossplot. Finally, log responses from wells without cores or cuttings are added to the crossplot. The carbonate rock type and depositional environment of wells without petrographic analysis can then be determined by the cluster in which each occurs on the crossplot chart (see Figure 8.13).

In Figure 8.13, the solid black circles and squares represent data from wells where petrographic analysis was used to determine carbonate rock type and depositional environment. The open circles represent data from wells without petrographic analysis. The carbonate rock types and depositional environments were determined by the cluster in which the open circles were plotted.

Figure 8.14 is a crossplot of deep resistivity ($R_t$) vs. sonic porosity ($\phi_S$) for the Lower Permian, Council

Grove B-zone in Ochiltree County, Texas. Clusters for the three carbonate rock types (oolite grainstone, oolitic wackestone, and argillaceous bioclastic wackestone) were established by petrographic analysis of cores and cuttings (open circles). The solid circles represent data from wells with only log control. Figure 8.15 is a facies map of the Council Grove B-zone based on the percentage distribution of the three carbonate rock types established by the resistivity/sonic-porosity crossplot (Figure 8.14).

The advantage of log crossplot techniques is that they maximize use of available information. Cores and cuttings are required from only a few control wells rather than all wells. This is very important in subsurface facies mapping because of the difficulty in obtaining cores and cuttings from every well in an area. Also, because petrographic analysis of every well is unnecessary, a great deal of time can be saved.

However, it should be emphasized that petrographic analysis of cores or cuttings from control wells is an essential first step to firmly establish the rock-type cluster used in the crossplots.

## REVIEW

1. Neutron and density logs can be used in a crossplot to determine lithology when a limited number of rock types are present.
2. Where lithology is more complex, a sonic log or a \(P_{e}\) curve used in conjunction with the neutron and density curves is necessary to construct \(M - N\) lithology or matrix identification crossplots.
3. Spontaneous potential (SP) and gamma ray logs can be used to map shaly vs. nonshaly carbonates or sandstones.
4. Crossplotting of multiple log responses can be used to establish relationships between log responses and rock types, provided some petrographic data from cores or cuttings are available.

Petrophysical Techniques

143

![img-10.jpeg](img-10.jpeg)

Figure 8.1. Induction, neutron, and density lag through the Silurian Fusselman Formation, West Texas.

![img-11.jpeg](img-11.jpeg)

Figure 8.2. Sonic lag through the Silurian Fusselman Formation, West Texas.

144

ASQUITH AND KRYGOWSKI

![img-12.jpeg](img-12.jpeg)

Figure 8.3. Neutron-density crossplot and resulting lithology estimation, Fusselman Formation, West Texas. Data are from Figures 8.1 and 8.2. A lithology key is shown in Figure 8.6.

![img-13.jpeg](img-13.jpeg)

Figure 8.4. Neutron-sonic crossplot and resulting lithology estimation, Fusselman Formation, West Texas. Data are from Figures 8.1 and 8.2. A lithology key is shown in Figure 8.6.

Petrophysical Techniques

145

![img-14.jpeg](img-14.jpeg)

![img-15.jpeg](img-15.jpeg)

Figure 8.5. Density-sonic crossplot and resulting lithology estimation, Fusselman Formation, West Texas. Data are from Figures 8.1 and 8.2. A lithology key is shown in Figure 8.6.

![img-16.jpeg](img-16.jpeg)

![img-17.jpeg](img-17.jpeg)

Figure 8.6. *M-N* lithology crossplot and resulting lithology estimation, Fusselman Formation, West Texas. Data are from Figures 8.1 and 8.2.

146

ASQUITH AND KRYGOWSKI

![img-18.jpeg](img-18.jpeg)

![img-19.jpeg](img-19.jpeg)

Figure 8.7. Matrix identification plot (apparent matrix density vs. apparent matrix traveltime) and resulting lithology estimation, Fusselman Formation, West Texas. Data are from Figures 8.1 and 8.2. A lithology key is shown in Figure 8.6.

![img-20.jpeg](img-20.jpeg)

![img-21.jpeg](img-21.jpeg)

Figure 8.8. Matrix identification plot (apparent matrix density vs. apparent matrix capture cross section) and resulting lithologic estimation. Fusselman Formation, West Texas. Data are from Figures 8.1 and 8.2. A lithology key is shown in Figure 8.6.

Petrophysical Techniques

147

![img-22.jpeg](img-22.jpeg)

![img-23.jpeg](img-23.jpeg)

![img-24.jpeg](img-24.jpeg)

Figure 8.9. Lithologies from the matrix identification plot and porosities from the neutron-density crossplot, Fusselman Formation, West Texas.

![img-25.jpeg](img-25.jpeg)

SP scale is \(20\mathrm{mV}\) /division

Figure 8.10. Determining alpha ($\alpha$) from an SP log.

Two different cutoffs are demonstrated: 50% alpha ($\alpha < 0.50$) and 75% alpha ($\alpha < 0.75$). The alpha percentage is determined as an inverse function of shallowness [100% alpha (1.0 $\alpha$) is shale-free; 50% alpha (0.50 $\alpha$) is shaly].

Given: You must first determine SSP. From Chapter 2:

$$
SSP = -K \times \log(R_{mf} / R_w) \tag{2.2}
$$

where:

$$
K = (0.133 \times T_f) + 60 \tag{2.3}
$$

and:

$$
R_{mf} = 2.0 \text{ at } 120^\circ\text{F},
$$

$$
R_w = 0.04 \text{ at } 120^\circ\text{F},
$$

$$
T_f = 120^\circ\text{F}
$$

$$
SSP = -130 \text{ mV}
$$

Procedure:

1. From the formulas above, we determine that SSP = -130 mV. Plot a scale of 130 mV on the SP log, using the shale baseline as the zero point; then use the SP scale to establish the value of your scale increments (in this case, each increment is 20 mv).
2. In this exercise, a thickness and depth will be determined for both \(\alpha < 0.50\) and \(\alpha < 0.75\), so draw vertical lines through the SSP scale approximately halfway (50%) and three-quarters of the way (75%) across, and draw vertical lines to intersect the SP curve at the desired depth range.
3. From the intersections, follow the values horizontally to the depth scale on the log. From this log-depth scale you can count depth increments to determine alpha thickness, as well as the top and bottom boundaries of the given alpha zone.

In this example $\alpha < 0.75$ is the thinner of the two, and measures 27 ft, from approximately x125 ft to x152 ft; whereas $\alpha < 0.50$ is thicker and measures 45 ft, from approximately x121.5 ft to x166.5 ft.

148

ASQUITH AND KRYGOWSKI

Figure 8.11. Neutron-density-gamma ray log in the Mission Canyon Formation, Montana

Given: The volume of shale ($V_{\text{shale}}$) cutoff is arbitrarily set at 5% ($V_{\text{shale}} = 0.05$).

Next, determine the gamma ray index from the chart in Figure 3.2, Chapter 3

Gamma ray index, $I_{GR} = 0.10$ when $V_{\text{shale}} = 0.05$

Determine gamma ray cutoff (see log and Figure 3.2).

Remember:

$$
I_{GR} = \frac{GR_{\log} - GR_{\min}}{GR_{\max} - GR_{\min}} \quad 3.1
$$

where:

$GR_{\log} =$ gamma ray log

$GR_{\max} =$ gamma ray maximum (shale)

$GR_{\min} =$ gamma ray minimum (shale-free sandstone or carbonate)

From the log:

$GR_{\max} = 90$ API units (from shale zone on log)

$GR_{\min} = 12$ API units (from clean carbonate zone on log)

$I_{GR} = 0.10$ ($I_{GR}$ for $V_{\text{shale}} = 0.05$; given)

![img-26.jpeg](img-26.jpeg)

![img-27.jpeg](img-27.jpeg)

Then, rearranging the equation above to solve for $GR_{\log}$:

$GR_{\log} = 19.8$ (round off to 20 API units)

20 API units represents clean carbonate where the volume of shale is equal to (or less than) 5%.

Draw a vertical line from the scale value of 20 API units and determine the thickness and limits of the clean carbonate formation (bioherm) much as you determined alpha values in Figure 8.10.

Figure 8.12. Isopach map of clean carbonates from the Mississippian Mission Canyon Formation, Roosevelt County, Montana, described in the text and in Figure 8.11.

![img-28.jpeg](img-28.jpeg)

Petrophysical Techniques

149

![img-29.jpeg](img-29.jpeg)

Figure 8.13. Example crossplot of formation resistivity, $R_{f}$ (in this case from a deep laterolog) vs. neutron porosity.

This comparison of log response to facies helps the geologist develop rock-type clusters. This example is from the Ordovician Red River C and D zones and Richland and Roosevelt Counties, Montana (after Asquith, 1979).

Solid squares and circles represent wells with core or cuttings available, in addition to log response. Open circles represent wells with log control only. Facies classifications are first confirmed by core or cuttings analysis, but once clusters are established only log control is necessary for facies prediction.

![img-30.jpeg](img-30.jpeg)

Figure 8.14. Example crossplot of formation resistivity ($R_{f}$) (in this case from deep induction) with sonic porosity ($\phi_{2}$).

As with Figure 8.13, the rock-type clusters are developed by core or cuttings analysis, but well logs are all that's necessary once the relationship is defined. This example comes from the Lower Permian Council Grove B-zone, Ochiltree County, Texas. After Asquith (1979).

Open circles represent wells with both core/cuttings analysis and log control. Solid black circles represent wells with only log control.

![img-31.jpeg](img-31.jpeg)

Figure 8.15. Example facies map of the Lower Permian Council Grove B-zone, Ochiltree County, Texas.

The map was prepared from the facies clusters established by crossplotted log data in Figure 8.13. After Asquith (1979). The legend defines the position of core, cuttings, and log-only control.

9

Hurley, Neil, 2004, Borehole Images, in G. Asquith and D. Krygowski, Basic Well Log Analysis: AAPG Methods in Exploration 16, p. 151-163.

# Borehole Images

## GENERAL

Borehole images are electronic pictures of the rocks and fluids encountered by a wellbore. Such images are made by electrical, acoustic, or video devices which have been lowered into the well. Images are oriented, they have high vertical and lateral resolution, and they provide critical information about bedding dip, fractures, faults, unconformities, paleocurrent directions, vuggy and fracture porosity, and other geological features. Case studies have shown that borehole images are best used in conjunction with other available wellbore data, such as other logs, cuttings, cores, and production data.

Because of the high expense and risk, relatively few wells are now being cored. Cores taken are generally short, so they may miss all or part of the target formation. In exploration wells, the depth to the target formation may even be unknown. Some lithologies tend to have poor core recovery, such as unconsolidated sands, and fractured, vuggy, or brecciated intervals. In some cores, the electrical or acoustic contrast between different lithologies may be more significant than the contrast apparent to the human eye. In recent years, all of these factors have led to the increased use of borehole images to characterize subsurface sedimentary rocks. This chapter provides a guide to the acquisition, processing, and interpretation of borehole images.

## ELECTRICAL BOREHOLE IMAGES

Electrical borehole images are based on dipmeter technology that has been commercially available since the 1950s (Bigelow, 1985a, b, c, d, e; Gilbreath, 1987; Adams et al., 1987). Figure 9.1 is an illustration of the tool configuration and basic principles behind dipmeter logs. Electrical borehole-imaging tools are, in essence, sophisticated dipmeters. The imaging tools have microresistivity electrodes arranged around the

wellbore on pads that are pressed against the borehole wall. The evolutionary trend from dipmeters to borehole images has been from a few electrodes to a complex array of electrodes on multiple pads (Figure 9.2).

*Data Acquisition*—Tools are first run into the hole with the pads closed. At the start of the log run, either four, six, or eight pads are pressed against the borehole wall. The number of pads depends on the logging device which is being used (Table 9.1). Electrical current is forced into the rock through the electrodes, and remote sensors measure the current after it interacts with the formation (Figure 9.3). Raw data include multiple electrode readings, caliper readings from individual pads or pairs of pads, and $x$-, $y$-, and $z$-axis accelerometer and magnetometer readings. Borehole deviation and pad 1 (tool) orientation are determined from the magnetometers.

The sample rate for electrode and accelerometer data is very high, normally 120 samples/ft (400 samples/m). Because of this, digital file size can be quite large. In fact, it is common to record tens to hundreds of megabytes of data from one log run. Areal coverage of the borehole face is a function of width of the electrode arrays, number of pads, and borehole diameter. In general, 40 to 80% of the borehole face is imaged in typical boreholes. Unimaged parts of the borehole appear as blank strips between the pads. Depth of investigation is small, generally less than 1 in (2.5 cm) into the formation (Williams et al., 1997). Logging rate, which is comparable to other openhole logs, is 1,600 to 1,800 ft/hr (500 to 550 m/hr). Because they are electrical devices, the drilling mud must be conductive. Mud resistivities higher than 50 ohm-m are unsuitable for most electrical borehole images, although commercial tools are now available for oil-based muds. The best images are acquired when the ratio between formation and mud resistivity is less than 1,000 (Grace and Newberry, 1998). Pressure and temperature limitations are comparable to those placed

151

152

HURLEY

Table 9.1. Electrical Borehole-Imaging Tools

|  Company | Trade Name | Number of Pads | Number of Electrodes | Useful References  |
| --- | --- | --- | --- | --- |
|  Halliburton | EMI (Electrical Micro Imaging Tool) | 6 | 150 | Seiler et al. (1994)  |
|  Schlumberger | FMS (Formation MicroScanner) | 4 | 64 | Ekstrom et al. (1986)  |
|  Schlumberger | FMI (Formation MicroImager) | 8 | 192 | Grace and Newberry (1998)  |
|  Baker Atlas | STAR (SimulTaneous Acoustic and Resistivity Imager) | 6 | 144 | Lacazette (1996)  |

on conventional logging tools. For example, the EMI tool is designed to withstand $350^{\circ}\mathrm{F}$ $(177^{\circ}\mathrm{C})$ temperature and 20,000 psi $(137,900\mathrm{kPa})$ pressure. Electrical borehole images can only be acquired openhole. Currently, there are no cased-hole applications.

## Data Processing

A processed electrical borehole image is basically a map of rock resistivity at the borehole face. Because it is more difficult to examine borehole images in 3-D, it is common to split the borehole along true north, then unroll the cylinder until it becomes a 2-D view (Figure 9.4). In highly deviated and horizontal wells, it is common to split the borehole image along the top of the hole (Figure 9.5). Planar features that intersect the cylindrical borehole appear as sine waves in the 2-D view.

Data processing is done by service companies or individuals on workstation, PC, or mainframe computers using commercially available or proprietary software. Processing steps involve correcting the directional data, that is, pad 1 azimuth (tool orientation) and hole azimuth, for magnetic declination. Some programs also correct for magnetic inclination. Note that magnetic declination varies with time and space. Charts and computer programs are available to compute magnetic declination for any location in the world on any logging date. Next, accelerometer corrections are applied, making sure that the accelerometer curve is on depth with the resistivity traces. The accelerometer accounts for differential sticking, speed variations, and resonant vibrations that occur as the tool moves up the hole (Figure 9.6). Finally, resistivity traces must be depth shifted using physical tool specifications, so that different rows of buttons are in line where the same slice of the borehole, perpendicular to the tool, was imaged. At very small scales (less than 6 in; $15\mathrm{cm}$ ), nonlinear depth shifts occur that may not be correctable by conventional data-processing algorithms.

As a result, not every surface that shows electrical contrast is exactly on depth.

Borehole images are created by assigning color maps to different bins or ranges of resistivity values. Colored pixels are then arranged in their proper geometric position around the wellbore. By convention, low-resistivity features, such as shales or fluid-filled fractures, are displayed as dark colors. High-resistivity features, such as sandstones and limestones, are displayed as shades of brown, yellow, and white (Figures 9.7 and 9.8).

Two main types of processed borehole images are available: static and dynamic (Figure 9.9). Static images are those which have had one contrast setting applied to the entire well. They provide useful views of relative changes in rock resistivity throughout the borehole. Static images can be calibrated in ohm-m to devices such as the LLS (Shallow Latero-log), a shallow-reading resistivity log. With normal processing, borehole images are uncalibrated. Images can be corrected for EMEX voltage, a background voltage that is adjusted on the logging truck to improve image quality. Dynamic images, which have had variable contrast applied in a moving window, provide enhanced views of features such as vugs, fractures, and bed boundaries. Dynamic images bring out subtle features in rocks that have very low resistivities, such as shales, and very high resistivities, such as carbonates and crystalline rocks.

## ACOUSTIC BOREHOLE IMAGES

Acoustic borehole images, also known as borehole televiewers, are based on technology first developed in the 1960s (Zemanek et al., 1970). In these tools, which are centralized in the well, a rotating transducer emits and records sound waves which bounce off of the borehole wall (Figure 9.10). Both acoustic amplitude and travel time are recorded and processed into images.

Borehole Images

153

# Data Acquisition

The tool is run into the hole with a stiff, spring-like centralizer. It is very important that the transducer is in the center of the well because reflections must strike the borehole wall and return to the tool at the proper reflection angle (Figure 9.11). The transducer rotates as it emits and records signals. The frequency of the emitted signal is generally in the several hundred kilohertz range. The CBIL tool, for example, rotates at a rate of 6 revolutions/s, and has a sample rate of 250 samples/rotation. Vertical resolution is about 0.3 in (0.8 cm) at a logging speed of 1200 ft/hr (365 m/hr). Commercially available tools and the associated service companies are listed in Table 9.2. Acoustic borehole images basically acquire a spiral trace of first-arrival amplitude and travel time to and from the borehole face. Acoustic caliper readings can be extracted from the logs. Orientation and borehole deviation are computed from an attached orientation device with $x$-, $y$-, and $z$-axis magnetometers. Accelerometer readings may or may not be recorded.

Table 9.2. Acoustic Borehole-Imaging Tools

|  Company | Trade Name | Useful References  |
| --- | --- | --- |
|  Halliburton | CAST (Circumferential Acoustic Scanning Tool) | Seiler et al. (1990)  |
|  Schlumberger | UBI (Ultrasonic Borehole Imager) | Schlumberger (1993)  |
|  Baker Atlas | CBIL (Circumferential Borehole Imaging Log) | Baker Atlas Web Page  |
|  Baker Atlas | STAR (SimulTaneous Acoustic and Resistivity Imager) | Lacazette (1996)  |

Again, because the sample rate is high, digital file size can be large. As with electrical images, it is common to record tens to hundreds of megabytes of data from one log run. Depth of investigation is zero, because this logging tool truly images the exposed borehole face. Areal coverage of the borehole face is 100%, which is a significant advantage of these tools. Vertical resolution is a function of logging rate, which is generally slower than other openhole logs. Maximum resolution (100 samples/in) for the openhole

CAST, for example, requires a rate of 1200 ft/hr (365 m/hr). Because these devices do not depend on electrical conductivity, they can be run in nonconducting muds. In fact, the ability to run in oil-based mud has been a major advantage of this tool. Because of signal dispersion, acoustic imaging logs do not work well with mud weights in excess of 12 pounds/gallon (1.44 kg/l). Also, because of increased travel time, the tools do not perform well if borehole diameter exceeds 12 in (30 cm). Pressure and temperature limitations are comparable to the those placed on conventional logging tools. The CAST tool, for example, is designed to withstand 350° F (177° C) temperature and 20,000 psi (137,900 kPa) pressure. Acoustic images are useful in both cased and openhole applications.

# Data Processing

Acoustic borehole images are basically compressed helical ultrasonic travel time or amplitude maps of the borehole wall. Data processing is normally done by service companies or individuals on workstation, PC, or mainframe computers using commercially available or proprietary software packages. Logging companies generally provide files in which the images have been corrected to true north. Individual amplitude and travel-time measurements are assigned colors based upon their different ranges of values. Colored pixels are arranged in their proper geometric position around the wellbore. By convention, low-amplitude or high travel-time features, such as shales, borehole irregularities (breakouts, washouts), and fluid-filled fractures are shown as dark colors (Figure 9.12). High-amplitude or low travel-time features, such as sandstones and limestones, are shown as shades of brown, yellow, and white. Accelerometer corrections are applied if they are available.

Acoustic borehole images have the cylinder split into 2-D views along true north, or along the top of the hole in deviated wells, in a manner illustrated in Figures 9.4 and 9.5. Planar features which intersect the borehole appear as sine waves in the 2-D view. Static and dynamic images can be created, as with electrical borehole images.

# DOWNHOLE VIDEO IMAGES

Downhole photographic images have been available since the 1960s (Mullins, 1966). However, limitations on the strength of the light source, maximum temperatures allowed, and data-transmission capabilities prevented them from gaining widespread acceptance. In recent years, however, better light sources,

154 HURLEY

more robust tools, oil-resistant coatings on lenses, and fiber-optic logging cables (Lau et al., 1987; Cobb and Schultz, 1992) have allowed these tools to emerge as viable options in the field of borehole imaging (Figure 9.13).

### *Data Acquisition and Processing*

The downhole video tool is run into the hole with a centralizer. A light source can be placed above or below the camera. Mirrors are generally placed so the operator has a fish-eye view of the well. Some devices allow the operator to have a sideways view of the well. The video is seen in real time and recorded at the surface. Borehole coverage is 100%; depth of investigation is zero because this logging tool images only the exposed borehole face. Logging rate is chosen by the operator at the surface. Because the images are processed instantly, it is possible to stop the tool to watch fluid flow, or to revisit the same depth a number of times. The tool works in liquid-filled or gas-filled wells, but borehole fluids must be relatively clear. A common misconception is that the tool does not work in flowing or pumping oil wells. If the well has any deviation and water cut, oil flows along the top of the hole, and the video can be acquired in the water-filled part of the hole (Whittaker and Linville, 1996). As an alternative, the well can be shut in and filled with water. The video can record what happens as the well is put on production. Temperature and pressure limitations on Halliburton's downhole video tool, for example, are 225° F (107° C) and 10,000 psi (69,000 kPa). Video images are more widely used in cased-hole studies, although they have important openhole applications.

### **EMERGING TECHNOLOGIES: OTHER BOREHOLE IMAGES**

With the demonstrated success of conventional borehole images, the oilfield service industry continues to try to generate images using other types of logging tools. Azimuthal resistivity images, obtained from a segmented laterolog-type device, have been described by Davies et al. (1992), Al-Waheed et al. (1994), and Smits et al. (1995). Resistivity images acquired at the bit using a measurement-while-drilling approach have been described by Rosthal et al. (1995) and Bonner et al. (1996). Azimuthal density images, also obtained while drilling, have been described by Bornemann et al. (1998).

### **BOREHOLE-IMAGE INTERPRETATION**

In practice, the log interpreter scrolls through the processed log on a computer workstation or PC, viewing static or dynamic images while fitting sine waves to observed bed boundaries, fractures, and other geologic features. Automated dip-picking programs are available, and the interpreter can choose to edit dips that have already been picked by various computer algorithms. This section outlines the most important uses of borehole images. A steadily increasing number of studies have used these tools. A set of reprints edited by Paillet et al. (1990) provides a good historical reference volume. In addition, a bibliography of borehole-image articles is maintained by S. Prensky on the SPWLA website.

### *Fracture and Fault Occurrence and Orientation*

The most obvious use of borehole images is in the area of structural interpretation, especially detecting and orienting fractures and faults (Figures 9.7 and 9.8). In some cases, a fault plane can be imaged and oriented. This is especially true for microfaults, which may have offset amounts of only a few inches (or cm). In other cases, faults correspond to washouts and may be poorly imaged. If this happens, the interpreter can look at nearby fractures, which may relate to fault orientation. Changes in bedding orientation may indicate that the borehole has crossed a fault or a fold axis (Bengsten, 1981, 1982; Bigelow, 1985d; Koepsell et al., 1989a, b; Hurley et al., 1994; Knight, 1999). Boundaries between bedding-plane dip domains, or consistent groups of dips, might be faults or unconformities (Hurley, 1994). For dip-slip faults, stereonet analysis of deformed beds above and below the fault can be used to determine the fault's strike azimuth.

Fracture analysis is typically done using stereonets which show various fracture sets (Younes et al., 1998). One can use borehole images to differentiate open fractures from healed fractures. Because the mud is conductive, an open fracture appears as a dark trace on an electrical borehole image. Note that shale-filled fractures could also appear as dark traces on electrical borehole images. Other logs, such as the gamma ray, can help resolve such situations. If the fracture is filled with cement such as calcite, anhydrite, or quartz, the fracture might appear as a resistive (white) trace on the electrical borehole image. Healed fractures in acoustic logs might appear on the amplitude but not the travel-time images.

Natural and induced fractures can be differentiated

Borehole Images

155

in some cases. Natural fractures can occur as one or more fracture sets, each with a distinct orientation. Induced fractures (Figure 9.12) are commonly near vertical, have a well defined strike azimuth, can cut across beds of different lithology (for example, sands and shales), and have a strike azimuth that is perpendicular to borehole breakouts, or oval elongations of the borehole. In deviated holes, induced tensile-wall fractures can occur as en echelon sets that do not cross the entire width of the borehole image (Barton et al., 1997).

## Fracture Aperture

In the parallel-plate model for fluid flow in fractures (Brown, 1987), permeability is proportional to the square of fracture-aperture width (Figure 9.14). Because fractures are not truly parallel plates, flow estimates must be modified to account for asperities, or irregularities, along the fracture walls (Brown, 1987). Because of the important relationship between permeability and aperture width, geologists and engineers are interested in aperture widths in boreholes.

Luthi and Souhaite (1990) modeled fracture aperture widths as recorded by electrical borehole images. They derived a method for aperture-width calculation using mud resistivity as the main input parameter. Based upon their technique, commercial software (available from Schlumberger) calculates aperture widths from electrical borehole images. Svor and Meehan (1991a, b) used this approach to create a grading system for fractures, and they related this to ultimate recovery in Austin Chalk horizontal wells.

## Borehole Breakouts, In Situ Stress Interpretation

Borehole breakouts (Figure 9.12), which can be measured using the caliper logs from electrical or acoustic borehole-imaging tools, commonly indicate the orientation of present-day *in situ* stress (Bell and Gough, 1979; Zoback et al., 1985; Plumb and Hickman, 1985; Springer, 1987; Parker and Heffernan, 1993; Barton et al., 1997). Borehole breakouts, when combined with the orientation of inferred natural and induced fracture sets, may be related to directional permeability in the subsurface (Heffer and Lean, 1993; Haws and Hurley, 1992). This information has considerable application to optimizing the orientation of horizontal wells and configuring injection patterns in secondary and tertiary recovery schemes. Also, the orientation of artificially induced fractures is generally parallel to the orientation of present-day maximum horizontal *in situ* stress.

## Stratigraphic Interpretation

Conventional stratigraphic interpretation from dipmeters (Bigelow, 1985e; Gilbreath, 1987), involves looking for steepening upward or shallowing upward patterns in bedding dips. Combined with core, other log signatures, and isopach maps, such interpretations can lead to new well locations (Grace and Newberry, 1998).

Authors such as Bourke et al. (1989), Höcker et al. (1990), and Bourke (1992) have shown that sedimentologic and stratigraphic interpretations from core and other logs can be combined with dipmeter results to improve reservoir characterization in clastic rocks.

Hurley (1994) showed that boundaries between dip domains can be subtle angular discordances between overlying and underlying sedimentary strata. Dip domains are groups of consistent dips that may be structural blocks or sequences at seismic scale. Berg (1998) used synthetic deviation plots with a similar objective. The recognition of unconformities can be important in detecting reservoir compartments and in making sequence-stratigraphic interpretations. In horizontal wells, borehole images combined with deviation surveys and other logs can provide powerful tools for the interpretation of fine scale (cm to m) microstratigraphy (Hurley et al., 1994)

In cyclic, well-bedded units, borehole images can be used to construct modified Fischer plots for parasequence-scale correlations (Hurley, 1996; Witton, 1999). The resulting curve has a distinctive shape which is based on changes in cycle thickness. This curve can be used like a well log to correlate cycles between wells, look for missing section, and hypothesize about changes in sea level or channel migration.

## Sedimentologic Interpretation

Sedimentologic interpretations are aided by the fact that the intrinsic lower resolution limit of borehole images is on the order of 0.2 in (5 mm). With electrical images, one can image conductive fractures in resistive rock that are fractions of a millimeter in width. Although grain types generally cannot be discerned, features such as burrows (Figure 9.15), clasts, vugs, and breccias are common. Vug shape can be diagnostic for certain fossils.

Vug quantification from borehole images using pixel-counting techniques has led to the recognition of flow units and bypassed pay in some reservoirs (Newberry et al., 1996; Martin et al., 1997; Hurley et al., 1998).

Baseline color shifts in static images can indicate

156

HURLEY

changes in the type or amount of matrix porosity. Cemented versus open-fracture and breccia porosity can commonly be imaged. Sedimentary structures, such as fluid-escape features, ripples, cross beds, and imbricated clasts can be apparent (Figure 9.16). The observation of such structures may yield paleocurrent, facies, and depositional environment interpretations (Luthi and Banavar, 1988; Carr et al., 1997; Witton, 1999).

Thinly bedded sands and shales have bedding thicknesses on the scale of 2 to 20 in (5 to 50 cm). Such beds are below the resolution limits of most logging tools. Thin beds have been successfully resolved and quantified using borehole images (Sovich et al., 1996). Such analyses have led to better estimates of net reservoir thickness to gross reservoir thickness and improved volumetric calculations (Reid and Enderlin, 1998).

# REVIEW

1. The three most common types of borehole images are electrical, acoustic, and downhole video. The advantage of these tools is that they give high-resolution pictures of the geologic features that occur in the borehole. Borehole images are best used in combination with other logs and rock information to allow more definitive interpretations of the downhole log signatures.
2. Electrical borehole-imaging logs are sophisticated dipmeters. Arrays of electrodes occur on 4, 6, or 8

pads which are pressed against the borehole wall. Images are resistivity maps of the borehole face.

3. Electrical images are generally run in conducting mud. They work because there is resistivity contrast between various lithologies, like sands and shales, and mud-filled fractures.
4. Acoustic borehole images have a rotating transducer which emits a high-frequency sound signal that bounces off of the borehole wall. Processed images are helical maps of acoustic amplitude and travel time for the reflected sound waves.
5. Acoustic images can be run in oil-based mud. They work because there is commonly acoustic contrast between different lithologies, mud-filled fractures, and borehole irregularities such as washouts or breakouts.
6. Downhole video logs have seen significant technological improvements, especially in the form of fiber-optic cables. They provide real-time, dynamic images of the well and flowing fluids. They are useful for casing inspection, fluid-flow documentation, fracture detection, and other applications, assuming the borehole fluid is relatively clear.
7. Borehole images have been used to document fracture and fault occurrence and orientation, fracture aperture widths, borehole breakouts and in situ stress orientation. They are also commonly used for stratigraphic and sedimentologic interpretations, including paleocurrent analysis, vug quantification, and thin-bed detection.

Borehole Images

157

![img-0.jpeg](img-0.jpeg)

Figure 9.1. Basic principles of electrical dipmeter tools are illustrated by this diagram of Schlumberger's SHDT (Stratigraphic High Resolution Dipmeter Tool), which became commercially available in 1982. Two measuring electrodes on each of four pads generate eight row electrode traces, as shown at the bottom. Magnetometers measure borehole deviation. Accelerometers record high-frequency tool-speed variations which occur as the tool is being run. Formation dip is computed from planes that are fit through correlative peaks and troughs on the speed-corrected electrode traces. Caliper logs record borehole diameter between pads 1 and 3 and between pads 2 and 4. After Schlumberger (1983) and Höcker et al. (1990).

![img-1.jpeg](img-1.jpeg)

Figure 9.2. Schematic illustration of pad and electrode configurations for one commercially available dipmeter and all of the common electrical borehole-imaging logs. Numbers in parentheses represent the year in which the tool was released. Refer to Table 9.1 for tool and company names. Modified from Grace and Newberry (1998).

158

HURLEY

Figure 9.3. Basic elements of electrical borehole-imaging tools. Electrical currents pass through button arrays into the formation. Current drop is recorded at a remote detector. Magnetometers record borehole deviation, and accelerometers record speed variations. The processed borehole image is a speed-corrected resistivity map of the borehole wall. Modified from Williams et al. (1997).

![img-2.jpeg](img-2.jpeg)

Figure 9.4. Schematic diagram of a vertical, cylindrical borehole intersected by a planar feature such as a steeply dipping fracture. The intersection between the plane and the cylinder is either a circle or an oval. To view the borehole in two dimensions, the cylinder is generally cut along a line with an azimuth of true north (N). When the cylinder is flattened, the line of intersection of an oval trace becomes a sinusoidal curve. Modified from Serra (1989).

![img-3.jpeg](img-3.jpeg)

Borehole Images

159

![img-4.jpeg](img-4.jpeg)

![img-5.jpeg](img-5.jpeg)

![img-6.jpeg](img-6.jpeg)

Figure 9.5. Schematic diagram of a horizontal, cylindrical borehole intersected by a planar feature such as a bedding plane. The intersection between the plane and the cylinder is either a circle or an oval. To view the borehole in two dimensions, the cylinder is generally cut along the top of the borehole. When the cylinder is flattened, the line of intersection of an oval trace becomes a sinusoidal curve. Modified from Serra (1989).

|  0 | GR (API) | 200  |
| --- | --- | --- |
|  6 | C13, C24 (in) | 16  |
|  7.5 | AZ (m/s²) | 12  |

Accelerometer Corrected

Not Accelerometer Corrected

![img-7.jpeg](img-7.jpeg)

Figure 9.6. Illustration of the benefits of speed correction. FMI images on the left have been accelerometer (AZ) corrected; images on the right have not. The vugs (V1) are compressed on the right-hand image (V2) because of a negative acceleration (decreasing AZ) at this depth. The shale (S2) has been stretched because of a fast acceleration (increasing AZ) at its top. Vertical scale is in ft. Note the washout (enlarged calipers C13 and C24) and increased GR corresponding to shale (S1). N-S-N refers to the true-north reference shown in Figure 9.4.

160

HURLEY

![img-8.jpeg](img-8.jpeg)

Figure 9.7. FMI display in a sandstone of partially healed fractures, which appear as discontinuous conductive segments. Conductive features are imaged as dark colors. Red sine waves show fracture traces. Vertical scale is in ft. N-S-N refers to the true-north reference shown in Figure 9.4. After Knight (1999).

![img-9.jpeg](img-9.jpeg)

Figure 9.8. Small-scale fault, or microfault (M), and bed boundaries (B) in a sand and shale interval. The shales occur in the lower part of the section. Vertical offset on the microfault is approximately 0.25 ft (8 cm). Vertical scale is in ft. N-S-N refers to the true-north reference shown in Figure 9.4. After Knight (1999).

Figure 9.9. Comparison between static (left) and dynamic (right) images in a sandstone interval that appears massive and nonlaminated when the core is viewed in visible light. Note the fine-scale bedding and the truncation surface (T). Dynamic processing, in which the image contrast is normalized in a moving S-ft window, sharpens the image and makes geologic features easier to see. Vertical scale is in ft. N-S-N refers to the true-north reference shown in Figure 9.4. The green line is a sine wave fit to a bedding plane. After Knight (1999).

![img-10.jpeg](img-10.jpeg)

Borehole Images

161

![img-11.jpeg](img-11.jpeg)

Figure 9.10. Schematic illustration of the basic operating principles behind acoustic borehole-imaging logs. A rotating transducer emits and records sound pulses. First-arrival amplitudes and travel times are recorded and mapped into processed logs. Tool names and companies are shown in Table 9.2. Modified from Zemanek et al. (1970).

![img-12.jpeg](img-12.jpeg)

Figure 9.11. This diagram, which is a view looking down on a borehole, shows the reason the acoustic borehole-imaging tool needs to be centralized. If the tool is off-center, the travel times may be too long (top) or too short (bottom). Some parts of the borehole are not even imaged because the reflected sound wave does not return to the transducer (left and right sides).

![img-13.jpeg](img-13.jpeg)

Figure 9.12. Example of an amplitude image from a CBIL log in a fractured sand and shale interval. Note the open fracture (F). This fracture, which terminates (T) at a shale bed, is thought to be drilling induced. Borehole breakouts (B), which occur as dark patches $180^{\circ}$ from each other, are well imaged by this log. Depth is in ft. N-S-N refers to the true-north reference shown in Figure 9.4.

162

HURLEY

![img-14.jpeg](img-14.jpeg)

![img-15.jpeg](img-15.jpeg)

![img-16.jpeg](img-16.jpeg)

![img-17.jpeg](img-17.jpeg)

Figure 9.13. Examples of downhole video still shots. (a) Top of a tubing fish. (b) Hole in casing. (c) Production deposits (scale) with oil flow (black bubbles). (d) Openhole fractures. From Halliburton (1996).

Figure 9.14. Simple parallel-plate model for fluid flow in a fracture. $L =$ length; $d =$ aperture width; $Q =$ flow rate; $p =$ pressure; $\mu =$ viscosity; $K =$ permeability. The Darcy equation for linear flow (upper equation), when applied to this geometry, suggests that permeability $(k)$ is proportional to the square of the aperture width ( $d$ , lower equation). Modified from Brown (1987).

![img-18.jpeg](img-18.jpeg)

Borehole Images

163

![img-19.jpeg](img-19.jpeg)

Figure 9.15. Static FMI image of interbedded sands (light color) and shales (dark color). Based on core studies, the sandy laminated sediments represent storm deposits. Shaly bioturbated sediments (B) represent fair-weather deposits. Vertical scale is in ft. N-S-N refers to the true-north reference shown in Figure 9.4. After Knight (1999).

(a)

![img-20.jpeg](img-20.jpeg)

(b)

![img-21.jpeg](img-21.jpeg)

Figure 9.16. STAR electrical images in a deep-water sandstone show climbing ripple laminations in a 3-D view (above), and flame structures, or fluid-escape structures (below). The height of each image is 6 in (15 cm). After Witton (1999).

10

Asquith, G., and D. Krygowski, 2004, Log Interpretation Case Studies, in G. Asquith and D. Krygowski, Basic Well Log Analysis: AAPG Methods in Exploration 16, p. 165–239.

# Log Interpretation Case Studies

## INTRODUCTION

A major hurdle for geologists is learning how the theory and the many formulas of log interpretation are translated into practice. The learning process is slow, and takes place only after a good deal of repetitive effort is supported by actual experience with logs. There are absolutely no shortcuts. Memorizing log patterns and curve values just doesn't work, and can, in fact, prove disastrous. However, to assist the process of changing what's done into how it's done, case studies can be an invaluable asset. The ones presented here cover several geographical areas, geologic ages, lithologies and log packages. This variety is not necessarily a classic representation of any of the categories. The reader will need to engage his or her intellect in finding appropriate solutions for each problem, and will also need to apply material already learned from thorough study of the preceding text.

In these case studies, the authors are trying to:

- show examples of evaluation under a range of conditions: clastic rocks and carbonate rocks, oil and gas;
- show examples with ranges of data, from minimal to substantial, from old to new; and
- move the reader from observing an illustration of an interpretation to interpretation as a self-directed exercise (with a solution provided, to verify the reader's conclusions).

Although all the case studies are based on actual field examples, in some studies the amount of log data analyzed would be superfluous in practice. In many instances, to set pipe or not doesn't require a complete log analysis. The unusual amount of detail is offered here for use in a learning experience. Nevertheless, careful study of a log almost always yields information that furthers the development of expertise.

These case studies are a progressive series of problems. In solution of the first example the reader is

asked to do very little, but to solve the final example the reader should be prepared to work almost independently. An effort is made to define variables and terms in the case studies, even though they may have been defined earlier in the text.

No matter how significant log interpretation is to a geologist as an exploration method, it must also be viewed in the larger context of exploration decision-making. That's why each case study includes a volumetric calculation of reserves. In several studies, the reader is asked to determine a rate of return on investment. As everyone intimately connected with petroleum exploration knows, wells can be geologic successes but economic failures. In a successful exploration program, petrophysical log interpretation is used as a way to tip the risk scale toward economically successful wells.

The list of equations that follows is an important part of petroleum exploration. Derivation of variables is included in this listing, although in most instances the reader is not asked to solve them. Instead, the values will be given, for use in the formulas.

### Items of note

In all the case studies, only a small number of representative depths is used in the Work Tables to illustrate reading the raw-curve data and making the calculations, whereas the graphical displays (crossplots and log plots) show data from every half-foot of the intervals of interest.

In the solutions to these case studies, the values of the raw log data—resistivity, bulk density, neutron porosity, and so on—were determined from visual inspection of the data and verified with the digital data, which itself was derived from paper copies of the logs. In that process, the number of significant digits determined in the visual inspection was retained. Those numbers were believed to be more representa-

165

166

ASQUITH AND KRYGOWSKI

tive of the results of the reader's efforts to determine the log values than reversion to the digitally derived data, which is displayed to an arbitrary number of digits to the right of the decimal point. The reader will note that some types of data—neutron porosity and sonic porosity, for example—are shown to the same number of significant digits, whereas other data, notably resistivity, vary in the number of significant digits shown; this practice is based on the ability of the analyst to read that data from logarithmic scales. Computations were done with a variety of machine-assisted methods, rather than by hand; therefore the computations tend to reflect an arbitrary number of values to the right of the decimal point. The values that the reader determines should be close to those in the solutions tables, but they probably will not match exactly. In general, if the reader has read the original log values to the best of his/her ability and made the calculations properly, the decisions derived from those calculations will agree with the solutions to the case studies.

### Equations useful for the following case studies

The equations are presented in most, if not all, the case studies. They are reproduced here and referenced from those studies. Equations specific to each study will appear in the corresponding text.

Archie Water Saturation:

$$S_{wa} = \left[ \frac{a \times R_w}{\phi^m \times R_i} \right]^{\frac{1}{n}} \quad 10.1 \text{ (Equation 7.1)}$$

Flushed-zone Water Saturation (Archie Equation):

$$S_{xo} = \left[ \frac{a \times R_{mf}}{\phi^m \times R_{xo}} \right]^{\frac{1}{n}} \quad 10.2 \text{ (Equation 7.2)}$$

Ratio Water Saturation:

This equation can be used to estimate water saturation when no porosity logs are available, but in the case study, the solution of this equation will be compared with calculations of the Archie water saturation.

$$S_{wr} = \left[ \frac{R_{xo} / R_i}{R_{mf} / R_w} \right]^{0.625} \quad 10.3 \text{ (Equation 7.7)}$$

Moveable Hydrocarbon Index (MHI):

This form of the equation is derived from the ratio water saturation method, above.

$$MHI = S_w / S_{xo} = \left[ \frac{R_{xo} / R_i}{R_{mf} / R_w} \right]^{\frac{1}{2}} \quad 10.4 \text{ (Equation 7.4)}$$

Bulk Volume Water:

The proportion of water in the total formation is referred to as bulk volume water. It can be an indicator that the formation is at irreducible water saturation.

$$BVW = \phi \times S_w \quad 10.5 \text{ (Equation 7.22)}$$

Residual Oil Saturation:

$$ROS = 1.0 - S_{xo} \quad 10.6$$

Moveable Oil Saturation:

$$MOS = S_{xo} - S_w \quad 10.7$$

### Equations used for calculating volumetric producible hydrocarbon reserves

Oil-bearing formations:

$$N_f = \frac{7758 \times A \times h \times \phi \times S_h \times RF}{B_{oi}} \quad 10.8$$

where:

$N_f$ = volumetric recoverable oil reserves in stock-tank barrels (STB)

7758 = barrels per acre-foot

A = drainage area in acres

h = reservoir thickness in feet

$\phi$ = porosity (decimal fraction)

$S_h$ = hydrocarbon saturation ($1.0 - S_w$) (decimal fraction)

RF = recovery factor

$B_{oi}$ = oil volume factor, or reservoir barrels per stock-tank barrel

$$B_{oi} = 1.05 + 0.5 \times \left( \frac{GOR}{100} \right) \quad 10.9$$

where:

$$GOR \text{ (gas - oil ratio)} = \frac{\text{gas in cubic feet}}{\text{oil in barrels}} \quad 10.10$$

Gas-bearing formations:

$$G_f = 43,560 \times A \times h \times \phi \times S_h \times B_{gi} \times RF \quad 10.11$$

Log Interpretation Case Studies

167

where:

$G_f$ = volumetric recoverable gas reserves in standard cubic feet (SCF)

43,560 = area of 1 acre, in square feet

$A$ = drainage area in acres

$h$ = reservoir thickness in feet

$\phi$ = porosity, decimal

$S_h$ = hydrocarbon saturation (1.0 - $S_w$), decimal

$RF$ = recovery factor

$B_{gi}$ = gas volume factor (in SCF/cu ft)

$$\begin{array}{l} B_{gi} = \frac{T_w}{P_{sc}} \times \frac{P}{Z \times T_f} \\ = \left[ \frac{459.7 + 60}{15} \times \frac{P}{Z \times (459.7 + T_f)} \right] \end{array} \tag{10.12}$$

where:

$T_{sc}$ = temperature ($^\circ$F) at standard conditions

$P_{sc}$ = surface pressure (psi) at standard conditions

$P$ = reservoir pressure (psi)

$Z$ = gas compressibility factor

$T_f$ = formation temperature ($^\circ$F)

Equation 10.12 can be solved also by the form below, where $B_{gi}$ is approximated by the ratio of surface pressure and formation pressures:

$$G_f = 43,560 \times A \times h \times \phi \times S_h \times \left( \frac{Pf_2}{Pf_1} \right) \times RF \tag{10.13}$$

where:

$G_f$ = volumetric recoverable gas reserves in standard cubic feet (SCF)

43,560 = area of 1 acre, in square feet

$A$ = drainage area in acres

$h$ = reservoir thickness in feet

$\phi$ = porosity, decimal

$S_h$ = hydrocarbon saturation (1.0 - $S_w$), decimal

$RF$ = recovery factor

$Pf_1$ = surface pressure (psi) (atmospheric, approximately 15 psi)

$Pf_2$ = reservoir pressure (psi)

$$\frac{Pf_2}{Pf_1} = \frac{0.43 \times depth}{15} \tag{10.14}$$

where:

0.43 is the average pressure gradient (in psi/ft), and depth is in feet.

Estimation of formation pressure:

Static mud column pressure

= depth $\times$ mud weight $\times$ 0.052. 10.15

Rule of thumb for static bottom-hole pressure:

$$P_{ws} = P_{wh} + 0.25 \times \left( \frac{P_{wh} \times depth}{100} \right) \tag{10.16}$$

where:

$P_{ws}$ = static bottom hole pressure (psi)

$P_{wh}$ = well-head pressure (psi)

Estimation of geothermal gradient:

$$g = \frac{(T_f - T_s) \times 100}{depth} \tag{10.17}$$

where:

$g$ = temperature gradient in $^\circ$F/100 ft

$T_f$ = formation temperature in $^\circ$F

$T_s$ = mean surface temperature in $^\circ$F

depth = formation depth in feet

As you begin trying the formulas in case studies, keep in mind the fact that many values such as water saturation ($S_w$) and porosity ($\phi$) may be expressed in percentages, especially on older logs and in older calculations. So, even though this will be immediately obvious to you, remember to change percentages to decimal fractions before doing the calculations.

168

ASQUITH AND KRYGOWSKI

# Case Study 1:

# PENNSYLVANIAN ATOKA SANDSTONE, PERMIAN BASIN, U.S.A.:

# The Problem.

Case Study 1 illustrates the evaluation of a clean, gas-bearing sandstone. Because this is the first case study, the interpretation is largely done for the reader, with only minor calculations required of the reader. Two terms are defined here:

- A gas chromatograph is a device that samples the gases from the circulating drilling mud and analyzes them for the presence of methane \((\mathrm{C_1H_4})\) and heavier hydrocarbons. The instrument alerts the geologist to a show of hydrocarbons from a formation.
- A drilling break is an increase in the rate of penetration of the drill bit, which indicates a difference in the rock. For example, penetration rate commonly increases when the bit goes from a shale into porous sandstone. A reverse drilling break, when the rate of penetration slows, may indicate passage of the bit from sandstone into shale, or the drilling of a highly cemented, low-porosity formation. Penetration rate is measured in minutes/foot rather than feet/minute, so the larger the number the slower the penetration rate. For example, a penetration rate of \(20\mathrm{min / ft}\) is slower penetration than \(10\mathrm{min / ft}\).

# Background

Your company has just finished drilling a 15,900-ft wildcat well in the Permian Basin of Texas. The primary target was Morrowan sandstones. They are not developed sufficiently for commercial production and you face these alternatives: declare the well dry and abandoned (D&A), or find another zone, one that would produce hydrocarbons at an exceptional profit.

Samples of bit cuttings indicated that at 14,600 ft the Atoka Sandstone (Figure 10.1) is predominantly loose, subrounded, coarse to very coarse, quartzose sandstone with minor amounts of arkosic sandstone that is tan, medium grained to coarse grained, poorly sorted, and friable. This information leads to the inference that the Atoka Sandstone might be permeable, because the rock is coarse grained and accordingly, pore spaces should be large. Poor cementation and good permeability are indicated, because the sandstone is friable.

Other information about the Atoka Sandstone—information that you consider to be favorable—is the emission of a few gas bubbles from sample cuttings and gas recorded on the mud logger's gas chromatograph. During drilling of the bottom 4 ft of the sandstone, total gas background on the chromatograph increased from 10 units to 40 units of gas with a trace of C₂ and C₃ hydrocarbons, a significant change. The neutron-density log (Figure 10.2) shows evidence that supports your conclusions.

Even though you are optimistic about the potential of good production from the Atoka Sandstone—because of the nature of the sample cuttings and the gas shows—you are concerned about a reverse drilling break that occurred as the sandstone was penetrated. Strata that directly overlie and underlie the Atoka Sandstone were penetrated at 8 to 10 min/ft. However, the penetration rate through most of the sandstone was 15.5 min/ft; it slowed to 20 min/ft through the bottom 10 ft. The slower drilling times may mean that the sandstone is not as porous and permeable as sample-examination suggested.

Now, inspect the logs, calculate the important quantitative attributes of the sandstone, assess the log-derived information, and decide whether the Atoka Sandstone should produce oil and gas in sufficiently profitable quantities.

# Well site information and other pertinent information:

Total depth \((TD) = 15,962\) ft
- bottom hole temperature (BHT): \(197^{\circ}\mathrm{F}\)
- bit diameter \(= 8.5\) in.
- fluid in the hole: "freshwater mud"
- mud filtrate resistivity \((R_{mf})\): 1.34 ohm-m at \(87^{\circ}\mathrm{F}\)
- mean annual surface temperature \(= 75^{\circ}\mathrm{F}\) (estimated by the well site geologist)
temperature of the formation \((T_{f}) = 187^{\circ}\mathrm{F}\) estimated from formation temperature chart (Chapter 1)
- resistivity of formation water \((R_{w}) = 0.065\) ohm-m at \(T_{f}\) from local information (water produced nearby, water recovered during drill-stem tests, or a formation-water catalogue)
- resistivity of mud filtrate \((R_{mf}) = 0.65\) ohm-m at \(T_{f}\) from the log header, corrected to formation temperature by the Arps equation (see Chapter 1)
- Archie parameters: \( a = 0.81 \), \( m = n = 2 \), for use in Equations 10.1 and 10.2

Log Interpretation Case Studies

169

# Helpful equations

Neutron-density porosity in a gas zone:

Values for neutron porosity and density porosity are read from the neutron-density log and evaluated jointly:

$$
\phi_{ND_{\text{gas}}} = \sqrt{\frac{\phi_D^2 + \phi_N^2}{2}} \tag{10.18 (Equation 4.8)}
$$

$R_t$ Minimum, to determine true formation resistivity, $R_f$: This technique approximates $R_f$ in thin resistive zones; it is an alternate (approximate) approach to the use of a variety of correction charts.

$$
R_{t \min} = LL8 \times \frac{R_o}{R_{mf}} \tag{10.19 (Equation 5.3)}
$$

where LL8 is shallow resistivity, read by the laterolog 8.

Static SP:

The value of the SP in a clean (“shale-free”) formation is the Static SP.

$$
SSP = -K \times \log\left(\frac{R_{mf}}{R_o}\right) \tag{10.20 (Equation 8.6)}
$$

On the Work Table (Table 10.1), points were selected to illustrate a range of resistivities and porosities. Notice that the log values recorded at each depth actually may be peak or trough values from as much as 1 ft above or below the listed depths. This is a reasonable approach, for two reasons: (1) the logs have different vertical resolutions, and (2) because a suite of logs generally requires more than one logging “run” out of the borehole, some logs differ slightly in depth-registry of beds. This approach also allows the interpreter to provide data for the most optimistic interpretation that can be made, in the context of the given data values.

170

ASQUITH AND KRYGOWSKI

Table 10.1. Case Study 1: Atoka Sandstone, Permian Basin, U.S.A.: Work table.

The work table shows values of the raw data—extracted from Figures 10.1 and 10.2—and sample calculations for several depths. You should verify this operating assumption: your reading of the logs produces the "same" values for the original data, and for the calculated quantities. The values may differ, but they should be close. As you work through the problem, do the calculations, to ensure that you understand the mechanics of the computations and of the plots. The symbol "v/v" indicates volume-for-volume decimal fraction.

|  Parameters  |   |   |   |
| --- | --- | --- | --- |
|  Ann. Mean Surf. Temp: 75°F |   |   | Rw (measured): (not given)  |
|  Total Depth: 15,962 ft |   |   | Rw @ fm. temp.: 0.065 ohm-m @ °F  |
|  Bottom Hole Temp: 197°F |   |   | Rmf (measured): 1.34 ohm-m @ 87°F  |
|  Formation Depth: 14,600 ft |   |   | Rmf @ fm. temp.: 0.65 ohm-m @°F  |
|  Formation Temperature: 187°F |   |   |   |
|  GRclean: 15 API |   |   | GRshale: 65 API  |
|   | a: 0.81 | m: 2 | n: 2  |

|  Raw data  |   |   |   |   |   |
| --- | --- | --- | --- | --- | --- |
|  Depth feet | ILD ohm-m | ILM ohm-m | LL8 ohm-m | DPHI v/v decimal | NPHI v/v decimal  |
|  14,604 | 130 | 260 | 510 | 0.180 | 0.068  |
|  14,607 | 160 | 240 | 1100 | 0.214 | 0.064  |
|  14,609 | 190 | 210 | 1300 | 0.185 | 0.070  |
|  14,613 | 300 | 410 | 1500 | 0.260 | 0.085  |
|  14,618 | 160 | 250 | 520 | 0.245 | 0.100  |
|  14,622 | 110 | 100 | 190 | 0.215 | 0.115  |

|  Rt from tornado chart  |   |   |   |   |   |
| --- | --- | --- | --- | --- | --- |
|  Depth feet | ILM/ILD | LL8/ILD | Rt/ILD | Rt ohm-m | Rt min ohm-m  |
|  14,604 | 2.00 | 3.92 | 0.46 | 59.8 | 51  |
|  14,607 |  |  |  |  |   |
|  14,609 |  |  |  |  |   |
|  14,613 | 1.37 | 5.00 | 0.92 | 266.8 | 150  |
|  14,618 |  |  |  |  |   |
|  14,622 | 0.91 | 1.73 | 1.00 | 110.0 | 19  |

|  Calculations  |   |   |   |   |   |   |   |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  Depth feet | PhiNDgas v/v decimal | Swa v/v decimal | Sxo v/v decimal | BVW | ROS v/v decimal | MOS v/v decimal | MHI  |
|  14,604 | 0.136 | 0.242 | 0.262 | 0.033 | 0.738 | 0.020 | 0.924  |
|  14,607 |  |  |  |  |  |  |   |
|  14,609 |  |  |  |  |  |  |   |
|  14,613 | 0.193 | 0.081 | 0.108 | 0.016 | 0.892 | 0.027 | 0.750  |
|  14,618 |  |  |  |  |  |  |   |
|  14,622 | 0.172 | 0.141 | 0.339 | 0.024 | 0.661 | 0.198 | 0.416  |

Log Interpretation Case Studies

171

![img-22.jpeg](img-22.jpeg)

![img-23.jpeg](img-23.jpeg)

Environmental information:

Total depth = 15,962 ft

bottom hole temperature (BHT) = 197°F (maximum recorded temperature)

bit diameter = 8½ in.

type of fluid in hole = freshwater mud

R_Hf at measured temperature = 1.34 ohm-m at 87°F

R_Hs at measured temperature = 3.34 ohm-m at 87°F

R_M at measured temperature = 1.67 ohm-m at 87°F

Note the following attributes of the logs in the interval from 14,600 ft to 14,625 ft.

1) Resistivity curves in tracks 2 and 3 show high resistivities.
2) Gamma ray count in the Atoka Sandstone interval (track 1, dashed line) is less than that in shales above and below.
3) The SP curve (track 1, solid line) shows evidence of hydrocarbon suppression, especially in the upper part of the zone. (If water saturation were 100%, the shape of the SP curve would be strongly similar to the shape of the gamma ray curve. If the zone were shaly and water saturation were 100%, the gamma ray curve would mimic the shape of the SP curve shown here.)

Figure 10.1. Dual induction laterolog 8 with spontaneous potential log and gamma ray log, Atoka Sandstone, Permian Basin, U.S.A.

This log, and those that follow in this and the other case studies, are displayed in what is commonly referred to as a "standard API format." The format, from the American Petroleum Institute, is described from left to right as:

Track 1, generally displaying correlation logs (SP, gamma ray, and caliper);

Depth Track, showing the depths of the log readings;

Track 2, which shows the main measurements, such as resistivity; and

Track 3, which also shows main measurements, such as porosity.

Commonly, as in this figure and in Figure 10.2, tracks 2 and 3 are combined for a single display. In this figure the tracks show resistivity over four decades of values, with no physical distinction mode of the boundary between tracks 2 and 3. Even when this type of combined display is used, it is common practice to reference the combined track to the right of the depth track as "tracks 2 and 3."

In this log, and in the other logs shown in this chapter, depth is indicated by a fine line every 2 ft, a medium-thick line every 10 ft, and a heavy line every 50 ft.

172

ASQUITH AND KRYGOWSKI

![img-24.jpeg](img-24.jpeg)

Figure 10.2. Combination neutron-density log with gamma ray log and caliper log, Atoka Sandstone, Permian Basin, U.S.A.

Neutron and density porosities were recorded in sandstone-porosity units.

Note the following attributes of the logs in the stratigraphic interval from 14,600 ft to 14,625 ft.

1) Mudcake is shown by the caliper curve (CALI) in track 1; the hole diameter is smaller than the diameter of the bit \((8\frac{1}{2}\) in.).
2) Strong gas effect is shown in tracks 2 and 3. The density-porosity curve (DPHI) shows much higher porosities than the neutron-porosity curve (NPHI), and both logs show high porosity.

Log Interpretation Case Studies

173

# Case Study 1:

# PENNSYLVANIAN ATOKA SANDSTONE, PERMIAN BASIN, U.S.A.:

## The Solution.

Information from the well site produced the following positive indicators: (1) Probable permeability, due to the coarseness and friability of the formation, and (2) gas bubbles in the bit cuttings and gas indicated by the mudlogger's chromatograph. The information also produced this negative indicator: decrease in the drilling rate through the sandstone, which might indicate that porosity and permeability are less than assumed from inspection of the cuttings.

Careful examination of the logs recorded through the Atoka Sandstone provided the following information:

- The gamma ray curve (Figure 10.1) shows a fairly consistent low value (slightly greater than 15 API units) through the sandstone, which indicates that the sandstone is clean.
- The SP curve (Figure 10.1) is deflected less in the upper part of the formation than in the lower part. This could be due to shaliness, hydrocarbon suppression, or both. Because the gamma ray curve is fairly constant and at low values, hydrocarbon suppression is the most likely cause.
- Resistivity curves all show high values. In this borehole, mud filtrate resistivity is greater than formation water resistivity; the invasion pattern of resistivity curves is characteristic of hydrocarbon-bearing rock \((\mathrm{ILD} < \mathrm{ILM} < \mathrm{LL8})\). (Compare Figure 10.1 with Figure 1.8.)
- The caliper curve (Figure 10.2), shows mudcake. Opposite the Atoka Sandstone, the diameter of the borehole is markedly smaller than above or below, and the diameter of the hole is less than the diameter of the drill bit (see BitSize line). This mudcake is important evidence: it formed by accumulation of solid particles on walls of the borehole, as drilling mud invaded porous and permeable rock.
- The neutron-log and density-log responses (NPHI and DPHI) through the sandstone support the presumption that the hydrocarbons are gas; the density curve reads much higher porosity than the neutron log—"crossover," due to gas in the formation. (See Figure 4.10.)
- Visual examination of the neutron-porosity and density-porosity curves indicates porosity of

about 0.15 (15%), which should be sufficient for production of gas.

To derive more information from the data, calculations can be made. The Static SP (SSP) can be calculated by Equation 10.20:

$$
\begin{array}{l}
SSP = -K \times \log \left( \frac{R_{mf}}{R_w} \right) \\
\quad = -(60 + (0.133 \times 187)) \times \log \left( \frac{0.65}{0.065} \right) \\
\quad = -84.87 \text{ mV}
\end{array}
$$

The maximal $SP$ in the sandstone, near the bottom of the zone, is about $-30 \text{ mV}$. Comparison of the recorded $SP$ with the *Static SP* leads to the conclusion that the SP curve is suppressed throughout the Atoka Sandstone. This suppression denotes the presence of hydrocarbons.

Next, calculate porosity from the neutron and density logs. Because gas in the formation is indicated by the porosity-curve crossover, Equation 10.18 should be used to calculate gas-corrected porosity, (*PhiND-gas*). In the six intervals to be analyzed, calculated porosity ranges from slightly less than 14% to approximately 19% (Table 10.2).

Water saturation is the next calculation, but before Archie's equation is used, resistivity should be corrected for effects of invasion. A tornado chart (Figure 10.3) is used to determine true formation resistivity ($R_t$) from the deep induction, medium induction, and laterolog-8 measurements of resistivity. The section in the work table (Table 10.1) labeled "Rt from tornado chart" shows ratios to be calculated, ratios to be read from the chart, and the resulting value of $R_t$. The caption of Figure 10.3 explains how to use the chart.

An alternate method to determine true formation resistivity is to calculate $R_{tmin}$ (Equation 10.19). As explained in Chapter 5, $R_{tmin}$ is compared to $R_t$ from tornado-chart calculations, and at any depth the greater of the two is used as the best estimate of $R_t$. In this case, for all depths, the value of $R_t$ from the tornado charts is greater than $R_{tmin}$, so the tornado-chart values are used (Table 10.2).

The Archie equation (Equation 10.1) is used to calculate water saturation (noted here as $S_{wa}$, to distinguish it from water saturation estimated by the ratio method, $S_{wr}$). $R_t$ is used for the measurement of resistivity, and PhiNDgas (derived from the neutron and density porosity logs) is used for the quantity of porosity. The values for $R_w$ and the Archie parameters are listed above, under the topic "Well site information

174

ASQUITH AND KRYGOWSKI

and other pertinent information." The estimates of water saturation are consistently low (Table 10.2), which is an indication that the reservoir may be at irreducible water saturation. The flushed zone water saturation ($S_{xo}$) is also calculated from Archie's equation, with $R_{mf}$ substituted for $R_w$, and $R_{xo}$ substituted for $R_t$. For the calculations in this case study, the laterolog 8 (LL8) values should be used for $R_{xo}$.

Bulk volume water ($BVW$) is calculated from Equation 10.5. It shows low, fairly consistent values for all the zones, suggesting—as do the water saturations—that the formation is at irreducible water saturation. Figure 10.4 shows $BVW$ graphically, by the plot of water saturation ($S_{wa}$) versus porosity ($PhiNDgas$). A large sample of points plots near the line that is equivalent to $BVW$ of 0.02. Clustering of points around a constant $BVW$ line supports the conclusion that the reservoir is at irreducible water saturation.

Another crossplot that provides supportive information is Figure 10.5. Porosity is plotted against water saturation, with estimates of permeability (derived from Equation 7.31) superimposed on the data. The plot indicates that permeability of the sandstone may be very good, especially if the reservoir is at irreducible water saturation, as indicated by water saturations and $BVW$ values (Table 10.2 and Figure 10.4).

The increase in penetration rate downward through the Atoka was unfavorable information; there is additional negative information. Residual oil saturations (ROS), calculated by Equations 10.2 and 10.6, are high (Table 10.2). This fact is anomalous because other evidence, discussed above, supports the conclusion that the reservoir has high porosity and permeability. Ordinarily, under these conditions of porosity and permeability, mobility of hydrocarbons would be expected. Furthermore, calculations of moveable oil saturation ($MOS$) (Equation 10.7), produce low values (Table 10.2). Initially, this is puzzling; in a reservoir with high porosity and permeability, moveable oil saturation should be high. Additional anomalous information is produced by calculation of the moveable hydrocarbon index ($MHI$) (Equation 10.4 and Table 10.2). Most values are greater than 0.7, but in the general case, movable hydrocarbon indices of productive reservoirs are less than 0.7. Analyses of $ROS$, $MOS$, and the moveable hydrocarbon index $MHI$ suggest that hydrocarbons will not move. Indeed, all these factors give notice that most of the hydrocarbons would remain in place, in the reservoir.

In the initial evaluation of logs, information about inadequate moveability of hydrocarbons should not be ignored; however, sometimes evidence of deficient moveability can be explained in the following way. In

the case at hand, what is significant is the high residual gas saturation in the flushed zone ($1.0 - S_{xo} =$ residual hydrocarbon saturation, ($ROS$) (Equation 10.6)). High residual gas saturation is the result of bypassing of gas by drilling fluids during invasion of a reservoir. Residual gas saturation can be read and interpreted erroneously by the logs as being the consequence of stationary hydrocarbons.

You were justifiably concerned about negative information from the drill-penetration rate, and the pessimistic moveability data. Nevertheless, you decided that when considered altogether, evidence of shows in bit cuttings, gas shows recorded by the mud logger, and qualitative and quantitative log interpretation overrode the negative evidence and supported the decision to set pipe. Log-interpretation information that was especially significant to your decision included:

- high porosities shown on the neutron-density logs;
- strong gas effect on the display of the neutron-density logs;
- low water saturation, calculated by the Archie equation;
- high log-derived permeabilities, from crossplots; and
- low bulk-volume-water values.

Although you believe that the well penetrated a gas-filled reservoir, you are quite interested in whether the well would be a commercial success. Equation 10.11 is used to calculate volumetric gas reserves. Estimated gas recovery of 11 BCF is calculated by using the following parameters:

- geothermal gradient \(= 0.014^{\circ} / \mathrm{ft}\times\) formation depth;
- pressure gradient \(= 0.35\) psi/ft \(\times\) formation depth;
- drainage area \(= 560\) acres;
reservoir thickness \(= 15\) ft;
- effective porosity \(= 0.15\) (15%);
water saturation \(= 0.13\) (13%);
- gas gravity \(= 0.65\)
recovery factor \(= 0.85\)
- formation temperature \(= 205^{\circ}\mathrm{F}\)
- initial bottom hole pressure \(= 5,117\) psi; and the
Z factor \(= 0.988\)

The Atoka Sandstone was perforated from 14,610 ft to 14,615 ft. The calculated absolute open flow ($CAOF$) was 21,900,000 cu ft of gas per day (21,900

Log Interpretation Case Studies

175

mcfgpd) with a high shut-in tubing pressure (*SITP*) of 3758 pounds per square inch (psi) and a high initial bottom hole pressure (*IBHP*) of 5556 psi. The gas gravity was 0.599 at bottom hole temperature of 219°F. The well’s first-year cumulative production was 3,268,129 mcf plus 95,175 barrels of condensate.

Figure 10.6 is a computer-derived log of the Atoka Sandstone. It shows calculated porosity (*PhiNDgas*)

and water saturation ($S_{wa}$), among other calculated values. Log displays containing both raw and calculated values are available at the well site, either during or immediately after data acquisition. The same calculations and displays can be made by commercially available software packages; however, the calculated results are only as accurate and reliable as the log data and the parameters that are used for computations.

176

ASQUITH AND KRYGOWSKI

Table 10.2. Case Study 1: Atoka Sandstone, Permian Basin, U.S.A.: Solution table. The symbol "v/v" indicates volume-for-volume decimal fraction.

|  Parameters  |   |   |   |
| --- | --- | --- | --- |
|  Ann. Mean Surf. Temp: 75°F |   |   | Rw (measured): (not given)  |
|  Total Depth: 15,962 ft |   |   | Rw @ fm. temp.: 0.065 ohm-m @ °F  |
|  Bottom Hole Temp: 197°F |   |   | Rmf (measured): 1.34 ohm-m @ 87°F  |
|  Formation Depth: 14,600 ft |   |   | Rmf @ fm. temp.: 0.65 ohm-m @ °F  |
|  Formation Temperature: 187°F |   |   |   |
|  GRclean: 15 API |   |   | GRshale: 65 API  |
|   | a: 0.81 | m: 2 | n: 2  |

|  Raw data  |   |   |   |   |   |
| --- | --- | --- | --- | --- | --- |
|  Depth feet | ILD ohm-m | ILM ohm-m | LL8 ohm-m | DPHI v/v decimal | NPHI v/v decimal  |
|  14,604 | 130 | 260 | 510 | 0.180 | 0.068  |
|  14,607 | 160 | 240 | 1100 | 0.214 | 0.064  |
|  14,609 | 190 | 210 | 1300 | 0.185 | 0.070  |
|  14,613 | 300 | 410 | 1500 | 0.260 | 0.085  |
|  14,618 | 160 | 250 | 520 | 0.245 | 0.100  |
|  14,622 | 110 | 100 | 190 | 0.215 | 0.115  |

|  Rt from tornado chart  |   |   |   |   |   |
| --- | --- | --- | --- | --- | --- |
|  Depth feet | ILM/ILD | LL8/ILD | Rt/ILD | Rt ohm-m | Rt min ohm-m  |
|  14,604 | 2.00 | 3.92 | 0.46 | 59.8 | 51  |
|  14,607 | 1.50 | 6.88 | 0.88 | 140.8 | 110  |
|  14,609 | 1.11 | 6.84 | 0.99 | 188.1 | 150  |
|  14,613 | 1.37 | 5.00 | 0.92 | 266.8 | 150  |
|  14,618 | 1.56 | 3.25 | 0.70 | 112.0 | 52  |
|  14,622 | 0.91 | 1.73 | 1.00 | 110.0 | 19  |

|  Calculations  |   |   |   |   |   |   |   |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  Depth feet | PhiNDgas v/v decimal | Swa v/v decimal | Sxo v/v decimal | BVW | ROS v/v decimal | MOS v/v decimal | MHI  |
|  14,604 | 0.136 | 0.242 | 0.262 | 0.033 | 0.738 | 0.020 | 0.924  |
|  14,607 | 0.158 | 0.122 | 0.138 | 0.019 | 0.862 | 0.016 | 0.884  |
|  14,609 | 0.140 | 0.120 | 0.144 | 0.017 | 0.856 | 0.024 | 0.832  |
|  14,613 | 0.193 | 0.081 | 0.108 | 0.016 | 0.892 | 0.027 | 0.750  |
|  14,618 | 0.187 | 0.116 | 0.170 | 0.022 | 0.830 | 0.054 | 0.681  |
|  14,622 | 0.172 | 0.141 | 0.339 | 0.024 | 0.661 | 0.198 | 0.416  |

Log Interpretation Case Studies

177

![img-25.jpeg](img-25.jpeg)

Figure 10.3. Tornado chart, for determination of true formation resistivity ($R_t$) from measurements of induction resistivity and the laterolog 8.

Procedure for using this chart is as follows. The numbers were extracted from Table 10.1, at 14,613 ft.

1. Calculate two ratios from the raw resistivity data:

a. ILM/ILD = 410/300 = 1.37, and
b. LL8/ILD = 1500/300 = 5.

2. Plot the ratios on the tornado chart: ILM/ILD on the X-axis, and LL8/ILD on the Y-axis.
3. At the intersection point, read and record the following values:

a. From the heavy, solid black lines (nearly horizontal), $R_{xo}/R_t = 7.8$.
b. From the light, dashed black lines (nearly vertical), diameter of invasion, $d_l = 42$ in.
c. From the light, solid red lines (nearly vertical), $R_t/R_{ILd} = 0.94$.

4. From the ratios that were recorded from the tornado chart:

a. $R_t = (R_t/R_{ILd}) \times ILD = 0.94 \times 300 = 282$ ohm·m.
b. $R_{xo} = (R_{xo}/R_t) \times R_t = 7.8 \times 282 = 2200$ ohm·m.

5. Diameter of invasion at that point, $d_l = 42$ in.

The tornado chart for the induction log assumes that invasion follows a step profile, and that neither transition zones nor an annulus exist. In practice, invasion corrections using the tornado chart are often applied even when a transition zone is apparent. In this well, attempting to apply an invasion correction over the interval from 14,600 to 14,603 ft will result in points that plot outside the tornado chart. In this example, the maximum correction on the chart ($R_t/ILd = 0.4$) was applied to the deep induction log. Also, the tornado-chart readings could be ignored and the deep-induction reading used, because of the anomalous pattern of the curves. From 14,603 to 14,607 ft, invasion caused a significant difference between $R_{ILd}$ and $R_t$, whereas below 14,607 ft, the differences were minimal. This is shown in Figure 10.6

178

ASQUITH AND KRYGOWSKI

Figure 10.4. Bulk-volume-water crossplot ($S_{wa}$ vs. $P_{lb}$), Atoka Sandstone, Permian Basin, U.S.A.

![img-26.jpeg](img-26.jpeg)

Figure 10.5. Crossplot, water saturation ($S_{wa}$) versus porosity ($P_{lb}$), for estimating permeability, Atoka Sandstone, Permian Basin, U.S.A.

The estimate of permeability is valid only if water saturation is irreducible. Permeability lines were extracted from Timur (1968). Permeability is scaled in millidarcies.

![img-27.jpeg](img-27.jpeg)

Log Interpretation Case Studies

179

![img-28.jpeg](img-28.jpeg)

Figure 10.6. Computer-processed evaluation log, Atoka Sandstone, Permian Basin, U.S.A.

In the interval from 14,600 ft to 14,625 ft, note:

1) In track 1, volume of shale (Vshale) was calculated from the gamma ray log. These criteria were the basis for calculation: \( GR_{\mathrm{clean}} = 15 \) API units; \( GR_{\mathrm{shale}} = 65 \) API units.
2) In track 2, shading emphasizes the separation between resistivity of the sandstone at water saturation of \(100\%\) \((R_{\mathrm{s}})\) and true formation resistivity \((R_{\mathrm{f}})\), as derived from the deep resistivity (ILD), which shows the presence of hydrocarbons. The greater the separation, the greater the hydrocarbon saturation.
3) In track 3, these five important quantities are shown, in order from left to right: (1) water saturation of the uninvaded zone, computed by the ratio method \((S_{\mathrm{up}})\); (2) water saturation of the uninvaded zone, computed by the Archie method \((S_{\mathrm{up}})\); (3) the differential caliper log (DiffCal), which is the caliper value minus the bit size; (4) porosity (PhiNDgas); and (5) bulk volume water (BVW). The black area (between PhiNDgas and BVW) shows the proportion of pore space occupied by hydrocarbons (in this instance, gas). The gray area (between BVW and zero, at the track edge) shows the proportion of pore space occupied by water.

180

ASQUITH AND KRYGOWSKI

# Case Study 2:

# MISSISSIPPIAN MISSION CANYON FORMATION, WILLISTON BASIN, U.S.A.:

# The Problem.

Case Study 2 illustrates the interpretation of mixed-lithology carbonate rock. Some lithology-porosity crossplots are used to confirm the types of rock seen in a core. For the various crossplots the stratigraphic interval is divided into two zones, based on the production potential estimated from observation of the logs.

# Background

A wildcat well is in progress in the Williston Basin, to be drilled to the Ordovician Red River Formation. As drilling proceeds, two zones are encountered that have hydrocarbon shows—the Mississippian Mission Canyon and the Devonian Duperow. The well has just penetrated the Devonian Duperow, the second “show” zone. A decision is made to stop and drill-stem test (DST) the Duperow. Unfortunately, the drill-stem-test tool is stuck in the borehole. Several attempts are made to remove the tool but none succeed. Meanwhile, collapse of the borehole wall (caving) begins.

Now you face the choice of either halting drilling—with hope that the first show zone, the Mississippian Mission Canyon Formation, might be a productive reservoir—or continuing efforts to remove the DST tool. If the “fish” (the stuck DST tool) is removed from the hole successfully, the Duperow can be tested and the hole can be deepened to the Red River Formation. However, more attempts to recover the fish undoubtedly will lead to further deterioration of the hole, and logging measurements taken when walls of the borehole are enlarged may be unreliable. Also, the DST tool might not be dislodged.

Because the well is a wildcat, you made a decision several weeks ago to core the Mission Canyon. The Mission Canyon is at approximately 9297 ft to 9409 ft. Rock was cored from 9302 ft to 9358 ft. Twenty-five feet of oil-stained, fractured, microcrystalline dolomite was recovered; the remaining core consisted of microcrystalline limestone and anhydrite. After coring, several drill-stem tests were tried; when none were successful, drilling was resumed.

You decided that information from coring is favorable enough to halt drilling, to log to the top of the fish while hole conditions seem still to be reasonably good, and then to assess the potential of the Mission Canyon

for production of oil and gas. Your company agrees with your suggestion to run a very complete log package, because the well is exploratory and carbonate rocks commonly are more difficult to evaluate than sandstones. The logs are shown in Figures 10.7, 10.8, and 10.9.

# Well site information and other pertinent information:

- mean annual surface temperature = 40°F
- formation temperature ($T_f$) = 207°F
- formation water resistivity ($R_w$) at $T_f$ = 0.023 ohm-m
- mud filtrate resistivity ($R_{mf}$) at $T_f$ = 0.017 ohm-m
- $Dt_{fl}$ = 185 μsec/ft, the acoustic-wave fluid transit time of saltwater mud filtrate
- $RHO_{fl}$ = 1.1 gm/cc, which is the density of saltwater mud filtrate
- tortuosity factor ($a$) = 1, cementation exponent ($m$) = 2, and saturation exponent ($n$) = 2

Preliminary examination of the logs indicates that several zones in the Mission Canyon are quite porous. Log data and core data indicate that the zone is potentially productive. A reliable estimate of the amount of oil in place is needed; but first, verify the quality of the log data, confirm the estimate of formation water resistivity, and calculate porosity and fluid saturations.

# Tasks required for interpretation of the logs

- General comparison of lithologies described from the core with lithologies predicted from the logs would give you some opinion about whether the logging tools operated properly. The neutron porosity-density porosity and neutron porosity-sonic interval transit time crossplots would provide the necessary information. In addition, a mineral identification (“MID”) plot (apparent matrix density, $RHO_{maa}$, vs. apparent matrix traveltime, $DT_{maa}$) and an M-N lithology plot would test the proposition that the rock is composed of more than two significant minerals. Also, neutron-density crossplot porosity can be estimated from the neutron-density crossplot. This quantity (shown in the crossplots as $PHIE$, effective porosity) will be used in later calculations.
- To confirm the estimate of formation water saturation ($R_w$) several methods could be used. Apparent water resistivity ($R_{wa}$) generally is dependable, but in this case the most useful

Log Interpretation Case Studies

181

method is a Pickett plot, a plot of formation resistivity against porosity. Not only would it indicate the water saturations of the zones of interest, it also would evaluate the number that was used for formation water resistivity ($R_w$), and the estimated cementation exponent ($m$). (Again, both methods are shown in the answer section for completeness.)

- Calculate water saturation of the formation ($S_w$), and use $S_w$ and PHIE to calculate bulk volume water (BVW) and create a BVW plot.
- Other useful quantities are moveable hydrocarbon index (MHI), moveable hydrocarbon saturation (MOS), and residual hydrocarbon saturation (ROS), all of which are indicators of producibility.
- Finally, calculate the volume of oil in place; use Equation 10.8.

Because information about porosity is required for the Pickett plot, and because the neutron-density crossplot porosity is the best choice, start with lithology-porosity crossplots. Work tables 10.3a, 10.3b, and 10.3c provide a start for measuring the log values.

Useful equations:

Apparent matrix density, RHOmaa:

$$\rho_{maa} = \frac{\rho_b - \phi_{ND} \times \rho_{fl}}{1 - \phi_{ND}} \quad 10.21 \text{ (Equation 4.11)}$$

Apparent matrix traveltime, DTmaa:

$$\Delta t_{maa} = \frac{\Delta t - \phi_{NS} \times \Delta t_{fl}}{1 - \phi_{NS}} \quad 10.22 \text{ (Equation 4.12)}$$

Lithology $M$:

$$M = \frac{\Delta t_{fl} - \Delta t}{\rho_b - \rho_{fl}} \times 0.01$$

$$\left( M = \frac{\Delta t_{fl} - \Delta t}{\rho_b - \rho_{fl}} \times 0.003 \text{ (metric)} \right) \quad \text{(Equation 4.9)} \quad 10.23$$

Lithology $N$:

$$N = \frac{\phi_{Nfl} - \phi_N}{\rho_b - \rho_{fl}} \quad 10.24 \text{ (Equation 4.10)}$$

Apparent water resistivity, $R_{wa}$:

$$R_{wa} = \frac{R_t \times \phi^m}{a} \quad 10.25 \text{ (Equation 7.16)}$$

Table 10.3a. Case Study 2: Mission Canyon Formation, Williston Basin, U.S.A.: Raw data work table. The symbol "v/v" indicates volume-for-volume decimal fraction.

|  **Parameters**  |   |   |   |   |
| --- | --- | --- | --- | --- |
|  Ann. Mean Surf. Temp: 40°F |   |   |   | Rw (measured): (not given)  |
|  Total Depth: 11,122 ft |   |   |   | Rw @ fm. temp.: 0.023 ohm-m @ 207°F  |
|  Bottom Hole Temp: (thermometer failed) |   |   |   | Rmf (measured): 0.046 ohm-m @ 74°F  |
|  Formation Depth: 9,300 ft |   |   |   | Rmf @ fm. temp.: 0.017 ohm-m @ 207°F  |
|  Formation Temperature: 207°F |   |   |   |   |
|  DT matrix (Wyllie): 47.6 μsec/ft |   |   |   | DT fluid (Wyllie): 185 μsec/ft  |
|  RHO matrix: 2.71 g/cm³ |   |   |   | RHO fluid: 1.1 g/cm³  |
|  PHIN fluid: 1 |   |   |   |   |
|   | a: 1 | m: 2 | n: 2 |   |

182

ASQUITH AND KRYGOWSKI

Table 10.3a. Case Study 2: Mission Canyon Formation, Williston Basin, U.S.A.: Raw data work table. The symbol "v/v" indicates volume-for-volume decimal fraction. (Cont'd.)

|  Raw data  |   |   |   |   |   |   |
| --- | --- | --- | --- | --- | --- | --- |
|  Depth feet | ILD ohm-m | ILS ohm-m | MSFL ohm-m | DT μsec/ft | DPHI v/v decimal | NPHI v/v decimal  |
|  9,310 | 26 | 20.5 | 1.2 | 63 | 0.090 | 0.260  |
|  9,322 |  |  |  |  |  |   |
|  9,326 | 17 | 8.3 | 3.8 | 53.5 | 0.030 | 0.120  |
|  9,332 | 9 | 6.1 | 2.4 | 58 | 0.050 | 0.140  |
|  9,335 |  |  |  |  |  |   |
|  9,347 |  |  |  |  |  |   |
|  9,353 |  |  |  |  |  |   |
|  9,362 |  |  |  |  |  |   |
|  9,367 | 22 | 16 | 8.8 | 52.5 | -0.015 | 0.125  |
|  9,373 | 11 | 7.7 | 3.5 | 53.5 | 0.000 | 0.155  |
|  9,376 |  |  |  |  |  |   |
|  9,383 |  |  |  |  |  |   |
|  9,387 |  |  |  |  |  |   |
|  9,398 |  |  |  |  |  |   |
|  9,406 | 5.1 | 3.5 | 2.2 | 55 | 0.030 | 0.150  |

Table 10.3b. Case Study 2: Mission Canyon Formation, Williston Basin, U.S.A.: Work table for determination of lithology. The symbol "v/v" indicates volume-for-volume decimal fraction.

|  Lithology Calculations  |   |   |   |   |   |   |   |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  Depth feet | RHOB g/cm³ | PhiNDxpt v/v decimal | RHOmaa g/cm³ | PhiNSxpt v/v decimal | DTmaa μsec/ft | M | N  |
|  9,310 | 2.57 | 0.170 | 2.865 | 0.145 | 42.3 | 0.833 | 0.505  |
|  9,322 |  |  |  |  |  |  |   |
|  9,326 | 2.66 | 0.075 | 2.788 | 0.065 | 44.4 | 0.842 | 0.563  |
|  9,332 | 2.63 | 0.095 | 2.790 | 0.090 | 45.4 | 0.830 | 0.562  |
|  9,335 |  |  |  |  |  |  |   |
|  9,347 |  |  |  |  |  |  |   |
|  9,353 |  |  |  |  |  |  |   |
|  9,362 |  |  |  |  |  |  |   |
|  9,367 | 2.73 | 0.060 | 2.838 | 0.060 | 44.0 | 0.811 | 0.535  |
|  9,373 | 2.71 | 0.085 | 2.860 | 0.070 | 43.6 | 0.817 | 0.525  |
|  9,376 |  |  |  |  |  |  |   |
|  9,383 |  |  |  |  |  |  |   |
|  9,387 |  |  |  |  |  |  |   |
|  9,398 |  |  |  |  |  |  |   |
|  9,406 | 2.66 | 0.090 | 2.816 | 0.075 | 44.5 | 0.832 | 0.544  |

Log Interpretation Case Studies

183

Table 10.3c. Case Study 2: Mississippian Mission Canyon Formation, Williston Basin, U.S.A.: Work table for calculation of water saturation and other estimators. The symbol "v/v" indicates volume-for-volume decimal fraction.

|  Saturation and other calculations  |   |   |   |   |   |   |   |   |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  Depth feet | Rwa ohm-m | Ro ohm-m | Sw v/v decimal | Sxo v/v decimal | MHI v/v decimal | MOS v/v decimal | ROS v/v decimal | BVW  |
|  9,310 | 0.751 | 0.8 | 0.166 | 0.700 | 0.237 | 0.534 | 0.300 | 0.028  |
|  9,322 |  |  |  |  |  |  |  |   |
|  9,326 | 0.096 | 4.1 | 0.490 | 0.892 | 0.550 | 0.401 | 0.108 | 0.037  |
|  9,332 | 0.081 | 2.5 | 0.532 | 0.886 | 0.601 | 0.354 | 0.114 | 0.051  |
|  9,335 |  |  |  |  |  |  |  |   |
|  9,347 |  |  |  |  |  |  |  |   |
|  9,353 |  |  |  |  |  |  |  |   |
|  9,362 |  |  |  |  |  |  |  |   |
|  9,367 | 0.079 | 6.4 | 0.539 | 0.733 | 0.736 | 0.194 | 0.267 | 0.032  |
|  9,373 | 0.079 | 3.2 | 0.538 | 0.820 | 0.656 | 0.282 | 0.180 | 0.046  |
|  9,376 |  |  |  |  |  |  |  |   |
|  9,383 |  |  |  |  |  |  |  |   |
|  9,387 |  |  |  |  |  |  |  |   |
|  9,398 |  |  |  |  |  |  |  |   |
|  9,406 | 0.041 | 2.8 | 0.746 | 0.977 | 0.764 | 0.231 | 0.023 | 0.067  |

184

ASQUITH AND KRYGOWSKI

![img-29.jpeg](img-29.jpeg)

Figure 10.7. Dual laterolog-MSFL with gamma ray log and caliper log, Mission Canyon Formation, Williston Basin, U.S.A.

From 9308 ft to 9408 ft: Note the separation of the three resistivity logs, which read the following resistivities: lowest resistivity, MSFL ($R_{10}$), intermediate resistivity, LLS ($R_i$), and highest resistivity, LLD ($R_i$). On a Dual Laterolog-MSFL this type of resistivity profile indicates presence of hydrocarbons (see Chapter 1).

Log Interpretation Case Studies

185

![img-30.jpeg](img-30.jpeg)

Figure 10.8. Combination neutron-density log with gamma ray log and caliper log, Mission Canyon Formation, Williston Basin, U.S.A.

From 9308 ft to 9408 ft, porosities recorded by the neutron (NPHI) and density (DPHI) curves are high. Both are recorded in limestone units, in tracks 2 and 3. The neutron log reads higher porosity than the density log, indicating that the rock is dolomite.

![img-31.jpeg](img-31.jpeg)

Figure 10.9. Sonic log with gamma ray log and caliper log, Mission Canyon Formation, Williston Basin, U.S.A.

From 9308 ft to 9408 ft, note that zones of porous rock are numerous. (They are indicated by increase of interval transit time (DT) in tracks 2 and 3.)

186

ASQUITH AND KRYGOWSKI

# Case Study 2:

# MISSISSIPPIAN MISSION CANYON FORMATION, WILLISTON BASIN, U.S.A.:

# The Solution.

Information from the logs and cores produced the following positive indicators: (1) 25 ft of oil-stained core, (2) porous zones, indicated on the neutron-density and sonic logs, and (3) separation of curves on resistivity logs, indicative of invasion in the porous zones. The information also produced this negative indicator: evidence that water saturation is greater in the lower part of the logged interval.

In this case, there is no significant conflicting information; all information points to the presence of hydrocarbons in the rock. Therefore, the task is composed of two parts: (1) to assess the quality of the logs and of the well site processing, so that a confident estimate of the oil in place can be made, and then (2) to judge whether the Mission Canyon is a reservoir that will produce oil and gas in volumes sufficient for a suitable return on investment.

# Information from the logs

The log package run in this well is complete; it includes a suite for measurement of resistivity, and a combination neutron-density log and a sonic log for measurement of porosity and estimation of lithology.

Because walls of the borehole have caved, your assessment begins with a careful check of the caliper curve, CALI (Figure 10.8). The caliper log shows relatively constant hole diameter and no significant, differential enlargement. Consistency of the hole diameter indicates that log measurements should be reliable.

The next step in evaluation includes examination of the resistivity logs (Figure 10.7). The salt-saturated drilling mud ($R_{mf} \sim R_w$) necessitated using a dual laterolog with a microspherically focused log (MSFL). The MSFL measures resistivity of the flushed zone ($R_{xo}$), whereas the shallow laterolog (LLS) and deep laterolog (LLD) measure resistivities of the invaded ($R_i$) and uninvaded ($R_t$) zones, respectively.

Next, scrutinize the resistivity curves to identify invasion profiles; they are useful for location of zones that merit detailed analysis.

Between 9308 ft and 9409 ft, the resistivity curves (MSFL, LLS, and LLD) show different values of $R_{xo}$, $R_i$, and $R_t$; the curves are separated. The separation suggests that the rock is invaded, and that hydrocarbons are in the porous and permeable zones. (If the

curves were not separated you could conclude that either the formation wasn't invaded, or that hydrocarbons were not present.)

Also, note that the zones of porous rock low in the formation (9370 ft to 9409 ft) show less separation between the MSFL and the deep laterolog, LLD. The lessening of separation in the lower zones indicates higher water saturations. (Remember: Higher water saturations mean lower hydrocarbon saturations.)

Porous and permeable zones in the interval from 9308 ft to 9409 ft are identified by inspecting the neutron-density log (Figure 10.8) and the sonic log (Figure 10.9); more than eleven zones of porous and permeable rock can be identified. On the neutron-density log (Figure 10.8), the zones of porosity and permeability are evident as concurrent increase in neutron porosity (NPHI) and density porosity (DPHI). They are identified on the sonic log by increase in the interval transit time (DT).

# Information from crossplots

As evaluation of the Mission Canyon continues, you decide to compare your observations of the core lithologies with inferences about lithology, derived from log data. Study of the core indicates that the rock is microcrystalline dolomite, limestone and anhydrite. To compare this information with log data, construct a neutron-density porosity crossplot, a neutron-sonic porosity crossplot, a matrix identification plot, and an M-N lithology plot. (Ordinarily only one or two of the crossplots described here would be created, but all are discussed here for experience in learning.) On the basis of observations from the logs, you divide the zone into two intervals on the crossplots: the "Upper MC," from 9308 ft to 9370 ft, and the "Lower MC," from 9370 ft to 9409 ft.

The first crossplot is a neutron-density crossplot (Figure 10.10). It is consistent with the core description, showing a mixture of lithologies ranging from limestone to dolomite. The scatter of rock types in the crossplot is more than the rock types described in the core, because the limits of vertical resolution of the logging tools introduce averaging ("smearing") of lithologic effects on signals, especially among thin beds. From Figure 10.10, neutron-density crossplot porosity ($PhiND_{xpt}$) can be estimated; it is determined from the location of each point with respect to the porosity indications on each lithology line. These numbers will be used to construct a Pickett plot, to calculate apparent water resistivity ($R_{wa}$), and to estimate water saturation ($S_w$). Neutron-density crossplot porosity also will be used to calculate apparent matrix

Log Interpretation Case Studies

187

density, *RHOmaa*, for use in a matrix identification plot.

The second crossplot is a neutron-sonic crossplot (Figure 10.11). It too is consistent with core data, showing scatter of points between the limestone and dolomite lines. Neutron-sonic crossplot porosity (*PhiNSxpt*) can be estimated in the same manner as neutron-density crossplot porosity was estimated; it will be used to calculate apparent matrix density, *DTmaa*, one of the variables in the matrix identification plot.

The third crossplot augments results of the first two. In the matrix identification (MID) plot (Figure 10.12) apparent matrix density and apparent matrix traveltime (estimated from Figures 10.10 and 10.11, and Equations 10.21 and 10.22) are used to display a complex model of the rock. Figure 10.12 shows that most of the points are of limestone or dolomite (or a mixture) with fewer points that tend slightly toward anhydrite.

The fourth crossplot is the M-N plot (Figure 10.13). Like the MID plot, it is a complex model of lithology, based on the plotting of two calculated parameters, M, a function of sonic and bulk density, and N, a function of bulk density and neutron porosity (Equations 10.23 and 10.24). The M-N plot (Figure 10.13) shows that the Mission Canyon Formation consists of limestone and dolomite.

Calculations to determine porosities, apparent matrix values, and M and N are based on raw log data shown in Table 10.4a. Porosities, apparent matrix density, matrix interval transit time, and the lithology-dependent variables M and N are shown in Table 10.4b.

The next step is to verify the estimate of formation water resistivity. Although a single method usually is sufficient, two are shown here for aid in learning. The methods are described in detail in Chapter 7. The first method is calculation of $R_{wa}$ (apparent water resistivity) from the LLD and neutron-density crossplot porosity (Equation 10.25). As shown in the Solution Table (Table 10.4c) the two lowest values of $R_{wa}$, hence the best estimates of $R_w$, are 0.033 ohm-m (at 9387 ft) and 0.041 ohm-m (at 9406 ft). These numbers are only a bit higher than the reported $R_w$ of 0.023 ohm-m. The difference could be due to the manner in which logs were read, the effects of properties of adjacent beds on log readings, or to residual hydrocarbons. $R_{wa}$ also is presented in a log format (Figure 10.14), plotted in the same logarithmic track as the deep laterolog, LLD. In some cases, $R_{wa}$ plotted in this format allows for a better estimate of $R_w$.

The second method to approximate formation

formation-water resistivity is a Pickett plot (Figure 10.15). The deep laterolog (LLD) is used for plotting resistivity along the X-axis. Neutron-density crossplot porosity (PHIE: "effective porosity"), is plotted on the Y-axis. The water-bearing line—drawn through the lower part of the lowest cluster of points—estimates formation water resistivity ($R_w$) to be 0.023 ohm-m, in agreement with the published value. From the slope of the $R_o$ line—the line signifying that water saturation is 100%—data on the Pickett plot also indicate that the cementation exponent ($m$) is 2.

As discussed previously, deep induction resistivity of the stratigraphic section from 9370 ft to 9409 ft is less than that of the upper Mission Canyon (Figure 10.7). The likelihood of production of water from strata at 9370 ft to 9409 ft also is indicated by evidence from the Pickett crossplot (Figure 10.15). Most data points that show water saturations greater than 0.75 (75%) are of the "Lower MC" zone.

Saturation lines on the Pickett plot (Figure 10.15) are based on the saturation exponent ($n$) of 2.

At this juncture in your evaluation of the Mission Canyon from 9308 ft to 9409 ft, you have reason to be optimistic about the potential of the well. The interval shows evidence of porosity and invasion, it comprises interbedded permeable strata and "tight" strata, and the rock type, dolomite, generally is a good reservoir. However, you should be concerned about whether completion of the lower Mission Canyon should be attempted, especially from 9370 ft to 9409 ft. The well site log calculation, the diminished separation of resistivity curves with depth, and high water saturations on the Pickett crossplot (Figure 10.15) all strongly support your judgment that fluid from the lower Mission Canyon will not be water-free. How much water these zones will produce, relative to oil, is not known.

In order to support the decision to not perforate the lower Mission Canyon, a bulk-volume-water (BVW) crossplot is constructed (Figure 10.16). On the bulk-volume-water plot, data points above 0.035 are mostly from porosity zones of the lower Mission Canyon; these zones are not at irreducible water saturation, and they will produce some water.

The positions of data points on a bulk-volume-water crossplot can indicate differences in types of carbonate-rock porosity. Points that are below 0.035 generally represent rock with vuggy porosity, with some intercrystalline porosity (Table 7.1).

One of the last log evaluation procedures is finding values for the moveable hydrocarbon index (MHI), for moveable oil saturation (MOS), and for residual-oil saturation (ROS). Most of the moveable hydrocarbon index values are less than 0.7, and these are concen

188 ASQUITH AND KRYGOWSKI

trated in the upper Mission Canyon (Table 10.4c); so oil in these beds is moveable. Moveability of oil also is apparent from the high values of moveable oil saturation and low values of residual oil saturation (Table 10.4c).

A log of water saturation, porosity, and bulk volume water is shown in Figure 10.17.

Your log evaluation of this well has been uncommonly detailed. In part, the extensive evaluation was necessary; the well is a wildcat well, and visual inspection of logs of the lower Mission Canyon suggested that water would be produced. Fortunately, because of the log package used for this well a large amount of data was available for analysis.

Rather early in the evaluation the fact was apparent that the data seemed to support a decision to set pipe. Nevertheless, to know the correct interval for perforating was important, so that production of water could be minimized.

For the gross interval from 9308 ft to 9357 ft, the

estimated recovery of oil from the Mission Canyon Formation is 376,650 stock-tank barrels (STB) (Equation 10.8). This number is based on the following parameters:

- drainage area = 160 acres;
- reservoir thickness = 28 ft;
- average porosity = 0.11 (11%);
- average water saturation = 0.49 (49%);
- recovery factor = 0.20; and
- $B_{oi}$ (estimated) = 1.35.

The Mission Canyon Formation was perforated selectively from 9308 ft to 9357 ft. After a light acid clean-up, the well's production was 569 barrels of oil per day (BOPD), 31 barrels of water a day (BWPD), and 700,000 cubic feet of gas per day (700 mcfgpd); the gas/oil ratio was 1230:1. During the first five months the well produced 56,495 barrels of oil and 5,802 barrels of water.

Log Interpretation Case Studies

189

Table 10.4a. Case Study 2: Mission Canyon Formation, Williston Basin, U.S.A.: Raw data solution table. The symbol "v/v" indicates volume-for-volume decimal fraction.

|  Parameters  |   |   |   |
| --- | --- | --- | --- |
|  Ann. Mean Surf. Temp: 40°F |   |   | Rw (measured): ohm-m @ °F  |
|  Total Depth: 11,122 ft |   |   | Rw @ fm. temp.: 0.023 ohm-m @ 207°F  |
|  Bottom Hole Temp: (thermometer failed) |   |   | Rmf (measured): 0.46 ohm-m @ 74°F  |
|  Formation Depth: 9,300 ft |   |   | Rmf @ fm. temp.: 0.017 ohm-m @ 207°F  |
|  Formation Temperature: 207°F |   |   |   |
|  DT matrix (Wyllie): 47.6 μsec/ft |   |   | DT fluid (Wyllie): 185 usec/ft  |
|  RHO matrix: 2.71 g/cm³ |   |   | RHO fluid: 1.1 g/cm³  |
|  PHIN fluid: 1 |   |   |   |
|   | a: 1 | m: 2 | n: 2  |

|  Raw data  |   |   |   |   |   |   |
| --- | --- | --- | --- | --- | --- | --- |
|  Depth feet | ILD ohm-m | ILS ohm-m | MSFL ohm-m | DT μsec/ft | DPHI v/v decimal | NPHI v/v decimal  |
|  9,310 | 26 | 20.5 | 1.2 | 63 | 0.090 | 0.260  |
|  9,322 | 18 | 10 | 5.7 | 52 | 0.020 | 0.060  |
|  9,326 | 17 | 8.3 | 3.8 | 53.5 | 0.030 | 0.120  |
|  9,332 | 9 | 6.1 | 2.4 | 58 | 0.050 | 0.140  |
|  9,335 | 32 | 6.8 | 13 | 52.5 | 0.035 | 0.085  |
|  9,347 | 4.8 | 2.4 | 0.8 | 61.5 | 0.100 | 0.230  |
|  9,353 | 4.7 | 2.3 | 1.6 | 61.5 | 0.045 | 0.250  |
|  9,362 | 40 | 17 | 11 | 53 | -0.015 | 0.135  |
|  9,367 | 22 | 16 | 8.8 | 52.5 | -0.015 | 0.125  |
|  9,373 | 11 | 7.7 | 3.5 | 53.5 | 0.000 | 0.155  |
|  9,376 | 5.1 | 3.3 | 2.1 | 57.5 | 0.075 | 0.165  |
|  9,383 | 3.3 | 1.5 | 1.2 | 62 | 0.090 | 0.220  |
|  9,387 | 3.3 | 1.5 | 1.3 | 62 | 0.080 | 0.135  |
|  9,398 | 6.4 | 3.2 | 2.2 | 58 | 0.055 | 0.135  |
|  9,406 | 5.1 | 3.5 | 2.2 | 55 | 0.030 | 0.150  |

190

ASQUITH AND KRYGOWSKI

Table 10.4b. Case Study 2: Mission Canyon Formation, Williston Basin, U.S.A.: Work table for determination of lithology. The symbol "v/v" indicates volume-for-volume decimal fraction.

|  Lithology Calculations  |   |   |   |   |   |   |   |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  Depth feet | RHOB g/cm³ | PhiNDxpt v/v decimal | RHOmaa g/cm³ | PhiNSxpt v/v decimal | DTmaa μsec/ft | M | N  |
|  9,310 | 2.57 | 0.170 | 2.865 | 0.145 | 42.3 | 0.833 | 0.505  |
|  9,322 | 2.68 | 0.040 | 2.744 | 0.035 | 47.2 | 0.843 | 0.596  |
|  9,326 | 2.66 | 0.075 | 2.788 | 0.065 | 44.4 | 0.842 | 0.563  |
|  9,332 | 2.63 | 0.095 | 2.790 | 0.090 | 45.4 | 0.830 | 0.562  |
|  9,335 | 2.65 | 0.055 | 2.744 | 0.075 | 41.8 | 0.853 | 0.589  |
|  9,347 | 2.55 | 0.160 | 2.825 | 0.125 | 43.9 | 0.852 | 0.531  |
|  9,353 | 2.64 | 0.140 | 2.888 | 0.130 | 43.0 | 0.803 | 0.488  |
|  9,362 | 2.73 | 0.065 | 2.848 | 0.065 | 43.8 | 0.808 | 0.529  |
|  9,367 | 2.73 | 0.060 | 2.838 | 0.060 | 44.0 | 0.811 | 0.535  |
|  9,373 | 2.71 | 0.085 | 2.860 | 0.070 | 43.6 | 0.817 | 0.525  |
|  9,376 | 2.59 | 0.120 | 2.792 | 0.095 | 44.1 | 0.856 | 0.561  |
|  9,383 | 2.57 | 0.150 | 2.824 | 0.125 | 44.4 | 0.840 | 0.532  |
|  9,387 | 2.58 | 0.100 | 2.746 | 0.105 | 47.6 | 0.830 | 0.584  |
|  9,398 | 2.62 | 0.090 | 2.772 | 0.090 | 45.4 | 0.835 | 0.569  |
|  9,406 | 2.66 | 0.090 | 2.816 | 0.075 | 44.5 | 0.832 | 0.544  |

Table 10.4c. Case Study 2: Mission Canyon Formation, Williston Basin, U.S.A.: Calculations for solution table. The symbol "v/v" indicates volume-for-volume decimal fraction.

|  Saturation and other calculations  |   |   |   |   |   |   |   |   |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  Depth feet | Rwa ohm-m | Ro ohm-m | Sw v/v decimal | Sxo v/v decimal | MHI v/v decimal | MOS v/v decimal | ROS v/v decimal | BVW  |
|  9,310 | 0.751 | 0.8 | 0.166 | 0.700 | 0.237 | 0.534 | 0.300 | 0.028  |
|  9,322 | 0.029 | 14.4 | 0.894 | 1.000 | 0.894 | 0.106 | 0.000 | 0.036  |
|  9,326 | 0.096 | 4.1 | 0.490 | 0.892 | 0.550 | 0.401 | 0.108 | 0.037  |
|  9,332 | 0.081 | 2.5 | 0.532 | 0.886 | 0.601 | 0.354 | 0.114 | 0.051  |
|  9,335 | 0.097 | 7.6 | 0.487 | 0.657 | 0.741 | 0.170 | 0.343 | 0.027  |
|  9,347 | 0.123 | 0.9 | 0.433 | 0.911 | 0.475 | 0.478 | 0.089 | 0.069  |
|  9,353 | 0.092 | 1.2 | 0.500 | 0.736 | 0.679 | 0.237 | 0.264 | 0.070  |
|  9,362 | 0.169 | 5.4 | 0.369 | 0.605 | 0.610 | 0.236 | 0.395 | 0.024  |
|  9,367 | 0.079 | 6.4 | 0.539 | 0.733 | 0.736 | 0.194 | 0.267 | 0.032  |
|  9,373 | 0.079 | 3.2 | 0.538 | 0.820 | 0.656 | 0.282 | 0.180 | 0.046  |
|  9,376 | 0.073 | 1.6 | 0.560 | 0.750 | 0.746 | 0.190 | 0.250 | 0.067  |
|  9,383 | 0.074 | 1.0 | 0.557 | 0.793 | 0.701 | 0.237 | 0.207 | 0.083  |
|  9,387 | 0.033 | 2.3 | 0.835 | 1.000 | 0.835 | 0.165 | 0.000 | 0.083  |
|  9,398 | 0.052 | 2.8 | 0.666 | 0.977 | 0.682 | 0.311 | 0.023 | 0.060  |
|  9,406 | 0.041 | 2.8 | 0.746 | 0.977 | 0.764 | 0.231 | 0.023 | 0.067  |

Log Interpretation Case Studies

191

![img-32.jpeg](img-32.jpeg)

Figure 10.10. Mission Canyon Formation, Williston Basin, U.S.A.: Crossplot, bulk density (RHOB) versus neutron porosity (NPHI), for determining apparent matrix density (RHOmaa), a variable for the matrix identification plot (Figure 10.12). See Chapter 4 for detailed information about interpretation of the crossplot.

![img-33.jpeg](img-33.jpeg)

Figure 10.11. Mission Canyon Formation, Williston Basin, U.S.A.: Crossplot, interval transit time (DT) versus neutron porosity (NPHI), for determining apparent matrix transit time (DTmaa), a variable for the matrix identification plot (Figure 10.12). See Chapter 4 for detailed information about interpretation of the crossplot.

192

ASQUITH AND KRYGOWSKI

Figure 10.12. Matrix identification plot, Mission Canyon Formation, Williston Basin, U.S.A.: Values for apparent matrix density (RHOmaa) and apparent matrix traveltime (DTmaa) were recorded from Figure 10.10 and Figure 10.11. Two mineral triangles are shown: quartz-calcite-dolomite, and calcite-dolomite-anhydrite. Scatter of points in the plot suggests that most of the rock is a mixture of calcite and dolomite.

![img-34.jpeg](img-34.jpeg)

Figure 10.13. M-N lithology crossplot for identification of matrix and secondary porosity, Mission Canyon Formation, Williston Basin, U.S.A. Lithology indicators were calculated from porosity logs: M from acoustic and density, and N from neutron and density. Two mineral triangles are shown: quartz-calcite-dolomite, and calcite-dolomite-anhydrite. Most points indicate a mixture of calcite and dolomite.

![img-35.jpeg](img-35.jpeg)

Log Interpretation Case Studies

193

![img-36.jpeg](img-36.jpeg)

Figure 10.14. Mission Canyon Formation, Williston Basin, U.S.A.: Log of apparent water resistivity (Rwa) with gamma ray log, apparent matrix density log (RHOmaa), deep resistivity laterolog, neutron-porosity log, density-porosity log, and effective porosity log.

Apparent matrix density (RHOmaa) is plotted in track 1 with the gamma ray (GR). Apparent water resistivity (Rwa) is plotted in track 2 with the deep laterolog. Neutron-density crossplot porosity, indicated by PHIE (effective porosity) is plotted in track 3, with the original neutron and density porosities.

![img-37.jpeg](img-37.jpeg)

Figure 10.15. Mission Canyon Formation, Williston Basin, U.S.A.: Pickett crossplot of deep laterolog resistivity vs. neutron-density crossplot porosity. Note that the "Lower MC" zones generally have the higher water saturations; they define the water-bearing line $(5w = 1.0)$ . See Chapter 7 for detailed information about interpretation of the Pickett crossplot.

Upper MC
Lower MC

194

ASQUITH AND KRYGOWSKI

Figure 10.16. Bulk-volume-water crossplot (effective porosity, PHIE, vs. water saturation, $S_{w}$), Mission Canyon Formation, Williston Basin, U.S.A.

![img-38.jpeg](img-38.jpeg)

- Upper MC

- Lower MC

Figure 10.17. Mission Canyon Formation, Williston Basin, U.S.A. Final results in log format.

Apparent water resistivity ($R_{\mathrm{ws}}$) is plotted in track 1 with the gamma ray log.

Resistivity of rock at $100\%$ water saturation (Ro) is plotted in track 2, with the deep laterolog. Separation of the two curves (shaded) indicates hydrocarbons in the rock.

Track 3 shows water saturation (Sw), effective porosity (PHIE), and bulk volume water (BVW). The dark shaded area between the porosity curve (left-hand) and the bulk-volume-water curve indicates the proportion of pore space that is occupied by hydrocarbons, whereas the light shaded area between the bulk-volume-water curve and the right margin of the track (scale value of zero) indicates the proportion that is occupied by water. DiffCal is the differential caliper (caliper minus bit size). Negative values indicate the presence of mudcake.

![img-39.jpeg](img-39.jpeg)

Feet MD

9300

9400

![img-40.jpeg](img-40.jpeg)

Log Interpretation Case Studies

195

### Case Study 3:

### EOCENE WILCOX SANDSTONE, GULF COAST, U.S.A.:

### The Problem.

Case Study 3 reflects the logging technology available when the well was drilled. At the time, logging tools could be combined in single tool strings in limited ways. The neutron and density tools could be combined, as could the induction and sonic tools. In the U.S. Gulf Coast, the induction-sonic log was the tool string of choice for the first entry in a well on any run, especially in difficult boreholes, because if no other logging data could be acquired, the acquisition of resistivity and porosity at the same time allowed a reasonable evaluation of the formation. Although current technology permits the simultaneous acquisition of more wireline data, the analysis in this exercise is a good example of the approach that can be used in older wells with this limited suite of data, or other similarly limited suites of data. Techniques shown here are very effective in looking for bypassed pay.

### Background

Assume that you are assigned to evaluate the logs of a lower Wilcox sandstone in South Texas. A fairly typical Gulf Coast log package was used to document the well. It consists of an induction electric log with an SP log, a sonic log, and an $R_{wa}$ quick-look curve. The induction electric log has a deep induction curve, IL, to measure resistivity in the uninvaded zone ($R_t$), and a short normal (SN) to measure resistivity in the invaded zone ($R_i$). The log package was run on a single tool string, and because it required only one run in the well, it saved your company rig time and money. The log is shown as Figure 10.18.

Drilling operations halted at 10,936 ft after penetration of a sandstone. Gas in the drilling mud increased suddenly and by a large amount: 3200 units over background on the chromatograph. In response to this, mud weight was increased from 14.8 lbs/gal to 15.4 lbs/gal, to confine the gas within the formation. When drilling operations were resumed, gas continued to cut the mud; mud weight was 15.4 lbs/gal going into the hole and 15.2 lbs/gal coming out. Also, the mud logger's chromatograph maintained about 100 units of gas, even when the well was deepened beyond the zone of initial gas show.

### Well site information and other pertinent information:

- $R_w = 0.022$ ohm-m at $T_f$ (from other sources)
- Archie parameters: a = 0.62; m = 2.15; n = 2.0
- $R_{mf} = 0.222$ ohm-m at $T_f$
- formation temperature, $T_f = 260^\circ\text{F}$
- $\Delta t_{sh} = 116$ $\mu\text{sec/ft}$
- surface temperature = 80°F

Recoverable reserves of gas are to be calculated from the gas volumetric equation (Equation 10.11). The following parameters are needed:

- drainage area = 320 acres
- reservoir thickness (to be determined from the calculations)
- porosity (to be determined from the calculations)
- water saturation (to be determined from the calculations)
- recovery factor = 0.6
- bottom hole pressure (estimated) = 8,100 psi
- Z factor = 1.229
- surface pressure = 15 psi

Your company has purchased a 25% working interest (WI) in the well, which has a net revenue interest (NRI) of 82.5 percent. (Net revenue interest is the total interest of 100% minus royalties, such as an interest granted to a mineral-rights owner.)

Estimated cost of the well is $1,800,000. Use a product price of $1.90 per mcf to find the return your company can expect on its investment.

### Useful equations

The only porosity tool at your disposal is the sonic log, so porosity can be calculated either by the Wyllie time-average equation or the Raymer-Hunt-Gardner equation (see Chapter 4). Because of your knowledge of the geology of the area, you decide that the Wyllie time-average equation (Equation 4.3) will yield the better estimate of porosity:

$$PHIS = \left( \frac{\Delta t_{log} - \Delta t_{ma}}{\Delta t_{fl} - \Delta t_{ma}} \right) \times \frac{1}{Cp} \tag{10.26}$$

where:

$$Cp = \frac{\Delta t_{sh} \times C}{100}$$

196

ASQUITH AND KRYGOWSKI

$\Delta t_{ma} = 55.5~\mu \mathrm{sec / ft}$ for Wilcox sandstones in this province

$\Delta t_{fl} = 189~\mu \mathrm{sec / ft}$

$\Delta t_{sh} = 116~\mu \mathrm{sec / ft}$

$C = 1$

Because the sonic log is strongly affected by gas, correction of sonic porosity is necessary.

$$
\phi_{S\text{gas\ corrected}} = 0.7 \times \phi_S \tag{10.27}
$$

## Tasks required for interpretation of the logs

Eleven depths (or points) within the Wilcox sandstone interval are selected, in the interval from 10,925 ft to 10,982 ft. Depths are picked on the basis of an approximately even distribution through the interval being evaluated.

Table 10.5 is designed to assist you with your work. Some of the log values have been recorded, to guide you in reading the log and completing the array of data.

As you approach this problem, think about the parameters and calculations necessary to determine porosity and water saturation. Also, consider some of the plots done in the first two case studies that may help you understand the formation better.

Log Interpretation Case Studies

197

Table 10.5. Case Study 3: Eocene Wilcox sandstone, Gulf Coast, U.S.A.: Work table. Depths in italics indicate data from the lower part of the Wilcox, the "B" zone. The symbol "v/v" indicates volume-for-volume decimal fraction.

|  Parameters  |   |   |   |
| --- | --- | --- | --- |
|  Ann. Mean Surf. Temp: 80°F |   |   | Rw (measured): (not given)  |
|  Total Depth: 12,186 ft |   |   | Rw @ fm. temp.: 0.022 ohm-m @ 260°F  |
|  Bottom Hole Temp: 280°F |   |   | Rmf (measured): 0.77 ohm-m @ 70°F  |
|  Formation Depth: 10,950 ft |   |   | Rmf @ fm. temp.: 0.222 ohm-m @ 260°F  |
|  Formation Temperature: 260°F |   |   |   |
|  DT matrix (Wyllie): 55.5 μsec/ft |   |   | DT fluid (Wyllie): 189 μsec/ft  |
|  DT shale: 116 μsec/ft |   |   | Compaction Correction, Cp: 1.16  |
|   | a: 0.62 | m: 2.15 | n: 2  |

|  Data |  |  |  |  |   |
| --- | --- | --- | --- | --- | --- |
|  Depth feet | IL ohm-m | SN ohm-m | DT μsec/ft | PHIS v/v decimal | Phia v/v decimal  |
|  10,925 | 1.8 | 3.1 | 88 | 0.210 | 0.147  |
|  10,930 |  |  |  |  |   |
|  10,935 |  |  |  |  |   |
|  10,942 |  |  |  |  |   |
|  10,947 | 2.3 | 4.0 | 91 | 0.229 | 0.160  |
|  10,954 |  |  |  |  |   |
|  10,960 |  |  |  |  |   |
|  10,966 | 1.0 | 2.5 | 96 | 0.262 | 0.183  |
|  10,970 | 0.8 | 2.5 | 95 | 0.255 | 0.179  |
|  10,974 |  |  |  |  |   |
|  10,978 |  |  |  |  |   |

|  Calculations  |   |   |   |   |
| --- | --- | --- | --- | --- |
|  Depth feet | Rwa ohm-m | Swa v/v decimal | Sxo v/v decimal | BVW  |
|  10,925 | 0.047 | 0.684 | >1.0 | 0.101  |
|  10,930 |  |  |  |   |
|  10,935 |  |  |  |   |
|  10,942 |  |  |  |   |
|  10,947 | 0.073 | 0.550 | >1.0 | 0.088  |
|  10,954 |  |  |  |   |
|  10,960 |  |  |  |   |
|  10,966 | 0.042 | 0.725 | >1.0 | 0.133  |
|  10,970 | 0.032 | 0.832 | >1.0 | 0.149  |
|  10,974 |  |  |  |   |
|  10,978 |  |  |  |   |

198

ASQUITH AND KRYGOWSKI

![img-0.jpeg](img-0.jpeg)

Figure 10.18. Induction electric log with SP log, sonic log, and Rwa curve, Wilcox sandstone, Gulf Coast, U.S.A.

Note:

(1) In the upper part of the Wilcox (10,923 to 10,958 ft), deflection of the Rwa quick-look curve (track 1) to the right, opposite general deflection of the SP curve. The deflection indicates the presence of oil or gas. Based on the mudlogger's report, gas is present.
(2) In track 2, increase of resistivity in the upper part of the Wilcox (10,923 to 10,958 ft). Increase of resistivity also indicates the presence of gas.
(3) In the lower part of the Wilcox (10,958 to 10,982 ft), low resistivities and deflection of the Rwa curve to the left indicate a probable water-bearing zone.

Log Interpretation Case Studies

199

# Case Study 3:

# EOCENE WILCOX SANDSTONE, GULF COAST, U.S.A.:

# The Solution.

Evaluation of the logs (Figure 10.18) begins with assessment of the quality of sandstone through the Wilcox interval, because this is where a good gas show was recorded. You discern the following attributes of the formation:

- Porous and permeable sandstone is documented by the SP curve from 10,923 to 10,982 ft, evident by leftward deflection of the curve from the shale baseline.
- Porosity of sandstone over that interval is almost uniform, as shown by small variation of the sonic (DT) curve.
- In the upper part of the Wilcox (10,923 to 10,958 ft), the \( R_{wa} \) quick-look curve is deflected rightward from the SP curve. Such a deflection is evidence of hydrocarbons in the sandstone—in this case, gas.
- In the same interval, induction log (IL) resistivity increases, indicating that the sandstone contains hydrocarbons.
- Fairly abrupt decrease of resistivity into the lower zone (10,958 to 10,982 ft) and leftward deflection of the \( R_{wa} \) curve means higher water saturation. These observations alert you that the lower zone may be water productive.

In order to establish whether the lower Wilcox zone would produce water, you decide that a rather detailed log evaluation is necessary. The evaluation will include use of the $R_{wa}$ quick-look curve, a Pickett crossplot (to verify the value of $R_w$ estimated from $R_{wa}$, and to estimate water saturations), water saturations calculated from the Archie equation, and a crossplot for estimation of bulk volume water. The following calculations will be needed:

- Gas-corrected sonic porosity, from Equations 10.26 and 10.27, for use in the Pickett plot, and for calculation of \( S_{w} \) and \( S_{xo} \) by the Archie equation.
- \( S_{w} \), and \( S_{xo} \), to calculate moveable oil saturation (MOS), bulk volume water (BVW), and the moveable hydrocarbon index (MHI).

Note that the short normal resistivity (SN) will be used to calculate $S_{xo}$. The short normal curve actually measures resistivity of the invaded zone ($R_i$), and in the strictest sense, water saturation calculated from

that measurement would be $S_i$, the invaded-zone saturation, not $S_{xo}$, the flushed-zone saturation. Because there is no $R_{xo}$ measurement available, the short normal is used as an approximate $R_{xo}$ measurement; the resulting estimate of "$S_{xo}$" is somewhat lower than $S_{xo}$ based on an actual $R_{xo}$ measurement. However, the approximation usually is sufficient for analyses like the one dealt with here.

Results of calculations are shown in Table 10.6. In the various plots, the lower Wilcox was divided into two zones: the "lower Wilcox A," from 10,923 to 10,958 ft, and the "lower Wilcox B," from 10,958 to 10,982 ft. In the table, depths in italics denote points in the "lower Wilcox B" zone.

Examination of the gas-corrected sonic-log porosity (Table 10.6, *Phia*, apparent porosity) reveals that porosity ranges from almost 0.15 to approximately 0.20 (15% to 20%), with average porosity of 0.18. These sonic porosities are used in the $R_{wa}$ calculation, the Archie water saturation equation, and in making crossplots.

The apparent water resistivity curve, $R_{wa}$ (Figure 10.18), can be used in a quick-look technique for comparison with the SP. It can also be used to determine formation water resistivity, $R_w$. From study of Chapter 7, you will remember that the minimal value of $R_{wa}$ in an interval can be considered as the "best estimate" of $R_w$. In the Wilcox in this well, the minimal value of $R_{wa}$, from 10,970 to 10,980 ft, is 0.028 ohm-m (Table 10.6). From independent evidence, $R_w$ of the Wilcox in this province is known to be 0.022 ohm-m; therefore, the log-derived value indicates that hydrocarbons probably are in the interval, although not as much as are in the overlying part of the Wilcox.

A Pickett crossplot (Figure 10.19; see also Chapter 7) of deep-induction log resistivities (IL) versus corrected sonic porosity (*Phia*) (i.e., porosity corrected for gas effect) shows a water-saturated sandstone line constructed with an $R_w$ of 0.022 ohm-m. Water saturations range from about 90% to less than 50%. Water saturations greater than 75% are from samples of the lower Wilcox B zone. This supports your suspicions about the potential for water production from the lower Wilcox B.

Compare bulk volume water and water saturations of the upper part, "A," and lower part, "B," of the Wilcox sandstone (Figure 10.20). The lower bulk-volume-water values and lower water saturations of the Wilcox A indicate that only the Wilcox A is above a gas/water transition zone. Most of the bulk-volume-water values that are much greater than 0.1 (Figure 10.20) are in the Wilcox B, from 10,958 to 10,982 ft (Figure 10.18; Table 10.6). In this interval, the volume

200

ASQUITH AND KRYGOWSKI

of pore water is greater than irreducible water saturation.

Values of $S_{xo}$ are needed to calculate the moveable hydrocarbon index, MHI, and moveable oil saturation, MOS. Unfortunately the $S_{xo}$ values calculated for all zones are greater than 1.0, making the MHI and MOS calculations of no value. There are two likely causes for the calculations' being greater than is physically possible. The first is an incorrectly measured or recorded value of $R_{mf}$. This is a rare occurrence, but given the nature of work on an active rig, it cannot be dismissed. For values of $S_{xo}$ to be around 1.0, the actual $R_{mf}$ value would be about half the recorded value. The second probable cause would be use of the short normal as an $R_{xo}$ measurement. If the formation were invaded, the short normal would read formation fluid resistivity that is a mix of $R_w$ and $R_{mf}$, in this case, the value would be greater than $R_w$ but less than $R_{mf}$. For the values of $S_{xo}$ to be around 1.0, short-normal resistivity measurements would necessarily be three times the recorded values. Given the information at hand, the cause for the unreasonable $S_{xo}$ calculations can't be determined with certainty.

All data produced by your evaluation support the early assessment of a reservoir with gas above water. You were alerted immediately to a potential problem after you examined the $R_{wa}$ quick-look curve and saw leftward deflection through the lower Wilcox zone, and also when you saw the fairly abrupt decrease of resistivity in the lower Wilcox.

By volumetric calculations (Equations 10.11 and 10.12) estimated recoverable reserves are 3.1 BCF, based on the following parameters:

- drainage area = 320 acres
- reservoir thickness = 15 ft
- porosity = 0.18 (18%)
- water saturation = 0.67 (67%)
- recovery factor = 0.6 (estimated conservatively)
- formation temperature (estimated) = 260°F
- bottom-hole pressure (estimated) = 8,100 psi
- Z factor = 1.229
- surface pressure = 15 psi

Return on investment of the Wilcox sandstone is estimated as follows:

1: Working-interest well cost
= Total well cost × Working interest.
10.28
Working-interest well cost
= $1,800,000 × 0.25 = $450,000.

2: Net-revenue working interest
= Net-revenue interest (lease)
× Working interest.
10.29
Working interest = 0.825 × 0.25
= 0.20625 (20.6%).

3: Gross revenue = Reserves × Product price.
10.30
Gross revenue = 3,100,000 mcf ×
$1.90 / mcf = $5,890,000.

4: Net-revenue (working interest) = Gross revenue
× Net-revenue working interest.
10.31

Net-revenue (working interest) =
= $5,890,000 × 0.20625 = $1,205,812.50

5: Return on investment (before taxes and expenses)
= Net revenue (working interest)
Working-interest well costs.
10.32

Return on investment
= $1,214,812.50
$450,000
≅ 2.7 : 1.

The relatively poor return (2.7 to 1) on your company's investment is weighed with your judgment about the reservoir's high water saturations. The conclusion is that gas could be produced only at fairly low levels, so that production of water from the lower zone can be kept under control. However, in conjunction with your company's management, a decision is made to set pipe, because of hope for increase in gas prices. (This decision may be questioned by readers who conclude that the rate of return doesn't meet their economic criteria—even with the assumed price increases.)

The Wilcox sandstone was perforated from 10,962

Log Interpretation Case Studies

201

to 10,963 ft. Gas flowed 11 hours on a 10/64-in. choke at 1584 mcfgpd, with 5 barrels of condensate per day (BCPD) and 1090 barrels of water per day (BWPD). The interval (10,962 to 10,963 ft) was squeezed (i.e., cemented off) and sandstone from 10,925 to 10,933 ft was perforated. Results were as follows:

- calculated absolute open flow (CAOF) of 7000 mcfgpd and 7.8 BC/mmcf,
- SITP = 7130 psi;
- IBHP = 8480 psi;

- BHT = 283°F;
- gas gravity = 0.657; and
- liquid gravity = 46.7 degAPI.

The well produced 350 mmcf during the first 10 months.

Figure 10.21 shows results of evaluation of the interval by petrophysical software. Parameters described in this case study were used and calculations were made at the sample intervals defined for recording of the original data—one sample every 0.5 ft.

202

ASQUITH AND KRYGOWSKI

Table 10.6. Case Study 3: Eocene Wilcox sandstone, Gulf Coast U.S.A.: Solution table. Depths in italics indicate data from the lower part of the Wilcox, the "B" zone. The symbol "v/v" indicates volume-for-volume decimal fraction.

|  Parameters  |   |   |   |
| --- | --- | --- | --- |
|  Ann. Mean Surf. Temp: 80°F |   |   | Rw (measured): (not given)  |
|  Total Depth: 12,186 ft |   |   | Rw @ fm. temp.: 0.022 ohm-m @ 260°F  |
|  Bottom Hole Temp: 280°F |   |   | Rmf (measured): 0.77 ohm-m @ 70°F  |
|  Formation Depth: 10,950 ft |   |   | Rmf @ fm. temp.: 0.222 ohm-m @ 260°F  |
|  Formation Temperature: 260°F |   |   |   |
|  DT matrix (Wyllie): 55.5 μsec/ft |   |   | DT fluid (Wyllie): 189 μsec/ft  |
|  DT shale: 116 μsec/ft |   |   | Compaction Correction, Cp: 1.16  |
|   | a: 0.62 | m: 2.15 | n: 2  |

|  Data |  |  |  |  |   |
| --- | --- | --- | --- | --- | --- |
|  Depth feet | IL ohm-m | SN ohm-m | DT μsec/ft | PHIS v/v decimal | Phia v/v decimal  |
|  10,925 | 1.8 | 3.1 | 88 | 0.210 | 0.147  |
|  10,930 | 1.3 | 3.0 | 98 | 0.274 | 0.192  |
|  10,935 | 1.8 | 3.0 | 96 | 0.262 | 0.183  |
|  10,942 | 1.5 | 3.2 | 97 | 0.268 | 0.188  |
|  10,947 | 2.3 | 4.0 | 91 | 0.229 | 0.160  |
|  10,954 | 1.3 | 3.1 | 100 | 0.287 | 0.201  |
|  10,960 | 1.1 | 2.9 | 94 | 0.249 | 0.174  |
|  10,966 | 1.0 | 2.5 | 96 | 0.262 | 0.183  |
|  10,970 | 0.8 | 2.5 | 95 | 0.255 | 0.179  |
|  10,974 | 0.8 | 2.2 | 93 | 0.242 | 0.170  |
|  10,978 | 0.9 | 2.1 | 92 | 0.236 | 0.165  |

|  Calculations  |   |   |   |   |
| --- | --- | --- | --- | --- |
|  Depth feet | Rwa ohm-m | Swa v/v decimal | Sxo v/v decimal | BVW  |
|  10,925 | 0.047 | 0.684 | >1.0 | 0.101  |
|  10,930 | 0.060 | 0.603 | >1.0 | 0.116  |
|  10,935 | 0.075 | 0.540 | >1.0 | 0.099  |
|  10,942 | 0.066 | 0.576 | >1.0 | 0.108  |
|  10,947 | 0.073 | 0.550 | >1.0 | 0.088  |
|  10,954 | 0.067 | 0.574 | >1.0 | 0.116  |
|  10,960 | 0.041 | 0.730 | >1.0 | 0.127  |
|  10,966 | 0.042 | 0.725 | >1.0 | 0.133  |
|  10,970 | 0.032 | 0.832 | >1.0 | 0.149  |
|  10,974 | 0.029 | 0.864 | >1.0 | 0.146  |
|  10,978 | 0.030 | 0.854 | >1.0 | 0.141  |

Log Interpretation Case Studies

203

![img-1.jpeg](img-1.jpeg)

Figure 10.19. Pickett crossplot of resistivity, IL, versus porosity from the sonic log, corrected for gas effect (Phia), Eocene Wilcox sandstone, Gulf Coast, U.S.A.

Saturation lines are placed on the basis of $R_{w} = 0.022$ ohm-m at formation temperature; a widely accepted value for the Wilcox in this area.

![img-2.jpeg](img-2.jpeg)

Figure 10.20. Bulk volume water crossplot (apparent porosity, Phi vs. water saturation, $S_{wo}$), Eocene Wilcox sandstone, Gulf Coast, U.S.A.

Bulk-volume-water values (BVW) plotted above the 0.1 hyperbolic line are from samples of the lower ("B") part of the Wilcox sandstone; in this part of the reservoir the volume of pore water is greater than irreducible water saturation.

204

ASQUITH AND KRYGOWSKI

![img-3.jpeg](img-3.jpeg)

Figure 10.21. Computer-processed interpretation, Eocene Wilcox sandstone, Gulf Coast, U.S.A.

Track 1 shows the SP curve and an Rwa curve calculated from the induction curve, IL.

Track 2 shows the induction log, IL.

Track 3 shows Archie water saturation, Swa, calculated from gas-corrected sonic porosity from the sonic log (Phia) and bulk volume water (BVW). The dark shaded area between the porosity curve (left-hand) and the bulk-volume-water curve indicates the proportion of pore space that is occupied by gas, whereas the light shaded area between the bulk-volume-water curve and the right margin of the track (scale value of zero) indicates the proportion that is occupied by water.

Log Interpretation Case Studies

205

# Case Study 4:

# PENNSYLVANIAN UPPER MORROW SANDSTONE, ANADARKO BASIN, U.S.A.:

# The Problem.

Although the location of this well is in a depositional basin that is a significant distance from that of Case Study 3, the similarity of data, of lithology (sandstone), and of the interpreted depositional environment lead to the use of the same techniques. In Case Study 3, the scenario was that of a drilling well with significant gas shows. In this case study, the task is one of mapping existing data. If one is alert to the data at hand, a more robust prospect can be developed; the prospect includes not only geologic data of the area, but also description of opportunities missed by other operators.

# Background

An area covering several counties in the Anadarko Basin has been assigned to you. Your responsibility is to map and develop hydrocarbon prospects and to oversee all company activity in these counties.

As you pursue the assignment, many well logs are reviewed; some of the wells are producing and some are dry and abandoned. One particular dry-and-abandoned well captures your attention. The well wasn't tested before abandonment. However, it was logged with an induction electric log (Figure 10.22) to determine resistivities of the invaded ($R_i$) and uninvaded ($R_i$) zones, and with a sonic log (Figure 10.23) to determine porosity. The induction log shows high resistivities and the sonic log indicates that the sandstone has "good" porosity.

# Well site information and other pertinent information:

- $R_{mf} = 0.527$ ohm-m at $T_f$
- $R_w = 0.11$ ohm-m at $T_f$ (a questioned value)
- $T_f = 130^\circ\text{F}$
- Archie parameters: $a = 0.81$; $m = n = 2$
- surface temperature = $70^\circ\text{F}$

Volumetric recoverable oil reserves are calculated from the following parameters:

- drainage area = 160 acres;
- $B_{oi} = 1.3$;
- recovery factor ($RF$) = 0.15;

- porosity = (to be determined);
- water saturation ($S_w$) = (to be determined); and
- thickness ($h$) = 8 ft.

An analysis by the company's engineering department leads to a judgment that the well can be re-entered if evidence supports the inference that the well would be productive and profitable. Estimated cost of re-entry and completion of the well is $275,000. With a gross product price of $32.00 per barrel and a lease that has a 3/16th royalty, what would you estimate as an expectable return on investment?

# Useful equations

The sonic porosity formula (Wyllie time-average equation 4.1) is:

$$\phi_S = \frac{\Delta t_{log} - \Delta t_{ma}}{\Delta t_{fl} - \Delta t_{ma}} \tag{10.33}$$

For calculating $R_w$ from the SP:

$$R_w = 10^{(K \times \log(R_{wa}) + SP) \cdot K} \tag{10.34}$$

Where: $K = 61 + 0.133 \times T_f$, and where SP is a negative number. 10.35

In this older log-display format (Figure 10.22), resistivity is displayed on a linear scale; conductivity is also shown. In parts of formations where resistivity is low, the accuracy of estimated formation resistivity can be improved by reading the conductivity (which normally is recorded on a more sensitive scale); the reciprocal is formation resistivity. The equation is:

$$R_{ILD} = \frac{1000}{C_{ILD}} \tag{10.36}$$

# Tasks required for interpretation of the logs

The key variable in determining whether this well will be successful is the estimated effect of water. You have an estimate of $R_w$ (shown above), but its accuracy is questioned and the estimate is regarded as being unreliable. You will need to determine $R_w$ before calculating water saturation ($S_w$); use the SP log and charts (see "Formation Water Resistivity ($R_w$), Determination," Chapter 2, or Equations 10.34 and 10.35, above). Also, you may want to calculate $R_{wa}$ to corroborate the estimate of $R_w$ from the SP curve.

Use the upper Morrow Sandstone log evaluation table (Table 10.7) to complete the evaluation.

206

ASQUITH AND KRYGOWSKI

Table 10.7. Case Study 4: Upper Morrow Sandstone, Anadarka Basin, U.S.A.: work table. The symbol "v/v" indicates volume-for-volume decimal fraction.

|  Parameters  |   |   |   |   |
| --- | --- | --- | --- | --- |
|  Ann. Mean Surf. Temp: 70°F |   |   | Rw (measured): (not given)  |   |
|  Total Depth: 8,007 ft |   |   | Rw @ fm. temp.: 0.140 ohm-m @ 130°F  |   |
|  Bottom Hole Temp: 135°F |   |   | Rmf (measured): (not given)  |   |
|  Formation Depth: 7,441 ft |   |   | Rmf @ fm. temp.: 0.527 ohm-m @ 130°F  |   |
|  Formation Temperature: 130°F |   |   |   |   |
|  DT matrix (Wyllie): 55.5 μsec/ft |   |   | DT fluid (Wyllie): 189 μsec/ft  |   |
|   | a: 0.81 | m: 2 | n: 2 |   |

|  Data and Calculations  |   |   |   |   |   |   |   |   |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  Depth feet | CILD mmho | IL ohm-m | SN ohm-m | DT μsec/ft | SPHI v/v decimal | Rwa | Swa v/v decimal | BVW  |
|  7442 |  |  |  |  |  |  |  |   |
|  7446 |  |  |  |  |  |  |  |   |
|  7349 |  |  |  |  |  |  |  |   |
|  7453 |  |  |  |  |  |  |  |   |
|  7455 |  |  |  |  |  |  |  |   |
|  7459 |  |  |  |  |  |  |  |   |

Log Interpretation Case Studies

207

![img-4.jpeg](img-4.jpeg)

Figure 10.22. Induction electric log with spontaneous potential, upper Morrow Sandstone, Anadarko Basin, U.S.A.

Note:

1. Deflection of the SP curve leftward in track 1, away from the shale baseline (7441 to 7452 ft), opposite the upper Morrow Sandstone.
2. Separation of the short normal resistivity curve (SN) and the induction resistivity curve (IL) in track 2; this indicates that the sandstone was invaded by mud filtrate.
3. At the depth of the upper Morrow Sandstone, leftward deflection of the SP curve and separation of the SN and induction resistivity curves are collateral evidence that leads to this conclusion: the sandstone is porous and permeable.
4. Looking at all the logs together, the resistivity logs (IL and SN) show the formation to be from 7441 to 7460 ft, whereas the SP shows the formation to be from 7441 to 7452 ft. Close inspection of the SP shows very slight deflection from the shale baseline over the bottom 8 ft of formation (7452 to 7460). The logs indicate that this interval is very shaly (SP response) and impermeable (IL and SN read the same, except for minor variation that is due to differences in vertical resolution of the measurements.).

208

ASQUITH AND KRYGOWSKI

Figure 10.23. Sonic log with spontaneous potential, upper Morrow Sandstone, Anadarko Basin, U.S.A.

Note:

The relatively high interval transit time at 7446 ft (DT = 81 μsec/ft) indicates that porosity of the sandstone is high. (See Track 2 between 7441 and 7460 ft.)

![img-5.jpeg](img-5.jpeg)

Log Interpretation Case Studies

209

# Case Study 4:

# PENNSYLVANIAN UPPER MORROW SANDSTONE, ANADARKO BASIN, U.S.A.:

The Solution.

# Information from the logs

The upper Morrow sandstone is in the interval from 7441 to 7460 ft as shown by the response of the logs (Figure 10.22). The logs show that the top 11 ft (from 7441 to 7452) is permeable, by leftward deflection of the SP from the shale baseline, and by separation between the short normal curve, SN ($R_t$), and the induction resistivity curve, IL ($\sim R_t$). Separation between the SN and IL indicates that the rock was invaded by mud filtrate. Porosity of the sand from 7441 to 7460 ft is apparent from the comparatively high interval transit time (DT, 70 to 81 $\mu$sec/ft, Figure 10.23). The interval from 7452 to 7460 ft is not permeable, as shown by the lack of SP response and by the SN and IL curves' having the same values (indicating no invasion).

The SP is read from Figure 10.22 as -45 mV. Remember that the shale baseline is assumed to have a value of zero, and that in this display the scale sensitivity is 20 mV per scale division. From Equations 10.34 and 10.35:

$$K = 61 + (0.133 \times T_f).$$

$$K = 61 + (0.133 \times 130).$$

$$K = 78.3$$

$$R_w = 10^{(K \times \log(R_{wa}) + SP)/K}$$

$$R_w = 10^{(78.3 \times \log(0.527) - 45)/78.3}$$

$$R_w = 0.140 \text{ ohm-m}$$

The calculated $R_w$ value is close to the suspect one (0.11 ohm-m at formation temperature).

Acoustic (sonic) porosity, SPHI, is calculated from the Wyllie time-average equation, Equation 10.33. Use the accepted values for matrix and fluid parameters: $\Delta t_{ma} = 55.5 \text{ } \mu\text{sec/ft}$; $\Delta t_{fl} = 189 \text{ } \mu\text{sec/ft}$.

Apparent water resistivity ($R_{wa}$) (see Chapter 7) is calculated from the induction log and the sonic porosity. The low value at the top of the formation (Table 10.8, 7442 ft) probably is due to boundary effects of shale on the induction log, which produce a lower-than-actual resistivity value. The other low value, 0.028 ohm-m at 7455 ft, is higher than the value calculated from the SP (0.014 ohm-m), and probably indicates residual hydrocarbons in that very shaly interval. In

general, the $R_{wa}$ results are consistent with the calculated value of $R_w$. The value of $R_w$ calculated from the SP (0.14 ohm-m) is considered to be the estimate most likely to be true; therefore it is used in the water saturation equation.

Archie water saturation ($S_{wa}$) is calculated using this estimate of $R_w$ and values of porosity determined above, and the other parameters noted previously.

# Information from crossplots

As suspected, water saturation ($S_{wa}$) values in the interval of porous sandstone (7441-7452 ft) are high (Table 10.8), ranging from 40 to 80 percent, and so are bulk volume water values (Figure 10.24). On the bulk volume water crossplot, the scatter of data points around the hyperbolic line is minor; this indicates that the reservoir may be at or near irreducible water saturation, but the points cluster around a value higher than the normal Morrow production cutoff. Therefore, water-production potential of the well remains in question.

You have completed assessment of the log and you should be encouraged by evidence of good porosities on the sonic log and good indications of permeability on the resistivity log. Also, you are aware that the low cost of re-entry of the well enhances the economics of the prospect.

However, you weigh the positive aspects of the prospect against the relatively thin zone and the few data points that you have used. The limited number of points calls into question the statistical accuracy of the information, and in turn, conclusions based on such limited data. Also, fine-grained reservoirs are not as permeable as coarse-grained reservoirs. Estimated recoverable oil is 78,000 stock-tank barrels (STB). Estimated return on investment is:

$$\text{Return} = \frac{\text{stock tank barrels (STB)} \times \text{product price}}{\frac{\times \text{net revenue interest (NRI)}}{\text{total cost}}} \tag{10.37}$$

$$\text{Return} = \frac{78,000 \times \$32.00 \times 0.8125}{\$275,000} = 7.4:1.$$

The ratio 7.4:1 is an excellent return on investment; the company accepts your recommendation to re-enter the well. (Note that the $32.00 per barrel price of oil used in this example was the value at the time the well was evaluated.)

The upper Morrow Sandstone was perforated from 7443 to 7451 ft. Initial production flowing (IPF) was

210 ASQUITH AND KRYGOWSKI

100 barrels of oil per day (BOPD) and 6 barrels of salt water per day (BSWPD), with oil gravity of 38.3. During the first four months, production averaged 75 BOPD, and after six months, production stabilized at 50 BOPD. Two years after completion, an offset well was drilled 1320 ft away. The second well had initial

production flowing (*IPF*) of 336 BOPD and no water, from a 19-ft upper Morrow sandstone. The sandstone was 13 ft higher than Morrow sandstone in the well that was the subject of this analysis.

Figure 10.25 Shows the results of detailed processing of data over the interval.

Log Interpretation Case Studies

211

Table 10.8. Case Study 4: Upper Morrow Sandstone, Anadarko Basin, U.S.A.: Solution table. The symbol "v/v" indicates volume-for-volume decimal fraction.

|  Parameters  |   |   |   |
| --- | --- | --- | --- |
|  Ann. Mean Surf. Temp: 70°F |   |   | Rw (measured): (not given)  |
|  Total Depth: 8,007 ft |   |   | Rw @ fm. temp.: 0.140 ohm-m @ 130°F  |
|  Bottom Hole Temp: 135°F |   |   | Rmf (measured): (not given)  |
|  Formation Depth: 7,441 ft |   |   | Rmf @ fm. temp.: 0.527 ohm-m @ 130°F  |
|  Formation Temperature: 130°F |   |   |   |
|  DT matrix (Wyllie): 55.5 μsec/ft |   |   | DT fluid (Wyllie): 189 μsec/ft  |
|   | a: 0.81 | m: 2 | n: 2  |

|  Data and Calculations  |   |   |   |   |   |   |   |   |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  Depth feet | CILD mmho | IL ohm-m | SN ohm-m | DT μsec/ft | SPHI v/v decimal | Rwa | Swa v/v decimal | BVW  |
|  7442 | 120 | 8.3 | 20 | 60 | 0.034 | 0.012 | >1.0 | 0.034  |
|  7446 | 90 | 11.1 | 30 | 81 | 0.191 | 0.500 | 0.529 | 0.101  |
|  7349 | 95 | 10.5 | 24 | 73 | 0.131 | 0.223 | 0.792 | 0.104  |
|  7453 | 130 | 7.7 | 8 | 97 | 0.311 | 0.918 | 0.391 | 0.121  |
|  7455 | 140 | 7.1 | 8 | 63 | 0.056 | 0.028 | >1.0 | 0.056  |
|  7459 | 120 | 8.3 | 11 | 84 | 0.213 | 0.469 | 0.546 | 0.117  |

212

ASQUITH AND KRYGOWSKI

Figure 10.24. Bulk-volume-water crossplot (SPHI vs. Swa), upper Morrow Sandstone, Anadarko Basin, U.S.A.

![img-6.jpeg](img-6.jpeg)

Figure 10.25. Upper Morrow Sandstone, Anadarko Basin, U.S.A. Computer-processed log.

In track 3 the dark shaded area between the porosity curve (SPHI) and the bulk-volume-water curve (BVW) indicates the proportion of pore space that is occupied by oil, whereas the light shaded area between the bulk-volume-water curve and the right margin of the track (scale value of zero) indicates the proportion that is occupied by water.

![img-7.jpeg](img-7.jpeg)

Log Interpretation Case Studies

213

# Case Study 5:

# **CRETACEOUS PICTURED CLIFFS SANDSTONE, SAN JUAN BASIN, U.S.A.:**

# *The Problem.*

Case Study 5 introduces a shaly sand interpretation, with equations for shale volume, effective porosities, and the Simandoux (1963) form of Archie's equation for shaly sands. The effective porosity and water saturation equations require the volume of shale ($V_{\text{shale}}$), calculated from the gamma ray log. Entering the equations into a spreadsheet program may be the most efficient way to do these somewhat-complex calculations.

# **Background**

The company that you work for has purchased a large block of acreage in the San Juan Basin, much of it with gas production. The company is pursuing an active development-drilling program of infilling new Pictured Cliffs Sandstone wells on 80-acre units, rather than on the 160-acre units required under previous rules of spacing.

You are presented with logs of a new infill well and are asked to evaluate them. In this well, the depth of the Pictured Cliffs Sandstone is from 1920 to 1964 ft. The log package includes an induction log with a spherically focused log (SFL) and an SP log (Figure 10.26). (Note that the induction log plot shows the spherically focused log as "SFLA," for Spherically Focused Log, Averaged. The SFL has been averaged so that its response resembles more closely the older short normal log. This allows better comparison of this new log with logs of older wells in the field.) A combination neutron-density log (recorded in sandstone porosity units) with a gamma ray log (Figure 10.27) also was run.

From experience you know that shale in sandstone can affect logging measurements adversely. Water saturations calculated by the Archie formula tend to be too high (see Chapter 7, Log Interpretation), because shale affects porosity logs and resistivity logs. Furthermore, shale in the reservoir tends to reduce permeability.

Careful examination of the neutron porosity log (NPHI) density porosity log (DPHI) and gamma ray log (GR) (Figure 10.27) convinces you that the Pictured Cliffs sandstone is shaly. A shaly sand analysis will be necessary. However, before following this investigative path, you decide to check the $R_w$ value

given for the area against a log-calculated $R_w$. (See Table 2.1 for $R_w$ formulas, and charts in Figures 2.3 to 2.5.)

# **Well site information and other pertinent information:**

- $BHT = 89^{\circ}\text{F}$ at 2145 ft
- surface temperature = $65^{\circ}\text{F}$
- formation temperature, $T_f = 87^{\circ}\text{F}$
- $R_{mf} = 2.26$ ohm-m at $65^{\circ}\text{F}$

Because of the infill-drilling program, your company is particularly interested in recoverable reserves based on 80-acre units. Reservoir depletion will not be a problem, because Pictured Cliffs Sandstone wells normally don't drain 160 acres. Volumetric recoverable gas reserves are estimated from the following parameters:

- drainage area ($DA$) = 80 acres
- reservoir thickness ($h$) (to be determined)
- effective porosity ($\phi_e$) (to be determined)
- water saturation ($S_w$) (to be determined)
- recovery factor ($RF$) = 0.75
- gas gravity (estimated) = 0.51
- reservoir temperature (estimated) = $87^{\circ}\text{F}$
- bottom hole pressure—estimated ) = 770 PSI
- Z factor = 0.928

# **Helpful equations**

In this older log-display format, resistivity is recorded on a linear scale, but conductivity is also shown, on a more sensitive scale. In strata where resistivity is low, a more accurate estimate of resistivity can be made by reading conductivity and reciprocating the number to get formation resistivity. The equation is shown in Case Study 4 (Equation 10.36):

$$R_{ILD} = \frac{1000}{C_{ILD}}$$

For shaly sand analysis of a formation, formulas for these calculations are required: volume of shale, corrected neutron and density porosity, and water saturation, corrected for the effect of shale.

Formulas for this shaly sand analysis are:

$$V_{shale} = I_{GR} = \frac{GR_{log} - GR_{clean}}{GR_{shale} - GR_{clean}} \tag{10.38}$$

$$NPHIc = NPHI - V_{shale} \times NPHI_{shale} \tag{10.39}$$

214

ASQUITH AND KRYGOWSKI

$$
DPHIc = DPHI - V_{\text{shale}} \times DPHI_{\text{shale}} \tag{10.40}
$$

$$
PHI = \sqrt{\frac{DPHIc^2 + NPHIc^2}{2}} \tag{10.41}
$$

$$
S_w = \frac{0.4 \times R_w}{PHI^2} \times \left[ \left( \frac{5 \times PHI^2}{R_t \times R_w} + \left( \frac{V_{\text{shale}}}{R_{\text{shale}}} \right)^2 \right)^{\frac{1}{2}} - \frac{V_{\text{shale}}}{R_{\text{shale}}} \right] \tag{10.42}
$$

where (formula variables):

$V_{\text{shale}} =$ calculated volume of shale

$GR_{\text{log}} =$ gamma ray reading from several positions in Pictured Cliffs Sandstone

$GR_{\text{clean}} =$ gamma ray reading of the cleanest part of the sandstone

$GR_{\text{shale}} =$ average gamma ray reading in a nearby shale

$NPHIc =$ neutron porosity corrected for shale

$NPHI_{\text{shale}} =$ neutron porosity of a nearby shale

$DPHIc =$ density porosity corrected for shale

$DPHI_{\text{shale}} =$ density porosity of a nearby shale

$PHI =$ effective porosity: neutron-density porosity corrected for shale and gas

$R_{\text{shale}} =$ deep resistivity reading of a nearby shale

Use Table 10.9 for the evaluation.

Table 10.9. Case Study 5: Pictured Cliffs Sandstone, San Juan Basin, U.S.A.: Work table. The symbol “v/v” indicates volume-for-volume decimal fraction.

|  Parameters  |   |   |   |
| --- | --- | --- | --- |
|  Ann. Mean Surf. Temp: 65°F |   |   | Rw (measured): ohm-m @ °F  |
|  Total Depth: 2145 ft |   |   | Rw @ fm. temp.: 0.24 ohm-m @ 87°F  |
|  Bottom Hole Temp: 89°F |   |   | Rmf (measured): 2.26 ohm-m @ 65°F  |
|  Formation Depth: 1930 ft |   |   | Rmf @ fm. temp.: 1.73 ohm-m @ 87°F  |
|  Formation Temperature: 87°F |   |   |   |
|  DT matrix (Wyllie): 55.5 μsec/ft |   |   | DT fluid (Wyllie): 189 μsec/ft  |
|  RHO matrix: 2.65 g/cm³ |   |   | RHO fluid: 1.0 g/cm³  |
|  GRclean : 63 API |   |   | GRshale: 120 API  |
|  DPHIshale: 0.14 |   |   | NPHIshale: 0.4  |
|  Rshale: 4.2 ohm-m |   |   |   |
|   | a: 1 | m: 2 | n: 2  |

|  Raw Data  |   |   |   |   |   |   |
| --- | --- | --- | --- | --- | --- | --- |
|  Depth feet | GR API | CILD mmho/m | ILD ohm-m | SFLA ohm-m | DPHI v/v decimal | NPHI v/v decimal  |
|  1,928 | 70 | 90 | 11.1 | 16 | 0.175 | 0.275  |
|  1,935 |  |  |  |  |  |   |
|  1,942 |  |  |  |  |  |   |
|  1,945 | 75 | 72 | 13.9 | 16 | 0.150 | 0.225  |
|  1,949 |  |  |  |  |  |   |
|  1,953 |  |  |  |  |  |   |
|  1,958 |  |  |  |  |  |   |
|  1,962 | 83 | 100 | 10.0 | 10 | 0.120 | 0.260  |

Log Interpretation Case Studies

215

Table 10.9. Case Study 5: Pictured Cliffs Sandstone, San Juan Basin, U.S.A.: Work table. The symbol "v/v" indicates volume-for-volume decimal fraction. (Cont'd.)

|  Porosity calculations  |   |   |   |   |
| --- | --- | --- | --- | --- |
|  Depth feet | Vshale v/v decimal | DPHIc v/v decimal | NPHIc v/v decimal | PHI v/v decimal  |
|  1,928 | 0.123 | 0.158 | 0.226 | 0.195  |
|  1,935 |  |  |  |   |
|  1,942 |  |  |  |   |
|  1,945 | 0.211 | 0.121 | 0.141 | 0.131  |
|  1,949 |  |  |  |   |
|  1,953 |  |  |  |   |
|  1,958 |  |  |  |   |
|  1,962 | 0.351 | 0.071 | 0.120 | 0.098  |

|  Saturation and other indicators  |   |   |   |   |   |   |
| --- | --- | --- | --- | --- | --- | --- |
|  Depth feet | Swa v/v decimal | Sw v/v decimal | Sxo v/v decimal | MHI | MOS | BVW  |
|  1,928 | 0.754 | 0.605 | >1.0 | 0.604 | 0.396 | 0.118  |
|  1,935 |  |  |  |  |  |   |
|  1,942 |  |  |  |  |  |   |
|  1,945 | >1.0 | 0.660 | 1.000 | 0.660 | 0.341 | 0.086  |
|  1,949 |  |  |  |  |  |   |
|  1,953 |  |  |  |  |  |   |
|  1,958 |  |  |  |  |  |   |
|  1,962 | >1.0 | 0.806 | >1.0 | 0.805 | 0.195 | 0.079  |

216

ASQUITH AND KRYGOWSKI

![img-8.jpeg](img-8.jpeg)

Figure 10.26. Induction-SFL log with spontaneous potential, Pictured Cliffs Sandstone, San Juan Basin, U.S.A.

Note:

SP deflection (negative, track 1) and resistivity (tracks 2 and 3) increase upward through the Pictured Cliffs Sandstone (1970 to 1924 ft), the result of decrease of shale within the sandstone.

Log Interpretation Case Studies

217

![img-9.jpeg](img-9.jpeg)

Figure 10.27. Combination neutron-density log with gamma ray and caliper logs, Pictured Cliffs Sandstone, San Juan Basin, U.S.A.

Note:

1) Neutron and density readings are recorded in units relative to sandstone.
2) On the caliper log (track 1), decrease of hole diameter in the interval 1926 to 1958 ft indicates mudcake, and therefore indicates that the sandstone is permeable.
3) Neutron porosity, NPHI, is greater than density porosity, DPHI (tracks 2 and 3), which is anomalous, for this reason: Sandstone-calibrated neutron and density logs in a clean, gas-bearing sandstone should show neutron porosity that is less than density porosity, because of gas effect ("crossover"). This explanation is justified by the evidence at hand: High neutron porosity of the Pictured Cliffs formation is the result of shale in the sandstone. Concentration of hydrogen in clay minerals of shale is high; consequently neutron porosity is recorded as being greater than the actual porosity.

218

ASQUITH AND KRYGOWSKI

# Case Study 5:

# **CRETACEOUS PICTURED CLIFFS SANDSTONE, SAN JUAN BASIN, U.S.A.:**

*The Solution.*

# **Visual evaluation of the logs**

The combination neutron-density log (Figure 10.27) was run on a sandstone matrix; the general configuration of the gamma ray curve and the mutual disposition of the neutron- and density-porosity curves alert you to the likelihood of shale in the reservoir. The gamma ray curve is only about 40 API units leftward from the shale baseline, on the average. Moreover, you know that in shale-free sandstone that contains oil or water, if the neutron and density logs were recorded on the basis of a sandstone matrix, one curve should approximately overlie the other. If the sandstone is shale-free and contains gas, the density-porosity reading should be greater than the neutron-porosity reading—the curves should show “crossover.” However, your examination of the Pictured Cliffs indicates that neutron porosity is greater than density porosity, except in the uppermost 4 ft. The absence of crossover and the high neutron porosity are indicative of shaly sandstone. In this case, response of the neutron and density logs to abundant shale has masked any response to gas.

Although the mudlog data is not available to verify the interpretation, you interpret the top 4 ft of the Pictured Cliffs to be coal. Your hypothesis is based on the following observations (Figure 10.27):

- (a) neutron porosity, NPHI, greater than 0.4;
- (b) density porosity, DPHI, greater than 0.4;
- (c) caliper curve in gauge—at hole diameter—except for topmost 1 ft; and
- (d) DRHO-curve average is almost zero.

If the hole were washed out, then neutron and density porosity should show large amounts of porosity—and they do, but caliper curve should show evidence of a washout and DRHO should show evidence of correction—but they don’t. The log signature could be explained with convergence of these four lines of evidence and one other—the resistivity spike at 1920-1924 ft. The weight of evidence is in favor of a 4-ft bed of coal. Following this line of reasoning, coal is also indicated at 1820-1824 ft, 1846-1850 ft and 1900-1908 ft—low density of coal: high density-porosity; cleat with high content of water: high neutron porosity.

Presumably the high carbon content of coal would

be manifest as high resistivity. Over the intervals that you estimate to be coal, in the uppermost two, the resistivity increases only slightly (Figure 10.26), but this is probably due to the thinness of the coal beds and the fact that the induction log has a vertical resolution of at the least 4 ft (depending on formation and borehole properties). The induction log is affected by the adjacent shales, even around the thickest of the coal beds.

Note that from 1923 to 1957 ft the caliper log (Figure 10.27) shows that the diameter of the borehole is less than the diameter of the drill bit. The reduced hole diameter indicates mudcake, which means that the sandstone has been invaded by mud filtrate.

# **Calculations**

First, calculate $R_w$. Equations in Table 2.1 (Chapter 2) or charts in Figures 2.3 to 2.5 are appropriate. The SP of -57 mV at 1935 ft (Figure 10.26; measured from the shale baseline, which is assumed to have an SP value of zero) yields these values:

$R_{mf}$ at $T_f$: $R_{mf} = 1.73$ ohm-m;

equivalent formation-water resistivity: $R_{we} = 0.284$ ohm-m; and

$R_w$ at $T_f$: $R_w = 0.24$ ohm-m.

Next, calculate effective porosity, PHI (average neutron-density porosity, shale- and gas-corrected), using Equations 10.39 to 10.41, and calculate the shaly sand water saturation using Equation 10.42. To do so, first calculate shale volume, $V_{shale}$, from the gamma ray log (Figure 10.27), by Equation 10.38: $GR_{clean} = 63$ API units (at 1953 ft) and $GR_{shale} = 120$ API units (at 1909 and 1915 ft).

Also, inspect the following parameters of clay, at 1897 ft (Figure 10.27): $NPHI_{shale} = 0.40$, $DPHI_{shale} = 0.14$, and $R_{shale} = 4.2$ ohm-m, all to be used in computing porosities and water saturation.

The resistivity can be determined more accurately if conductivity (CILD) is read (Figure 10.26), and resistivity is calculated from those values by use of Equation 10.36. Calculations of shale volume, effective porosity, and water saturation are shown in Table 10.10 (calculated by the Archie equation and by the method for shaly sand, from Equation 10.42).

Water saturation calculated by the standard Archie equation ($S_{wa}$) ranges from 0.66 to 1.0 (66% to 100%) (Table 10.10). These high water saturation values are a result of shale in the reservoir; $V_{shale}$ ranges from 0.0 to 0.35 (0% to 35%). By using the Simandoux (1963) shaly sand equation to correct for the effect of shale, water saturation estimates ($S_w$) are reduced to the range

Log Interpretation Case Studies

219

of 0.52 to 0.81 (52% to 81%). Such a substantial modification illustrates the importance of shaly sand analysis in the evaluation of some sandstone reservoirs.

The bulk-volume-water plot (Figure 10.28) shows deviation of points from a constant BVW value, indicating the potential for some water production.

Below 1956 ft the caliper log (Figure 10.27) shows no evidence of mudcake, indicating that permeability of the strata may be so low as to preclude production of water. Also, resistivity curves below 1956 ft (Figure 10.26) are almost of the same value, showing no attributes of an invasion profile.

Volumetric calculations yield a production estimate of approximately 0.19 BCF, based on the following parameters:

- drainage area \((DA) = 80\) acres
reservoir thickness \((h) = 30\) ft
- effective porosity \((\phi_e) = 0.15\) (15%)
water saturation \((S_w) = 0.60\) (60%)
recovery factor \((RF) = 0.75\)
- gas gravity (estimated) = 0.51
reservoir temperature (estimated) \(= 87^{\circ}\mathrm{F}\)
- bottom hole pressure (estimated) = 770 PSI
Z factor \(= 0.928\)

The information you have developed, the shallow reservoir, the low cost of drilling and production, and

the very low level of risk are altogether a compelling basis to recommend completion of the well.

Consider the writing of a report on the Pictured Cliffs Sandstone infill well: Summarize all of the favorable indicators. First, the formation is approximately 30 ft thick. Second, it is permeable, as shown by the mudcake (caliper log, Figure 10.27). Permeability also is indicated by the moveable hydrocarbon estimators (MHI and MOS, Table 10.10). Third, porosity that ranges from 10% to about 20% is documented by the neutron and density logs (Table 10.10).

The Pictured Cliffs was perforated from 1926 to 1954 ft. After an acid treatment and a sand frac, the well produced 350 mcfgpd with no water, on a 3/4-in. choke. During the first year of production, the well produced approximately 60 million cubic feet (60,000 mcf) of gas.

Figure 10.29 shows a computer-processed log of the Pictured Cliffs interval. Track 3 shows water saturation computed on the basis of the Simandoux (1963) shaly sand equation, corrected porosity, and bulk volume water. The dark shaded area between the porosity curve (left-hand) and the bulk-volume-water curve indicates the proportion of pore space that is occupied by gas; the light shaded area between the bulk-volume-water curve and the right margin of the track (scale value of zero) indicates the proportion occupied by water.

220

ASQUITH AND KRYGOWSKI

Table 10.10. Case Study 5: Pictured Cliffs Sandstone, San Juan Basin, U.S.A.: Solution table. The symbol "v/v" indicates volume-for-volume decimal fraction.

|  Parameters  |   |   |   |
| --- | --- | --- | --- |
|  Ann. Mean Surf. Temp: 65°F |   |   | Rw (measured): ohm-m @ °F  |
|  Total Depth: 2145 ft |   |   | Rw @ fm. temp.: 0.24 ohm-m @ 87°F  |
|  Bottom Hole Temp: 89°F |   |   | Rmf (measured): 2.26 ohm-m @ 65°F  |
|  Formation Depth: 1930 ft |   |   | Rmf @ fm. temp.: 1.73 ohm-m @ 87°F  |
|  Formation Temperature: 87°F |   |   |   |
|  DT matrix (Wyllie): 55.5 μsec/ft |   |   | DT fluid (Wyllie): 189 μsec/ft  |
|  RHO matrix: 2.65 g/cm³ |   |   | RHO fluid: 1.0 g/cm³  |
|  GRclean : 63 API |   |   | GRshale: 120 API  |
|  DPHIshale: 0.14 |   |   | NPHIshale: 0.4  |
|  Rshale: 4.2 ohm-m |   |   |   |
|   | a: 1 | m: 2 | n: 2  |

|  Raw Data  |   |   |   |   |   |   |
| --- | --- | --- | --- | --- | --- | --- |
|  Depth feet | GR API | CILD mmho/m | ILD ohm-m | SFLA ohm-m | DPHI v/v decimal | NPHI v/v decimal  |
|  1,928 | 70 | 90 | 11.1 | 16 | 0.175 | 0.275  |
|  1,935 | 74 | 70 | 14.3 | 19 | 0.160 | 0.240  |
|  1,942 | 72 | 60 | 16.7 | 20 | 0.170 | 0.230  |
|  1,945 | 75 | 72 | 13.9 | 16 | 0.150 | 0.225  |
|  1,949 | 70 | 65 | 15.4 | 19 | 0.180 | 0.260  |
|  1,953 | 63 | 87 | 11.5 | 15 | 0.120 | 0.220  |
|  1,958 | 82 | 95 | 10.5 | 12 | 0.155 | 0.240  |
|  1,962 | 83 | 100 | 10.0 | 10 | 0.120 | 0.260  |

Log Interpretation Case Studies

221

Table 10.10. Case Study 5: Pictured Cliffs Sandstone, San Juan Basin, U.S.A.: Solution table. The symbol "v/v" indicates volume-for-volume decimal fraction. (Cont'd.)

|  Porosity calculations  |   |   |   |   |
| --- | --- | --- | --- | --- |
|  Depth feet | Vshale v/v decimal | DPHIc v/v decimal | NPHIc v/v decimal | PHI v/v decimal  |
|  1,928 | 0.123 | 0.158 | 0.226 | 0.195  |
|  1,935 | 0.193 | 0.133 | 0.163 | 0.149  |
|  1,942 | 0.158 | 0.148 | 0.167 | 0.158  |
|  1,945 | 0.211 | 0.121 | 0.141 | 0.131  |
|  1,949 | 0.123 | 0.163 | 0.211 | 0.188  |
|  1,953 | 0.000 | 0.120 | 0.220 | 0.177  |
|  1,958 | 0.333 | 0.108 | 0.107 | 0.108  |
|  1,962 | 0.351 | 0.071 | 0.120 | 0.098  |

|  Saturation and other indicators  |   |   |   |   |   |   |
| --- | --- | --- | --- | --- | --- | --- |
|  Depth feet | Swa v/v decimal | Sw v/v decimal | Sxo v/v decimal | MHI | MOS | BVW  |
|  1,928 | 0.754 | 0.605 | >1.0 | 0.604 | 0.396 | 0.118  |
|  1,935 | 0.872 | 0.605 | 0.878 | 0.689 | 0.273 | 0.090  |
|  1,942 | 0.761 | 0.551 | 0.924 | 0.596 | 0.373 | 0.087  |
|  1,945 | >1.0 | 0.660 | 1.000 | 0.660 | 0.341 | 0.086  |
|  1,949 | 0.663 | 0.519 | 0.973 | 0.534 | 0.454 | 0.098  |
|  1,953 | 0.815 | 0.729 | >1.0 | 0.729 | 0.272 | 0.129  |
|  1,958 | >1.0 | 0.760 | 0.955 | 0.796 | 0.195 | 0.082  |
|  1,962 | >1.0 | 0.806 | >1.0 | 0.805 | 0.195 | 0.079  |

222

ASQUITH AND KRYGOWSKI

Figure 10.28. Bulk-volume-water crossplot (porosity, PHI vs. water saturation, Sw), Pictured Cliffs Sandstone, San Juan Basin, U.S.A.

![img-10.jpeg](img-10.jpeg)

Log Interpretation Case Studies

223

![img-11.jpeg](img-11.jpeg)

![img-12.jpeg](img-12.jpeg)

Figure 10.29. Pictured Cliffs Sandstone, San Juan Basin, U.S.A. Computer-processed log.

Track 3: The dark shaded area between the porosity curve (left-hand) and the bulk-volume-water curve indicates the proportion of pore space that is occupied by gas. The light-shaded area between the bulk-volume-water curve and the right-hand margin of the track (scale value of zero) indicates the proportion of pore space that is occupied by water.

224

ASQUITH AND KRYGOWSKI

# Case Study 6:

# **ORDOVICIAN-SILURIAN CHIMNEYHILL SUBGROUP, HUNTON GROUP, ANADARKO BASIN, U.S.A.:**

# *The Problem.*

The well that is the subject of Case Study 6 is in a carbonate-rock province. Logs of this well show information that can be attributed to variation in both lithology and formation fluid. Because this case study is in the latter part of the sequence of case studies, interpretation is left almost entirely to the reader.

# **Background**

A well owned by your company has just reached final depth after penetration of the target zone, carbonate rocks of the Hunton Group, in the Anadarko Basin. The top of the zone is at 16,303 ft. The well was drilled because subsurface geologic maps indicated an updip fault and a structurally low well that produced gas and water. When the log evaluation is finished, you will make a decision about whether to set casing and test the well for its production potential. If the well is to be tested, then you will be responsible for selecting depths for perforations.

# **Well site information and other pertinent information**

- Logs of this well were correlated with logs of the offset well, which produced gas and water. This well is 40 ft structurally high to the offset well.
- When this well penetrated the Chimneyhill Subgroup of the Hunton Group (Figures 10.30, 10.31), a drilling break was recorded. The penetration rate decreased from 10 min/ft to 5 min/ft, and the mud logger's chromatograph increased by 20 gas units.
- Examination of the bit cuttings showed that this part of the Hunton is dolomite, with minor amounts of chert. The dolomite is gray to gray-brown, medium crystalline, and sucrosic with vuggy porosity.

- Samples collected through the interval of the drilling break did not show evidence of fluorescence or oil-cut.
- Formation temperature, $T_f$, is 221°F; mean surface temperature is 70°F; $R_{mf}$ is 0.249 ohm-m at $T_f$.
- Recoverable volumetric gas reserves are calculated with these parameters:
  - drainage area ($DA$) = 640 acres
  - gas gravity = 0.63 (estimated)
  - reservoir temperature (estimated) = 221°F
  - bottom-hole pressure ($BHP$, estimated) = 7,260 psi
  - recovery factor (RF) = 0.75
  - Z factor = 1.165

# **Tasks required for interpretation of the logs**

To complete the calculation of reserves, the following information is needed: porosity ($\phi$), water saturation ($S_w$), and reservoir thickness ($h$).

In deep, hot wells—generally, wells deeper than 12,000 ft—correction of the neutron log usually is required for effects of temperature, and possibly, for effects of pressure. In Chapter 4, the influence of environmental conditions on the neutron log was explained. Of all the conditions, pressure and temperature were described as being the basis for the greatest correction of the neutron log. Also explained was the fact that charts used for correction must correspond to the service company and the type of neutron tool that was used.

A shortcut for computation—which will provide accuracy sufficient for this evaluation—is to determine the amount of correction needed for a high porosity value and a low porosity value in the formation, average the corrections, and apply the average correction to each neutron-log porosity value before using that measurement in additional calculations of porosity. In this well, that correction is +0.015 (an additional 1.5% porosity) to be added to each value of neutron porosity read from the log.

Table 10.11 will help you organize the information. A list of depths is provided, but you are free to determine your own depths for analysis.

Log Interpretation Case Studies

225

Table 10.11. Case Study 6: Chimneyhill Subgroup, Hunton Group, Anadarko Basin, U.S.A.: Work table. The symbol "v/v" indicates volume-for-volume decimal fraction.

|  Parameters |   |   |   |   |
| --- | --- | --- | --- | --- |
|  Ann. Mean Surf. Temp: 70°F |   |   |   | Rw (measured):  |
|  Total Depth: 16490 ft |   |   |   | Rw @ fm. temp.:  |
|  Bottom Hole Temp: 222°F |   |   |   | Rmf (measured): 0.70 ohm-m @ 74°F  |
|  Formation Depth: 16320 ft |   |   |   | Rmf @ fm. temp.: 0.249 ohm-m @ 22°F  |
|  Formation Temperature: 221°F |   |   |   |   |
|  a: 1 | m: 2 | n: 2 |  |   |

|  Raw data  |   |   |   |   |   |
| --- | --- | --- | --- | --- | --- |
|  Depth feet | ILD ohm-m | SFL ohm-m | DPHI v/v decimal | NPHI v/v decimal | NPHIc v/v decimal  |
|  16,305 |  |  |  |  |   |
|  16,308 |  |  |  |  |   |
|  16,310 |  |  |  |  |   |
|  16,315 |  |  |  |  |   |
|  16,321 |  |  |  |  |   |
|  16,325 |  |  |  |  |   |
|  16,330 |  |  |  |  |   |
|  16,339 |  |  |  |  |   |
|  16,345 |  |  |  |  |   |
|  16,351 |  |  |  |  |   |
|  16,357 |  |  |  |  |   |
|  16,361 |  |  |  |  |   |
|  16,367 |  |  |  |  |   |
|  16,371 |  |  |  |  |   |
|  16,376 |  |  |  |  |   |
|  16,382 |  |  |  |  |   |
|  16,389 |  |  |  |  |   |
|  16,400 |  |  |  |  |   |
|  16,410 |  |  |  |  |   |

226

ASQUITH AND KRYGOWSKI

Table 10.11. Case Study 6: Chimneyhill Subgroup, Hunton Group, Anadarko Basin, U.S.A.: Work table. The symbol "v/v" indicates volume-for-volume decimal fraction. (Cont'd.)

|  Saturation and other calculations  |   |   |   |   |   |   |
| --- | --- | --- | --- | --- | --- | --- |
|  Depth feet | Phia v/v decimal | Sw v/v decimal | Sxo v/v decimal | BVW | MHI | MOS  |
|  16,305 |  |  |  |  |  |   |
|  16,308 |  |  |  |  |  |   |
|  16,310 |  |  |  |  |  |   |
|  16,315 |  |  |  |  |  |   |
|  16,321 |  |  |  |  |  |   |
|  16,325 |  |  |  |  |  |   |
|  16,330 |  |  |  |  |  |   |
|  16,339 |  |  |  |  |  |   |
|  16,345 |  |  |  |  |  |   |
|  16,351 |  |  |  |  |  |   |
|  16,357 |  |  |  |  |  |   |
|  16,361 |  |  |  |  |  |   |
|  16,367 |  |  |  |  |  |   |
|  16,371 |  |  |  |  |  |   |
|  16,376 |  |  |  |  |  |   |
|  16,382 |  |  |  |  |  |   |
|  16,389 |  |  |  |  |  |   |
|  16,400 |  |  |  |  |  |   |
|  16,410 |  |  |  |  |  |   |

Log Interpretation Case Studies

227

![img-13.jpeg](img-13.jpeg)

Figure 10.30. Dual induction-SFL with spontaneous potential log and Rxo/Rt curve, Chimneyhill Subgroup, Hunton Group, Anadarko Basin, U.S.A.

Note:

1) In track 1, from 16,300 ft to 16,390 ft, deflection of the Rxo/Rt curve rightward from the SP curve indicates the presence of hydrocarbons.
2) In tracks 2 and 3, from 16,325 ft to 16,370 ft, resistivities are markedly lower than resistivities of strata above and below. This is evidence of a water-bearing zone or of a substantial difference in the type of carbonate rock.

228

ASQUITH AND KRYGOWSKI

![img-14.jpeg](img-14.jpeg)

Figure 10.31. Combination neutron-density log with gamma ray and caliper, Chimneyhill Subgroup, Hunton Group, Anadarko Basin, U.S.A.

Note:

(1) In Track 1, the decrease in hole diameter on the caliper curve, CALI, from 16,303 ft to 16,384 ft.: In this interval the thick mudcake is evidence of permeable rock.
(2) From 16,303 ft to 16,384 ft, neutron porosity, NPHI, and density porosity, DPHI, are greater than in strata above and below. Also, the neutron and density porosity are approximately equal. Because the Chimneyhill is dolomite, if the rock were water saturated or oil bearing, apparent neutron porosity should be greater than density porosity (the lithology effect of dolomite). This explanation would account for the facts: Because the Chimneyhill is gas bearing, the neutron-density porosities are recorded as being approximately equal; gas effect compensated for the effect of dolomite.

Log Interpretation Case Studies

229

# Case Study 6:

# ORDOVICIAN-SILURIAN CHIMNEYHILL SUBGROUP, HUNTON GROUP, ANADARKO BASIN, U.S.A.:

The Solution.

# Information from logs

- On the neutron-density log (Figure 10.31) the caliper curve (CALI) shows reduction of hole diameter from 16,303 ft to 16,384 ft, an indication of invasion. Also, the density correction (DRHO) is high over that interval, due to thick mudcake.
- Samples of bit cuttings indicated that the formation is dolomite, but the neutron and density curves are approximately overlain, which is a response suggestive of limestone (Figure 10.31). In dolomite, the neutron log should read more porosity than the density log, but in a gas zone the recorded neutron response tends to be decreased, in some cases to the point of being less than the density reading. The pattern that you are observing probably is that of gas-bearing dolomite. This inference would be in agreement with the well site observation that the mud-logger's instrument detected gas from the formation. (The fact is interesting to note that below the invaded zone, the neutron-density pattern is that of dolomite (Figure 10.31).)
- On the dual induction log (Figure 10.30), The SP shows negative deflection over the invaded interval, but boundaries of the negative salient are poorly defined (a common pattern in carbonate rock). The SP is deflected away from the Rxo/Rt curve by about four chart divisions; this pattern is indicative of the presence of hydrocarbons.
- Resistivities of strata from 16,303 ft to 16,324 ft (Figure 10.30) are greater than resistivities of strata in the underlying zone (16,324 to 16,362 ft) by approximately a factor of 10; from 16,362 ft to 16,384 ft resistivity increases. The pattern could be explained by increase of water saturation in the middle part of the stratigraphic section analyzed, by distinct differences in lithology, or by both.

As the analysis is begun, you decide to define these three zones in the invaded interval, and one zone directly below (from 16,384 ft to 16,412 ft, Figure 10.30), to decide whether differences will affect your

interpretation significantly. You've chosen the zones on the basis of distinct variation in log response. The zones, and provisional explanations of them are:

- Chimneyhill A: 16,303 ft to 16,324 ft (Figures 10.30, 10.31): High resistivity, neutron and density logs almost overlain; perhaps a dolomite response is masked by gas effect.
- Chimneyhill B: 16,324 ft to 16,362 ft: Comparatively low resistivity, neutron and density logs almost overlain and showing approximately the same porosity; possibly a zone of higher water saturation.
- Chimneyhill C: 16,362 ft to 16,384 ft: Porosity slightly greater than that of zone B, but higher resistivity. The higher resistivity is attributed more plausibly to difference in lithology than to lower water saturation—especially in consideration of its lower structural position, and the apparent vertical continuity of porous rock.
- Lower Zone: 16,384 ft to 16,412 ft: Higher resistivity than the zone directly above, but a distinct dolomite response of the porosity logs—low neutron porosity and negative density porosity; tight dolomite, probably with anhydrite (given the density log's excursion into negative porosities).

# Calculations and interpretation

Your first decision is to determine formation water resistivity, $R_w$, from the SP. Connect the apparent shale baselines above and below the Chimneyhill; at about 16,350 ft the SP is approximately -95 mV, as measured from the baseline. By use of formulas in Table 2.1 (or charts in Figures 2.4 and 2.5), $R_w$ is determined as being 0.021 ohm-m.

Next, calculate "apparent" porosity, Phia, by using the equation for neutron-density porosity in a gas zone (Case Study 1, Equation 10.18), with the neutron porosity corrected for temperature and pressure effects. On the basis of the calculated porosity, interpret $R_w$ from the Pickett plot (Figure 10.32) and compare it to $R_w$ calculated from the SP. Scatter of the points makes selection of a slope (from which to determine "m") difficult, but a slope of 2, consistent with "m" of carbonate rocks in general, is a reasonable fit. The Ro line (the line that depicts porosities and resistivities of dolomite at 100% water saturation) is set among the lowest group of points, at porosity of about 4%. (You will find this fact to be interesting: The group of points by which the 100%-water-saturation line is set was recorded from the Chimneyhill B zone,

230

ASQUITH AND KRYGOWSKI

rather than the underlying "C" zone. Because the logs show no evidence of a permeability barrier between the zones, a reasonable assumption is that lithology of the "C" zone is markedly different from lithology of zones A and B. Note that most of the points recorded from the highest zone, Chimneyhill A, show evidence of low water saturation.)

$R_w$ determined from the Pickett plot (Figure 10.32) is 0.04 ohm-m at formation temperature, somewhat different from the 0.021 ohm-m calculated from the SP. You decide to use the higher value of $R_w$, based on your confidence in the Pickett plot and the fact that the SP is unreliable in some carbonate-rock environments; also, the SP is affected by hydrocarbons. The choice of 0.04 ohm-m will produce pessimistic results ($S_w$ values will be higher than with an $R_w$ of 0.021), but if the analysis using this value is favorable, you should have more confidence in the production potential of the well.

Using the results of the calculations for porosity and $R_w$, calculate $S_w$ and $S_{so}$ from the Archie equation (Equations 10.1 and 10.2); then calculate the moveable oil saturation, MOS, moveable hydrocarbon index, MHI, and bulk volume water.

Now, consider the results (Table 10.12): In the Chimneyhill A and B zones (16,303 ft to 16,362 ft), all MHI values are less than 0.7; MOS values are high. The implication of these quantities is that hydrocarbons in zones A and B were moved by invading mud filtrate.

The bulk-volume-water crossplot (Figure 10.33) confirms that the "A" zone is at irreducible water saturation; BVW values are clustered around a line of about 0.008. This fact indicates that the formation is vuggy (Chapter 7, Table 7.1), consistent with the sample descriptions. Some data points of the Chimneyhill C zone lie along the 0.015 line (Figure 10.33), indicating a mix of vuggy and intergranular porosity, but a significant number of points are plotted distant from that line, indicating that the zone would produce water. However, interpretation of the Chimneyhill B zone is indistinct. Some of the points lie along a line of higher BVW (Figure 10.33), perhaps because of a different

lithology, or perhaps the zone is not at irreducible water saturation. Scatter of the points (Figure 10.33), as well as low resistivities, tend to indicate that water would be produced.

Zone A of the Chimneyhill (16,303 ft to 16,324 ft) has several favorable indicators. First, porosity ranges from about 4% to about 9% (Figure 10.31); it is intercrystalline and vuggy. Water saturations and bulk-volume-water values are low (Table 10.12). This evidence supports your decision to set pipe and to perforate the zone. In zone B (16,324 ft to 16,362 ft) water saturations and bulk-volume-water values are higher (Table 10.12); zone B may be water-productive. Because subsurface geologic maps indicate down-dip water, zone B might be avoided in perforating; however, in comparison to zone A, the higher water saturation and bulk-volume-water values of zone B may be due to a distinct difference in lithology. Evidence of different rock is the apparent reduction in vuggy porosity, indicated by the increase in bulk volume water from 16,324 ft to 16,362 ft (Table 10.12). If, in fact, the abrupt transition to lower resistivities in zone B (Table 10.12) is due to diminished vuggy porosity, then zone B may be at irreducible water saturation—zone B may be productive. Unfortunately, with no core to analyze, this explanation could be tested only by perforating the interval from 16,324 ft to 16,362 ft. This decision is made: do not perforate the Chimneyhill B interval.

Estimated recovery of gas is 3.27 BCF. Parameters employed to arrive at this figure are:

porosity \((\phi) = 0.06\) \((6\%)\)
water saturation \((S_w) = 0.17\) \((17\%)\) ; and
reservoir thickness \((h) = 8\) ft.

The Chimneyhill was perforated from 16,306 to 16,314 ft with 27 holes. Completion was natural and the calculated open flow (CAOF) of the well was 67,023 mcfgpd; shut-in tubing pressure was 4,639 psi. During the first six months of production, the well produced 0.455 BCF and 2,030 barrels of condensate.

Figure 10.34 shows a computer-processed log of the Chimneyhill interval.

Log Interpretation Case Studies

231

Table 10.12. Case Study 6: Chimneyhill Subgroup, Hunton Group, Anadarko Basin, U.S.A.: Solution table. The symbol "v/v" indicates volume-for-volume decimal fraction.

|  Parameters  |   |   |   |
| --- | --- | --- | --- |
|  Ann. Mean Surf. Temp: 70°F |   |   | Rw (measured):ohm-m @ °F  |
|  Total Depth: 16490 ft |   |   | Rw @ fm. temp.: 0.04 ohm-m @ 221°F  |
|  Bottom Hole Temp: 222°F |   |   | Rmf (measured): 0.70 ohm-m @ 74°F  |
|  Formation Depth: 16320 ft |   |   | Rmf @ fm. temp.: 0.249 ohm-m @ 221°F  |
|  Formation Temperature: 221°F |   |   |   |
|   | a: 1 | m: 2 | n: 2  |

|  Raw data  |   |   |   |   |   |
| --- | --- | --- | --- | --- | --- |
|  Depth feet | ILD ohm-m | SFL ohm-m | DPHI v/v decimal | NPHI v/v decimal | NPHIc v/v decimal  |
|  16,305 | 600 | 610 | 0.000 | 0.035 | 0.050  |
|  16,308 | 600 | 600 | 0.040 | 0.070 | 0.085  |
|  16,310 | 600 | 510 | 0.005 | 0.050 | 0.065  |
|  16,315 | 320 | 320 | 0.065 | 0.075 | 0.090  |
|  16,321 | 500 | 530 | 0.100 | 0.060 | 0.075  |
|  16,325 | 100 | 170 | 0.010 | 0.080 | 0.095  |
|  16,330 | 33 | 60 | 0.045 | 0.060 | 0.075  |
|  16,339 | 70 | 280 | 0.080 | 0.080 | 0.095  |
|  16,345 | 20 | 39 | 0.090 | 0.080 | 0.095  |
|  16,351 | 30 | 63 | 0.035 | 0.040 | 0.055  |
|  16,357 | 15 | 32 | 0.060 | 0.090 | 0.105  |
|  16,361 | 12 | 17 | 0.075 | 0.125 | 0.140  |
|  16,367 | 51 | 90 | 0.010 | 0.060 | 0.075  |
|  16,371 | 43 | 68 | 0.075 | 0.110 | 0.125  |
|  16,376 | 210 | 120 | 0.120 | 0.110 | 0.125  |
|  16,382 | 100 | 100 | 0.090 | 0.110 | 0.125  |
|  16,389 | 170 | 160 | -0.060 | 0.025 | 0.040  |
|  16,400 | 200 | 370 | -0.070 | 0.015 | 0.030  |
|  16,410 | 210 | 330 | -0.035 | 0.010 | 0.025  |

232 ASQUITH AND KRYGOWSKI

**Table 10.12.** Case Study 6: Chimneyhill Subgroup, Hunton Group, Anadarko Basin, U.S.A.: Solution table. The symbol "v/v" indicates volume-for-volume decimal fraction. (Cont'd.)

|  Saturation and other calculations  |   |   |   |   |   |   |
| --- | --- | --- | --- | --- | --- | --- |
|  Depth feet | Phia v/v decimal | Sw v/v decimal | Sxo v/v decimal | BVW | MHI | MOS  |
|  16,305 | 0.035 | 0.231 | 0.571 | 0.008 | 0.404 | 0.340  |
|  16,308 | 0.066 | 0.123 | 0.306 | 0.008 | 0.401 | 0.183  |
|  16,310 | 0.046 | 0.177 | 0.479 | 0.008 | 0.370 | 0.302  |
|  16,315 | 0.079 | 0.142 | 0.355 | 0.011 | 0.401 | 0.213  |
|  16,321 | 0.088 | 0.101 | 0.245 | 0.009 | 0.413 | 0.144  |
|  16,325 | 0.068 | 0.296 | 0.566 | 0.020 | 0.523 | 0.270  |
|  16,330 | 0.062 | 0.563 | 1.001 | 0.035 | 0.562 | 0.438  |
|  16,339 | 0.088 | 0.272 | 0.339 | 0.024 | 0.802 | 0.067  |
|  16,345 | 0.093 | 0.483 | 0.863 | 0.045 | 0.560 | 0.379  |
|  16,351 | 0.046 | 0.792 | 1.001 | 0.037 | 0.791 | 0.209  |
|  16,357 | 0.086 | 0.604 | 1.001 | 0.052 | 0.603 | 0.397  |
|  16,361 | 0.112 | 0.514 | 1.001 | 0.058 | 0.514 | 0.487  |
|  16,367 | 0.054 | 0.523 | 0.982 | 0.028 | 0.533 | 0.459  |
|  16,371 | 0.103 | 0.296 | 0.587 | 0.030 | 0.504 | 0.291  |
|  16,376 | 0.123 | 0.113 | 0.371 | 0.014 | 0.303 | 0.259  |
|  16,382 | 0.109 | 0.184 | 0.458 | 0.020 | 0.401 | 0.274  |
|  16,389 | -0.010 | 1.001 | 1.001 | 0.000 | 1.000 | 0.000  |
|  16,400 | -0.020 | 0.707 | 1.001 | 0.000 | 0.706 | 0.294  |
|  16,410 | -0.005 | 1.001 | 1.001 | 0.000 | 1.000 | 0.000  |

Log Interpretation Case Studies

233

![img-15.jpeg](img-15.jpeg)

![img-16.jpeg](img-16.jpeg)

Figure 10.32. Pickett plot, Chimneyhill Subgroup, Hunton Group, Anadarko Basin, U.S.A.

The *Ka* line (where water saturation is 100%) is interpreted from a group of points from the Chimney Hill B interval (Figure 10.30, at 16,324 ft to 16,362 ft). From the *Ka* line, *Kw* is interpreted as 0.04 ohm-m. The Archie cementation exponent, "m," is deduced from the plot as being 2, from measurement of the slope of the line.

Figure 10.33. Bulk-volume-water (BVW) crossplot (porosity, Phia vs. water saturation, Sw), Chimneyhill Subgroup, Hunton Group, Anadarko Basin, U.S.A.

234

ASQUITH AND KRYGOWSKI

![img-17.jpeg](img-17.jpeg)

Figure 10.34. Chimneyhill Subgroup, Hunton Group, Anadarko Basin, U.S.A. Computer-processed log.

Track 1 shows the SP curve and the gamma ray curve.

Track 2 shows the deep induction log and the spherically focused log.

Track 3 shows Archie water saturation, calculated from apparent (corrected) porosity. Also shown in track 3 are apparent porosity and bulk volume water. The dark shaded area between the porosity curve (left-hand) and the bulk-volume-water curve indicates the proportion of pore space that is occupied by gas. The light-shaded area between the bulk-volume-water curve and the right-hand margin of the track (scale value of zero) indicates the proportion that is occupied by water.

Log Interpretation Case Studies

235

# Case Study 7:

# PENNSYLVANIAN CANYON LIMESTONE, NEW MEXICO, U.S.A.:

# The Problem.

This case study illustrates the advantage of having a measurement of lithology that is largely independent of porosity and fluid saturation: the photoelectric effect ($Pe$) from the spectral density log. Because this case study is the final one of the sequence, the interpretation is left largely up to the reader to plan and complete. As with the other case studies, solutions are provided for validation of the reader's efforts.

If you decide to make an invasion correction of the dual laterolog, this equation will provide accuracy that is sufficient for this case study:

$$
R_{t} = (2 \times LLD) - LLS \tag{10.43}
$$

# Background

In the late 1990s an independent oil company drilled a 7150-ft well in southeastern New Mexico that

penetrated Precambrian basement. The well was drilled on a small faulted anticline. After the well was at total depth ($TD$), it was logged with this saltwatermud logging suite: Dual Laterolog-Rxo and Gamma Ray-Neutron-Spectral Density (Figure 10.35). Your task is to determine whether the zone is potentially productive, and if so, how much hydrocarbon is in place.

# Well site information and other pertinent information

These facts pertain to the porous Canyon zone from 6758 to 6772 ft (Figure 10.35):

- The neutron and density porosities (PHIN and PHID, respectively) are quantified with reference to limestone.
- From samples of bit cuttings, the zone was described as light tan to gray ooid grainstone with abundant oomoldic porosity.
- \(R_{w} = 0.03\) ohm-m at formation temperature.
- \(R_{mf} = 0.0406\) ohm-m at formation temperature.

The Work Table, Table 10.13, shows depths of zones suggested for interpretation; entries in the Solution Table (Table 10.14) are based on these depths.

Table 10.13. Canyon Sandstone, New Mexico, U.S.A.: Work table. The symbol "v/v" indicates volume-for-volume decimal fraction.

|  Parameters |   |   |   |   |
| --- | --- | --- | --- | --- |
|  Rw (measured): 0.03 ohm-m @ Tf |   |   |   | Rmf @ fm. temp.: 0.041 ohm-m @ Tf  |
|   | a: 1 | m: 2 | n: 2 |   |

|  Data  |   |   |   |   |   |   |
| --- | --- | --- | --- | --- | --- | --- |
|  Depth feet | LLD ohm-m | LLS ohm-m | MSFL ohm-m | Pe b/electron | PHID v/v decimal | PHIN v/v decimal  |
|  6760 |  |  |  |  |  |   |
|  6763 |  |  |  |  |  |   |
|  6768 |  |  |  |  |  |   |

|  Calculations  |   |   |   |   |   |   |   |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  Depth feet | Rt ohm-m | PhiNDgas v/v decimal | Swa v/v decimal | Sxo v/v decimal | Swr v/v decimal | MHI | BVW  |
|  6760 |  |  |  |  |  |  |   |
|  6763 |  |  |  |  |  |  |   |
|  6768 |  |  |  |  |  |  |   |

236

ASQUITH AND KRYGOWSKI

![img-18.jpeg](img-18.jpeg)

Figure 10.35. Dual laterolog-Rxo. Canyon Limestone, New Mexico, U.S.A. Vertical scale: 2 ft per chart division. Gamma ray curve scaled in API units. Resistivity curves scaled in ohm-m. Density porosity and neutron porosity scaled in porosity units, 0.04 per chart division.

Dual laterolog-Rxo. Canyon Limestone, New Mexico, U.S.A.

In the interval 6758 to 6772 ft note the following facts:

1. The dual laterolog exhibits a salt-mud hydrocarbon invasion profile. (See Chapter 1, Figure 1.5 for an example.)
2. The neutron and density porosity curves show crossover \((\phi \mathrm{d} > \phi \mathrm{n})\) in the zone described from cutting samples as limestone; the crossover is indicative of the presence of gas.
3. Average value of the Pe curve is about 5, which confirms that the zone is limestone.

Log Interpretation Case Studies

237

## Case Study 7:

### PENNSYLVANIAN CANYON LIMESTONE, NEW MEXICO, U.S.A.:

### The Solution.

From Figure 10.35 the following attributes of the Canyon interval (6758 to 6772 ft) can be discerned:

- The dual laterolog shows a profile consistent with invasion in a hydrocarbon-bearing zone.
- Neutron porosity is less than the density porosity (“crossover”). Because the formation is described as a limestone, and because the porosity curves are referenced to limestone, one would expect the porosity curves to be overlain directly if the formation were liquid-filled (oil or water). The crossover indicates gas in the formation.
- The Pe curve averages about 5 units, confirming that the zone is limestone, and that the neutron-density crossover is a pore-fluid effect (i.e. gas).

The following conclusions should be drawn from your calculations:

- The zone is porous, with gas-zone, neutron-density porosity (Equation 10.18) showing from 0.10 to 0.18 (10 to 18 %) (Table 10.14).
- Archie water saturations (Equation 10.1) range from 0.07 to 0.12 (7 to 12 %).
- Estimates of bulk volume water, BVW (Figure 10.36, and Table 10.14) range between 0.011 and 0.013; they are below the carbonate cutoff value of 0.015 (Chapter 7, Table 7.1), indicating

that the formation should produce water-free.

- The values for moveable hydrocarbon index (MHI) are under the carbonate cutoff of 0.6, also indicating that the Canyon should produce hydrocarbons.
- The Archie water saturation values ($S_{wa}$) are less than the ratio water saturation values ($S_{wr}$)—which is expected—because porosity of the Canyon zone is oomoldic (see pg. 117), as described from inspection of the bit-cutting samples.

The Canyon was perforated from 6760 to 6770 ft; initial potential flowing (IPF) was 918 mcfgpd plus 3 bopd and NO water. If you assume that this well will drain 160 acres, the original gas in place (OGIP), estimated from the equation below (from Equation 10.12), is 1.74 BCF (billion cubic feet).

$$OGIP = 43,560 \times PhiNDgas \times (1 - S_w) \times thickness \times ((0.43 \times depth)/14.7) \times area$$

where:

- $PhiNDgas = 0.14$ (average)
- $S_w = 0.10$ (average)
- thickness = 10 ft
- depth = 6766 ft (average)
- area = 160 acres

With the average recovery factor for this formation in this area of 0.70 (70%), the well could produce 1.21 bcf of gas. At a price of $2.00 per mcf, the production would be worth approximately $2,400,000.

See the sample calculations in Table 10.14, and results computed from samples spaced at one-half-foot intervals, shown in Figure 10.37.

238

ASQUITH AND KRYGOWSKI

Table 10.14. Case Study 7: Canyon Sandstone, New Mexico, U.S.A.: Solution table. The symbol “v/v” indicates volume-for-volume decimal fraction.

|  Parameters |   |   |   |   |
| --- | --- | --- | --- | --- |
|  Rw (measured): 0.03 ohm-m @ Tf |   |   |   | Rmf @ fm. temp.: 0.041 ohm-m @ Tf  |
|   | a: 1 | m: 2 | n: 2 |   |

|  Data  |   |   |   |   |   |   |
| --- | --- | --- | --- | --- | --- | --- |
|  Depth feet | LLD ohm-m | LLS ohm-m | MSFL ohm-m | Pe b/electron | PHID v/v decimal | PHIN v/v decimal  |
|  6760 | 170 | 150 | 80 | 5.0 | 0.135 | 0.050  |
|  6763 | 200 | 130 | 40 | 4.6 | 0.125 | 0.065  |
|  6768 | 130 | 95 | 35 | 4.9 | 0.230 | 0.115  |

|  Calculations  |   |   |   |   |   |   |   |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  Depth feet | Rt ohm-m | PhiNDgas v/v decimal | Swa v/v decimal | Sxo v/v decimal | Swr v/v decimal | MHI | BVW  |
|  6760 | 190 | 0.102 | 0.123 | 0.222 | 0.479 | 0.555 | 0.013  |
|  6763 | 270 | 0.100 | 0.106 | 0.321 | 0.249 | 0.329 | 0.011  |
|  6768 | 165 | 0.182 | 0.074 | 0.188 | 0.312 | 0.394 | 0.013  |

Log Interpretation Case Studies

239

![img-0.jpeg](img-0.jpeg)

Figure 10.36. Bulk-volume-water (BVW) plot, Canyon Limestone, New Mexico, U.S.A.

![img-1.jpeg](img-1.jpeg)

Figure 10.37. Canyon Limestone, New Mexico, U.S.A. Computer-processed log.

Note:

1. True formation resistivity, \( Rt \), calculated from LLD and LLS, is shown in Track 2 with the deep laterolog, LLD.
2. Archie water saturation, Swa, is shown as the light-shaded area from Swa = 1.0, on the left-hand side of Track 3.
3. Hydrocarbon-filled pore space is shown as the dark shaded area on the right-hand side of Track 3, between the porosity, PhiNDgas, and the bulk volume water, BVW. Water-filled pore space is shown as the light shaded area between BVW and the right-hand margin of the track (scale value of zero).

240 ASQUITH AND KRYGOWSKI

# References

Adams, J., L. Bourke, and R. Frisinger, 1987, Strategies for dipmeter interpretation: Part 2: The Technical Review, v. 35, p. 20–31.
Alger, R. P., 1980, Geological use of wireline logs (p. 207–222) in G. D. Hobson, ed., Developments in Petroleum–2: London, Applied Science Publishers, Ltd., 345 p.
Al-Waheed, H. H., T. M. Audah, and C. Cao Minh, 1994, Application of the azimuthal resistivity imager tool in Saudi Arabia: Society of Petroleum Engineers, Annual Conference and Exhibition, p. 811–818, paper SPE-28439.
Akkurt, R., D. Mardon, J. S. Gardner, D. M. Marschall, and F. Solanet, 1998, Enhanced diffusion: expanding the range of NMR direct hydrocarbon-typing applications: Society of Professional Well Log Analysts, 39th Annual Logging Symposium, Transactions, paper GG.
Archie, G. E., 1942, The electrical resistivity log as an aid in determining some reservoir characteristics: Journal of Petroleum Technology, v. 5, p. 54–62.
Asquith, G. B., 1979, Subsurface carbonate depositional models: a concise review: Tulsa, Oklahoma, PennWell Books, 121 p.
Asquith, G. B., 1980, Log analysis by microcomputer: Tulsa, Oklahoma, PennWell Books, 105 p.
Asquith, G. B., 1991, Log Evaluation of Shaly Sandstone Reservoirs: A Practical Guide: AAPG Course Notes Series, no. 31, 59 p.
Barber, T. D., 1983, Introduction to the Phasor dual induction tool; Society of Petroleum Engineers, 58th Annual Technical Conference, paper SPE-12049.
Barton, C. A., D. Moos, P. Peska, and M. D. Zoback, 1997, Utilizing wellbore image data to determine the complete stress tensor: Application to permeability anisotropy and wellbore stability: The Log Analyst, v. 38, p. 21–33.
Bassiouni, Z., 1994, Theory, Measurement, and Interpretation of Well Logs: Richardson, Texas, Society of Petroleum Engineers, 372 p.
Bateman, R. M., and C. E. Konen, 1977, The log analyst and the programmable pocket calculator: The Log Analyst, v. 18, p. 3–11.
Bell, J. S., and D. I. Gough, 1979, Northeast-southwest compressive stress in Alberta: Evidence from oil wells: Earth and Planetary Science Letters, v. 45, p. 475–482.
Bengsten, C. A., 1981, Statistical curvature analysis techniques for structural interpretation of dipmeter data: AAPG Bulletin, v. 65, p. 312–332.
Bengsten, C. A., 1982, Structural and stratigraphic uses of dip profiles in petroleum exploration, in M. T. Halbouty (ed.), The Deliberate Search for the Subtle Trap: AAPG Memoir 32, p. 31–45.
Berg, C. R., 1998, Synthetic deviation: A new dipmeter interpretation method: AAPG Bulletin, v. 82, p. 1133–1139.
Bigelow, E. L., 1985a, Making more intelligent use of log derived dip information. Part 1, Suggested guidelines: The Log Analyst, v. 26, no. 1, p. 41–53.
Bigelow, E. L., 1985b, Making more intelligent use of log derived dip information. Part 2, Well site data gathering considerations: The Log Analyst, v. 26, no. 2, p. 25–41.
Bigelow, E. L., 1985c, Making more intelligent use of log derived dip information. Part 3, Computer processing considerations: The Log Analyst, v. 26, no. 3, p. 18–31.
Bigelow, E. L., 1985d, Making more intelligent use of log derived dip information. Part 4, Structural interpretation: The Log Analyst, v. 26, no. 4, p. 21–43.
Bigelow, E. L., 1985e, Making more intelligent use of log derived dip information. Part 5, Stratigraphic interpretation: The Log Analyst, v. 26, no. 5, p. 25–64.
Bonner, S., M. Fredette, J. Lovell, B. Montaron, R. Rosthal, J. Tabanou, P. Wu, B. Clark, R. Mills, R. Williams, 1996, Resistivity while drilling—images from the string: Schlumberger Oilfield Review, v. 8, no. 1, p. 4–19.
Bornemann, E., T. Bourgeois, K. Bramlett, K. Hodenfield, and D. Maggs, 1998, The application and accuracy of geological information from a logging-while-drilling density tool: Society of Professional Well Log Analysts, 39th Annual Logging Symposium, Paper L, 14 p.
Bourke, L. T., P. Delfiner, J. C. Trouiller, T. Fett, M. Grace, S. Luthi, O. Serra, and E. Standen, 1989, Using Formation MicroScanner images: The Technical Review, v. 37, no. 1, p. 16–40.
Bourke, L. T., 1992, Sedimentological borehole image analysis in clastic rocks: A systematic approach to interpretation, in A. Hurst, C. M. Griffiths, and P. F. Worthington (eds.), Geological Applications of Wireline Logs II: London, The Geological Society, Special Publication 65, p. 31–42.
Brown, S. R., 1987, Fluid flow through rock joints: The effect of surface roughness: Journal of Geophysical Research, v. 92, no. B2, p. 1337–1347.

References

241

Buckles, R. S., 1965, Correlating and averaging connate water saturation data, Journal of Canadian Petroleum Technology, v. 9, no. 1, p. 42–52.

Carothers, J. E., 1968, A statistical study of the formation factor relation to porosity: The Log Analyst, v. 9, p. 38–52.

Carothers, J. E., and C. R. Porter, 1970, Formation factor-porosity relation from well log data, Society of Professional Well Log Analysts, 11th Annual Logging Symposium, Transactions, paper D.

Carr, D. L., R. A. Johns, R. Y. Elphick, and L. S. Foulk, 1997, High-resolution reservoir characterization of midcontinent sandstones using wireline resistivity imaging, Boonsville (Bend Conglomerate) gas field, Fort Worth Basin, Texas: The Log Analyst, v. 38, no. 6, p. 54–70.

Clavier, C., G. Coates, and J. Dumanoir, 1977, Theoretical and experimental bases for the dual-water model for interpretation of shaly sands: Society of Petroleum Engineers, Annual Meeting, paper SPE-6859.

Clavier, C., W. R. Hoyle, and D. Meunier, 1971, Quantitative interpretation of thermal neutron decay time logs: Part 1. Fundamentals and techniques: Journal of Petroleum Technology, v. 23, p. 743–755.

Coates, G., and J. L. Dumanoir, 1973, A new approach to improve log-derived permeability: Society of Professional Well Log Analysts, 14th Annual Logging Symposium, Transactions, paper R.

Coates, G. R., L. Xiao, and M. G. Prammer, 1999, NMR Logging Principles and Applications: Houston, Texas, Halliburton Energy Services, 232 p.

Cobb, C. C., and P. K. Schultz, 1992, Real-time electro-fiber-optic downhole video system: presented at the Offshore Technology Conference, Houston, TX, p. 575–582, paper SPE 25137.

Davies, D. H., O. Faivre, M-T. Gounot, B. Seeman, J-C. Troullier, D. Benimeli, A. E. Ferreira, D. J. Pittman, J-W. Smits, M. Randrianavony, B. I. Anderson, and J. Lovell, 1992, Azimuthal resistivity imaging—a new generation laterolog: Society of Petroleum Engineers, Annual Conference and Exhibition, p. 143–153, SPE-24676.

Dewan, J., 1983, Essentials of Modern Open-Hole Log Interpretation: Tulsa, Oklahoma, PennWell Publishing Company, 361 p.

Doll, H. G., 1948, The SP log, theoretical analysis and principles of interpretation: Transactions, AIME, v. 179, p. 146–185.

Dresser Atlas, 1974, Log Review 1: Houston, Texas, Dresser Industries, Inc.

Dresser Atlas, 1975, Log interpretation fundamentals: Houston, Texas, Dresser Industries, Inc.

Dresser Atlas, 1979, Log interpretation charts: Houston, Texas, Dresser Industries, Inc., 107 p.

Dresser Atlas, 1981, Spectralog, Houston, Texas, Dresser Industries, Inc.

Ekstrom, M. P., C. A. Dahan, M. Chen, P. M. Lloyd, and D. J. Rossi, 1986, Formation imaging with microelectrical scanning arrays: Society of Professional Well Log Analysts, 27th Annual Logging Symposium, Transactions, Paper BB, 21 p.

Ellis, D. V., 1987, Well Logging for Earth Scientists: New York, Elsevier, 532 p.

Fertl, W. H., 1975, Shaly sand analysis in development wells, Society of Professional Well Log Analysts, 16th Annual Logging Symposium Transactions, Paper A.

Fertl, W. H., 1978, Rwa Method-fast formation evaluation, in Practical log analysis-8: Oil and Gas Journal, v. 76, no. 37, p. 73–76.

Fertl, W. H., and W. C. Vercellino, 1978, Predict water cut from well logs, in Practical log analysis-4: Oil and Gas Journal, v. 76, no. 25, p. 111–116.

Gilbreath, J. A., 1987, Strategies for dipmeter interpretation: Part I: The Technical Review, v. 35, no. 3, p. 28–41.

Grace, L. M., and B. Newberry, 1998, Geological applications of electrical images and dipmeter: Short Course Notes, Schlumberger Oilfield Services, v. 8.1.

Guillotte, J. G., J. Schrank, and E. Hunt, 1979, Smackover reservoir: interpretation case study of water saturation versus production: Gulf Coast Association of Geological Societies, Transactions, v. 29, p. 121–126.

Halliburton Energy Services, 1994, Log Interpretation Charts (third printing): Houston, Texas, Halliburton Company.

Halliburton, 1996, Downhole video services: Applications and well preparation: Best Practices Series, Document H00023, Houston, Texas, Halliburton Company, 20 p.

Haws, G. W., and N. F. Hurley, 1992, Applications of pressure-interference data in reservoir characterization studies, Big Horn basin, Wyoming: Society of Petroleum Engineers, Annual Conference and Exhibition, p. 53–62, paper SPE 24668.

Hearst, J. R., P. H. Nelson, and F. L. Paillet, 2000, Well Logging for Physical Properties (second edition): Chichester, England, John Wylie and Sons, 106 p.

Heffer, K. J., and J. C. Lean, 1993, Earth stress orientation—a control on, and guide to, flooding directionality in a majority of reservoirs: in W. Linville

242 ASQUITH AND KRYGOWSKI

(ed.), *Reservoir Characterization III*, Tulsa, Oklahoma, PennWell, p. 799–822.Hilchie, D. W., 1978, *Applied openhole log interpretation*: Golden, Colorado, D. W. Hilchie, Inc., 309 p.Hilchie, D. W., 1979, *Old electric log interpretation*: Golden, Colorado, D. W. Hilchie, Inc., 161 p.Hilchie, D. W., 1982, *Advanced Well Log Interpretation*: Golden, Colorado, D. W. Hilchie, Inc., 300 p.Hingle, A. T., 1959, *The use of logs in exploration problems*: Society of Exploration Geophysicists, 29th Meeting.Höcker, C., K. M. Eastwood, J. C. Herweijer, and J. T. Adams, 1990, *Use of dipmeter data in clastic sedimentological studies*: AAPG Bulletin, v. 74, p. 105–118.Hurley, N. F., 1994, *Recognition of faults, unconformities, and sequence boundaries using cumulative dip plots*: AAPG Bulletin, v. 78, p. 1173–1185.Hurley, N. F., D. R. Thorn, J. L. Carlson, and S. L. W. Eichelberger, 1994, *Using borehole images for target zone evaluation in horizontal wells*: AAPG Bulletin, v. 78, p. 238–246.Hurley, N. F., 1996, *Parasequence-scale stratigraphic correlations in deep-marine sediments using borehole images*, in J. A. Pacht, R. E. Sheriff, and R. F. Perkins (eds.), *Stratigraphic Analysis Utilizing Advanced Geophysical, Wireline, and Borehole Technology for Petroleum Exploration and Production*: Gulf Coast Section SEPM, 17th Annual Research Conference, p. 147–152.Hurley, N. F., R. A. Zimmermann, D. Pantoja, 1998, *Quantification of vuggy porosity in a dolomite reservoir from borehole images and core*, Dagger Draw Field, New Mexico: Society of Petroleum Engineers, Annual Conference and Exhibition, 14 p., paper SPE 49323.Jaafar, I. B., 1980, *Depositional and diagenetic history of the B-zone of the Red River Formation (Ordovician) of the Beaver Creek Field*, Golden Valley County, North Dakota: M.S. thesis, West Texas State University, Canyon, Texas, 68 p.Knight, C. N., 1999, *Structural and stratigraphic controls on Mesaverde reservoir performance*: North La Barge field, Sublette County, Wyoming: Unpublished Ph.D. dissertation, Colorado School of Mines, Golden, Colorado, 217 p.Kobesh, F. P. and R. B. Blizzard, 1959, *Geometric factors in sonic logging*: Geophysics, v. 24, p. 64–76.Koepsell, R. J., F. E. Jenson, and R. L. Langley, 1989a, *Formation imaging—1, Formation imaging yields precise fault orientation, minimizes dry offsets*: Oil & Gas Journal, v. 87, no. 49, p. 55–58.Koepsell, R. J., F. E. Jenson, and R. L. Langley, 1989b, *Formation imaging—2, Imaging aids visualization of faults*: Oil & Gas Journal, v. 87, no. 50, p. 85–86.Lacazette, A., 1996, *The STAR (Simultaneous Acoustic and Resistivity) Imager*: London Petrophysical Society, Borehole Imaging Seminar, 3 p.Larionov, V. V., 1969, *Borehole Radiometry*: Moscow, U.S.S.R., Nedra.Lau, J. S. O., L. F. Auger, and J. G. Bisson, 1987, *Subsurface fracture surveys using a borehole television camera and acoustic televiewer*: Canadian Geotechnical Journal, v. 24, p. 499–508.Logan, W. D., J. P. Horkowitz, R. Laronga, and D. Cromwell, 1997, *Practical application of NMR logging in carbonate reservoirs*: Society of Petroleum Engineers, Annual Technical Conference and Exhibition, Proceedings (Formation evaluation and reservoir geology), p. 203–215, Paper SPE 38740.Luthi, S. M., and J. R. Banavar, 1988, *Application of borehole images to three-dimensional geometric modeling of eolian sandstone reservoirs*, Permian Rotliegende, North Sea: AAPG Bulletin, v. 72, p. 1074–1089.Luthi, S. M., and P. Souhaite, 1990, *Fracture apertures from electrical borehole scans*: Geophysics, v. 55, p. 821–833.Maute, R. E., 1992, *Electrical Logging: State-of-the-Art*: The Log Analyst, v. 33, p. 206–227.Martin, A. J., S. T. Solomon, and D. J. Hartmann, 1997, *Characterization of petrophysical flow units in carbonate reservoirs*: AAPG Bulletin, v. 81, p. 734–759.Morris, R. L., and W. P. Biggs, 1967, *Using log-derived values of water saturation and porosity*: Society of Professional Well Log Analysts, 8th Annual Logging Symposium, Transactions, Paper O.Mullins, J. E., 1966, *Stereoscopic deep well photography in opaque fluids*: Society of Professional Well Log Analysts, 7th Annual Logging Symposium Transactions, Paper N, 9 p.Newberry, B. M., L. M. Grace, and D. D. Stief, 1996, *Analysis of carbonate dual porosity systems from borehole electrical images*: Society of Petroleum Engineers, Permian Basin Oil And Gas Recovery Conference, p. 123–129, paper SPE-35158.Paillet, F. L., C. Barton, S. Luthi, F. Rambow, and J. Zemanek (eds.), 1990, *Borehole imaging*: Society of Professional Well Log Analysts Reprint Volume, 472 p.Parker, D. L., and P. D. Heffernan, 1993, *Methods of determining induced fracture orientation—Ferrier*

References

243

field application: Canadian Well Logging Society Annual Journal, p. 284–298.

Pickett, G. R., 1966, A review of current techniques for determination of water saturation from logs: Journal of Petroleum Technology, v. 18, no. 11, p. 1425–1433.

Pickett, G. R., 1973, Pattern recognition as a means of formation evaluation, Society of Professional Well Log Analysts, 14th Annual Logging Symposium, Transactions, Paper A.

Pickett, G. R., 1977, Recognition of environments and carbonate rock type identification: in Formation evaluation manual unit II, section exploration wells: Tulsa, Oklahoma, Oil and Gas Consultants International, Inc., p. 4–25.

Plumb, R. A., and S. H. Hickman, 1985, Stress-induced borehole elongation—a comparison between the four-arm dipmeter and the borehole televiewer in the Auburn geothermal well: Journal of Geophysical Research, v. 90, no. B7, p. 5513–5521.

Poupon, A., and J. Leveaux, 1971, Evaluation of water saturation in shaly formations: The Log Analyst, v. 12, no. 4, p. 3–8.

Raymer, L. L., E. R. Hunt, and J. S. Gardner, 1980, An improved sonic transit time-to-porosity transform: Society of Professional Well Log Analysts, 21st Annual Logging Symposium, Transactions, Paper P.

Reid, R. R., and M. B. Enderlin, 1998, True pay thickness determination of laminated sand and shale sequences using borehole resistivity image logs: Society of Professional Well Log Analysts, 39th Annual Logging Symposium, Transactions, Paper GGG, 9 p.

Rosthal, R. A., R. A. Young, J. R. Lovell, L. Buffington, and C. L. Arceneaux Jr., 1995, Formation evaluation and geological interpretation from the resistivity-at-the-bit tool: Society of Petroleum Engineers, Annual Conference and Exhibition, p. 187–199, paper SPE 30550.

Schlumberger, 1972, Log Interpretation, Vol. I—Principles: New York, Schlumberger Limited, 112 p.

Schlumberger, 1974, Log Interpretation, Vol. II—Applications: New York, Schlumberger Limited, 116 p.

Schlumberger, 1975, A guide to wellsite interpretation for the Gulf Coast: Schlumberger Offshore Services, 58 p.

Schlumberger, 1979, Log Interpretation Charts: Houston, Texas, Schlumberger Limited, 97 p.

Schlumberger, 1983, Stratigraphic high resolution dipmeter tool: Paris, Schlumberger Limited, Document No. M-08630, 23 p.

Schlumberger, 1984, Electromagnetic Propagation Tool: Houston, Texas, Schlumberger Well Services.

Schlumberger, 1993, Ultrasonic Imaging—USI, Ultrasonic Imager; UBI, Ultrasonic Borehole Imager: Houston, Texas, Schlumberger Wireline and Testing, Document No. SMP-9230, 28 p.

Schlumberger, 1998, Log Interpretation Charts: Sugar Land, Texas, Schlumberger Wireline and Testing, SMP-7006.

Seiler, D., C. Edmiston, D. Torres, and J. Goetz, 1990, Field performance of a new borehole televiewer tool and associated image processing techniques: Society of Professional Well Log Analysts, 31st Annual Logging Symposium, Transactions, Paper H, 20 p.

Seiler, D., G. King, and D. Eubanks, 1994, Field test results of a six arm microresistivity borehole imaging tool: Society of Professional Well Log Analysts, 35th Annual Logging Symposium, Transactions, Paper W, 21 p.

Serra, O., 1984, Fundamentals of Well-log Interpretation: New York, Elsevier, 423 p.

Serra, O., 1989, Formation MicroScanner image interpretation: Houston, Texas, Schlumberger Educational Services, 117 p.

Sethi, D. K., 1979, Some considerations about the formation resistivity factor-porosity relationships: Society of Professional Well Log Analysts, 20th Annual Logging Symposium, Transactions, paper L.

Society of Professional Well Log Analysts, 1984, Glossary of terms and expressions used in well logging: Houston, Texas, Society of Professional Well Log Analysts, 116 p.

Simandoux, P., 1963, Mesures dielectriques en milieu poreux, application a mesure des saturations en eau: Etude du Comportement des Massifs Argileux, Revue de l'institut Francais du Petrole, Supplementary Issue.

Smits, J. W., D. Benimeli, I. Dubourg, O. Faivre, D. Hoyle, V. Tourillon, J-C. Troullier, and B. I. Anderson, 1995, High resolution from a new laterolog with azimuthal imaging: Society of Petroleum Engineers, Annual Conference and Exhibition, p. 563–576, paper 30584.

Sovich, J., J. Klein, and N. Gaynor, 1996, A thin bed model for the Kuparuk A sand, Kuparuk River field, North Slope, Alaska: Society of Professional Well Log Analysts, 37th Annual Logging Symposium, Transactions, Paper D, 13 p.

244 ASQUITH AND KRYGOWSKI

Springer, J., 1987, Stress orientations from wellbore breakouts in the Coalinga area: *Tectonics*, v. 6, p. 667–676.Steiber, S. J., 1970, Pulsed neutron capture log evaluation in the Louisiana Gulf Coast: Society of Petroleum Engineers, 45th Annual Meeting, paper SPE-2961.Suau, J., P. Grimaldi, A. Poupon, and G. Souhaite, 1972, Dual Laterolog—Rxo tool: Society of Petroleum Engineers, 47th Annual Meeting, paper SPE-4018.Svor, T. R., and D. N. Meehan, 1991a, Quantifying horizontal well logs in naturally fractured reservoirs—I: Society of Petroleum Engineers, Annual Conference and Exhibition, p. 469–480., paper SPE 22704.Svor, T. R., and D. N. Meehan, 1991b, Quantifying horizontal well logs in naturally fractured reservoirs—II: Society of Petroleum Engineers, Annual Conference and Exhibition, p. 471–480, paper SPE 22932.Timur, A., 1968, An investigation of permeability, porosity, and residual water saturation relationships for sandstone reservoirs: *The Log Analyst*, v. 9, p. 8–17.Tittman, J., and J. S. Wahl, 1965, The physical foundations of formation density logging (Gamma-Gamma): *Geophysics*, v. 30, p. 284–294.Tixier, M. P., R. P. Alger, and C. A. Doh, 1959, Sonic logging, *Journal of Petroleum Technology*, v. 11, no. 5, p. 106–114.Tixier, M. P., R. P. Alger, W. P. Biggs, and B. N. Carpenter, 1963, Dual induction-laterolog—a new tool for resistivity analysis: Society of Petroleum Engineers, 38th Annual Meeting, paper SPE-713.Truman, R., R. P. Alger, J. Connell, and R. L. Smith, 1972, Progress report on interpretation of the dual spacing neutron log (CNL): Society of Professional Well Log Analysts, 13th Annual Logging Symposium, Transactions, paper U.Watney, W. L., 1979, Gamma ray-Neutron cross-plots as an aid in sedimentological analysis (p. 81–100), in D. Gill and D. F. Merriam (eds.), *Geomathematical and petrophysical studies in sedimentology*: New York, Pergamon Press, 266 p.Watney, W. L., 1980, Cyclic sedimentation of the Lansing-Kansas City groups in northwestern Kansas and southwestern Nebraska: Kansas Geological Survey Bulletin 220, 72 p.Waxman, M. H., and L. J. M. Smits, 1968, Electrical conductivities in oil-bearing shaly sands: Society of Petroleum Engineers *Journal*, v. 245, p. 107–122.Waxman, M. H., and E. C. Thomas, 1974, Electrical conductivity in shaly sands—I: *Journal of Petroleum Technology*, v. 257, p. 213–225.Wermund, E. G., 1975, Upper Pennsylvanian limestone banks, north central Texas: University of Texas, (Austin), Bureau of Economic Geology Circular 75-3, 34 p.Western Atlas International, Inc., 1995, Log Interpretation Charts, Houston, Texas, Western Atlas, 300 p.Whittaker, J. L., and G. D. Linville, 1996, Well preparation—essential to successful video logging: Society of Petroleum Engineers, 66th Western Region Meeting, p. 297–308, paper SPE 35680.Williams, C. G., P. D. Jackson, M. A. Lovell, and P. K. Harvey, 1997, Assessment and interpretation of electrical borehole images using numerical simulations: *The Log Analyst*, v. 38, no. 6, p. 34–44.Witton, E. M., 1999, Outcrop and subsurface characterization of the Lewis Shale, Carbon County, Wyoming: Unpublished M.S. thesis, Colorado School of Mines, Golden, Colorado, 214 p.Wyllie, M. R. J., and W. D. Rose, 1950, Some theoretical considerations related to the quantitative evaluations of the physical characteristics of reservoir rock from electric log data: *Journal of Petroleum Technology*, v. 189, p. 105–110.Wyllie, M. R. J., A. R. Gregory, and G. H. F. Gardner, 1958, An experimental investigation of the factors affecting elastic wave velocities in porous media: *Geophysics*, v. 23, p. 459–493.Younes, A. I., T. Engelder, and W. Bosworth, 1998, Fracture distribution in faulted basement blocks: Gulf of Suez, Egypt, in M. P. Coward, T. S. Daltaban, and H. Johnson, (eds.), *Structural Geology in Reservoir Characterization: London, The Geological Society, Special Publication 127*, p. 167–190.Zemanek, J., E. E. Glenn, L. J. Norton, and R. L. Caldwell, 1970, Formation evaluation by inspection with the borehole televiewer: *Geophysics*, v. 35, p. 254–269.Zoback, M. D., D. Moos, L. Mastin, and R. N. Anderson, R. N., 1985, Well bore breakouts and in situ stress: *Journal of Geophysical Research*, v. 90, no. B7, p. 5523–5530.

