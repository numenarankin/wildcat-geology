<!-- Source: geodecider-lithology-agentic-workflow.pdf -->
<!-- Converted: mistral-ocr-latest -->

arXiv:2605.03383v2 [cs.AI] 27 Jul 2026

# GeoDecider: An Evidence-Grounded Agent for Geological Interpretation via Deliberative Reasoning

Xiaoyu Tao

State Key Laboratory of Cognitive Intelligence, University of Science and Technology of China, Hefei, China
txytiny@mail.ustc.edu.cn

Yitong Zhou

State Key Laboratory of Cognitive Intelligence, University of Science and Technology of China, Hefei, China
yitong.zhou@mail.ustc.edu.cn

Qi Liu

State Key Laboratory of Cognitive Intelligence, University of Science and Technology of China, Hefei, China
qiliuql@ustc.edu.cn

Mingyue Cheng

State Key Laboratory of Cognitive Intelligence, University of Science and Technology of China, Hefei, China
mycheng@ustc.edu.cn

Qingyang Mao

State Key Laboratory of Cognitive Intelligence, University of Science and Technology of China, Hefei, China
maoqy0503@mail.ustc.edu.cn

Shijin Wang

State Key Laboratory of Cognitive Intelligence, iFLYTEK Research
sjwang3@iflytek.com

Jiahao Wang

State Key Laboratory of Cognitive Intelligence, University of Science and Technology of China, Hefei, China
jiahao.wang@mail.ustc.edu.cn

Yimin Dou

School of Earth and Space Sciences, University of Science and Technology of China, Hefei, China
douyimin@ustc.edu.cn

Enhong Chen

State Key Laboratory of Cognitive Intelligence, University of Science and Technology of China, Hefei, China
cheneh@ustc.edu.cn

## Abstract

Geological interpretation infers subsurface properties and structures from indirect geophysical observations. Well-log classification provides a measurable setting by assigning geological classes to depth-indexed petrophysical records. The task is difficult because different subsurface units may exhibit similar logging responses, whereas accurate interpretation often depends on local measurements, depth-wise context, domain knowledge, and reasonable transitions between neighboring layers. Existing automated methods mainly follow fixed prediction pipelines, leaving little room to gather additional evidence for difficult samples. In this work, we propose GeoDecider, an evidence-grounded agent for deliberative geological interpretation. GeoDecider retains efficient numerical prediction as the first stage, then selectively invokes tool-assisted reasoning for difficult intervals. A lightweight classifier produces point-wise predictions and estimates sample difficulty from its prediction scores. High-difficulty points act as routing anchors, triggering interval-level analysis so that nearby observations can be examined together. For each activated interval, specialized tools build an Evidence Profile that summarizes geological knowledge, depth-wise trends, previous predictions from the same well, and similar cases retrieved from training wells. Three complementary scientific views generate candidate interpretations. GeoDecider compares their supporting evidence, resolves disagreements, then

Permission to make digital or hard copies of all or part of this work for personal or classroom use is granted without fee provided that copies are not made or distributed for profit or commercial advantage and that copies bear this notice and the full citation on the first page. Copyrights for components of this work owned by others than the author(s) must be honored. Abstracting with credit is permitted. To copy otherwise, or republish, to post on servers or to redistribute to lists, requires prior specific permission and/or a fee. Request permissions from permissions@acm.org.

Conference acronym 'XX, Woodstock, NY

© 2018 Copyright held by the owner/author(s). Publication rights licensed to ACM.

ACM ISBN 978-1-4503-XXXX-X/2018/06

https://doi.org/XXXXXXXX.XXXXXXX

applies geology-informed checks on continuity, boundary cues, and petrophysical consistency. Experiments on four public well-log benchmarks show that GeoDecider consistently outperforms representative baselines, demonstrating the value of selective evidence gathering and deliberative reasoning for geological interpretation. \( ^{1} \)

## Keywords

Geological interpretation, lithology classification, scientific reasoning, large language models, tool-augmented reasoning

### ACM Reference Format:

Xiaoyu Tao, Mingyue Cheng, Jiahao Wang, Yitong Zhou, Qingyang Mao, Yimin Dou, Qi Liu, Shijin Wang, and Enhong Chen. 2018. GeoDecider: An Evidence-Grounded Agent for Geological Interpretation via Deliberative Reasoning. In Proceedings of Make sure to enter the correct conference title from your rights confirmation email (Conference acronym 'XX). ACM, New York, NY, USA, 12 pages. https://doi.org/XXXXXXX.XXXXXXX

## 1 Introduction

Geological interpretation infers subsurface properties and stratigraphic organization from indirect observations, supporting reservoir evaluation and geological modeling  \( [1, 5, 46] \) . Well-log target-class interpretation provides a concrete setting by assigning rock types, lithofacies, or geological layers to depth-indexed measurements  \( [20, 30] \) . Despite its supervised classification formulation, the task cannot be reduced to independent point-wise prediction. Similar logging responses may correspond to different subsurface units, making accurate interpretation dependent on local measurements, depth-wise context, domain knowledge, and stratigraphic constraints  \( [44] \) . We therefore formulate automated well-log classification as an evidence-grounded interpretation problem that requires both point-level accuracy and depth-wise coherence.

\( ^{1} \) Our code is available at https://github.com/Xiaoyu-Tao/GeoDecider

Conference acronym 'XX, June 03–05, 2018, Woodstock, NY

Tao et al.

![img-0.jpeg](img-0.jpeg)

Figure 1: Overview of the geological interpretation task and the motivation for GeoDecider.

Over the years, well-log interpretation has evolved from expert-driven analysis to data-driven methods [48, 56]. As shown in Figure 1, traditional expert interpretation integrates well-log observations with geological knowledge and stratigraphic patterns but remains labor-intensive and hard to scale. Machine learning and deep learning models have improved automated lithology and facies classification [9, 15]. Recent studies further explore advanced deep models. Sequence models and stratigraphic priors, including recurrent, CRF-based, and HMM-based approaches, exploit depth-wise correlations to improve sequence continuity [33, 40, 47]. However, these methods typically follow fixed inference pipelines: they cannot determine when further analysis is needed, acquire complementary evidence, or reconcile conflicting interpretations through verification [27]. Thus, ambiguous intervals, formation boundaries, and overlapping logging responses remain challenging, motivating conditional and evidence-grounded workflows rather than more complex single-pass predictors. Recent large language models (LLMs) offer opportunities for integrating domain knowledge, tool usage, and hypothesis comparison in scientific interpretation [4, 49]. Tool-augmented and agentic reasoning further suggest that LLMs can coordinate external evidence and intermediate decisions rather than acting as static predictors [54]. However, applying LLMs directly to raw numerical well logs is inefficient and insufficiently grounded. The key challenge is coordinating efficient prediction with selective evidence acquisition and deliberative reasoning while maintaining geological consistency.

To address this challenge, we propose GeoDecider, a scientific agent for geological interpretation via evidence-grounded deliberation. As shown in Figure 1, we regard GeoDecider as a scientific agent because it detects observations that warrant further investigation, conditionally activates specialized tools, compares competing interpretations through separate scientific views, and records the evidence used to verify the resulting decision. GeoDecider transforms conventional single-pass well-log target-class classification into an adaptive fast-slow interpretation workflow. A lightweight classifier produces point-wise predictions and estimates sample difficulty from its prediction scores. Rather than treating each high-difficulty point as an isolated query, GeoDecider uses such points as routing anchors that activate deliberation over their containing depth intervals. For each activated interval, it collects geological knowledge, depth-wise trends, analogical cases retrieved from training wells,

and finalized predictions from preceding depths, organizing them into a provenance-preserving Evidence Profile. Data-, context-, and knowledge-oriented views then produce candidate sequences, and an evidence-aware reconciliation stage resolves their agreements and conflicts. Finally, GeoDecider applies geology-informed checks based on stratigraphic continuity, coordinated log changes, and petrophysical compatibility to verify and, when necessary, refine the interval-level interpretation.

Our contributions are summarized as follows:

- We propose GeoDecider, a scientific agent transforming well-log classification into an adaptive fast-slow workflow. Prediction scores identify high-difficulty routing anchors, activating evidence-grounded deliberation over depth intervals.
- We develop a deliberative reasoning workflow that builds an Evidence Profile through specialized tools, reconciles candidate sequences from complementary views, and verifies revisions using continuity, boundary, and petrophysical evidence.
- Experiments on public well-log benchmarks show that GeoDecider outperforms baselines. Analyses reveal depth-wise geological context as key evidence for ambiguous intervals, highlighting the need for contextual evolution beyond isolated measurements.

## 2 Related Work

### 2.1 Lithology Interpretation from Well Logs

Lithology interpretation from well logs aims to infer subsurface geological compositions, facies, and stratigraphic units from petrophysical measurements, supporting reservoir evaluation, geological modeling, and resource characterization [22, 42]. Early interpretation relied on expert-driven analysis, where geoscientists integrated logging responses with domain knowledge, stratigraphic patterns, and geological experience [2, 3]. Although physically meaningful, such approaches require substantial manual effort and are difficult to scale to large volumes of well-log data [17, 38]. With the development of machine learning, data-driven approaches have been widely adopted for automated lithology classification. Traditional methods learn patterns from engineered logging features, while deep learning models extract nonlinear representations from raw or multi-dimensional measurements [41, 43]. These approaches improve prediction efficiency but typically formulate interpretation as

GeoDecider: An Evidence-Grounded Agent for Geological Interpretation via Deliberative Reasoning

Conference acronym 'XX, June 03–05, 2018, Woodstock, NY

a direct mapping from observations to labels, making them vulnerable to ambiguous responses [10, 29, 39]. To capture the sequential nature of geological formations, subsequent studies incorporated depth-wise dependencies and geological constraints through sequence models and structure-aware approaches, including recurrent networks, probabilistic graphical models, and stratigraphic consistency modeling [33, 40, 47]. While improving continuity and geological plausibility, these methods rely on predefined structures or manual constraints, limiting their ability to adaptively acquire evidence, compare interpretations, and resolve uncertainty through reasoning [26]. Therefore, effective lithology interpretation requires not only accurate classification but also evidence-grounded reasoning for dynamic decision refinement.

## 2.2 Evidence-Grounded LLM Reasoning

Large language models (LLMs) have demonstrated strong capabilities in language understanding, knowledge integration, and reasoning [18, 19, 60]. Unlike conventional predictive models, LLM-based reasoning decomposes problems into intermediate inference processes and generates decisions conditioned on contextual information. Chain-of-thought (CoT), self-consistency, and related structured prompting strategies enable multi-step reasoning, while retrieval-augmented generation improves knowledge grounding [37, 53, 55]. Recent agentic reasoning frameworks further extend LLMs by enabling tool interaction and external information retrieval [45, 58]. By integrating specialized models and computational tools, LLMs can perform dynamic problem solving beyond static generation. However, applying LLM reasoning to scientific interpretation remains challenging due to heterogeneous observations, domain constraints, and the need for traceable evidence [34, 57]. Existing approaches mainly target textual tasks and lack mechanisms for integrating structured measurements, domain tools, and physical consistency [35, 59]. Reliable geological reasoning requires decisions grounded in observable evidence and geological principles. Motivated by these challenges, we develop evidence-grounded reasoning that combines prediction, evidence acquisition, and geological verification. LLMs serve as reasoning agents to integrate evidence and refine ambiguous interpretations.

## 3 Preliminaries

This section defines depth-indexed well-log sequences, summarizes the geological characteristics that motivate contextual reasoning, and formalizes the interpretation task studied in this work.

### 3.1 Well-Log Sequences and Labels

A well log consists of multivariate petrophysical measurements sampled at ordered depth locations $\mathbf{d} = [d_1, \ldots, d_L]$, where $d_1 < \cdots < d_L$. For a well with $L$ depth points and $M$ logging channels, let $\mathbf{x}_t \in \mathbb{R}^M$ denote the measurements at depth $d_t$. The complete well-log sequence is represented as $\mathbf{X} = [\mathbf{x}_1^\top; \ldots; \mathbf{x}_L^\top] \in \mathbb{R}^{L \times M}$, where the $t$-th row of $\mathbf{X}$ corresponds to $\mathbf{x}_t^\top$. Typical channels include gamma ray, resistivity, density, neutron porosity, and sonic measurements, while available channels vary across datasets. The corresponding target interpretation sequence is $\mathbf{Y} = [y_1, y_2, \ldots, y_L] \in \mathbb{C}^L$, where $y_t \in \mathbb{C}$ denotes the target interpretation class at depth $d_t$, and $\mathbb{C}$ is the dataset-specific class set. Depending on the benchmark, target

classes may represent rock lithologies, lithofacies, or geological layers. Lithology interpretation is the primary setting.

A sample denotes an individual depth point, whereas an interval denotes a consecutive group of points. For a target depth $d_t$, the contextual indices within a physical depth radius $\rho$ are defined as $\mathcal{J}_t(\rho) = \{j \mid |d_j - d_t| \leq \rho\}$, and the corresponding context sequence is $\mathbf{X}_t^{\text{ctx}} = (\mathbf{x}_j)_{j \in \mathcal{J}_t(\rho)}$, where $\mathbf{X}_t^{\text{ctx}}$ preserves the increasing-depth order and $\rho$ uses the same physical unit as $d_t$. A point-wise model takes $\mathbf{z}_t = \mathbf{x}_t$, whereas a context-aware model uses $\mathbf{z}_t = \phi(\mathbf{X}_t^{\text{ctx}})$ with feature extractor $\phi$.

### 3.2 Geological Characteristics of Lithology Interpretation

Lithology interpretation differs from conventional point-wise classification in three respects [12, 48, 56]. First, the mapping from logging responses to lithology is non-unique: different rock types may exhibit overlapping petrophysical signatures, while the same lithology may vary with porosity, fluid content, pressure, and burial conditions. Second, interpretations depend on ordered depth-wise context. Surrounding trends, turning points, and formation boundaries can provide information that is unavailable from an isolated measurement, motivating models that exploit correlations across neighboring depths. Third, unsupported isolated label changes can fragment an otherwise continuous local sequence. Local continuity is therefore a useful diagnostic, but it is only a proxy rather than proof of complete geological validity. Reliable interpretation consequently requires local pattern recognition, contextual evidence integration, and explicit checking of the predicted sequence against the observed well-log context.

### 3.3 Problem Formulation

Within the broader setting of geological interpretation, this work focuses on well-log lithology interpretation, formulated as supervised depth-wise classification of dataset-specific interpretation classes. Geological interpretation aims to infer subsurface units from indirect measurements, while target-class prediction provides the operational task for model training and evaluation.

Given labeled training wells $\mathcal{D}_{\text{train}} = \{(\mathbf{d}^{(i)}, \mathbf{X}^{(i)}, \mathbf{Y}^{(i)})\}_{i=1}^N$, where $\mathbf{d}^{(i)} \in \mathbb{R}^{L_i}$, $\mathbf{X}^{(i)} \in \mathbb{R}^{L_i \times M}$, and $\mathbf{Y}^{(i)} \in \mathbb{C}^{L_i}$ denote the depth locations, well-log sequence, and interpretation sequence of the $i$-th well, the goal is to predict an unseen well's target sequence $\hat{\mathbf{Y}} = \mathcal{F}(\mathbf{X}, \mathbf{d}; \mathcal{D}_{\text{train}}, \mathcal{K})$, where $\mathcal{K}$ denotes domain knowledge and $\hat{y}_t \in \mathbb{C}$ is the prediction at depth $d_t$. The target well is disjoint from training wells, and retrieved analogical cases must originate from $\mathcal{D}_{\text{train}}$. Reliable interpretation requires both point-level accuracy and sequence-level coherence. The former measures agreement with reference classes, while the latter evaluates depth-wise consistency and avoids unsupported isolated changes. However, ambiguous samples and intervals remain challenging because local measurements may provide insufficient or conflicting evidence. Resolving such cases requires integrating surrounding trends, domain knowledge, historical predictions, and analogous observations. Therefore, we seek a framework that can selectively acquire evidence, perform traceable reasoning, and generate predictions that are both accurate and consistent with depth-wise geological context.

Conference acronym 'XX, June 03–05, 2018, Woodstock, NY

Tao et al.

![img-1.jpeg](img-1.jpeg)

Figure 2: The GeoDecider framework. Point-wise prediction scores identify high-difficulty routing anchors that activate interval-level evidence construction, multi-perspective reasoning, evidence reconciliation, and physics- and geology-informed refinement.

## 4 The Proposed GeoDecider

GeoDecider operationalizes this formulation through a fast-slow workflow. The fast stage produces predictions and difficulty signals, while the slow stage reasons over difficult intervals. This design preserves geological context by estimating sample difficulty, constructing evidence, comparing hypotheses, and refining sequences.

### 4.1 Framework Overview

As illustrated in Figure 2, GeoDecider processes the target well as ordered intervals. A lightweight classifier estimates sample difficulty from prediction scores and marks high-difficulty points as routing anchors. Intervals without routing anchors retain fast predictions, while anchored intervals activate deliberation with neighboring observations. Specialized tools construct a provenance-preserving Evidence Profile, and three role-conditioned calls analyze intervals from data, contextual, and geological perspectives. Evidence-aware fusion reconciles candidate sequences, followed by refinement using continuity, log variations, and petrophysical compatibility. Intervals are processed shallow-to-deep, allowing previous predictions to provide historical evidence. No target-well labels are exposed during reasoning under strict evaluation protocols.

### 4.2 Lightweight Point-Wise Prediction

Well-log datasets contain many observations with comparatively distinctive logging patterns. GeoDecider uses a conventional classifier as the fast stage for these routine cases and as a statistical prior for subsequent reasoning. The framework is not restricted to a particular architecture: the classifier may be point-wise or context-aware, provided that it returns a score for every target class. Given the feature representation  \( z_{t} \)  defined from the target measurement or its contextual window, the lightweight classifier  \( f_{fast} \)  produces a probability distribution over the candidate target classes,  \( \mathbf{p}_{t} = f_{\mathrm{fast}}(\mathbf{z}_{t}) \) , where  \( p_{t} = [p_{t,1}, \ldots, p_{t,|C|}] \)  and C denotes

the dataset-specific target class set. The initial prediction is obtained as  \( \hat{y}_{t}^{fast} = \arg\max_{c \in C} p_{t,c} \) . As defined in the preliminaries,  \( z_{t} = x_{t} \)  for a point-wise classifier and may be obtained from  \( X_{t}^{tx} \)  for a context-aware classifier. GeoDecider treats the resulting scores as model outputs rather than calibrated probabilities. Their role in the framework is to provide an initial hypothesis and a scheduling signal for deciding where additional analysis may be warranted.

### 4.3 Difficulty-Aware Routing

Well-log observations exhibit heterogeneous classification difficulty. We estimate sample difficulty from the maximum class score:

\[
q _ {t} = \max _ {c \in C} p _ {t, c}. \tag {1}
\]

A lower  \( q_{t} \)  indicates a higher-difficulty sample because the fast classifier does not strongly prefer a single target class. Given a routing threshold  \( \tau \)  selected on validation wells, the point-level routing indicator is:

\[
r _ {t} = \left\{ \begin{array}{l l} 0, & q _ {t} \geq \tau , \\ 1, & q _ {t} <   \tau , \end{array} \right. \tag {2}
\]

where  \( r_{t} = 1 \)  marks depth t as a high-difficulty routing anchor. Let  \( B_{b} = \{s_{b}, \ldots, e_{b}\} \)  denote the indices of the b-th consecutive inference interval and define:

\[
a _ {b} = \mathbb {I} \left(\sum_ {t \in \mathcal {B} _ {b}} r _ {t} > 0\right). \tag {3}
\]

Here,  \( a_{b}=1 \)  activates deliberation for the complete interval rather than only for the routing anchors. This distinction is important because neighboring high-score observations provide context for resolving a difficult boundary and may themselves be reconsidered during interval-level reconciliation. If  \( a_{b}=0 \) , the fast predictions for the interval are retained without invoking the slow stage. The threshold  \( \tau \)  is fixed using validation wells before test inference.

GeoDecider: An Evidence-Grounded Agent for Geological Interpretation via Deliberative Reasoning

Conference acronym 'XX, June 03–05, 2018, Woodstock, NY

### 4.4 Evidence-grounded Deliberative Reasoning

For an activated interval, GeoDecider does not directly ask an LLM to reclassify raw well-log inputs. It first constructs a structured Evidence Profile through specialized tools and then performs multi-perspective reasoning followed by evidence-aware reconciliation.

4.4.1 Tool-Augmented Evidence Profile Construction. For an activated interval  \( B_{b} \) , GeoDecider collects complementary evidence and organizes it as the ordered record:

\[
\mathcal {E} _ {b} = \left(E _ {b} ^ {\text { pred }}, E _ {b} ^ {\text { case }}, E _ {b} ^ {\text { context }}, E _ {b} ^ {\text { history }}, E _ {b} ^ {\text { know }}\right), \tag {4}
\]

where each component contains a source identifier, content, and relevance to classes. This record preserves provenance to distinguish outputs, retrieved cases, trends, predictions, and domain knowledge. Five components are organized into two categories: retrieved cases and historical predictions constitute common evidence, while initial predictions, depth-wise trends, and geological knowledge provide specialized evidence.

Initial prediction evidence. For every  \( t \in B_{b} \) , the profile records the initial label  \( \hat{y}_{t}^{fast} \)  and the maximum prediction score  \( q_{t} \)  used for difficulty estimation; the complete score vector  \( p_{t} \)  may also be retained when it is available from the base classifier. These quantities are treated as statistical evidence rather than direct final decisions and are further interpreted during subsequent reasoning stages to support reliable geological interpretation processes.

Geological knowledge tool. The knowledge base contains feature descriptions, dataset-specific class descriptions, and geology-informed interpretation guidelines concerning attribute combinations, boundary cues, and local transitions. The knowledge source is fixed before test inference and is supplied with identifiers so that subsequent decisions can cite the rules or descriptions they use.

Neighbor retrieval tool. Let  \( U_{b} = \{t \in B_{b} \mid r_{t} = 1\} \)  be the routing anchors in interval b. For each anchor, GeoDecider retrieves k analogical observations from the labeled training wells:

\[
\mathcal {N} _ {b} = \bigcup_ {t \in \mathcal {U} _ {b}} \operatorname{TopK} _ {(i, j) \in \mathcal {D} _ {\text {train}}} \text {sim} \left(\psi (\mathbf {z} _ {t}), \psi (\mathbf {z} _ {j} ^ {(i)})\right), \tag {5}
\]

where \((i,j)\) identifies depth \(j\) in training well \(i\), \(\psi\) is a feature transform fitted on training wells, and sim is a fixed similarity function. Each record stores well identifier, depth, target label, similarity score, and reference identifier. Thus, \(E_b^{\mathrm{case}} = \mathcal{N}_b\) provides empirical analogies without accessing labels from validation or test wells [31].

Depth-wise trend analysis tool. The trend tool analyzes the observed logging curves within  \( B_{b} \)  together with available measurements immediately above and below the interval. It summarizes stable regimes, gradual variations, turning points, coordinated abrupt changes, and potential boundary locations. Only observed features are used; target-well labels are never supplied.

Historical classification tool. Because intervals are processed from shallow to deep, the history tool can use finalized predictions immediately preceding the current interval:

\[
E _ {b} ^ {\text { history }} = \left\{\hat {y} _ {s _ {b} - h}, \dots , \hat {y} _ {s _ {b} - 1} \right\}, \tag {6}
\]

where indices are clipped at the beginning of the well, and h is the historical range. The history is empty for the first interval. These predictions are soft context and cannot override a transition supported by the observed logs.

Table 1: Statistics of each dataset in the experiments.

|  Statistics | SEAM | Facies | FORCE | GeoLink  |
| --- | --- | --- | --- | --- |
|  #of total wells | 5 | 7 | 11 | 128  |
|  #of total samples | 7,092 | 3,164 | 52,766 | 580,205  |
|  #of used input channels | 9 | 7 | 9 | 9  |
|  #of total labels | 7 | 9 | 5 | 11  |
|  #of sampling interval (m) | 10 | 0.5 | 0.15 | 0.125  |

All tool outputs are normalized into the shared record  \( E_{b} \) . The same profile is supplied to every view, while role instructions determine which evidence components receive primary attention.

4.4.2 Multi-Perspective Reasoning and Fusion. GeoDecider uses three separate role-conditioned calls that do not observe one another's outputs [36]. The Data Scientist emphasizes fast predictions, local measurements, and retrieved analogical cases. The Context Scientist focuses on depth-wise trends, candidate boundaries, and preceding finalized predictions. The Knowledge Scientist evaluates candidate classes using feature semantics, class descriptions, petrophysical compatibility, and geology-informed guidelines. Each view returns a candidate sequence for the complete interval together with the identifiers of the evidence supporting its decisions:

\[
\hat {\mathrm{Y}} _ {b} ^ {(v)} = R _ {v} (\mathcal {E} _ {b}), \quad v \in \{\text { data,   context,   knowledge } \}, \tag {7}
\]

where \(\hat{\mathbf{Y}}_b^{(v)}\in C^{|\mathcal{B}_b|}\). Their outputs are subsequently reconciled by an evidence-aware fusion process:

\[
\widetilde {\mathbf {Y}} _ {b} = R _ {\text { fuse }} \left(\{\hat {\mathbf {Y}} _ {b} ^ {(v)} \} _ {v}, \mathcal {E} _ {b}\right). \tag {8}
\]

Unlike deterministic majority voting,  \( R_{fuse} \)  may retain a majority candidate or select an alternative when the associated evidence more strongly supports it. The fusion output records the competing candidates, cited evidence, and reason for each resolved conflict. This makes disagreement visible rather than hiding it behind an arbitrary tie-breaking rule.

### 4.5 Physics- and Geology-Informed Refinement

The reconciled sequence may still contain changes that are weakly supported by the observed depth-wise context. GeoDecider therefore applies a physics- and geology-informed refinement process:

\[
\hat {\mathbf {Y}} _ {b} ^ {\text { slow }} = R _ {\text { refine }} \left(\widetilde {\mathbf {Y}} _ {b}, \mathcal {E} _ {b}\right). \tag {9}
\]

The refinement process checks whether label changes coincide with coordinated variations in surrounding well-log signals, whether isolated predictions are supported by a plausible boundary, and whether the selected class is compatible with observed petrophysical measurements. A revision must identify the evidence that motivates it; otherwise, the fused candidate is retained. These are soft, geology-informed checks rather than a proof of physical validity or a complete geological model. Combining interval activation with the fast and slow outputs gives, for every  \( t \in B_{b} \) ,

\[
\hat {y} _ {t} = \left\{ \begin{array}{l l} \hat {y} _ {t} ^ {\text { fast }}, & a _ {b} = 0, \\ \hat {y} _ {b, t} ^ {\text { slow }}, & a _ {b} = 1. \end{array} \right. \tag {10}
\]

Conference acronym 'XX, June 03–05, 2018, Woodstock, NY

Tao et al.

Table 2: Classification performance comparison of GeoDecider and other baseline models across four datasets. The best results are highlighted in bold, while the underlined results indicate the second-best performance.

|  Method | SEAM |   |   | Facies |   |   | FORCE |   |   | GeoLink  |   |   |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|   |  Precision | Recall | F1 | Precision | Recall | F1 | Precision | Recall | F1 | Precision | Recall | F1  |
|  XGBoost | 0.7889 | 0.7188 | 0.7355 | 0.4532 | 0.4388 | 0.4357 | 0.4799 | 0.4597 | 0.4573 | 0.5110 | 0.4185 | 0.4347  |
|  nn-DTW | 0.6299 | 0.4275 | 0.4396 | 0.4095 | 0.3631 | 0.3589 | 0.3806 | 0.3701 | 0.3616 | 0.3953 | 0.3710 | 0.3675  |
|  GBDT | 0.8006 | 0.7546 | 0.7626 | 0.4883 | 0.4388 | 0.4440 | 0.4763 | 0.4401 | 0.4445 | 0.4944 | 0.4038 | 0.4149  |
|  LSTMFCN | 0.8217 | 0.7559 | 0.7694 | 0.4318 | 0.3942 | 0.3869 | 0.4679 | 0.4054 | 0.4046 | 0.5154 | 0.3929 | 0.3983  |
|  MLP | 0.8462 | 0.7512 | 0.7647 | 0.4532 | 0.4212 | 0.4201 | 0.5935 | 0.5073 | 0.5068 | 0.5166 | 0.4442 | 0.4501  |
|  MiniRocket | 0.8457 | 0.7485 | 0.7667 | 0.4615 | 0.4129 | 0.4129 | 0.5288 | 0.4791 | 0.4783 | 0.4857 | 0.4159 | 0.4252  |
|  InceptionTime | 0.8598 | 0.7546 | 0.7667 | 0.4444 | 0.3641 | 0.3817 | 0.4919 | 0.4342 | 0.4450 | 0.4575 | 0.3969 | 0.4083  |
|  InstructTime | 0.8684 | 0.7552 | 0.7659 | 0.4371 | 0.3797 | 0.3821 | 0.4537 | 0.4518 | 0.4448 | 0.4583 | 0.4025 | 0.4082  |
|  TableTime | 0.7912 | 0.6015 | 0.6288 | 0.4296 | 0.3506 | 0.3655 | 0.4719 | 0.3960 | 0.3912 | 0.4061 | 0.3778 | 0.3768  |
|  GPT4TS | 0.8042 | 0.7330 | 0.7489 | 0.4911 | 0.4409 | 0.4412 | 0.5118 | 0.4555 | 0.4651 | 0.4805 | 0.4073 | 0.4172  |
|  UniTS | 0.8005 | 0.7707 | 0.7745 | 0.4471 | 0.4025 | 0.3956 | 0.4418 | 0.4581 | 0.4332 | 0.5077 | 0.4511 | 0.4492  |
|  MOMENT | 0.7905 | 0.7195 | 0.7315 | 0.4379 | 0.3714 | 0.3887 | 0.4434 | 0.4286 | 0.4270 | 0.4488 | 0.3828 | 0.3961  |
|  GeoDecider | 0.8628 | 0.7748 | 0.7803 | 0.4758 | 0.4461 | 0.4481 | 0.6094 | 0.5271 | 0.5254 | 0.5040 | 0.4539 | 0.4582  |

Thus, sample difficulty is estimated point-wise, whereas an activated interval is interpreted jointly and may revise both anchor and neighboring positions. The final operational sequence is  \( \hat{Y} = [\hat{y}_{1}, \ldots, \hat{y}_{L}] \) , which instantiates the mapping F defined in the problem formulation. For each activated interval, GeoDecider additionally retains an evidence trace containing the tool records, three candidate sequences, fusion conflicts, and refinement changes.

## 5 Experiments

In this section, we evaluate GeoDecider across multiple datasets against representative baselines, analyze module effectiveness, and discuss practical industrial challenges and lessons learned under privacy and compliance constraints.

### 5.1 Experimental Settings

5.1.1 Datasets. We evaluate our method on public well-log datasets from established repositories: (1) SEAM: the SEG wiki open data catalog for reproducible geoscience benchmarking, (2) Facies: the Kaggle dataset, where our benchmark split uses seven wells from the Council Grove gas reservoir (Kansas), (3) FORCE: the Kaggle well-log dataset for lithology prediction, associated with the FORCE 2020 lithology prediction context, (4) GeoLink: the GEOLINK-S2 well-log dataset with analysis notebooks and preprocessing code. Details can be found in Table 1 and appendix A, B, and C.

5.1.2 Baselines. To conduct a comprehensive and fair comparison, we compare against several baselines grouped into four categories: Machine learning-based methods: XGBoost [6], nn-DTW [23], GBDT [24]. Deep learning-based methods: LSTMFCN [21], MLP [50], MiniRocket [8], InceptionTime [16]. LLM-based approaches: InstructTime [7], TableTime [52], GPT4TS [62]. Time-series foundation models: UniTS [11] and MOMENT [13]. For a detailed introduction to these baselines, please see appendix D.

5.1.3 Evaluation Metrics. To evaluate well-log target-class classification performance, we select three widely used metrics [51, 61],

i.e., Precision, Recall, and F1 measure [28, 32]. Considering our task is a multi-class classification problem, we use the weighted average scores to evaluate the performance of our proposed methods and all baselines. Specifically, we weight the metrics of each class by the number of samples from that class.

5.1.4 Implementation Details. In this work, we adopt DeepSeek-R1 [14] as the base LLM due to its open-source availability and accessible reasoning traces. Each configuration is evaluated over three runs, with predictions aggregated by majority voting, which is distinct from evidence-aware fusion among three scientific views within each run. Inference uses the official API with temperature=0.6, top-p=0.7, and max-tokens=8,192. Deep learning baselines and base classifiers are trained with Adam [25] in PyTorch on a single NVIDIA GeForce RTX 4090D GPU.

### 5.2 Classification Results Analysis

Table 2 summarizes the classification performance of GeoDecider and representative baselines across four well-log benchmarks. GeoDecider consistently achieves the best performance, obtaining the highest F1 scores on all datasets. Compared with conventional machine learning methods and deep sequence models, GeoDecider demonstrates that geological interpretation benefits from contextual and domain-specific evidence beyond direct feature-to-label mapping. The improvements are particularly evident on challenging benchmarks such as Facies and FORCE, where logging responses show ambiguity among neighboring lithological units. By activating deliberation on difficult intervals, GeoDecider integrates depth-wise trends, retrieved cases, geological knowledge, and previous predictions to resolve difficult samples. This evidence-grounded process produces more consistent interpretations than fixed prediction. Furthermore, GeoDecider remains competitive against foundation-model-based approaches, showing that general-purpose sequence models alone may not fully capture geological constraints. Overall, the results validate combining efficient prediction with tool-assisted deliberative reasoning for reliable geological interpretation.

GeoDecider: An Evidence-Grounded Agent for Geological Interpretation via Deliberative Reasoning

Conference acronym 'XX, June 03–05, 2018, Woodstock, NY

![img-2.jpeg](img-2.jpeg)

Figure 3: Performance comparison between lightweight models and their refined counterparts, evaluated by F1 score.

### 5.3 Effectiveness across Initial Predictors

As shown in Figure 3, to evaluate the general effectiveness of GeoDecider across initial predictors, we apply it to multiple lightweight classifiers and compare performance before and after refinement. GeoDecider consistently improves F1 scores across datasets, demonstrating classifier-independent effectiveness. The largest gains appear on challenging benchmarks such as FORCE, where geological evidence helps correct ambiguous predictions. These improvements across multiple classifiers indicate that GeoDecider enhances existing predictions through evidence-grounded reasoning rather than stronger representation learning. By integrating multiple evidence sources, GeoDecider refines inconsistent results under geological constraints. The results validate the fast-slow workflow, where efficient models provide initial predictions and deliberation focuses on difficult intervals with improved reliability.

### 5.4 Effectiveness of Difficulty-Aware Routing

Figure 4 shows that difficulty-aware routing improves weighted F1 across all four datasets while reducing the number of point-level cases selected as routing anchors. We evaluate routing by comparing the full model with a non-selective deliberation variant that activates additional reasoning without difficulty-based filtering. These counts show that prediction-score-based difficulty estimation concentrates additional analysis around a subset of difficult observations. Importantly, the slow stage operates on complete activated intervals rather than on isolated routing anchors. Neighboring lower-difficulty positions may therefore be included in the same prompt and revised during evidence reconciliation. Accordingly, Figure 4 characterizes the selectivity of the routing signal, not end-to-end inference cost; claims about efficiency require direct measurements of model calls.

### 5.5 Effectiveness of the Toolkit

As shown in Table 3, removing the entire toolkit leads to the largest performance degradation across all benchmarks, confirming that the structured evidence profile is essential for LLM-based lithology reasoning. Among the evaluated components, depth-wise trend analysis contributes the most, as its removal causes the largest single-tool degradation, highlighting the importance

![img-3.jpeg](img-3.jpeg)

Figure 4: Changes in F1 and point-level routing anchors after difficulty-aware routing. Anchor counts characterize routing selectivity rather than end-to-end LLM cost.

Table 3: Comprehensive ablation on the impact of the toolkit and geological refinement module, evaluated by F1 score.

|  Variant | SEAM | Facies | FORCE | GeoLink  |
| --- | --- | --- | --- | --- |
|  Full Model | 0.7803 | 0.4481 | 0.5254 | 0.4582  |
|  w/o Toolkit | 0.7642 | 0.4312 | 0.4985 | 0.4452  |
|  w/o Knowledge Base | 0.7745 | 0.4405 | 0.5132 | 0.4534  |
|  w/o Depth-Wise Trend Analysis | 0.7702 | 0.4362 | 0.5075 | 0.4505  |
|  w/o Neighbor Retrieval | 0.7791 | 0.4452 | 0.5198 | 0.4561  |
|  w/o Geological Refinement | 0.7742 | 0.4402 | 0.5135 | 0.4536  |

of depth-wise continuity and stratigraphic context. The knowledge base improves performance by providing geological priors for ambiguous well-log responses, while neighbor retrieval offers complementary fine-grained analogies. Furthermore, geological refinement enhances consistency by validating predictions against local transitions. These results confirm that different evidence sources play complementary roles in grounded lithology reasoning.

### 5.6 In-Depth Analysis of Geological Refinement

Table 4 shows that geological refinement consistently reduces the Flying Point Ratio (FPR) across all benchmarks. To evaluate local sequence continuity after refinement, FPR measures isolated label predictions along depth. Given \(\hat{\mathbf{Y}} = [\hat{y}_1,\dots ,\hat{y}_L]\), a flying point is a prediction differing from all labels within its local neighborhood. A lower FPR indicates stronger depth-wise continuity. The reduction demonstrates the ability of refinement to suppress spurious point-wise predictions and correct locally inconsistent labels using contextual evidence. However, FPR only measures local continuity and does not represent complete geological validity.

### 5.7 Analysis of Multi-Perspective Reasoning

Figure 6 shows that GeoDecider consistently achieves the best weighted F1 across all datasets. This experiment evaluates multi-perspective reasoning by comparing GeoDecider with three single-perspective variants based on the context, data, and knowledge views. The gains are particularly evident on FORCE, where combining perspectives outperforms individual strategies. Different

Conference acronym 'XX, June 03–05, 2018, Woodstock, NY

Tao et al.

#### You are a well log data analysis expert in lithology interpretation. Please help me classify these points.

Difficulty-Aware Routing and Interval Activation

Tool-Augmented Evidence Profile

Multi-Perspective Reasoning and Fusion

Physics- and Geology-Informed Refinement

#System: You are a petroleum well log data analysis expert. Please classify each depth point (each row/sample) in the Well Log Facies Dataset into one of 9 lithofacies categories using the provided well log features. The data is pre-classified by XGBast:

|  No. | DATE | SE | \( \mathrm{{AP}} \) | GeoDeciderCount  |
| --- | --- | --- | --- | --- |
|  6 | 2024 | 61.9 | 100.7 | (PME-CL-ASSISTED) Wackstone  |
|  7 | 2025 | 61.1 | 100.1 | Wackstone (0.3%) Packstone-groinsome (0.47)  |
|  8 | 2026 | 60.8 | 100.3 | (PME-CL-ASSISTED) Wackstone  |

#Feature Description
GR: Natural Gamma Ray log
#Classification suggestions:
Moderate GR and stable SP support
Wackstone: Packstone-groinsome
remains a nearby candidate.
#Trend Analysis: GR and SP vary
smoothly, indicating a coherent
facies interval.
#Neighbors: Similar reference
samples for Sample 7:

|  0 | 1 | 2 | 3 | 4 | 5  |
| --- | --- | --- | --- | --- | --- |
|  0.0 | 0.1 | 0.2 | 0.3 | 0.4 | 0.5  |

#Data Scientist: Based on the XGBast classification result, this interval is predicted as Wackstone, as its feature pattern matches retrieved Wackstone samples.
#Context Scientist: From the contextual trend analysis along depth, the surrounding intervals show stable GR and SP trends, suggesting Wackstone rather than an isolated class change.
#Knowledge Scientist: According to class descriptions and geological consistency cues, the observed logs are consistent with Wackstone.

#Stratigraphic Continuity: The depth-wise trend analysis shows smooth GR and SP variations across this interval, with no strong evidence for an abrupt facies boundary.
#Geological Consistency: Although the second candidate is Packstone-groinsome, the retrieved reference case, local trend, and class description evidence jointly support Wackstone as the final interpretation.

Figure 5: A case of how GeoDecider performs well-log target-class classification via pre-classified and tool-augmented reasoning.

![img-4.jpeg](img-4.jpeg)

Figure 6: Performance comparison between single-view reasoning and integrated multi-view reasoning across benchmarks for lithology interpretation.

perspectives provide complementary information: the context view captures stratigraphic continuity, the data view models local patterns, and the knowledge view enforces geological constraints.

### 5.8 Case Study

Figure 5 presents a case study illustrating GeoDecider's end-to-end decision process for well-log target-class classification. The base classifier provides point-wise pre-classification based on log features. High-difficulty routing anchors activate interval-level tool-augmented reasoning that incorporates feature descriptions, trend analysis, historical predictions, and neighboring reference cases. These signals are examined from multiple perspectives and reconciled according to their cited evidence. The refinement module then checks the fused sequence against observed geological patterns and local continuity cues to produce a contextually supported final prediction. This case demonstrates how GeoDecider combines evidence to generate coherent, evidence-supported and reliable target-class interpretations.

### 5.9 Limitations and Ethical Considerations

All experiments use public well-log benchmarks. GeoDecider was developed with a national oil company using proprietary data, but

Table 4: Flying Point Ratio (FPR) of the base classifier and GeoDecider with and without geological refinement.

|  Variant | SEAM | Facies | FORCE | GeoLink  |
| --- | --- | --- | --- | --- |
|  Base Classifier | 0.0148 | 0.1760 | 0.0873 | 0.1240  |
|  GeoDecider(w/o Ref) | 0.0141 | 0.1596 | 0.0792 | 0.1196  |
|  GeoDecider(w/ Ref) | 0.0135 | 0.1541 | 0.0746 | 0.1137  |

confidentiality prevents disclosure of raw logs, locations, and production results. Industrial collaboration only informs deployment constraints and design. Proprietary applications should follow data-governance policies and use de-identified results.

### 5.10 Generative AI Usage

The method applies large language models to difficult intervals using structured Evidence Profiles and role-conditioned prompts. No task-specific fine-tuning is performed. Authors designed prompts, verified outputs, and reviewed all claims, experiments, results, citations, and manuscript content, taking full responsibility.

## 6 Conclusion

In this work, we presented GeoDecider, a scientific agent for geological interpretation via evidence-grounded deliberation. GeoDecider transforms single-pass well-log classification into an adaptive fast-slow workflow, where lightweight models handle routine predictions and difficult intervals trigger evidence-based reasoning. Specialized tools construct Evidence Profiles from geological knowledge, depth-wise trends, analogical cases, and historical predictions. GeoDecider integrates complementary perspectives, reconciles conflicting evidence, and applies geology-informed refinement. Experiments on four public benchmarks demonstrate consistent improvements over representative baselines, highlighting the value of geological context for ambiguous intervals. Overall, GeoDecider shows that reliable interpretation requires not only accurate prediction, but also structured evidence integration, multi-perspective reasoning, and transparent decision-making.

GeoDecider: An Evidence-Grounded Agent for Geological Interpretation via Deliberative Reasoning

Conference acronym 'XX, June 03–05, 2018, Woodstock, NY

## References

[1] Roman Beloborodov, James Gunning, Marina Pervukhina, Juerg Hauser, Michael Ben Clennell, Alan Mur, and Vladimir Li. 2024. Automated lithofluid and facies classification in well logs: The rock-physics perspective. Geophysics 89, 4 (2024), MR209–MR222.

[2] Karianne J Bergen, Paul A Johnson, Maarten V de Hoop, and Gregory C Beroza. 2019. Machine learning for data-driven discovery in solid Earth geoscience. Science 363, 6433 (2019), eaau0323.

[3] Thiago Santi Bressan, Marcelo Kehl de Souza, Tiago J Girelli, and Farid Chemale Junior. 2020. Evaluation of machine learning methods for lithology classification using geophysical data. Computers & Geosciences 139 (2020), 104475.

[4] Ching Chang, Wen-Chih Peng, and Tien-Fu Chen. 2023. 1Jms4ts: Two-stage fine-tuning for time-series forecasting with pre-trained llms. CoRR (2023).

[5] Luoyuan Chen, Xingjian Wang, and Zhanbo Liu. 2025. Geological information-driven deep learning for lithology identification from well logs. Frontiers in Earth Science 13 (2025), 1662760.

[6] Tianqi Chen, Tong He, Michael Benesty, Vadim Khotilovich, Yuan Tang, Hyunsu Cho, Kailong Chen, Rory Mitchell, Ignacio Cano, Tianyi Zhou, et al. 2015. Xgboost extreme gradient boosting. R package version 0.4.2.1, 4 (2015), 1–4.

[7] Mingyue Cheng, Yiheng Chen, Qi Liu, Zhiding Liu, Yacong Luo, and Enhong Chen. 2025. InstrucTime: Advancing Time Series Classification with Multimodal Language Modeling. In Proceedings of the Eighteenth ACM International Conference on Web Search and Data Mining (Hannover, Germany) (WSDM '25). Association for Computing Machinery, New York, NY, USA, 792–800. doi:10.1145/3701551.3703499

[8] Angus Dempster, Daniel F. Schmidt, and Geoffrey I. Webb. 2021. MiniRocket: A Very Fast (Almost) Deterministic Transform for Time Series Classification. In Proceedings of the 27th ACM SIGKDD Conference on Knowledge Discovery & Data Mining (Virtual Event, Singapore) (KDD '21). Association for Computing Machinery, New York, NY, USA, 248–257. doi:10.1145/3447548.3467231

[9] Shao-Qun Dong, Zhao-Hui Zhong, Xue-Hui Cui, Lian-Bo Zeng, Xu Yang, Jian-Jun Liu, Yan-Ming Sun, and Jing-Ru Hao. 2023. A deep kernel method for lithofacies identification using conventional well logs. Petroleum Science 20, 3 (2023), 1411–1428.

[10] Zuochun Fan, Changhao Hu, Shu Jiang, Man Li, Ye Cai, Yue Jiang, Yang Li, and Mei Tian. 2025. Logging-data-driven lithology identification in complex reservoirs: an example from the Nixaintuo block of the Liaohe oilfield. Frontiers in Earth Science 13 (2025), 1491334.

[11] Shanghua Gao, Teddy Koker, Owen Queen, Tom Hartvigsen, Theodoros Tsiligkaridis, and Marinka Zitnik. 2024. Units: A unified multi-task time series model. Advances in Neural Information Processing Systems 37 (2024), 140589–140631.

[12] Yolanda Gil, Mark Greaves, James Hendler, and Haym Hirsh. 2014. Amplify scientific discovery with artificial intelligence. Science 346, 6206 (2014), 171–172.

[13] Mononito Goswami, Konrad Szafer, Arjun Choudhry, Yifu Cai, Shuo Li, and Artur Dubrawski. 2024. MOMENT: a family of open time-series foundation models. In Proceedings of the 41st International Conference on Machine Learning (Vienna, Austria) (ICML '24). JMLR.org, Article 642, 38 pages.

[14] Daya Guo, Dejian Yang, Haowei Zhang, Junxiao Song, Ruoyu Zhang, Runxin Xu, Qihao Zhu, Shirong Ma, Peiyi Wang, Xiao Bi, et al. 2025. Deepseek-r1: Incentivizing reasoning capability in llms via reinforcement learning. arXiv preprint arXiv:2501.12948 (2025).

[15] Brendon Hall. 2016. Facies classification using machine learning. The Leading Edge 35, 10 (2016), 906–909.

[16] Hassan Ismail Fawaz, Benjamin Lucas, Germain Forestier, Charlotte Pelletier, Daniel F Schmidt, Jonathan Weber, Geoffrey I Webb, Lhassane Idoumghar, Pierre-Alain Muller, and François Petitjean. 2020. Inceptiontime: Finding alexnet for time series classification. Data Mining and Knowledge Discovery 34, 6 (2020), 1936–1962.

[17] Shiyi Jiang, Panke Sun, Fengqing Lyu, Sicheng Zhu, Ruifeng Zhou, Bin Li, Taihong He, Yujian Lin, Yining Gao, Wendan Song, et al. 2024. Machine learning (ML) for fluvial lithofacies identification from well logs: A hybrid classification model integrating lithofacies characteristics, logging data distributions, and ML models applicability. Geenergy Science and Engineering 233 (2024), 212587.

[18] Yushan Jiang, Zijie Pan, Xikun Zhang, Sahil Garg, Anderson Schneider, Yuriy Nevmyvaka, and Dongjin Song. 2024. Empowering time series analysis with large language models: a survey. In Proceedings of the Thirty-Third International Joint Conference on Artificial Intelligence (Jeju, Korea) (IJCAI '24). Article 895, 9 pages. doi:10.24963/ijcai.2024/895

[19] Ming Jin, Yifan Zhang, Wei Chen, Kexin Zhang, Yuxuan Liang, Bin Yang, Jindong Wang, Shirui Pan, and Qingsong Wen. 2024. Position: what can large language models tell us about time series analysis. In Proceedings of the 41st International Conference on Machine Learning (Vienna, Austria) (ICML '24). JMLR.org, Article 895, 17 pages.

[20] John Jumper, Richard Evans, Alexander Pritzel, Tim Green, Michael Figurnov, Olaf Ronneberger, Kathryn Tunyasuvandavel, Russ Bates, Augustin Zidek, Anna Potapenko, et al. 2021. Highly accurate protein structure prediction with AlphaFold. nature 596, 7873 (2021), 583–589.

[21] Fazle Karim, Somshubra Majumdar, Houshang Darabi, and Samuel Harford. 2019. Multivariate LSTM-FCNs for time series classification. Neural networks 116 (2019), 237–245.

[22] Anuj Karpatne, Imme Ebert-Uphoff, Sai Ravela, Hassan Ali Babaie, and Vipin Kumar. 2018. Machine learning for the geosciences: Challenges and opportunities. IEEE Transactions on Knowledge and Data Engineering 31, 8 (2018), 1544–1554.

[23] Rohit J Kate. 2016. Using dynamic time warping distances as features for improved time series classification. Data mining and knowledge discovery 30 (2016), 283–312.

[24] Guolin Ke, Qi Meng, Thomas Finley, Taifeng Wang, Wei Chen, Weidong Ma, Qiwei Ye, and Tie-Yan Liu. 2017. LightGBM: a highly efficient gradient boosting decision tree. In Proceedings of the 31st International Conference on Neural Information Processing Systems (Long Beach, California, USA) (NIPS'17). Curran Associates Inc., Red Hook, NY, USA, 3149–3157.

[25] Diederik P Kingma. 2014. Adam: A method for stochastic optimization. arXiv preprint arXiv:1412.6980 (2014).

[26] Landi Kusuma and Alwin Djamaoeddin. 2025. Leveraging Hidden Markov Model with Window Filtering Technique for Unsupervised Facies Detection in Well Logs. In SPE Middle East Oil and Gas Show and Conference. SPE, D03150858006.

[27] Jia-Yu Li, Ji-Zhou Tang, Xian-Zheng Zhao, Bo Fan, Wen-Ya Jiang, Shun-Yao Song, Jian-Bing Li, Kai-Da Chen, and Zheng-Guang Zhao. 2025. A large-scale, high-quality dataset for lithology identification: Construction and applications. Petroleum Science (2025).

[28] Zhi Li, Zhefeng Wang, Zhicheng Wei, Xiangguang Zhou, Yijun Wang, Baoxing Huai, Qi Liu, Nicholas Jing Yuan, Renbin Gong, and Enhong Chen. 2021. Cross-oilfield reservoir classification via multi-scale sensor knowledge transfer. In Proceedings of the AAAI Conference on Artificial Intelligence, Vol. 35. 4215–4223.

[29] Yuxuan Liang, Haomin Wen, Yuqi Nie, Yushan Jiang, Ming Jin, Dongjin Song, Shirui Pan, and Qingsong Wen. 2024. Foundation models for time series analysis: A tutorial and survey. In Proceedings of the 30th ACM SIGKDD conference on knowledge discovery and data mining. 6555–6565.

[30] Jiming Liu and Dongjin Xu. 2025. Logging-data-driven lithology identification of conglomerate reservoir by the assistance of integrated machine learning methods. Scientific Reports (2025).

[31] Jingwei Liu, Ling Yang, Hongyan Li, and Shenda Hong. 2024. Retrieval-augmented diffusion models for time series forecasting. In Proceedings of the 30th International Conference on Neural Information Processing Systems (Vancouver, BC, Canada) (NIPS '24). Curran Associates Inc., Red Hook, NY, USA, Article 91, 21 pages.

[32] Qi Liu, Enhong Chen, Hui Xiong, Chris HQ Ding, and Jian Chen. 2011. Enhancing collaborative filtering by user interest expansion via personalized ranking. IEEE Transactions on Systems, Man, and Cybernetics, Part B (Cybernetics) 42, 1 (2011), 218–233.

[33] Zhege Liu, Junxing Cao, Jiachun You, Shuna Chen, Yujia Lu, and Peng Zhou. 2021. A lithological sequence classification method with well log via SVM-assisted bi-directional GRU-CRF neural network. Journal of Petroleum Science and Engineering 205 (2021), 108913.

[34] Yucong Luo, Yitong Zhou, Mingyue Cheng, Jialiao Wang, Daoyu Wang, Tingyue Pan, and Jintao Zhang. 2025. Time series forecasting as reasoning: A slow-thinking approach with reinforced llms. arXiv preprint arXiv:2506.10630 (2025).

[35] Mahmoud Mohammadi, Yipeng Li, Jane Le, and Wendy Yip. 2025. Evaluation and benchmarking of llm agents: A survey. In Proceedings of the 31st ACM SIGKDD Conference on Knowledge Discovery and Data Mining V.2. 6129–6139.

[36] Philipp Mondorf and Barbara Plank. 2024. Beyond accuracy: evaluating the reasoning behavior of large Language models—A survey. arXiv preprint arXiv:2404.01869 (2024).

[37] Reiichiro Nakano, Jacob Hilton, Suchir Balaji, Jeff Wu, Long Ouyang, Christina Kim, Christopher Hesse, Shantanu Jain, Vineet Kosaraju, William Saunders, et al. 2021. Webgpt: Browser-assisted question-answering with human feedback. arXiv preprint arXiv:2112.09332 (2021).

[38] An Hai Nguyen, Khang Nguyen, and Nga Mai. 2025. Classifying reservoir facies using attention-based residual neural networks. PeerJ Computer Science 11 (2025), e2977.

[39] Qingwei Pang, Chenglizhao Chen, Youzhuang Sun, and Shanchen Pang. 2025. Empowering lithology identification with FreLog: Leveraging frequency domain insights in well logging signal processing. Measurement 246 (2025), 116710.

[40] Gyeong-Tae Park, Jina Jeong, Irina Emelyanova, Marina Pervukhina, Lionel Esteban, and Seong-Taek Yun. 2022. Data-driven sequence labeling methods incorporating the long-range spatial variation of geological data for lithofacies sequence estimation. Journal of Petroleum Science and Engineering 208 (2022), 109345.

[41] Pal Washa Shahzad Rathore, Matloob Hussain, Muhammad Bilal Malik, and Yawar Amin. 2023. Well log analysis and comparison of supervised machine learning algorithms for lithofacies identification in pab formation, lower indus basin. Journal of Applied Geophysics 219 (2023), 105199.

[42] Markus Reichstein, Gustau Camps-Valls, Bjorn Stevens, Martin Jung, Joachim Denzler, Nuno Carvalhais, and F Prabhat. 2019. Deep learning and process understanding for data-driven Earth system science. Nature 566, 7743 (2019), 195–204.

Conference acronym 'XX, June 03–05, 2018, Woodstock, NY

Tao et al.

[43] HAN Ruiyi, WANG Zhuwen, WANG Wenhua, XU Fanghui, QI Xinghua, and CUI Yitong. 2021. Lithology identification of igneous rocks based on XGboost and conventional logging curves, a case study of the eastern depression of Liaohe Basin. Journal of Applied Geophysics 195 (2021), 104480.

[44] Muhammad Ansar Saleem, Ghulam Mohyuddin Sohail, Saif Ur Rehman, Qamar Yasin, and Ahmed E Radwan. 2025. Multiple machine learning algorithms for lithofacies prediction in the deltaic depositional system of the lower Goru Formation, Lower Indus Basin, Pakistan. Scientific Reports 15, 1 (2025), 34933.

[45] Timo Schick, Jane Dwivedi-Yu, Roberto Dessì, Roberta Raileanu, Maria Lomeli, Eric Hambro, Luke Zettlemoyer, Nicola Cancedda, and Thomas Scialom. 2023. Toolformer: Language models can teach themselves to use tools. Advances in Neural Information Processing Systems 36 (2023), 68539–68551.

[46] Michael Schmidt and Hod Lipson. 2009. Distilling free-form natural laws from experimental data. science 324, 5923 (2009), 81–85.

[47] Agnes Schumann. 2002. Hidden Markov models for lithological well log classification. Terra Nostra 4 (2002), 373–378.

[48] Heng Shi, ZhenHao Xu, Peng Lin, and Wen Ma. 2023. Refined lithology identification: Methodology, challenges and prospects. Geoenergy Science and Engineering 231 (2023), 212382.

[49] Mingtian Tan, Mike Merrill, Vinayak Gupta, Tim Althoff, and Tom Hartvigsen. 2024. Are language models actually useful for time series forecasting? Advances in Neural Information Processing Systems 37 (2024), 60162–60191.

[50] Hind Taud and Jean-Francois Mas. 2017. Multilayer perceptron (MLP). In Geomatic approaches for modeling land change scenarios. Springer, 451–455.

[51] Michele Tonutti, Emanuele Ruffaldi, Alessandro Cattaneo, and Carlo Alberto Avizzano. 2019. Robust and subject-independent driving manoeuvre anticipation through domain-adversarial recurrent neural networks. Robotics and Autonomous Systems 115 (2019), 162–173.

[52] Jiahao Wang, Mingyue Cheng, Qingyang Mao, Yitong Zhou, Daoyu Wang, Qi Liu, Feiyang Xu, and Xin Li. 2025. Tabletime: Reformulating time series classification as training-free table understanding with large language models. In Proceedings of the 34th ACM International Conference on Information and Knowledge Management. 3009–3019.

[53] Xuezhi Wang, Jason Wei, Dale Schuurmans, Quoc Le, Ed Chi, Sharan Narang, Aakanksha Chowdhery, and Denny Zhou. 2022. Self-consistency improves chain of thought reasoning in language models. arXiv preprint arXiv:2203.11171 (2022).

[54] Zihao Wang, Shaofei Cai, Guanzhou Chen, Anji Liu, Xiaojian Shawn Ma, and Yitao Liang. 2023. Describe, explain, plan and select: interactive planning with llms enables open-world multi-task agents. Advances in Neural Information Processing Systems 36 (2023), 34153–34189.

[55] Jason Wei, Xuezhi Wang, Dale Schuurmans, Maarten Bosma, Fei Xia, Ed Chi, Quoc V Le, Denny Zhou, et al. 2022. Chain-of-thought prompting elicits reasoning in large language models. Advances in neural information processing systems 35 (2022), 24824–24837.

[56] Xuanzhi Wu and Edo Nyland. 1987. Automated stratigraphic interpretation of well-log data. Geophysics 52, 12 (1987), 1665–1676.

[57] Zhenhao Xu, Zhaoyang Wang, Shucai Li, Xiao Zhang, and Peng Lin. 2024. GeoPredict-LLM: Intelligent tunnel advanced geological prediction by reprogramming large language models. Intelligent Geoengineering 1, 1 (2024), 49–57.

[58] Shunyu Yao, Jeffrey Zhao, Dian Yu, Nan Du, Izhak Shafran, Karthik Narasimhan, and Yuan Cao. 2023. React: Synergizing reasoning and acting in language models. In International Conference on Learning Representations (ICLR).

[59] Weijia Zhang, Chenlong Yin, Hao Liu, and Hui Xiong. 2025. Unleashing the power of pre-trained language models for irregularly sampled time series. In Proceedings of the 31st ACM SIGKDD Conference on Knowledge Discovery and Data Mining V. 2. 3831–3842.

[60] Xiyuan Zhang, Ranak Roy Chowdhury, Rajesh K. Gupta, and Jingbo Shang. 2024. Large language models for time series: a survey. In Proceedings of the Thirty-Third International Joint Conference on Artificial Intelligence (Jeju, Korea) (IJCAI '24). Article 921, 9 pages. doi:10.24963/ijcai.2024/921

[61] Yi Zheng, Qi Liu, Enhong Chen, Yong Ge, and J Leon Zhao. 2014. Time series classification using multi-channels deep convolutional neural networks. In International conference on web-age information management. Springer, 298–310.

[62] Tian Zhou, Peisong Niu, Liang Sun, Rong Jin, et al. 2023. One fits all: Power general time series analysis by pretrained lm. Advances in neural information processing systems 36 (2023), 43322–43355.

GeoDecider: An Evidence-Grounded Agent for Geological Interpretation via Deliberative Reasoning

Conference acronym 'XX, June 03–05, 2018, Woodstock, NY

## Appendix

### A Dataset Specifications and Input Features

To facilitate reproducibility and clarify the inputs used by the GeoDecider framework, we provide the detailed configuration for each benchmark dataset. Table 5 summarizes the specific geophysical logs and features selected as inputs for the model, along with the target interpretation classes.

For the Facies dataset, the 9 classes correspond to specific depositional environments ranging from Nonmarine sandstone to Phylloidalalga bafflestone. The FORCE dataset targets 5 primary lithologies: Shale, Sandstone, Limestone, Marl, and Sandstone/Shale. GeoLink includes 11 granular classes, distinguishing between variations such as Silty Sand, Cross Bedded Sand, and Argillaceous Limestone. Finally, SEAM classifies geological ages and salt bodies, including Mother Salt, Cretaceous, and Lower Miocene layers.

### B Datasets Description

We conduct experiments on four publicly available well-log benchmarks to assess the generalization ability of GeoDecider across different geological environments. These datasets provide depth-wise petrophysical measurements and lithology-related annotations, while varying in reservoir characteristics, sampling intervals, and well availability. All experiments follow the original benchmark settings, and no target-well labels are used during inference.

- SEAM: the SEG Wiki Open Data "Well logs" catalog \( ^{2} \) as an entry point to publicly released well-log resources for reproducible geoscience benchmarking;
- Facies: the Kaggle Well Log Facies Dataset \( ^{3} \) , where our benchmark split uses seven wells from the Council Grove gas reservoir (Kansas) with facies labels derived from core observations;
- FORCE: the Kaggle Well logs dataset for machine learning \( ^{4} \) , released for lithology (rock-type) prediction from multiple geophysical well-log measurements and associated with the FORCE 2020 lithology prediction context;
- GeoLink: the GEOLINK-S2 well-log dataset \( ^{5} \) accessed via the geolink_dataset repository, which provides analysis notebooks and preprocessing code for the GEOLINK-S2 data.

### C Dataset Splits and Leakage Control

All benchmark datasets are partitioned at the well level, so wells used for testing are disjoint from those used for training and validation. Table 6 summarizes the number of wells assigned to each split. Preprocessing statistics, including normalization and imputation values, are estimated from the training wells and then applied to validation and test wells. The routing threshold \(\tau\) is selected on validation wells before test inference. The neighbor retrieval index is built only from labeled training wells, and test-well labels are never exposed to the retrieval tool, Evidence Profile construction, LLM prompts, evidence reconciliation, or geological refinement.

\( ^{2} \) https://wiki.seg.org/wiki/Open_data#Well_logs

\( ^{3} \) https://www.kaggle.com/datasets/imeintanis/well-log-facies-dataset

\( ^{4} \) https://www.kaggle.com/datasets/faresazzam/well-logs-dataset-for-machine-learning

\( ^{5} \) https://github.com/LukasMosser/geolink_dataset?tab=readme-ov-file

### D Baselines

We compare GeoDecider with representative baselines from four categories: traditional machine learning methods, deep time-series classification models, LLM-based approaches, and time-series foundation models. These baselines cover different paradigms ranging from feature-based prediction and neural temporal modeling to large-scale pretrained models, providing a comprehensive evaluation of the proposed evidence-grounded reasoning framework.

- XGBoost: XGBoost is a tree-based gradient boosting method that builds an ensemble of decision trees to optimize a differentiable loss function. It is widely used as a strong traditional machine learning baseline due to its robustness and efficiency on tabular and time-series features.
- nn-DTW: nn-DTW combines nearest-neighbor classification with Dynamic Time Warping distance to handle temporal misalignments between time series. It serves as a classical non-parametric baseline that focuses on shape similarity rather than learned representations.
- GBDT: Gradient Boosting Decision Trees (GBDT) iteratively fits shallow decision trees to the residuals of previous trees to minimize prediction error. Compared with XGBoost, it provides a simpler yet competitive boosting baseline for sequence-level classification on hand-crafted features.
- LSTMFCN: LSTMFCN integrates a Long Short-Term Memory (LSTM) branch with a Fully Convolutional Network (FCN) branch to jointly capture temporal dependencies and local patterns in time series. This architecture has become a common deep learning baseline for multivariate time-series classification tasks.

Table 5: Detailed specification of input features and target classes for the four benchmark datasets. The input features represent the exact channels used by GeoDecider.

|  Dataset | # CIs | Input Features (Curves) | Target  |
| --- | --- | --- | --- |
|  SEAM | 7 | 9 Channels: Depth, Bed Dip (X, Y), Total Porosity, Horizontal Resistivity, TTI Dip (X, Y), P-wave Velocity (\( V_p \)), S-wave Velocity (\( V_s \)) | Layers  |
|  Facies | 9 | 7 Channels: Depth, Gamma Ray (GR), Deep Induction Resistivity (\( \log_{10} \)), Neutron-Density Porosity Diff (\( \Delta\phi \)), Neutron-Density Porosity (PHIND), Photoelectric Effect (PE), Nonmarine-Marine Indicator | Lithofacies  |
|  FORCE | 5 | 9 Channels: Depth, Caliper (CALI), Sonic Slowness (DTC), Gamma Ray (GR), Neutron Porosity (NPHI), Bulk Density (RHOB), Coordinates (X, Y, Z) | Lithology  |
|  GeoLink | 11 | 9 Channels: Depth, Caliper (CALI), Neutron Porosity (NPHI), Bulk Density (RHOB), Gamma Ray (GR), Sonic Slowness (DTC), Resistivity (Deep, Shallow, Medium) | Lithology  |

Conference acronym 'XX, June 03–05, 2018, Woodstock, NY

Tao et al.

Table 6: Well-level split statistics for the benchmark datasets.

|  Statistics | SEAM | Facies | FORCE | GeoLink  |
| --- | --- | --- | --- | --- |
|  # of total wells | 5 | 7 | 11 | 128  |
|  # of wells in training set | 3 | 4 | 4 | 80  |
|  # of wells in validation set | 1 | 1 | 2 | 23  |
|  # of wells in test set | 1 | 2 | 5 | 25  |
|  # of total samples | 7,092 | 3,164 | 52,766 | 580,205  |
|  Sampling interval (m) | 10 | 0.5 | 0.15 | 0.125  |

- MLP: The Multilayer Perceptron (MLP) treats each input segment as a fixed-length feature vector and performs classification through stacked fully-connected layers with nonlinear activations. Despite its simplicity and lack of explicit temporal modeling, it offers a strong baseline when features are informative.
- MiniRocket: MiniRocket applies a fixed set of convolutional kernels to time series and uses simple summary statistics as features, followed by a linear classifier. It is designed to provide very fast and competitive time-series classification with minimal training overhead.
- InceptionTime: InceptionTime is a deep convolutional architecture for time-series classification that uses Inception-style multi-scale convolutional blocks. By capturing patterns at different temporal resolutions, it achieves strong accuracy on a wide range of benchmark datasets.
- InstructTime: InstructTime reformulates time-series classification as an instruction-following task for multimodal language models. It leverages natural-language descriptions of tasks and features to enable flexible, training-free or lightly fine-tuned time-series understanding.
- TableTime: TableTime converts time series into tabular formats and uses large language models' table-understanding capabilities for classification. This approach treats time series as structured tables, enabling training-free inference with generic LLMs.
- GPT4TS: GPT4TS is a time-series analysis framework that adapts pretrained language-model-style architectures to forecasting and classification. It views time series as token sequences and leverages generative pretraining for downstream time-series tasks.
- UniTS: UniTS is a unified multi-task time-series model designed to support tasks such as classification, forecasting, and imputation within a backbone. It serves as a strong foundation model baseline for evaluating specialized methods.
- MOMENT: MOMENT is an open family of time-series foundation models pretrained on large-scale heterogeneous time-series corpora. It provides general-purpose representations

that can be adapted to downstream classification tasks with minimal task-specific tuning.

## E Additional Hyperparameter Analyses

### E.1 Impact of Different LLM Backbones

Table 7 isolates the effect of replacing only the reasoning backbone. We evaluate three LLM backbones: DeepSeek-R1, GPT-5, and Gemini 3 Pro within our framework, while the main results in Table 2 use DeepSeek-R1 as the default backbone. As shown in Table 7, the backbones achieve broadly comparable precision, recall, and weighted F1 on SEAM and Facies, with modest differences. This suggests that performance gains mainly arise from the system-level design rather than the specific LLM backbone, demonstrating that the proposed framework is largely backbone-agnostic and flexible for deployment under different constraints.

### E.2 Effect of Temperature on Model Performance

Figure 7 shows the sensitivity of GeoDecider to the temperature parameter. As the temperature increases, the weighted F1 score improves on the evaluated datasets, peaking at a moderate temperature. This indicates that an appropriate temperature balances exploration and determinism, enhancing multi-perspective evidence integration. However, further increases lead to performance degradation, suggesting that overly stochastic reasoning reduces stability and harms prediction quality. Overall, GeoDecider exhibits sensitivity to temperature, with an optimal range for robust performance.

Table 7: Performance comparison with different base LLMs.

|  Base LLM | SEAM |   |   | Facies  |   |   |
| --- | --- | --- | --- | --- | --- | --- |
|   |  Precision | Recall | F1 | Precision | Recall | F1  |
|  DeepSeek-R1 | 0.8628 | 0.7748 | 0.7803 | 0.4758 | 0.4461 | 0.4481  |
|  GPT-5 | 0.8037 | 0.7633 | 0.7716 | 0.4645 | 0.4284 | 0.4334  |
|  Gemini 3 Pro | 0.8486 | 0.7626 | 0.7841 | 0.4938 | 0.4388 | 0.4476  |

![img-5.jpeg](img-5.jpeg)

Figure 7: Sensitivity analysis of GeoDecider to the temperature parameter of LLMs, evaluated by weighted F1 score.