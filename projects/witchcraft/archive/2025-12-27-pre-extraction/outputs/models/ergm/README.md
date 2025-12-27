# ERGM Analysis for Lorraine Witchcraft Trials

## Files
- `node_attributes.csv`: Node-level attributes (gender, accused/witness status)
- `testimony_edges.csv`: Edge list of TESTIFIED_AGAINST relationships
- `adjacency_matrix.csv`: Binary adjacency matrix
- `node_order.json`: Node names corresponding to matrix rows/columns
- `run_ergm.R`: R script for ERGM analysis

## Running the Analysis

### Prerequisites
1. Install R (https://cran.r-project.org/)
2. Install required R packages:
   ```R
   install.packages(c("ergm", "network", "statnet"))
   ```

### Execution
1. Open R or RStudio
2. Set working directory to the sna_pipeline folder
3. Run the script:
   ```R
   source("output/models/ergm/run_ergm.R")
   ```

### Interpretation
The ERGM models test the following hypotheses:

1. **Reciprocity**: Do witnesses testify against people who testified against them?
   - Positive `mutual` coefficient = reciprocal accusation patterns

2. **Gender Homophily**: Do same-gender individuals accuse each other more often?
   - Positive `nodematch.gender_female` = women accuse women more

3. **Gender Sender Effects**: Are certain genders more likely to testify?
   - `nodeofactor.gender_female` = women's propensity to be witnesses

4. **Gender Receiver Effects**: Are certain genders more likely to be accused?
   - `nodeifactor.gender_female` = women's propensity to be accused

5. **Triadic Closure (GWESP)**: Do accusation chains form triangles?
   - Positive GWESP = if A accuses B and B accuses C, A more likely to accuse C

6. **Two-Paths (GWDSP)**: Do accusations flow through intermediaries?
   - Positive GWDSP = indirect accusation paths are common
