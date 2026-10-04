<!-- Source: https://www.netl.doe.gov/node/3953 -->
<!-- Converted: html2text -->

Skip to main content

Selection and Treatment of Stripper Gas Wells for Production Enhancement in the Midcontinent

Project Number

DE-FG26-00NT40789

Goal

Develop techniques or technologies that will improve the production performance of stripper gas wells by using artificial intelligence techniques to identify patterns in the way wells produce. This could lead to a better selection process for remedial work that improves production performance.

Performer(s)

Advanced Resources International, Inc. – Project management and all research products   
Oneok Resources – industry partner providing wells for testing

**Location:**  
Houston, TX 77042  
Tulsa, OK 74103

Background

Research conduct by GRI in the late 1990s showed that potential existed for adding reserves in existing non-conventional plays through the restimulation of carefully selected candidate wells. A field-demonstration program targeted at tight sand formations, concluded in 2001, resulted in the restimulation of nine wells in the Green River, Piceance and East Texas basins, and the addition of 2.9 Bcf of reserves at an average cost of $0.26/Mcf. A combination of fundamental engineering and advanced pattern recognition was found to be a more effective approach for identifying candidate wells than simple statistical methods.

This project was designed to determine if a similar approach could also be applied to stripper gas wells to identify more general production enhancement opportunities (beyond only restimulation), such as via artificial lift and compression. The overall approach for the project was to select a field test site, apply the candidate recognition methodology to select wells for remediation, remediate them, and then gauge project success based on the field results.

Impact

This project developed a methodology in which a stripper well operator can easily identify wells with remediation potential, verify well performance problems and select an appropriate remediation procedure. This methodology is beneficial to stripper well operators as they usually have limited technical and manpower resources and this methodology will help identify those wells which the operators should be focusing their resources on.

Accomplishments (most recent listed first)

  * Collected data and constructed type curves for relating well performance to permeability-thickness, drainage area and fracture efficiency in the study wells,
  * Constructed a well performance cross-plot to identify candidates for remediation,
  * Applied artificial neural networks and genetic algorithms to identify production enhancement candidates,
  * Estimated production enhancement opportunity represented by artificial lift and compression for the candidate wells,
  * Applied a heuristic approach to the selection of candidate wells using the data developed in each of the analyses, and
  * Successfully tested the accuracy of the candidate selections against the results from six actual workovers, two of which were candidates based on the selection procedure.


The site selected for the project was the Mocane-Laverne field in Oklahoma’s central Anadarko basin. The field produces from four main horizons, the Hoover and Tonkawa (Upper Pennsylvanian), the Morrow (Lower Pennsylvanian), and the Chester (Upper Mississippian) (in order of increasing depth). The uppermost three horizons are sandstones, and the lowermost (Chester) is a limestone. The industry partner for the project was Oneok Resources, who operates over 100 wells in the field. About 75% of the wells are completed in either the Morrow or Chester, and the wells date from the 1950’s to the 1990’s, representing a broad cross-section of completion practices. The study wells represent historically good-performing, older wells that have depleted. The wells now also suffer from liquid production, which can inhibit gas flow. Small-sized stimulations (or none in some cases), the absence of artificial lift, and limited compression suggest production enhancement opportunities.

Building upon the findings from the earlier research, the candidate selection procedure involved a combination of engineering, pattern recognition, and heuristic approaches. The specific procedure was: perform engineering (type-curve) analysis to identify potential candidates, perform artificial neural network (ANN) and genetic algorithm (GA) analyses to identify potential candidates, combine the results of the first two steps, plus the findings from data exploration, in a heuristic candidate selection process.

Type curves were created using producing history (volumes and pressures) net pay thickness, initial pressure and temperature, porosity, water saturation and fluid properties obtained from well files and public sources. Initial pressures were obtained from a correlation developed for individual formations using annual 24-hour buildup surveys. Using these data, type curve matches were made for each completion to determine permeability-thickness, thickness-drainage area, and fracture penetration. About 20 percent of the matches were considered “good” while 35 percent were considered “poor.” To determine production enhancement potential, a well performance cross-plot was created to relate normalized well performance (ultimate recovery divided by reservoir drawdown) to a reservoir volume and transmissibility function (the product of effective reservoir volume and permeability. This resulted in a simple model of well performance, with wells falling below the trend line highlighted as sub-performers.

The second analytic technique applied used artificial neural networks and genetic algorithms to identify production enhancement candidates. Artificial neural networks can recognize complex patterns in how multiple inputs (e.g., geologic, drilling, completion, stimulation, and workover data) impact an output (i.e., production). The relative contribution of “uncontrollable” geologic/reservoir parameters can thus be separated from “controllable” drilling, completion, and stimulation parameters. This in effect is the separation of reservoir and completion components (i.e., permeability and skin). Genetic algorithms are then used to “optimize” the “controllable” input parameters for any given well, and those wells where the greatest discrepancies exist between actual well performance and optimized performance are identified as production enhancement opportunities.

In this project, two models were constructed; one for wells that had been previously stimulated, and one for wells that had not been previously stimulated. For the first model, 61 wells were used for training the model and 31 were used to test it. For the second model, only 13 wells existed – 9 were used for model training and 4 for testing. Correlation coefficients for the model predictions versus actual well performance for the first model (stimulated wells) indicated a reasonably good match was achieved. Genetic algorithm analysis was then performed to determine restimulation potential for the wells. The magnitude of any differences between actual well performance (EUR) and predicted performance with optimized stimulation parameters was the ranking criteria for restimulation opportunity.

To estimate the production opportunity represented by artificial lift and compression, the performance of each well was modeled assuming the installation of a pumping unit, and reducing the flowing pressure to 28 psi (the average value for wells on compression). The total incremental potential was then summed and ranked on that basis. In this case, the total incremental could be allocated between the three production enhancement categories (restimulation, artificial lift, compression).

A heuristic approach to the selection of candidate wells was then applied. The criteria for selection included the results of the data exploration, the type-curve analysis, the artificial intelligence analysis, and also the most recent producing rate (prior R&D indicated that the better the most recent rate, the better the candidate a well is for production enhancement). Based on these criteria, two lists were created: the “A” list represented wells that had at least four “hits” of the above criteria, and the “B” list were wells with at least three “hits” each. List A had 5 wells and list B had 17 wells. Within each candidate group the wells were further prioritized based on the presence of an unstimulated horizon in the well, the rank within the top 45 based on both artificial intelligence and most recent producing rate, and rank within the top 30 for at least one of the above criteria. Using these rules, certain wells (one in list A and six in list B) were highlighted as the top priority candidates for production enhancement, based on the analysis performed, for the dataset of study wells evaluated.

The accuracy of the candidate selections was tested against the results from six actual workovers. Two of the six workover wells were the candidates from the selection procedure, and the other four were not. Workovers on the two selected candidates were considered “successful” based on the benchmark of an added reserve cost of < $0.50/Mcfe. The other four were deemed “unsuccessful” by the same measure. The two candidate wells provided almost 1 Bcf of added reserves as a result of the workovers at a cost of about $20,000, for an average reserve cost of < $0.02/Mcfe. An aspect of these results that must be considered is that the workovers performed on the four “non-candidate” wells were not identical to those performed on the candidate wells.

Current Status

**and Remaining Tasks:** This project is completed. Even with minimal reservoir data and noisy production data, the overall methodology (data exploration, engineering type curves, artificial intelligence and heuristic screening) successfully identified remediation candidates.

Project Start

08/08/2000

Project End

09/30/2003

DOE Contribution

$178,925

Performer Contribution

$243,320

Contact Information

NETL – Gary Covatch ([gary.covatch@netl.doe.gov](mailto:gary.covatch@netl.doe.gov) or 304-285-4589)  
ARI – Scott R. Reeves ([sreeves@adv-res-hou.com](mailto:sreeves@adv-res-hou.com) or 713-780-0815)

Additional Information

[Final Report ](https://www.netl.doe.gov/files/oil-gas/40789-Final-Report.pdf) [PDF-595KB]   
[Selection and Treatment of Stripper Wells ](https://www.netl.doe.gov/files/oil-gas/swr40789.pdf) [PDF-380KB]   
[Presentation](https://www.netl.doe.gov/files/oil-gas/swr40789CurrentPresentation.PDF) [PDF-686KB]  
[DOE Program Facts "Stripper Gas Wells"](https://www.netl.doe.gov/files/oil-gas/prog025.pdf) [PDF-421KB]
