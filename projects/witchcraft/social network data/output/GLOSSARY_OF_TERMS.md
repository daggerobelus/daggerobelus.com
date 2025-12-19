# Glossary of Social Network Analysis Terms
## For the Lorraine Witchcraft Trials Analysis

---

## Network Basics

### Node (Vertex)
An entity in the network. In this analysis, nodes represent **people** - accused witches, witnesses, or other individuals mentioned in trial records.

### Edge (Tie, Link)
A connection between two nodes. In this analysis, edges represent **relationships** like "testified against," "married to," or "appeared as co-witness."

### Directed vs Undirected Edges
- **Directed**: The relationship has a direction (A → B). Example: "Jean testified against Marie" - Jean is the source, Marie is the target.
- **Undirected**: The relationship is mutual (A — B). Example: "Jean and Marie are married."

### Multi-layer Network
A network with different *types* of edges. Our network has testimony edges, kinship edges, co-witness edges, etc. - each representing a different kind of social relationship.

---

## Centrality Measures

Centrality measures identify the most "important" nodes. Different measures capture different notions of importance.

### Degree
**What it is**: The number of connections a node has.

**Interpretation**: High degree = many connections. In our analysis, someone with degree 50 appeared in relationships with 50 other people.

**Example**: If Catherine testified against 30 people and was mentioned as a co-witness with 20 others, her degree could be ~50.

### Betweenness Centrality
**What it is**: How often a node lies on the shortest path between other pairs of nodes.

**Interpretation**: High betweenness = "bridge" or "gatekeeper" position. These individuals connect otherwise disconnected parts of the network.

**Why it matters**: In our analysis, high betweenness was **protective** against accusation (OR=0.5x). Bridge figures who connected distant communities seemed to have social capital that shielded them.

**Example**: A traveling merchant who knows people in multiple villages would have high betweenness - they're the "bridge" between communities.

### Closeness Centrality
**What it is**: The average shortest path distance from a node to all other nodes.

**Interpretation**: High closeness = can reach everyone quickly. These nodes are "close" to the center of the network.

**Example**: A village mayor who knows everyone would have high closeness.

### Eigenvector Centrality
**What it is**: A node's importance based on being connected to other important nodes.

**Interpretation**: It's not just how many connections you have, but *who* you're connected to. Being connected to well-connected people makes you important.

**Example**: Knowing the local lord matters more than knowing 10 peasants.

### PageRank
**What it is**: Google's algorithm for ranking web pages, adapted for social networks. Similar to eigenvector centrality but handles directed networks better.

**Interpretation**: Importance flows through the network - being "pointed to" by important nodes makes you important.

---

## Structural Measures

### Clustering Coefficient
**What it is**: The proportion of a node's neighbors who are also connected to each other.

**Interpretation**: High clustering = your friends know each other. You're embedded in a tight-knit group where everyone knows everyone.

**Why it matters**: In our analysis, high clustering dramatically **increased** accusation risk (OR=6.4x). Being embedded in tight local networks made individuals vulnerable.

**Example**:
- Low clustering: You know people from different villages who don't know each other
- High clustering: Everyone you know also knows each other (small village dynamics)

### Brokerage / Structural Holes
**What it is**: A "structural hole" exists when two of your contacts don't know each other. "Brokerage score" measures how many such holes you span.

**Interpretation**: High brokerage = you connect people who otherwise wouldn't be connected. You have access to diverse, non-redundant information.

**Why it matters**: In our analysis, high brokerage **increased** accusation risk (OR=4.1x). This seems counterintuitive but may reflect that brokers were visible/exposed figures.

**Example**: A midwife who serves multiple villages and knows people from each - she bridges structural holes between communities.

### Constraint
**What it is**: The opposite of brokerage. High constraint means your contacts are all interconnected, leaving you little room to maneuver.

**Interpretation**: High constraint = you're "trapped" in a dense network where your contacts all know each other. Low freedom, high surveillance.

---

## Network Structure Terms

### Connected Component
**What it is**: A group of nodes where you can reach any node from any other node by following edges.

**Example**: If the network has two isolated villages with no connections between them, there are two components.

**In our analysis**: 42.7% of nodes are in the largest connected component - meaning most of the network is interconnected.

### Network Density
**What it is**: The ratio of actual edges to possible edges.

**Formula**: Density = (actual edges) / (possible edges)

**Interpretation**:
- Density = 1.0: Everyone is connected to everyone (complete graph)
- Density = 0.0001: Very sparse network (few connections relative to size)

**Our network**: Density ≈ 0.0003 (very sparse - typical for large social networks)

### Giant Component
**What it is**: The largest connected component in the network. In social networks, there's typically one very large component and many tiny isolated ones.

---

## Statistical Terms

### Odds Ratio (OR)
**What it is**: How much more (or less) likely an outcome is given a predictor, relative to the baseline.

**Interpretation**:
- OR = 1.0: No effect
- OR = 2.0: Twice as likely
- OR = 0.5: Half as likely
- OR = 6.4: 6.4 times more likely

**Example**: OR=6.4 for clustering coefficient means someone with high clustering was 6.4x more likely to be accused than someone with low clustering.

### AUC (Area Under the Curve)
**What it is**: A measure of how well a classification model distinguishes between classes. Ranges from 0.5 (random guessing) to 1.0 (perfect prediction).

**Interpretation**:
- AUC = 0.5: Model is no better than chance
- AUC = 0.7-0.8: Acceptable discrimination
- AUC = 0.8-0.9: Excellent discrimination
- AUC = 0.9+: Outstanding discrimination

**Our model**: AUC = 0.917 means the model is excellent at distinguishing who was accused from who wasn't.

### Cross-Validation (CV)
**What it is**: A technique to test how well a model generalizes. The data is split into "folds" - the model trains on some folds and tests on others, rotating through all possibilities.

**Why it matters**: Prevents overfitting (memorizing the data rather than learning patterns). Our 5-fold CV means we did 5 train/test splits.

### Confidence Interval (CI)
**What it is**: A range of values that likely contains the true value. A 95% CI means we're 95% confident the true value falls within this range.

**Example**: "Rank 1 (95% CI: 1-3)" means the node ranked #1, and we're 95% confident its true rank is between 1 and 3.

### Bootstrap
**What it is**: A resampling technique. We randomly resample the data many times (with replacement) to estimate the variability of a statistic.

**In our analysis**: We bootstrapped centrality rankings 30 times to see how stable the rankings are.

---

## Temporal/Contagion Terms

### Cascade
**What it is**: A spreading process through a network, like a rumor or disease. In our simulation, we modeled how accusations might have spread.

**Parameters**:
- **Seed nodes**: Where the cascade starts
- **Transmission probability**: Chance of spreading to a neighbor
- **Cascade size**: How many nodes eventually get "infected"

### Contagion Model
**What it is**: A model treating accusations like an infectious disease - if your neighbor is accused, you might be "infected" and become accused too.

**Our finding**: Accusations did NOT spread like a simple contagion. The negative correlation (-0.17) between exposure and accusation means being near accused people actually made you *less* likely to be accused.

### Superspreader
**What it is**: A node that could spread a contagion to many others due to their network position. High degree + high-degree neighbors = high spreading potential.

---

## Graph File Formats

### GraphML
**What it is**: An XML-based file format for storing network data. Can be opened in visualization software like Gephi, Cytoscape, or yEd.

**Our files**: `full_network.graphml` contains the complete network with all node and edge attributes.

---

## Model Types

### Logistic Regression
**What it is**: A statistical model for predicting binary outcomes (yes/no, accused/not accused). Outputs the probability of an outcome based on predictor variables.

**Coefficients**: Tell you how much each predictor increases or decreases the log-odds of the outcome.

### ERGM (Exponential Random Graph Model)
**What it is**: A sophisticated network model that tests hypotheses about *why* ties form. Unlike standard regression, ERGM accounts for network dependencies (e.g., if A→B and B→C, is A→C more likely?).

**Terms tested**:
- **Reciprocity**: Do accusations go both ways?
- **Homophily**: Do similar people accuse each other?
- **Triadic closure**: Do accusation triangles form?

---

## Historical Context Terms

### Super-Witness
**What it is**: An individual who testified in 3 or more different witch trials. These were likely **professional witnesses** or **local officials** who repeatedly participated in prosecutions.

**Our finding**: 245 super-witnesses, mostly protected from becoming accused themselves (only 1.6% transition rate).

### Witness-to-Accused Transition
**What it is**: When someone who testified as a witness in one trial later becomes the accused in another trial.

**Our finding**: Only 9 people made this transition, and 7 were executed. This was a rare but deadly pattern.

---

## Quick Reference: Key Findings in Plain Language

| Technical Finding | Plain Language |
|-------------------|----------------|
| High clustering → high accusation risk (OR=6.4) | People embedded in tight-knit communities where everyone knew everyone were much more likely to be accused |
| High betweenness → low risk (OR=0.5) | People who bridged different communities were protected from accusation |
| Negative exposure-accusation correlation | Being neighbors with accused people did NOT increase your risk - accusations didn't spread like a disease |
| AUC = 0.917 | The model correctly identifies who was accused 91.7% of the time |
| 245 super-witnesses | A small group of repeat witnesses shaped many prosecutions |

---

*This glossary accompanies the Lorraine Witchcraft Trials Social Network Analysis*
